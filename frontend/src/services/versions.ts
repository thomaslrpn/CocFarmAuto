/**
 * Comparaison de versions SemVer (« 1.2.3 », « 1.3.0-beta.1 »), sans bibliothèque.
 * Règle SemVer : une pré-version passe avant la version finale (0.2.1-beta.1 < 0.2.1).
 */

/** « 0.3.0-beta.1 » : une version avec suffixe est une pré-version (bêta). */
export function isBetaVersion(version: string): boolean {
  return /^\d+\.\d+\.\d+-/.test(version);
}

/** Négatif si a < b, 0 si égales, positif si a > b. */
export function compareVersions(a: string, b: string): number {
  const [coreA = "", preA] = splitVersion(a);
  const [coreB = "", preB] = splitVersion(b);
  const numsA = coreA.split(".").map(Number);
  const numsB = coreB.split(".").map(Number);
  for (let i = 0; i < 3; i++) {
    const diff = (numsA[i] ?? 0) - (numsB[i] ?? 0);
    if (diff !== 0) return diff;
  }
  if (preA === preB) return 0;
  if (preA === undefined) return 1; // version finale > pré-version
  if (preB === undefined) return -1;
  return comparePrerelease(preA, preB);
}

function splitVersion(version: string): [string, string | undefined] {
  const dash = version.indexOf("-");
  return dash < 0 ? [version, undefined] : [version.slice(0, dash), version.slice(dash + 1)];
}

/** « beta.2 » < « beta.10 » : les parties numériques se comparent comme des nombres. */
function comparePrerelease(a: string, b: string): number {
  const partsA = a.split(".");
  const partsB = b.split(".");
  for (let i = 0; i < Math.max(partsA.length, partsB.length); i++) {
    const pa = partsA[i];
    const pb = partsB[i];
    if (pa === undefined) return -1;
    if (pb === undefined) return 1;
    const na = Number(pa);
    const nb = Number(pb);
    const diff = !Number.isNaN(na) && !Number.isNaN(nb) ? na - nb : pa.localeCompare(pb);
    if (diff !== 0) return diff;
  }
  return 0;
}

export interface UpdateAssessment {
  /** Retour à une version plus ancienne (bêta installée, canal stable choisi). */
  downgrade: boolean;
  /** La version proposée sait-elle lire la base de données actuelle ? */
  compatibility: "ok" | "unknown" | "incompatible";
}

/**
 * Évalue une version proposée. `schema_version` (dans latest.json) = structure de base
 * que cette version sait lire ; `installedSchema` = structure de la base actuelle.
 * Une version qui ne connaît pas la structure actuelle refuserait d'ouvrir la base.
 */
export function assessUpdate(
  update: { version: string; currentVersion: string; rawJson: Record<string, unknown> },
  installedSchema?: number,
): UpdateAssessment {
  const downgrade = compareVersions(update.version, update.currentVersion) < 0;
  const targetSchema = typeof update.rawJson.schema_version === "number" ? update.rawJson.schema_version : undefined;
  let compatibility: UpdateAssessment["compatibility"] = "ok";
  if (targetSchema !== undefined && installedSchema !== undefined) {
    compatibility = targetSchema < installedSchema ? "incompatible" : "ok";
  } else if (downgrade) {
    compatibility = "unknown"; // version publiée avant l'ajout de cette information
  }
  return { downgrade, compatibility };
}
