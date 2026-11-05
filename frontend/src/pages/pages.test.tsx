import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { setToken } from "../services/auth";
import type { LogEntry, UserSettings } from "../types/api";
import { Changelog } from "../components/Changelog";
import { filterLogs } from "./LogsPage";
import { SettingsPage } from "./SettingsPage";
import { dayLabel, goldShare, scoreHistogram } from "./statisticsData";

afterEach(() => vi.unstubAllGlobals());

describe("statistiques", () => {
  it("répartit les scores en 10 tranches (100 dans la dernière)", () => {
    const bins = scoreHistogram([0, 9, 10, 55, 99, 100]);
    expect(bins).toHaveLength(10);
    expect(bins[0]).toEqual({ label: "0–9", value: 2 });
    expect(bins[5]!.value).toBe(1);
    expect(bins[9]).toEqual({ label: "90–100", value: 2 });
  });

  it("formate les jours et la part d'or", () => {
    expect(dayLabel("2026-11-05")).toBe("05/11");
    expect(goldShare(300, 100)).toBe(0.75);
    expect(goldShare(0, 0)).toBe(0.5);
  });
});

describe("logs", () => {
  const log = (id: number, level: LogEntry["level"], category: string, message: string): LogEntry =>
    ({ id, time: "2026-11-05T10:00:00", level, category, logger: `app.${category}`, message, data: {} });
  const entries = [
    log(1, "INFO", "observer_service", "Observation démarrée"),
    log(2, "WARNING", "capture", "PrintWindow inutilisable"),
    log(3, "ERROR", "database", "Base verrouillée"),
  ];

  it("filtre par niveau minimal et trie du plus récent au plus ancien", () => {
    expect(filterLogs(entries, "INFO", "", "").map((e) => e.id)).toEqual([3, 2, 1]);
    expect(filterLogs(entries, "WARNING", "", "").map((e) => e.id)).toEqual([3, 2]);
    expect(filterLogs(entries, "ERROR", "", "").map((e) => e.id)).toEqual([3]);
  });

  it("filtre par module (libellé) et par texte", () => {
    expect(filterLogs(entries, "INFO", "observation", "").map((e) => e.id)).toEqual([1]);
    expect(filterLogs(entries, "INFO", "", "printwindow").map((e) => e.id)).toEqual([2]);
  });
});

describe("changelog", () => {
  it("affiche titres et listes", () => {
    render(<Changelog markdown={"# Changelog\n\n## 0.1.0\n### Moteur\n- Lecture du butin\n- Score"} />);
    expect(screen.getByRole("heading", { name: "0.1.0" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Moteur" })).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(screen.queryByText("Changelog")).not.toBeInTheDocument(); // titre principal omis
  });

  it("rattache une ligne indentée à l'élément de liste précédent", () => {
    render(<Changelog markdown={"- Mises à jour signées,\n  avec sauvegarde\n- Autre"} />);
    const items = screen.getAllByRole("listitem");
    expect(items).toHaveLength(2);
    expect(items[0]).toHaveTextContent("Mises à jour signées, avec sauvegarde");
  });
});

describe("page Paramètres", () => {
  const SETTINGS: UserSettings = {
    preferences: {
      priority: "balanced",
      target_loot: { gold: 600000, elixir: 600000, dark_elixir: 10000 },
      army_cost: { gold: 0, elixir: 0, dark_elixir: 0 },
      dark_elixir_importance: 1, min_gold_elixir: 0,
      very_good_threshold: 80, good_threshold: 60, average_threshold: 40,
    },
    simulation: {
      capture_rates: { gold: 0.75, elixir: 0.75, dark_elixir: 0.75 },
      attack_duration_s: 180, army_ready_delay_s: 0, search_cost_gold: 1500, search_time_s: null,
    },
    app: { observe_interval_s: 1 },
  };

  it("enregistre les modifications et met en évidence un champ refusé", async () => {
    setToken("t");
    const fetch = vi.fn(async (_url: string, init?: RequestInit) => {
      if (init?.method === "PUT") {
        return { ok: false, status: 422, statusText: "Unprocessable",
          json: async () => ({ detail: [{ loc: ["body", "app", "observe_interval_s"], msg: "trop court" }] }) } as Response;
      }
      return { ok: true, status: 200, json: async () => SETTINGS } as Response;
    });
    vi.stubGlobal("fetch", fetch);
    render(<SettingsPage />);

    const frequency = await screen.findByLabelText("Fréquence des analyses");
    const save = screen.getByRole("button", { name: "Enregistrer" });
    expect(save).toBeDisabled(); // rien n'a changé
    fireEvent.change(frequency, { target: { value: "0.1" } });
    expect(save).toBeEnabled();
    fireEvent.click(save);

    expect(await screen.findByText(/app\.observe_interval_s : trop court/)).toBeInTheDocument();
    await waitFor(() => expect(frequency).toHaveAttribute("aria-invalid", "true"));
    const body = JSON.parse(String((fetch.mock.calls.at(-1)![1] as RequestInit).body)) as UserSettings;
    expect(body.app.observe_interval_s).toBe(0.1);
  });
});

describe("changelog (paragraphes)", () => {
  it("réunit les lignes consécutives d'un paragraphe", () => {
    render(<Changelog markdown={"Première ligne,\nsuite de la phrase.\n\n## 1.0.0"} />);
    expect(screen.getByText("Première ligne, suite de la phrase.")).toBeInTheDocument();
  });
});
