import { KeyRound, PlugZap } from "lucide-react";
import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from "react";
import { API_URL, ApiError, api } from "../services/api";
import { captureTokenFromUrl, clearToken, getToken, setToken } from "../services/auth";

type GateState = "checking" | "ok" | "need-token" | "unreachable";
const RETRY_MS = 3000;

/**
 * Vérifie l'accès au backend avant d'afficher l'application :
 * - backend arrêté -> message + nouvel essai automatique ;
 * - jeton absent ou refusé -> formulaire de saisie du jeton.
 */
export function TokenGate({ children }: { children: ReactNode }) {
  const [state, setState] = useState<GateState>("checking");
  const [rejected, setRejected] = useState(false);

  const check = useCallback(async () => {
    if (!getToken()) {
      setState("need-token");
      return;
    }
    try {
      await api.status();
      setState("ok");
    } catch (err) {
      if (err instanceof ApiError && err.isUnauthorized) {
        clearToken();
        setRejected(true);
        setState("need-token");
      } else {
        setState("unreachable");
      }
    }
  }, []);

  useEffect(() => {
    captureTokenFromUrl();
    void check();
  }, [check]);

  useEffect(() => {
    if (state !== "unreachable") return;
    const timer = setInterval(() => void check(), RETRY_MS);
    return () => clearInterval(timer);
  }, [state, check]);

  if (state === "ok") return <>{children}</>;
  if (state === "checking") return <Centered>Connexion au moteur…</Centered>;
  if (state === "unreachable") {
    return (
      <Centered>
        <PlugZap aria-hidden className="mx-auto mb-3 size-8 text-warning" />
        <p className="font-medium">Le moteur d'analyse ne répond pas</p>
        <p className="mt-2 text-sm text-ink-secondary">
          Démarre-le dans un terminal : <code className="text-ink">python -m app.main</code>
        </p>
        <p className="mt-1 text-xs text-ink-muted">Nouvel essai automatique… ({API_URL})</p>
      </Centered>
    );
  }
  return <TokenForm rejected={rejected} onSubmit={(token) => { setToken(token); void check(); }} />;
}

function TokenForm({ rejected, onSubmit }: { rejected: boolean; onSubmit: (token: string) => void }) {
  const [value, setValue] = useState("");
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (value.trim()) onSubmit(value);
  };
  return (
    <Centered>
      <form onSubmit={submit} className="text-left">
        <KeyRound aria-hidden className="mx-auto mb-3 size-8 text-accent" />
        <label htmlFor="token" className="block text-center font-medium">
          Jeton d'accès au moteur
        </label>
        <p className="mt-2 text-center text-sm text-ink-secondary">
          {rejected ? "Jeton refusé (le moteur a redémarré ?). " : ""}
          Copie le jeton affiché par <code className="text-ink">python -m app.main</code>.
        </p>
        <input
          id="token"
          autoFocus
          value={value}
          onChange={(e) => setValue(e.target.value)}
          className="mt-4 w-full rounded-lg border border-line bg-page px-3 py-2 text-sm outline-none focus:border-accent"
          placeholder="Jeton"
        />
        <button type="submit" className="mt-3 w-full rounded-lg bg-accent-strong px-3 py-2 text-sm font-medium hover:bg-accent">
          Se connecter
        </button>
      </form>
    </Centered>
  );
}

function Centered({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-sm rounded-xl border border-line bg-surface p-6 text-center">{children}</div>
    </div>
  );
}
