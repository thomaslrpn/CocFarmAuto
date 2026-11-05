//! Gestion du moteur d'analyse (backend Python) depuis l'application de bureau.
//!
//! Au démarrage :
//!   1. on choisit un port libre sur 127.0.0.1 et on génère un jeton aléatoire ;
//!   2. on lance le moteur (sans fenêtre de console) en lui passant le port, le jeton
//!      (variable d'environnement) et notre PID (il s'arrête si nous disparaissons) ;
//!   3. le dashboard récupère adresse + jeton via la commande `backend_config`.
//! À la fermeture : demande d'arrêt propre (POST /api/shutdown), puis arrêt forcé
//! si le moteur n'a pas terminé dans le délai.
//!
//! Moteur utilisé :
//!   - en développement (`npm run dev`) : `python -m app.main` du venv de backend/ ;
//!   - dans l'application installée : `backend\backend.exe` (construit par PyInstaller).

use std::io::{Read, Write};
use std::net::{SocketAddr, TcpListener, TcpStream};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::time::{Duration, Instant};

use serde::Serialize;
use tauri::{AppHandle, Manager};

const HOST: &str = "127.0.0.1";
/// Délai laissé au moteur pour s'arrêter proprement (fin du cycle d'observation, base fermée).
const GRACEFUL_STOP: Duration = Duration::from_secs(8);

/// Ce que le dashboard reçoit pour se connecter.
#[derive(Clone, Serialize)]
pub struct BackendConfig {
    pub url: String,
    pub token: String,
}

/// État partagé : configuration (ou erreur de lancement) et processus du moteur.
pub struct Backend {
    config: Result<BackendConfig, String>,
    child: Mutex<Option<Child>>,
}

impl Backend {
    /// Lance le moteur. Une erreur ne bloque pas l'application : elle sera affichée
    /// dans la fenêtre (via `backend_config`) plutôt que de la faire planter.
    pub fn start(app: &AppHandle) -> Self {
        match spawn(app) {
            Ok((config, child)) => Backend { config: Ok(config), child: Mutex::new(Some(child)) },
            Err(err) => {
                eprintln!("[moteur] lancement impossible : {err}");
                Backend { config: Err(err), child: Mutex::new(None) }
            }
        }
    }

    pub fn config(&self) -> Result<BackendConfig, String> {
        self.config.clone()
    }

    /// Arrêt propre, puis forcé si nécessaire. Appelé à la fermeture de l'application.
    pub fn stop(&self) {
        let Some(mut child) = self.child.lock().ok().and_then(|mut guard| guard.take()) else {
            return;
        };
        if let Ok(config) = &self.config {
            if let Err(err) = request_shutdown(config) {
                eprintln!("[moteur] demande d'arrêt échouée : {err}");
            }
        }
        let deadline = Instant::now() + GRACEFUL_STOP;
        while Instant::now() < deadline {
            match child.try_wait() {
                Ok(Some(_)) => return, // arrêté proprement
                Ok(None) => std::thread::sleep(Duration::from_millis(100)),
                Err(_) => break,
            }
        }
        eprintln!("[moteur] pas d'arrêt dans le délai : arrêt forcé");
        let _ = child.kill();
        let _ = child.wait();
    }
}

/// Commande appelée par le dashboard : `invoke("backend_config")`.
#[tauri::command]
pub fn backend_config(state: tauri::State<'_, Backend>) -> Result<BackendConfig, String> {
    state.config()
}

/// Appelée par le dashboard juste avant d'installer une mise à jour : l'installateur
/// remplace `backend.exe`, qui ne doit donc plus tourner. L'installation quitte
/// l'application sans passer par la fermeture normale : on enregistre aussi la fenêtre ici.
/// `async` : exécutée hors du fil de l'interface (l'arrêt peut prendre quelques secondes).
#[tauri::command]
pub async fn prepare_update(app: AppHandle) -> Result<(), String> {
    use tauri_plugin_window_state::{AppHandleExt, StateFlags};
    let _ = app.save_window_state(StateFlags::all());
    app.state::<Backend>().stop();
    Ok(())
}

fn spawn(app: &AppHandle) -> Result<(BackendConfig, Child), String> {
    let port = free_port().map_err(|e| format!("aucun port local disponible : {e}"))?;
    let token = random_token()?;
    let (program, base_args, workdir) = backend_command(app)?;

    let mut command = Command::new(&program);
    command
        .args(base_args)
        .args(["--port", &port.to_string(), "--parent-pid", &std::process::id().to_string()])
        .current_dir(&workdir)
        .env("COC_AUTOFARM_TOKEN", &token)
        // Sortie standard = canal d'événements (alertes), lue par events.rs : en UTF-8, sans tampon.
        .env("PYTHONIOENCODING", "utf-8")
        .env("PYTHONUNBUFFERED", "1")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null()); // le moteur écrit ses journaux dans %LOCALAPPDATA%\CoCAutoFarm\logs
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000; // pas de console noire
        command.creation_flags(CREATE_NO_WINDOW);
    }
    let mut child = command
        .spawn()
        .map_err(|e| format!("impossible de lancer {} : {e}", program.display()))?;
    if let Some(stdout) = child.stdout.take() {
        let app = app.clone();
        std::thread::spawn(move || crate::events::forward(app, stdout));
    }
    Ok((BackendConfig { url: format!("http://{HOST}:{port}"), token }, child))
}

/// Programme, arguments et dossier de travail du moteur selon le mode.
fn backend_command(app: &AppHandle) -> Result<(PathBuf, Vec<String>, PathBuf), String> {
    if cfg!(debug_assertions) {
        // Développement : le code Python du dépôt, avec son environnement virtuel.
        let backend_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("..").join("..").join("backend");
        let python = backend_dir.join(".venv").join("Scripts").join("python.exe");
        if !python.exists() {
            return Err(format!("Python du projet introuvable : {}", python.display()));
        }
        return Ok((python, vec!["-m".into(), "app.main".into()], backend_dir));
    }
    // Application installée : backend.exe livré dans les ressources.
    let dir = app
        .path()
        .resource_dir()
        .map_err(|e| format!("dossier de l'application introuvable : {e}"))?
        .join("backend");
    let exe = dir.join("backend.exe");
    if !exe.exists() {
        return Err(format!("moteur introuvable : {} (installation incomplète ?)", exe.display()));
    }
    Ok((exe, Vec::new(), dir))
}

/// Port libre : on demande au système un port (0 = « n'importe lequel »), puis on le libère.
fn free_port() -> std::io::Result<u16> {
    Ok(TcpListener::bind((HOST, 0))?.local_addr()?.port())
}

/// Jeton de 32 octets aléatoires (générateur cryptographique du système), en hexadécimal.
fn random_token() -> Result<String, String> {
    let mut bytes = [0u8; 32];
    getrandom::fill(&mut bytes).map_err(|e| format!("générateur aléatoire indisponible : {e}"))?;
    Ok(bytes.iter().map(|b| format!("{b:02x}")).collect())
}

/// POST /api/shutdown en HTTP minimal (pas besoin d'une bibliothèque HTTP pour une requête).
fn request_shutdown(config: &BackendConfig) -> std::io::Result<()> {
    let host_port = config.url.trim_start_matches("http://");
    let addr: SocketAddr = host_port
        .parse()
        .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidInput, format!("{e}")))?;
    let mut stream = TcpStream::connect_timeout(&addr, Duration::from_secs(1))?;
    stream.set_read_timeout(Some(Duration::from_secs(2)))?;
    write!(
        stream,
        "POST /api/shutdown HTTP/1.1\r\nHost: {host_port}\r\nAuthorization: Bearer {}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n",
        config.token
    )?;
    let mut response = [0u8; 64];
    let _ = stream.read(&mut response); // on attend juste l'accusé de réception
    Ok(())
}
