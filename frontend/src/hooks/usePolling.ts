import { useCallback, useEffect, useRef, useState } from "react";

export interface PollingState<T> {
  data: T | undefined;
  error: Error | undefined;
  loading: boolean; // vrai uniquement avant la toute première réponse
  refresh: () => Promise<void>;
}

/**
 * Appelle `fetcher` immédiatement puis toutes les `intervalMs` millisecondes.
 * - Pas de requêtes qui se chevauchent : la suivante part après la fin de la précédente.
 * - En cas d'erreur, on garde les dernières données affichées (pas d'écran qui clignote).
 * - `refresh()` force une mise à jour immédiate (ex. après un clic).
 * - `key` : quand elle change (filtres, identifiant...), on recharge tout de suite
 *   (les anciennes données restent affichées jusqu'à la réponse).
 */
export function usePolling<T>(fetcher: () => Promise<T>, intervalMs: number, key = ""): PollingState<T> {
  const [data, setData] = useState<T>();
  const [error, setError] = useState<Error>();
  const [loading, setLoading] = useState(true);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refresh = useCallback(async () => {
    try {
      setData(await fetcherRef.current());
      setError(undefined);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      await refresh();
      if (!cancelled) timer = setTimeout(tick, intervalMs);
    };
    void tick();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [refresh, intervalMs, key]);

  return { data, error, loading, refresh };
}
