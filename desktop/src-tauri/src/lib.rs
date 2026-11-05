//! Application de bureau CoC AutoFarm (Tauri 2).
//!
//! Étape 7.1 : une fenêtre qui affiche le dashboard React compilé.
//! Étape 7.2 : lancement / arrêt du moteur Python embarqué (sidecar).

pub fn run() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("erreur au lancement de CoC AutoFarm");
}
