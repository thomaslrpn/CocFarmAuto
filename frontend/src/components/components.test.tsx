import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { setToken } from "../services/auth";
import type { VillageSummary } from "../types/api";
import { RecommendationBadge } from "./RecommendationBadge";
import { ScoreBreakdown } from "./ScoreBreakdown";
import { TokenGate } from "./TokenGate";
import { VillageTable } from "./VillageTable";

afterEach(() => vi.unstubAllGlobals());

describe("RecommendationBadge", () => {
  it("affiche le libellé (la couleur n'est jamais seule)", () => {
    render(<RecommendationBadge value="à passer" />);
    expect(screen.getByText("à passer")).toBeInTheDocument();
  });
});

describe("TokenGate", () => {
  it("demande le jeton s'il n'y en a pas", async () => {
    render(<TokenGate>contenu protégé</TokenGate>);
    expect(await screen.findByLabelText("Jeton d'accès au moteur")).toBeInTheDocument();
    expect(screen.queryByText("contenu protégé")).not.toBeInTheDocument();
  });

  it("affiche l'application quand le jeton est accepté", async () => {
    setToken("bon");
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, status: 200, json: async () => ({}) }) as Response));
    render(<TokenGate>contenu protégé</TokenGate>);
    expect(await screen.findByText("contenu protégé")).toBeInTheDocument();
  });

  it("redemande le jeton s'il est refusé", async () => {
    setToken("périmé");
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: false, status: 401, json: async () => ({}) }) as Response));
    render(<TokenGate>contenu protégé</TokenGate>);
    expect(await screen.findByText(/Jeton refusé/)).toBeInTheDocument();
  });

  it("explique comment démarrer le moteur s'il ne répond pas", async () => {
    setToken("bon");
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Failed to fetch"); }));
    render(<TokenGate>contenu protégé</TokenGate>);
    expect(await screen.findByText("Le moteur d'analyse ne répond pas")).toBeInTheDocument();
  });
});

describe("ScoreBreakdown", () => {
  it("affiche les critères mesurés, non disponibles et les avertissements", () => {
    render(
      <ScoreBreakdown
        factors={[
          { label: "Or", detail: "300 000 / 600 000 visés (50%), poids 40%", points: 20, max_points: 40, available: true },
          { label: "Difficulté", detail: "nécessite la détection des défenses", points: 0, max_points: 0, available: false },
        ]}
        warnings={["coût de l'armée non configuré"]}
      />,
    );
    expect(screen.getByRole("meter", { name: "Or : 20.0 points sur 40.0" })).toHaveAttribute("aria-valuenow", "20");
    expect(screen.getByText(/non disponible/)).toBeInTheDocument();
    expect(screen.getByText("coût de l'armée non configuré")).toBeInTheDocument();
  });
});

describe("VillageTable", () => {
  const village: VillageSummary = {
    id: 7, analyzed_at: "2026-11-05T10:58:42", gold: 556048, elixir: 779701, dark_elixir: 6555,
    profitability_score: 90, recommendation: "très intéressant", recommended_strategy: "elixir",
    recommended_strategy_label: "Farm élixir", detection_confidence: 0.9, loot_value: 95,
    relative_rank: 43, has_image: false,
  };

  it("ouvre la fiche au clic ou avec Entrée", () => {
    const onSelect = vi.fn();
    render(<VillageTable villages={[village]} onSelect={onSelect} />);
    const row = screen.getByText("556 048").closest("tr")!;
    fireEvent.click(row);
    fireEvent.keyDown(row, { key: "Enter" });
    expect(onSelect).toHaveBeenCalledTimes(2);
    expect(onSelect).toHaveBeenCalledWith(village);
  });

  it("affiche un message quand la liste est vide", () => {
    render(<VillageTable villages={[]} emptyMessage="Rien ici" />);
    expect(screen.getByText("Rien ici")).toBeInTheDocument();
  });
});

describe("TokenGate (application de bureau)", () => {
  afterEach(() => {
    delete (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__;
  });

  function fakeDesktop(invoke: (cmd: string) => Promise<unknown>) {
    (window as unknown as Record<string, unknown>).__TAURI_INTERNALS__ = { invoke, transformCallback: () => 0 };
  }

  it("se connecte tout seul avec la configuration fournie par l'application", async () => {
    fakeDesktop(async () => ({ url: "http://127.0.0.1:50123", token: "auto" }));
    const fetch = vi.fn(async () => ({ ok: true, status: 200, json: async () => ({}) }) as Response);
    vi.stubGlobal("fetch", fetch);
    render(<TokenGate>contenu protégé</TokenGate>);
    expect(await screen.findByText("contenu protégé")).toBeInTheDocument();
    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://127.0.0.1:50123/api/status");
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer auto");
  });

  it("affiche l'écran de démarrage tant que le moteur ne répond pas", async () => {
    fakeDesktop(async () => ({ url: "http://127.0.0.1:50124", token: "auto" }));
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("Failed to fetch"); }));
    render(<TokenGate>contenu protégé</TokenGate>);
    expect(await screen.findByText("Démarrage du moteur d'analyse…")).toBeInTheDocument();
    expect(screen.queryByLabelText("Jeton d'accès au moteur")).not.toBeInTheDocument(); // jamais de saisie
  });

  it("explique l'échec de lancement du moteur", async () => {
    fakeDesktop(async () => { throw "moteur introuvable : backend.exe"; });
    render(<TokenGate>contenu protégé</TokenGate>);
    expect(await screen.findByText("Le moteur d'analyse n'a pas pu démarrer")).toBeInTheDocument();
    expect(screen.getByText(/moteur introuvable/)).toBeInTheDocument();
  });
});
