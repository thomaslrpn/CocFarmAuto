/**
 * Client de l'API locale (backend FastAPI).
 * Toutes les requêtes passent par `request` : jeton, erreurs et JSON au même endroit.
 */
import type {
  ObserverStatus,
  StatisticsOverview,
  Status,
  VillageDetail,
  VillagePage,
  VillageQuery,
} from "../types/api";
import { getToken } from "./auth";

export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8765";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
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
    super(`Backend injoignable sur ${API_URL} (lance : python -m app.main)`);
    this.name = "BackendUnreachableError";
  }
}

type Query = Record<string, string | number | undefined>;

function buildUrl(path: string, query?: Query): string {
  const url = new URL(`/api${path}`, API_URL);
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
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* corps non JSON : on garde le statut HTTP */
    }
    throw new ApiError(response.status, detail);
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
};
