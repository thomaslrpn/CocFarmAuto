/**
 * Intégration avec l'application de bureau (Tauri).
 *
 * Dans l'application, le moteur est lancé automatiquement sur un port libre avec un
 * jeton aléatoire : on les demande à la fenêtre (commande Rust `backend_config`).
 * Dans un navigateur (développement), ce module n'est pas utilisé.
 */
import { invoke } from "@tauri-apps/api/core";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { setApiUrl } from "./api";
import { setToken } from "./auth";

interface DesktopBackendConfig {
  url: string;
  token: string;
}

/** Vrai quand la page tourne dans la fenêtre de l'application de bureau. */
export function isDesktopApp(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

/**
 * Récupère l'adresse et le jeton du moteur lancé par l'application.
 * Rejette avec le message d'erreur du lancement (ex. moteur introuvable).
 */
export async function connectDesktopBackend(): Promise<void> {
  const config = await invoke<DesktopBackendConfig>("backend_config");
  setApiUrl(config.url);
  setToken(config.token);
}

/** Vrai dans la mini-fenêtre « toujours au-dessus » (fenêtre Tauri « overlay »). */
export function isOverlayWindow(): boolean {
  if (!isDesktopApp()) return false;
  try {
    return getCurrentWindow().label === "overlay";
  } catch {
    return false;
  }
}

/** Ouvre ou ferme la mini-fenêtre. Renvoie `true` si elle est maintenant ouverte. */
export function toggleOverlay(): Promise<boolean> {
  return invoke<boolean>("toggle_overlay");
}
