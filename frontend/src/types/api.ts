/**
 * Types des réponses de l'API, calqués sur backend/app/api/schemas.py.
 * Toute modification d'un schéma Python doit être reportée ici.
 * (Les dates arrivent en texte ISO : on les convertit à l'affichage.)
 */

export type Recommendation = "très intéressant" | "intéressant" | "moyen" | "à passer";
export type GameWindowState = "found" | "not_found" | "unsupported";
export type ScreenName = "home" | "scout" | "battle" | "unknown";

export interface Status {
  app: string;
  version: string;
  data_dir: string;
  database: string;
  villages_count: number;
  vision_ready: boolean;
  game_window: GameWindowState;
}

export interface VillageSummary {
  id: number;
  analyzed_at: string;
  gold: number;
  elixir: number;
  dark_elixir: number;
  profitability_score: number;
  recommendation: Recommendation;
  recommended_strategy: string | null;
  recommended_strategy_label: string;
  detection_confidence: number;
  loot_value: number;
  relative_rank: number | null;
  has_image: boolean;
}

export interface VillagePage {
  total: number;
  limit: number;
  offset: number;
  items: VillageSummary[];
}

export interface DayStatistics {
  day: string;
  villages_count: number;
  total_gold: number;
  total_elixir: number;
  total_dark_elixir: number;
  average_score: number;
}

export interface StatisticsOverview {
  villages_count: number;
  total_gold: number;
  total_elixir: number;
  total_dark_elixir: number;
  average_score: number | null;
  days: DayStatistics[];
}

export interface ObservedVillage {
  village_id: number;
  analyzed_at: string;
  gold: number;
  elixir: number;
  dark_elixir: number;
  score: number;
  recommendation: Recommendation;
  strategy: string;
}

export interface ObserverStatus {
  running: boolean;
  started_at: string | null;
  interval_s: number | null;
  frames: number;
  villages_saved: number;
  missing_window: number;
  errors: number;
  last_screen: ScreenName | null;
  last_cycle_ms: number | null;
  last_village: ObservedVillage | null;
  last_error: string | null;
}

export interface VillageQuery {
  limit?: number;
  offset?: number;
  min_score?: number;
  strategy?: string;
  date_from?: string;
  date_to?: string;
  sort?: "date" | "score" | "value";
}
