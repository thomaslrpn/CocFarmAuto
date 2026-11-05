/**
 * Stratégies connues du backend (backend/app/strategy/strategies.py, DEFAULT_STRATEGIES).
 * « none » = villages qu'aucune stratégie n'attaquerait (score sous leur minimum de 70).
 */
export const STRATEGY_FILTERS = [
  { key: "gold", label: "Farm or" },
  { key: "elixir", label: "Farm élixir" },
  { key: "dark_elixir", label: "Farm élixir noir" },
  { key: "balanced", label: "Farm équilibré" },
  { key: "none", label: "Aucune stratégie" },
] as const;

export const PRIORITY_LABELS = {
  balanced: "Équilibrée",
  gold: "Or",
  elixir: "Élixir",
  dark_elixir: "Élixir noir",
} as const;
