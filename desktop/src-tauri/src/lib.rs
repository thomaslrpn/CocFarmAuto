//! Application de bureau CoC AutoFarm (Tauri 2).
//!
//! - Affiche le dashboard React compilé.
//! - Démarre le moteur d'analyse au lancement et l'arrête à la fermeture (voir backend.rs).

mod backend;

use backend::Backend;
use tauri::{Manager, RunEvent};

pub fn run() {
    let app = tauri::Builder::default()
        .setup(|app| {
            // Le moteur démarre pendant que la fenêtre s'ouvre ; le dashboard affiche
            // « Démarrage du moteur… » jusqu'à ce qu'il réponde.
            let backend = Backend::start(app.handle());
            app.manage(backend);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![backend::backend_config])
        .build(tauri::generate_context!())
        .expect("erreur au lancement de CoC AutoFarm");

    app.run(|handle, event| {
        // Fermeture de l'application : arrêt propre du moteur (une seule fois).
        if let RunEvent::Exit = event {
            handle.state::<Backend>().stop();
        }
    });
}
