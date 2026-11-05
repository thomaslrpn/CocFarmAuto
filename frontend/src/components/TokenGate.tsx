import { AlertTriangle, KeyRound, Loader2, PlugZap, Swords } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { ApiError, api, getApiUrl } from "../services/api";
import { captureTokenFromUrl, clearToken, getToken, setToken } from "../services/auth";
import { connectDesktopBackend, isDesktopApp } from "../services/desktop";

type GateState = "checking" | "ok" | "need-token" | "unreachable" | "desktop-error";

const RETRY_MS = 3000; // navigateur : le moteur est lancé à la main
const DESKTOP_RETRY_MS = 400; // application : le moteur est en train de démarrer
const DESKTOP_STARTUP_TIMEOUT_MS = 45_000; // au-delà, on considère que le démarrage a échoué

/**
 * Vérifie l'accès au moteur avant d'afficher l'application.
 * - Application de bureau : adresse et jeton fournis automatiquement ; écran de démarrage.
 * - Navigateur : jeton lu dans l'URL ou saisi ; nouvel essai si le moteur est arrêté.
 */
export function TokenGate({ children }: { children: ReactNode }) {
  const desktop = isDesktopApp();
  const [state, setState] = useState<GateState>("checking");
  const [rejected, setRejected] = useState(false);
  const [desktopError, setDesktopError] = useState<string>();
  const startedAt = useRef(Date.now());

  const check = useCallback(async () => {
    if (!getToken()) {
      setState("need-token");
      return;
    }
    try {
      await api.status();
      setState("ok");
    } catch (err) {
      if (err instanceof ApiError && err.isUnauthorized && !desktop) {
        clearToken();
        setRejected(true);
        setState("need-token");
      } else if (desktop && Date.now() - startedAt.current > DESKTOP_STARTUP_TIMEOUT_MS) {
        setDesktopError("Le moteur d'analyse ne répond pas après 45 secondes.");
        setState("desktop-error");
      } else {
        setState("unreachable");
      }
    }
  }, [desktop]);

  useEffect(() => {
    if (desktop) {
      connectDesktopBackend()
        .then(() => check())
        .catch((err: unknown) => {
          setDesktopError(String(err));
          setState("desktop-error");
        });
    } else {
      captureTokenFromUrl();
      void check();
    }
  }, [desktop, check]);

  useEffect(() => {
    if (state !== "unreachable") return;
    const timer = setInterval(() => void check(), desktop ? DESKTOP_RETRY_MS : RETRY_MS);
    return () => clearInterval(timer);
  }, [state, check, desktop]);

  if (state === "ok") return <>{children}</>;

  if (desktop) {
    if (state === "desktop-error") {
      return (
        <Centered>
          <AlertTriangle aria-hidden className="mx-auto mb-3 size-8 text-critical" />
          <p className="font-medium">Le moteur d'analyse n'a pas pu démarrer</p>
          <p className="mt-2 break-words text-sm text-ink-secondary">{desktopError}</p>
          <p className="mt-3 text-xs text-ink-muted">
            Détails dans %LOCALAPPDATA%\CoCAutoFarm\logs\autofarm.log. Ferme puis relance l'application.
          </p>
        </Centered>
      );
    }
    return <Splash />;
  }

  if (state === "checking") return <Centered>Connexion au moteur…</Centered>;
  if (state === "unreachable") {
    return (
      <Centered>
        <PlugZap aria-hidden className="mx-auto mb-3 size-8 text-warning" />
        <p className="font-medium">Le moteur d'analyse ne répond pas</p>
        <p className="mt-2 text-sm text-ink-secondary">
          Démarre-le dans un terminal : <code className="text-ink">python -m app.main</code>
        </p>
        <p className="mt-1 text-xs text-ink-muted">Nouvel essai automatique… ({getApiUrl()})</p>
      </Centered>
    );
  }
  return <TokenForm rejected={rejected} onSubmit={(token) => { setToken(token); void check(); }} />;
}

/** Écran de démarrage de l'application de bureau. */
function Splash() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <Swords aria-hidden className="size-14 text-accent" />
      <div className="text-2xl font-semibold">CoC AutoFarm</div>
      <div className="flex items-center gap-2 text-sm text-ink-secondary">
        <Loader2 aria-hidden className="size-4 animate-spin" /> Démarrage du moteur d'analyse…
      </div>
    </div>
  );
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
