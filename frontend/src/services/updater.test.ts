import { beforeEach, describe, expect, it, vi } from "vitest";

// Plugins Tauri et API simulés : on vérifie l'ordre des étapes, pas le vrai téléchargement.
const calls: string[] = [];
vi.mock("@tauri-apps/api/core", () => ({ invoke: vi.fn(async (cmd: string) => { calls.push(`invoke:${cmd}`); }) }));
vi.mock("@tauri-apps/plugin-process", () => ({ relaunch: vi.fn(async () => { calls.push("relaunch"); }) }));
vi.mock("@tauri-apps/plugin-updater", () => ({ check: vi.fn() }));
vi.mock("./api", () => ({
  api: { backupDatabase: vi.fn(async (label: string) => { calls.push(`backup:${label}`); return { path: "x" }; }) },
}));

import type { Update } from "@tauri-apps/plugin-updater";
import { describeUpdateError, installUpdate, type InstallStep } from "./updater";

function fakeUpdate(failInstall = false) {
  return {
    version: "0.2.0",
    download: vi.fn(async (onEvent: (e: unknown) => void) => {
      calls.push("download");
      onEvent({ event: "Started", data: { contentLength: 200 } });
      onEvent({ event: "Progress", data: { chunkLength: 50 } });
      onEvent({ event: "Progress", data: { chunkLength: 150 } });
      onEvent({ event: "Finished" });
    }),
    install: vi.fn(async () => {
      calls.push("install");
      if (failInstall) throw new Error("installer failed");
    }),
  } as unknown as Update;
}

beforeEach(() => { calls.length = 0; });

describe("installation d'une mise à jour", () => {
  it("télécharge, sauvegarde, arrête le moteur puis installe (dans cet ordre)", async () => {
    const steps: InstallStep[] = [];
    const progress: number[] = [];
    await installUpdate(fakeUpdate(), (s) => steps.push(s), (p) => progress.push(p.downloaded));
    expect(calls).toEqual(["download", "backup:avant-maj-0.2.0", "invoke:prepare_update", "install", "relaunch"]);
    expect(steps).toEqual(["download", "backup", "stop-engine", "install"]);
    expect(progress.at(-1)).toBe(200);
  });

  it("propage l'échec de l'installation", async () => {
    await expect(installUpdate(fakeUpdate(true), () => {}, () => {})).rejects.toThrow("installer failed");
    expect(calls).not.toContain("relaunch");
  });
});

describe("messages d'erreur", () => {
  it("traduit les erreurs courantes du plugin", () => {
    expect(describeUpdateError(new Error("Could not fetch a valid release JSON from the remote")))
      .toBe("Aucune version publiée pour l'instant.");
    expect(describeUpdateError("signature verification failed")).toMatch(/Signature invalide/);
    expect(describeUpdateError(new Error("error sending request: dns error"))).toMatch(/internet/);
    expect(describeUpdateError("autre chose")).toBe("autre chose");
  });
});
