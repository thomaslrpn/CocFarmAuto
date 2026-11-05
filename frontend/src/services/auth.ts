/**
 * Jeton d'accès à l'API locale.
 *
 * Le backend affiche au démarrage une URL de la forme http://localhost:5173/?token=XXX :
 * on lit le jeton dans l'URL, on le mémorise, puis on le retire de la barre d'adresse.
 * Stockage local du navigateur : simple confort (il change à chaque démarrage du
 * backend ; en phase 7, l'application de bureau le fournira directement).
 */

const STORAGE_KEY = "coc-autofarm-token";

function safeStorage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null; // stockage bloqué (navigation privée...) : on fonctionne sans
  }
}

export function getToken(): string | null {
  return safeStorage()?.getItem(STORAGE_KEY) ?? null;
}

export function setToken(token: string): void {
  safeStorage()?.setItem(STORAGE_KEY, token.trim());
}

export function clearToken(): void {
  safeStorage()?.removeItem(STORAGE_KEY);
}

/** Récupère un jeton passé dans l'URL (?token=...), le mémorise et nettoie l'URL. */
export function captureTokenFromUrl(location: Location = window.location): string | null {
  const params = new URLSearchParams(location.search);
  const token = params.get("token");
  if (!token) return null;
  setToken(token);
  params.delete("token");
  const query = params.toString();
  window.history.replaceState(null, "", `${location.pathname}${query ? `?${query}` : ""}${location.hash}`);
  return token;
}
