//! Application de bureau CoC AutoFarm (Tauri 2).
//!
//! - Affiche le dashboard React compilé.
//! - Démarre le moteur d'analyse au lancement et l'arrête à la fermeture (voir backend.rs).
//! - Une seule instance à la fois ; la taille et la position de la fenêtre sont mémorisées.
//! - Mises à jour automatiques signées (le dashboard pilote le plugin updater).

mod backend;

use backend::Backend;
use tauri::{AppHandle, Manager, RunEvent};

/// Remet la fenêtre principale au premier plan (appelé quand on relance l'application).
fn focus_main_window(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
    }
}

pub fn run() {
    let app = tauri::Builder::default()
        // Doit être enregistré en premier : une 2e instance s'arrête ici, avant de lancer
        // un 2e moteur sur la même base de données, et réveille la fenêtre existante.
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            focus_main_window(app);
        }))
        // Sauvegarde la géométrie de la fenêtre à la fermeture et la restaure au lancement
        // (fichier .window-state.json dans le dossier de configuration de l'application).
        .plugin(tauri_plugin_window_state::Builder::default().build())
        // Mises à jour : vérification, téléchargement et installation (signatures vérifiées
        // avec la clé publique de tauri.conf.json), puis redémarrage.
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            // Le moteur démarre pendant que la fenêtre s'ouvre ; le dashboard affiche
            // « Démarrage du moteur… » jusqu'à ce qu'il réponde.
            let backend = Backend::start(app.handle());
            app.manage(backend);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            backend::backend_config,
            backend::prepare_update
        ])
        .build(tauri::generate_context!())
        .expect("erreur au lancement de CoC AutoFarm");

    app.run(|handle, event| {
        // Fermeture de l'application : arrêt propre du moteur (une seule fois).
        if let RunEvent::Exit = event {
            handle.state::<Backend>().stop();
        }
    });
}
