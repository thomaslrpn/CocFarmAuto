import { describe, expect, it } from "vitest";
import { visibleVersions, type GitHubRelease } from "./releases";

const release = (tag: string, date: string, extra: Partial<GitHubRelease> = {}): GitHubRelease => ({
  tag_name: tag, name: tag, body: `notes ${tag}`, draft: false, prerelease: false, published_at: date, ...extra,
});

const RELEASES = [
  release("v0.1.0", "2026-11-05T12:00:00Z"),
  release("updater-beta", "2026-11-06T09:00:00Z", { prerelease: true }),
  release("v0.2.0-beta.1", "2026-11-06T10:00:00Z", { prerelease: true }),
  release("v0.1.1", "2026-11-05T13:00:00Z"),
  release("v0.3.0", "2026-11-07T10:00:00Z", { draft: true }),
];

describe("historique des versions", () => {
  it("canal stable : versions finalisées seulement, plus récente d'abord", () => {
    expect(visibleVersions(RELEASES, "stable").map((v) => v.version)).toEqual(["0.1.1", "0.1.0"]);
  });

  it("canal bêta : inclut les bêtas, jamais la release technique ni les brouillons", () => {
    const versions = visibleVersions(RELEASES, "beta");
    expect(versions.map((v) => v.version)).toEqual(["0.2.0-beta.1", "0.1.1", "0.1.0"]);
    expect(versions[0]).toMatchObject({ beta: true, notes: "notes v0.2.0-beta.1" });
  });
});
