/**
 * Historique des versions publiées, lu sur l'API publique de GitHub (sans compte).
 * Limite GitHub : 60 requêtes par heure et par adresse IP, largement suffisant
 * pour un affichage à l'ouverture de la page À propos.
 */
import type { UpdateChannel } from "../types/api";

const RELEASES_API = "https://api.github.com/repos/thomaslrpn/CocFarmAuto/releases?per_page=30";
/** Release technique qui porte le latest.json du canal bêta : pas une version. */
const BETA_CHANNEL_TAG = "updater-beta";

/** Champs utiles d'une release renvoyée par l'API GitHub. */
export interface GitHubRelease {
  tag_name: string;
  name: string | null;
  body: string | null;
  draft: boolean;
  prerelease: boolean;
  published_at: string | null;
}

export interface PublishedVersion {
  version: string;
  date?: string;
  beta: boolean;
  notes: string;
}

/** Versions à afficher pour ce canal, de la plus récente à la plus ancienne. */
export function visibleVersions(releases: GitHubRelease[], channel: UpdateChannel): PublishedVersion[] {
  return releases
    .filter((r) => !r.draft && r.tag_name !== BETA_CHANNEL_TAG && (channel === "beta" || !r.prerelease))
    .map((r) => ({
      version: r.tag_name.replace(/^v/, ""),
      date: r.published_at ?? undefined,
      beta: r.prerelease,
      notes: (r.body ?? "").trim(),
    }))
    .sort((a, b) => (b.date ?? "").localeCompare(a.date ?? ""));
}

export async function fetchReleases(): Promise<GitHubRelease[]> {
  const response = await fetch(RELEASES_API, { headers: { Accept: "application/vnd.github+json" } });
  if (!response.ok) throw new Error(`GitHub a répondu ${response.status}`);
  return (await response.json()) as GitHubRelease[];
}
