// En version finale, pas de fenêtre de console noire derrière l'application.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    coc_autofarm_lib::run()
}
