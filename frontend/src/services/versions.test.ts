import { describe, expect, it } from "vitest";
import { assessUpdate, compareVersions, isBetaVersion } from "./versions";

describe("versions", () => {
  it("reconnaît une version bêta", () => {
    expect(isBetaVersion("0.2.1-beta.1")).toBe(true);
    expect(isBetaVersion("0.2.1")).toBe(false);
  });

  it("compare selon SemVer", () => {
    expect(compareVersions("0.2.0", "0.2.1-beta.1")).toBeLessThan(0); // retour au stable = version plus ancienne
    expect(compareVersions("0.2.1", "0.2.1-beta.1")).toBeGreaterThan(0); // la finale passe après sa bêta
    expect(compareVersions("0.10.0", "0.9.9")).toBeGreaterThan(0);
    expect(compareVersions("1.0.0-beta.10", "1.0.0-beta.2")).toBeGreaterThan(0);
    expect(compareVersions("1.0.0", "1.0.0")).toBe(0);
  });
});

describe("évaluation d'une version proposée", () => {
  const update = (version: string, schema?: number) =>
    ({ version, currentVersion: "0.2.1-beta.1", rawJson: schema === undefined ? {} : { schema_version: schema } });

  it("mise à jour normale", () => {
    expect(assessUpdate({ ...update("0.3.0", 2) }, 1)).toEqual({ downgrade: false, compatibility: "ok" });
  });

  it("retour au stable possible si la base est lisible", () => {
    expect(assessUpdate(update("0.2.0", 1), 1)).toEqual({ downgrade: true, compatibility: "ok" });
  });

  it("retour bloqué si la bêta a fait évoluer la base", () => {
    expect(assessUpdate(update("0.2.0", 1), 2)).toEqual({ downgrade: true, compatibility: "incompatible" });
  });

  it("compatibilité inconnue pour une ancienne publication", () => {
    expect(assessUpdate(update("0.2.0"), 1)).toEqual({ downgrade: true, compatibility: "unknown" });
  });
});
