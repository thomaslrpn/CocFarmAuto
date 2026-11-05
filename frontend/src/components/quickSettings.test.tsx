import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { setToken } from "../services/auth";
import type { UserSettings } from "../types/api";
import { QuickSettings } from "./QuickSettings";

afterEach(() => vi.unstubAllGlobals());

const SETTINGS = {
  preferences: {
    priority: "dark_elixir",
    target_loot: { gold: 600_000, elixir: 600_000, dark_elixir: 10_000 },
    army_cost: { gold: 0, elixir: 0, dark_elixir: 0 },
    dark_elixir_importance: 1, min_gold_elixir: 0, very_good_threshold: 80, good_threshold: 60, average_threshold: 40,
  },
  simulation: {}, app: {},
} as unknown as UserSettings;

describe("réglages rapides de la mini-fenêtre", () => {
  it("affiche la priorité et son butin visé, et enregistre un changement de priorité", async () => {
    setToken("t");
    const fetch = vi.fn(async (_url: string, _init?: RequestInit) =>
      ({ ok: true, status: 200, json: async () => SETTINGS }) as Response);
    vi.stubGlobal("fetch", fetch);
    const onChange = vi.fn(async () => {});
    render(<QuickSettings onChange={onChange} />);

    expect(await screen.findByRole("button", { name: "Noir" })).toHaveAttribute("aria-pressed", "true");
    await waitFor(() => expect(screen.getByLabelText("Butin visé pour la ressource prioritaire")).toHaveValue("10000"));

    fireEvent.click(screen.getByRole("button", { name: "Or" }));
    await waitFor(() => expect(onChange).toHaveBeenCalled());
    const put = fetch.mock.calls.find(([, init]) => init?.method === "PUT")!;
    expect(JSON.parse(String(put[1]!.body))).toEqual({ preferences: { priority: "gold" } });
  });
});
