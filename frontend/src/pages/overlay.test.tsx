import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { attackDuration, recapRows } from "../components/AttackRecap";
import type { AttackSummary, ObserverStatus } from "../types/api";
import { OverlayView } from "./OverlayPage";

const STATUS: ObserverStatus = {
  running: true, started_at: "2026-11-05T15:00:00", interval_s: 1, frames: 10, villages_saved: 1,
  missing_window: 0, errors: 0, last_screen: "scout", last_cycle_ms: 120, last_error: null, last_attack: null,
  last_village: {
    village_id: 7, analyzed_at: "2026-11-05T15:01:00", gold: 650_000, elixir: 720_000, dark_elixir: 5_000,
    score: 91, recommendation: "très intéressant", strategy: "Farm élixir",
  },
};

describe("mini-fenêtre", () => {
  it("affiche le score, la recommandation et le butin du dernier village", () => {
    render(<OverlayView observer={STATUS} onChange={async () => {}} />);
    expect(screen.getByText("91")).toBeInTheDocument();
    expect(screen.getByText("très intéressant")).toBeInTheDocument();
    expect(screen.getByText("Élixir noir")).toBeInTheDocument();
    expect(screen.getByText(/Farm élixir/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Arrêter/ })).toBeEnabled();
  });

  it("explique quoi faire quand aucun village n'est encore analysé", () => {
    render(<OverlayView observer={{ ...STATUS, running: false, last_village: null }} onChange={async () => {}} />);
    expect(screen.getByText(/Démarre l'observation/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Démarrer/ })).toBeEnabled();
  });
});

const ATTACK: AttackSummary = {
  village_id: 7, started_at: "2026-11-05T15:01:30", ended_at: "2026-11-05T15:04:11",
  available_gold: 650_000, available_elixir: 720_000, available_dark_elixir: 5_000,
  gained_gold: 520_000, gained_elixir: 576_000, gained_dark_elixir: null, farm_score: 72, farm_rating: "bon",
};

describe("récapitulatif d'attaque", () => {
  it("calcule récupéré / disponible et le pourcentage", () => {
    const rows = recapRows(ATTACK);
    expect(rows[0]).toEqual({ key: "gold", gained: 520_000, available: 650_000, percent: 80 });
    expect(rows[2]).toMatchObject({ key: "dark_elixir", gained: null, percent: null });
    expect(attackDuration(ATTACK)).toBe("2 min 41 s");
  });

  it("s'affiche dans la mini-fenêtre juste après le combat, puis laisse la place au village suivant", () => {
    const { rerender } = render(<OverlayView observer={{ ...STATUS, last_attack: ATTACK }} onChange={async () => {}} />);
    expect(screen.getByText("Attaque terminée")).toBeInTheDocument();
    expect(screen.getByText("72/100")).toBeInTheDocument(); // note du farm
    expect(screen.getAllByText("80 %")).toHaveLength(2); // or 520/650 et élixir 576/720
    expect(screen.getByText("non lu")).toBeInTheDocument();
    const next = { ...STATUS.last_village!, village_id: 8, analyzed_at: "2026-11-05T15:05:00" };
    rerender(<OverlayView observer={{ ...STATUS, last_attack: ATTACK, last_village: next }} onChange={async () => {}} />);
    expect(screen.queryByText("Attaque terminée")).not.toBeInTheDocument();
  });
});
