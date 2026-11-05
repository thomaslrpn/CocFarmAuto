import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { setToken } from "../services/auth";
import { RecommendationBadge } from "./RecommendationBadge";
import { TokenGate } from "./TokenGate";

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
