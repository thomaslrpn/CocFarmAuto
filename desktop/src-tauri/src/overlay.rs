//! Mini-fenêtre « toujours au-dessus » : score, butin et recommandation du dernier
//! village, affichés par-dessus le jeu (page React dédiée, voir frontend OverlayPage).
//!
//! Elle ne fait qu'afficher : aucune interaction avec la fenêtre du jeu.
//! Sa position et sa taille sont mémorisées comme celles de la fenêtre principale
//! (plugin window-state).

use tauri::{AppHandle, Manager, WebviewUrl, WebviewWindowBuilder};

pub const LABEL: &str = "overlay";

/// `invoke("toggle_overlay")` : ouvre la mini-fenêtre, ou la ferme si elle est ouverte.
/// Renvoie `true` si elle est maintenant ouverte.
#[tauri::command]
pub async fn toggle_overlay(app: AppHandle) -> Result<bool, String> {
    if let Some(window) = app.get_webview_window(LABEL) {
        window.close().map_err(|e| e.to_string())?;
        return Ok(false);
    }
    WebviewWindowBuilder::new(&app, LABEL, WebviewUrl::default())
        .title("CoC AutoFarm")
        .inner_size(330.0, 400.0)
        .min_inner_size(280.0, 240.0)
        .always_on_top(true)
        .skip_taskbar(true)
        .background_color(tauri::window::Color(13, 13, 13, 255))
        .build()
        .map_err(|e| e.to_string())?;
    Ok(true)
}

/// `invoke("overlay_open")` : la mini-fenêtre est-elle ouverte ?
#[tauri::command]
pub fn overlay_open(app: AppHandle) -> bool {
    app.get_webview_window(LABEL).is_some()
}
