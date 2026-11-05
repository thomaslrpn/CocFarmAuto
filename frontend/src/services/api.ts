/**
 * Client de l'API locale (backend FastAPI).
 * Toutes les requêtes passent par `request` : jeton, erreurs et JSON au même endroit.
 */
import type {
  LogEntry,
  LogLevel,
  ObserverStatus,
  StatisticsOverview,
  Status,
  StrategyComparison,
  UserSettings,
  UserSettingsUpdate,
  ValidationIssue,
  VillageDetail,
  VillagePage,
  VillageQuery,
} from "../types/api";
import { getToken } from "./auth";

let apiUrl: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8765";

export function getApiUrl(): string {
  return apiUrl;
}

/** Application de bureau : adresse fournie au démarrage (le port est choisi automatiquement). */
export function setApiUrl(url: string): void {
  apiUrl = url;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    /** Détail des champs refusés (erreur 422 de validation). */
    readonly issues: ValidationIssue[] = [],
  ) {
    super(message);
    this.name = "ApiError";
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }
}

/** Le backend ne répond pas du tout (arrêté, mauvais port...). */
export class BackendUnreachableError extends Error {
  constructor() {
    super(`Moteur d'analyse injoignable (${apiUrl})`);
    this.name = "BackendUnreachableError";
  }
}

type Query = Record<string, string | number | undefined>;

function buildUrl(path: string, query?: Query): string {
  const url = new URL(`/api${path}`, apiUrl);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
  }
  return url.toString();
}

async function request<T>(path: string, init: RequestInit = {}, query?: Query): Promise<T> {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body) headers.set("Content-Type", "application/json");

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), { ...init, headers });
  } catch {
    throw new BackendUnreachableError();
  }
  if (!response.ok) {
    let detail = response.statusText;
    let issues: ValidationIssue[] = [];
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
      if (Array.isArray(body.detail)) {
        issues = body.detail as ValidationIssue[];
        detail = "Valeurs refusées : " + issues.map((i) => i.msg).join(" ; ");
      }
    } catch {
      /* corps non JSON : on garde le statut HTTP */
    }
    throw new ApiError(response.status, detail, issues);
  }
  return (await response.json()) as T;
}

/**
 * URL d'une capture, utilisable dans <img src> (le jeton passe en paramètre).
 * `width` : miniature JPEG légère (historique) ; sinon capture originale.
 */
export function villageImageUrl(villageId: number, width?: number): string {
  return buildUrl(`/villages/${villageId}/image`, { width, token: getToken() ?? undefined });
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  status: () => request<Status>("/status"),
  statistics: () => request<StatisticsOverview>("/statistics"),
  villages: (query: VillageQuery = {}) => request<VillagePage>("/villages", {}, { ...query }),
  village: (id: number) => request<VillageDetail>(`/villages/${id}`),
  observer: () => request<ObserverStatus>("/observer"),
  startObserver: (intervalS?: number) =>
    request<ObserverStatus>("/observer/start", {
      method: "POST",
      body: JSON.stringify(intervalS === undefined ? {} : { interval_s: intervalS }),
    }),
  stopObserver: () => request<ObserverStatus>("/observer/stop", { method: "POST" }),
  settings: () => request<UserSettings>("/settings"),
  updateSettings: (update: UserSettingsUpdate) =>
    request<UserSettings>("/settings", { method: "PUT", body: JSON.stringify(update) }),
  compareStrategies: () => request<StrategyComparison>("/strategies/compare"),
  logs: (afterId = 0, level: LogLevel = "INFO") =>
    request<LogEntry[]>("/logs", {}, { after_id: afterId, level, limit: 500 }),
  backupDatabase: (label: string) =>
    request<{ path: string }>("/database/backup", { method: "POST" }, { label }),
};
