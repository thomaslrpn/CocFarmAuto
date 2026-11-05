//! Vérification des mises à jour selon le canal choisi dans les Paramètres.
//!
//! Le plugin updater ne connaît qu'une adresse fixe (tauri.conf.json). Cette commande
//! fait la même vérification, mais vers le `latest.json` du canal demandé :
//!   - stable : dernière release GitHub (GitHub ignore les pre-releases) ;
//!   - beta   : release technique `updater-beta`, mise à jour à chaque publication
//!              (stable ou bêta) par desktop/scripts/release.ps1.
//!
//! La réponse a exactement la forme de celle du plugin : le dashboard en fait un objet
//! `Update` et utilise ensuite les commandes du plugin (téléchargement, signature
//! vérifiée, installation) sans rien changer.

use std::time::Duration;

use serde::{Deserialize, Serialize};
use tauri::{Manager, Url, Webview};
use tauri_plugin_updater::UpdaterExt;

const RELEASES: &str = "https://github.com/thomaslrpn/CocFarmAuto/releases";
const CHECK_TIMEOUT: Duration = Duration::from_secs(30);

#[derive(Debug, Clone, Copy, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Channel {
    Stable,
    Beta,
}

impl Channel {
    pub fn endpoint(self) -> String {
        match self {
            Channel::Stable => format!("{RELEASES}/latest/download/latest.json"),
            Channel::Beta => format!("{RELEASES}/download/updater-beta/latest.json"),
        }
    }
}

/// Même structure que les métadonnées renvoyées par le plugin (`check`).
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateMetadata {
    rid: tauri::ResourceId,
    current_version: String,
    version: String,
    date: Option<String>,
    body: Option<String>,
    raw_json: serde_json::Value,
}

/// `invoke("check_update", { channel: "stable" | "beta" })` : `null` si l'application est à jour.
#[tauri::command]
pub async fn check_update(webview: Webview, channel: Channel) -> Result<Option<UpdateMetadata>, String> {
    let endpoint = Url::parse(&channel.endpoint()).map_err(|e| e.to_string())?;
    let updater = webview
        .updater_builder()
        .endpoints(vec![endpoint])
        .map_err(|e| e.to_string())?
        .timeout(CHECK_TIMEOUT)
        .build()
        .map_err(|e| e.to_string())?;

    let Some(update) = updater.check().await.map_err(|e| e.to_string())? else {
        return Ok(None);
    };
    let date = update.raw_json.get("pub_date").and_then(|d| d.as_str()).map(String::from);
    Ok(Some(UpdateMetadata {
        current_version: update.current_version.clone(),
        version: update.version.clone(),
        date,
        body: update.body.clone(),
        raw_json: update.raw_json.clone(),
        // L'objet reste côté Rust ; le dashboard le désigne par cet identifiant.
        rid: webview.resources_table().add(update),
    }))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn endpoints_par_canal() {
        assert!(Channel::Stable.endpoint().ends_with("/releases/latest/download/latest.json"));
        assert!(Channel::Beta.endpoint().ends_with("/releases/download/updater-beta/latest.json"));
        assert!(Url::parse(&Channel::Beta.endpoint()).is_ok());
    }

    #[test]
    fn canal_lu_depuis_le_dashboard() {
        let channel: Channel = serde_json::from_str("\"beta\"").unwrap();
        assert!(matches!(channel, Channel::Beta));
        assert!(serde_json::from_str::<Channel>("\"nightly\"").is_err());
    }
}
