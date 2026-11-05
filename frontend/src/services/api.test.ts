import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, BackendUnreachableError, api, villageImageUrl } from "./api";
import { captureTokenFromUrl, getToken, setToken } from "./auth";

function mockFetch(response: Partial<Response> | Error) {
  const fn = vi.fn(async () => {
    if (response instanceof Error) throw response;
    return { ok: true, status: 200, statusText: "OK", json: async () => ({}), ...response } as Response;
  });
  vi.stubGlobal("fetch", fn);
  return fn;
}

afterEach(() => vi.unstubAllGlobals());

describe("client API", () => {
  it("envoie le jeton et les paramètres de requête", async () => {
    setToken("abc");
    const fetch = mockFetch({ json: async () => ({ total: 0, items: [] }) });
    await api.villages({ limit: 5, sort: "value", min_score: undefined });
    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://127.0.0.1:8765/api/villages?limit=5&sort=value");
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer abc");
  });

  it("transforme un 401 en ApiError non autorisée avec le détail du backend", async () => {
    mockFetch({ ok: false, status: 401, json: async () => ({ detail: "Jeton manquant ou invalide" }) });
    const error = await api.status().catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).isUnauthorized).toBe(true);
    expect((error as ApiError).message).toBe("Jeton manquant ou invalide");
  });

  it("signale un backend injoignable", async () => {
    mockFetch(new TypeError("Failed to fetch"));
    await expect(api.status()).rejects.toBeInstanceOf(BackendUnreachableError);
  });

  it("envoie le corps JSON au démarrage de l'observation", async () => {
    const fetch = mockFetch({ json: async () => ({ running: true }) });
    await api.startObserver(0.5);
    const [, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(init.method).toBe("POST");
    expect(init.body).toBe('{"interval_s":0.5}');
  });

  it("met le jeton dans l'URL des images", () => {
    setToken("xyz");
    expect(villageImageUrl(3)).toBe("http://127.0.0.1:8765/api/villages/3/image?token=xyz");
  });
});

describe("jeton", () => {
  it("récupère le jeton dans l'URL puis le retire de la barre d'adresse", () => {
    window.history.replaceState(null, "", "/?token=depuis-url#/historique");
    expect(captureTokenFromUrl()).toBe("depuis-url");
    expect(getToken()).toBe("depuis-url");
    expect(window.location.search).toBe("");
    expect(window.location.hash).toBe("#/historique");
  });
});
