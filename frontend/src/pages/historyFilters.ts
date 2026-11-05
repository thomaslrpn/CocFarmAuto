/**
 * Filtres de l'historique, stockés dans l'URL (#/historique?min_score=60&...) :
 * un retour arrière depuis une fiche village retrouve les mêmes filtres.
 */
import type { VillageQuery } from "../types/api";

export const PAGE_SIZE = 25;

export const PERIODS = [
  { key: "", label: "Toute la période" },
  { key: "today", label: "Aujourd'hui" },
  { key: "7d", label: "7 derniers jours" },
  { key: "30d", label: "30 derniers jours" },
] as const;

export const SORTS = [
  { key: "date", label: "Plus récents" },
  { key: "score", label: "Meilleur score" },
  { key: "value", label: "Plus gros butin" },
] as const;

export const MIN_SCORES = [
  { key: "", label: "Tous les scores" },
  { key: "40", label: "40 et plus" },
  { key: "60", label: "60 et plus" },
  { key: "80", label: "80 et plus" },
] as const;

/** Champs de butin minimal : nom dans l'URL -> paramètre de l'API. */
export const LOOT_FIELDS = [
  { param: "min_gold", label: "Or min.", swatch: "bg-gold" },
  { param: "min_elixir", label: "Élixir min.", swatch: "bg-elixir" },
  { param: "min_dark_elixir", label: "Noir min.", swatch: "bg-dark-elixir" },
] as const;

/** Date locale au format attendu par l'API (« 2026-11-05T00:00:00 », sans fuseau). */
export function localIso(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(
    date.getMinutes(),
  )}:${pad(date.getSeconds())}`;
}

const PERIOD_DAYS: Record<string, number> = { today: 0, "7d": 6, "30d": 29 };

/**
 * Début de période : minuit, N jours calendaires avant aujourd'hui.
 * On recule en JOURS (et non de N x 24 h) : sinon un changement d'heure dans
 * l'intervalle décale le résultat d'une heure (ex. 01:00 au lieu de minuit).
 */
export function periodStart(period: string, now: Date): string | undefined {
  const days = PERIOD_DAYS[period];
  if (days === undefined) return undefined;
  return localIso(new Date(now.getFullYear(), now.getMonth(), now.getDate() - days));
}

function positiveInt(value: string | null): number | undefined {
  if (!value) return undefined;
  const n = Number(value.replace(/\s/g, ""));
  return Number.isInteger(n) && n > 0 ? n : undefined;
}

export function currentPage(params: URLSearchParams): number {
  return positiveInt(params.get("page")) ?? 1;
}

/** Paramètres de l'URL -> requête GET /api/villages. */
export function filtersToQuery(params: URLSearchParams, now = new Date()): VillageQuery {
  const sort = params.get("sort");
  return {
    limit: PAGE_SIZE,
    offset: (currentPage(params) - 1) * PAGE_SIZE,
    sort: sort === "score" || sort === "value" ? sort : "date",
    min_score: positiveInt(params.get("min_score")),
    strategy: params.get("strategy") || undefined,
    date_from: periodStart(params.get("period") ?? "", now),
    min_gold: positiveInt(params.get("min_gold")),
    min_elixir: positiveInt(params.get("min_elixir")),
    min_dark_elixir: positiveInt(params.get("min_dark_elixir")),
  };
}
