import { describe, expect, it } from "vitest";
import { PAGE_SIZE, filtersToQuery, periodStart } from "./historyFilters";

const NOW = new Date(2026, 10, 5, 15, 30); // 5 novembre 2026, 15:30 (heure locale)

describe("filtres de l'historique", () => {
  it("valeurs par défaut : première page, tri par date", () => {
    expect(filtersToQuery(new URLSearchParams(), NOW)).toEqual({
      limit: PAGE_SIZE, offset: 0, sort: "date",
      min_score: undefined, strategy: undefined, date_from: undefined,
      min_gold: undefined, min_elixir: undefined, min_dark_elixir: undefined,
    });
  });

  it("traduit tous les filtres de l'URL", () => {
    const params = new URLSearchParams("page=3&sort=value&min_score=60&strategy=none&period=today&min_gold=500 000");
    const query = filtersToQuery(params, NOW);
    expect(query.offset).toBe(2 * PAGE_SIZE);
    expect(query.sort).toBe("value");
    expect(query.min_score).toBe(60);
    expect(query.strategy).toBe("none");
    expect(query.date_from).toBe("2026-11-05T00:00:00");
    expect(query.min_gold).toBe(500000); // espaces tolérées
  });

  it("ignore les valeurs invalides", () => {
    const query = filtersToQuery(new URLSearchParams("page=-2&sort=pirate&min_elixir=abc"), NOW);
    expect(query.offset).toBe(0);
    expect(query.sort).toBe("date");
    expect(query.min_elixir).toBeUndefined();
  });

  it("calcule le début des périodes glissantes", () => {
    expect(periodStart("7d", NOW)).toBe("2026-10-30T00:00:00"); // aujourd'hui + 6 jours avant
    expect(periodStart("30d", NOW)).toBe("2026-10-07T00:00:00"); // passe le changement d'heure du 25/10
    expect(periodStart("", NOW)).toBeUndefined();
  });
});
