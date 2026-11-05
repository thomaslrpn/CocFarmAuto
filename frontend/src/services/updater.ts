/**
 * Mises à jour de l'application de bureau (plugin Tauri « updater »).
 *
 * Le plugin lit `latest.json` sur GitHub Releases, compare avec la version installée,
 * télécharge l'installateur et vérifie sa signature avec la clé publique embarquée
 * (tauri.conf.json) : un fichier non signé par nous est refusé.
 *
 * Ordre d'installation (le plus sûr d'abord) :
 *   1. téléchargement (rien n'est modifié si ça échoue) ;
 *   2. sauvegarde de la base de données ;
 *   3. arrêt du moteur (l'installateur remplace backend.exe) ;
 *   4. installation : Windows ferme l'application, installe, puis la relance.
 */
import { invoke } from "@tauri-apps/api/core";
import { relaunch } from "@tauri-apps/plugin-process";
import { Update, type DownloadEvent } from "@tauri-apps/plugin-updater";
import type { UpdateChannel } from "../types/api";
import { api } from "./api";

export type { Update };

/** Métadonnées renvoyées par la commande Rust `check_update` (même forme que le plugin). */
type UpdateMetadata = ConstructorParameters<typeof Update>[0];

export interface DownloadProgress {
  downloaded: number;
  total?: number; // inconnu si le serveur ne donne pas la taille
}

export type InstallStep = "download" | "backup" | "stop-engine" | "install";

/**
 * Cherche une version plus récente sur le canal choisi. `null` = l'application est à jour.
 * La vérification est faite côté Rust (src-tauri/src/updates.rs), qui choisit le
 * `latest.json` du canal ; la suite (téléchargement, signature, installation) reste
 * celle du plugin.
 */
export async function checkForUpdate(channel: UpdateChannel): Promise<Update | null> {
  const metadata = await invoke<UpdateMetadata | null>("check_update", { channel });
  return metadata ? new Update(metadata) : null;
}

/**
 * Installe la mise à jour. Ne revient normalement pas : l'application est fermée
 * par l'installateur. Une erreur est levée avec l'étape qui a échoué.
 */
export async function installUpdate(
  update: Update,
  onStep: (step: InstallStep) => void,
  onProgress: (progress: DownloadProgress) => void,
): Promise<void> {
  onStep("download");
  const progress: DownloadProgress = { downloaded: 0 };
  await update.download((event: DownloadEvent) => {
    if (event.event === "Started") progress.total = event.data.contentLength;
    if (event.event === "Progress") progress.downloaded += event.data.chunkLength;
    onProgress({ ...progress });
  });

  onStep("backup");
  await api.backupDatabase(`avant-maj-${update.version}`);

  onStep("stop-engine");
  await invoke("prepare_update");

  onStep("install");
  await update.install();
  await relaunch(); // si l'installateur n'a pas déjà relancé l'application
}

/** Relance l'application (récupération si l'installation a échoué après l'arrêt du moteur). */
export function restartApp(): Promise<void> {
  return relaunch();
}

/** Message compréhensible pour une erreur du plugin (en anglais, technique). */
export function describeUpdateError(err: unknown): string {
  const raw = err instanceof Error ? err.message : String(err);
  if (/valid release JSON|404/i.test(raw)) return "Aucune version publiée pour l'instant.";
  if (/signature/i.test(raw)) return "Signature invalide : la mise à jour a été refusée par sécurité.";
  if (/network|connect|dns|timed? ?out|request/i.test(raw)) return "Impossible de joindre le serveur de mises à jour (connexion internet ?).";
  return raw;
}
