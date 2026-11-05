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
  schema_version: number;
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
  min_gold?: number;
  min_elixir?: number;
  min_dark_elixir?: number;
  strategy?: string;
  date_from?: string;
  date_to?: string;
  sort?: "date" | "score" | "value";
}

export interface ScoreFactor {
  label: string;
  detail: string;
  points: number;
  max_points: number;
  available: boolean;
}

export interface Loot {
  gold: number;
  elixir: number;
  dark_elixir: number;
}

export type Priority = "balanced" | "gold" | "elixir" | "dark_elixir";

export interface ScoringPreferences {
  priority: Priority;
  target_loot: Loot;
  army_cost: Loot;
  dark_elixir_importance: number;
  min_gold_elixir: number;
  very_good_threshold: number;
  good_threshold: number;
  average_threshold: number;
}

export interface VillageDetail extends VillageSummary {
  town_hall_level: number | null;
  estimated_difficulty: number | null;
  explanation: string[];
  factors: ScoreFactor[];
  warnings: string[];
  preferences_used: ScoringPreferences | null;
  image_url: string | null;
}

export interface CaptureRates {
  gold: number;
  elixir: number;
  dark_elixir: number;
}

export interface SimulationAssumptions {
  capture_rates: CaptureRates;
  attack_duration_s: number;
  army_ready_delay_s: number;
  search_cost_gold: number;
  search_time_s: number | null;
}

export type UpdateChannel = "stable" | "beta";

export interface AppPreferences {
  observe_interval_s: number;
  update_channel: UpdateChannel;
  auto_check_updates: boolean;
}

export interface UserSettings {
  preferences: ScoringPreferences;
  simulation: SimulationAssumptions;
  app: AppPreferences;
}

/** Modification partielle : seuls les champs envoyés changent (fusion côté backend). */
export interface UserSettingsUpdate {
  preferences?: Partial<ScoringPreferences>;
  simulation?: Partial<SimulationAssumptions>;
  app?: Partial<AppPreferences>;
}

export interface StrategyInfo {
  key: string;
  label: string;
  description: string;
  priority: Priority;
  min_score: number;
}

export interface SimulationResult {
  strategy: StrategyInfo;
  villages_seen: number;
  attacks: number;
  gross_loot: Loot;
  costs: Loot;
  net_loot: Loot;
  duration_s: number;
  net_per_hour: Loot;
  points_per_hour: number;
  skip_rate: number;
}

export interface StrategyComparison {
  villages_count: number;
  search_time_s: number;
  assumptions: string[];
  army_cost_configured: boolean;
  results: SimulationResult[];
}

export type LogLevel = "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";

export interface LogEntry {
  id: number;
  time: string;
  level: LogLevel;
  category: string;
  logger: string;
  message: string;
  data: Record<string, string | number | boolean>;
}

/** Erreur de validation FastAPI (422). */
export interface ValidationIssue {
  loc: (string | number)[];
  msg: string;
}
