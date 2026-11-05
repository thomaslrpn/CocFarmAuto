//! Événements envoyés par le moteur sur sa sortie standard (voir backend/app/alerts.py).
//!
//! Le moteur écrit une ligne `COCAF-EVENT {json}` quand un village mérite une alerte ;
//! on lit sa sortie en continu (sinon il pourrait se bloquer quand le tampon est
//! plein) et on affiche une notification Windows pour chaque alerte. Les autres
//! lignes (messages de démarrage...) sont ignorées : les journaux sont dans
//! %LOCALAPPDATA%\CoCAutoFarm\logs.
//!
//! La notification est silencieuse : le son est joué par le moteur (réglage séparé).

use std::io::{BufRead, BufReader, Read};

use serde::Deserialize;
use tauri::AppHandle;
use tauri_plugin_notification::NotificationExt;

const EVENT_PREFIX: &str = "COCAF-EVENT ";

#[derive(Debug, Deserialize, PartialEq)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum EngineEvent {
    VillageAlert {
        score: u32,
        recommendation: String,
        gold: u64,
        elixir: u64,
        dark_elixir: u64,
    },
}

/// Lit la sortie du moteur jusqu'à sa fermeture (à lancer dans un fil dédié).
/// Une ligne mal encodée est décodée au mieux, jamais bloquante : on lit toujours la suite.
pub fn forward(app: AppHandle, output: impl Read) {
    let mut reader = BufReader::new(output);
    let mut buffer = Vec::new();
    loop {
        buffer.clear();
        match reader.read_until(b'\n', &mut buffer) {
            Ok(0) | Err(_) => break, // moteur arrêté
            Ok(_) => {
                if let Some(event) = parse(&String::from_utf8_lossy(&buffer)) {
                    notify(&app, &event);
                }
            }
        }
    }
}

pub fn parse(line: &str) -> Option<EngineEvent> {
    let json = line.trim_end().strip_prefix(EVENT_PREFIX)?;
    match serde_json::from_str(json) {
        Ok(event) => Some(event),
        Err(err) => {
            eprintln!("[moteur] événement illisible ({err}) : {json}");
            None
        }
    }
}

/// Titre et texte de la notification.
pub fn message(event: &EngineEvent) -> (String, String) {
    match event {
        EngineEvent::VillageAlert { score, recommendation, gold, elixir, dark_elixir } => (
            format!("Village {recommendation} : {score}/100"),
            format!(
                "Or {} · Élixir {} · Élixir noir {}",
                thousands(*gold),
                thousands(*elixir),
                thousands(*dark_elixir)
            ),
        ),
    }
}

fn notify(app: &AppHandle, event: &EngineEvent) {
    let (title, body) = message(event);
    if let Err(err) = app.notification().builder().title(title).body(body).show() {
        eprintln!("[moteur] notification impossible : {err}");
    }
}

/// 1234567 -> « 1 234 567 » (espace insécable fine, comme dans le dashboard).
fn thousands(value: u64) -> String {
    let digits = value.to_string();
    let mut out = String::new();
    for (i, c) in digits.chars().enumerate() {
        if i > 0 && (digits.len() - i) % 3 == 0 {
            out.push('\u{202f}');
        }
        out.push(c);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    const LINE: &str = r#"COCAF-EVENT {"type": "village_alert", "village_id": 7, "score": 91, "recommendation": "très intéressant", "gold": 650000, "elixir": 720000, "dark_elixir": 5000}"#;

    #[test]
    fn lit_une_alerte_du_moteur() {
        let event = parse(LINE).expect("événement reconnu");
        let (title, body) = message(&event);
        assert_eq!(title, "Village très intéressant : 91/100");
        assert_eq!(body, "Or 650\u{202f}000 · Élixir 720\u{202f}000 · Élixir noir 5\u{202f}000");
    }

    #[test]
    fn ignore_les_autres_lignes() {
        assert!(parse("Dashboard : http://localhost:5173/?token=x").is_none());
        assert!(parse("COCAF-EVENT {pas du json").is_none());
        assert!(parse(r#"COCAF-EVENT {"type": "inconnu"}"#).is_none());
    }

    #[test]
    fn separateur_de_milliers() {
        assert_eq!(thousands(0), "0");
        assert_eq!(thousands(999), "999");
        assert_eq!(thousands(1_234_567), "1\u{202f}234\u{202f}567");
    }
}
