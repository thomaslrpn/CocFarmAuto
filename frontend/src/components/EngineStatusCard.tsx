import { AlertTriangle, CheckCircle2, CircleOff, Loader2, Play, Square } from "lucide-react";
import { useState, type ReactNode } from "react";
import { api } from "../services/api";
import type { ObserverStatus, ScreenName, Status } from "../types/api";
import { formatDuration, formatNumber, formatTime } from "../utils/format";
import { Card } from "./Card";
import { RecommendationBadge } from "./RecommendationBadge";

const SCREEN_LABELS: Record<ScreenName, string> = {
  home: "village",
  scout: "recherche d'adversaire",
  battle: "combat",
  unknown: "autre écran",
};

interface Props {
  status: Status | undefined;
  observer: ObserverStatus | undefined;
  onChange: () => Promise<void>; // rafraîchir après démarrage / arrêt
}

/** État du moteur + pilotage du mode observation. */
export function EngineStatusCard({ status, observer, onChange }: Props) {
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string>();
  const running = observer?.running ?? false;

  const toggle = async () => {
    setBusy(true);
    setActionError(undefined);
    try {
      await (running ? api.stopObserver() : api.startObserver());
      await onChange();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  const elapsed = observer?.started_at ? (Date.now() - new Date(observer.started_at).getTime()) / 1000 : 0;

  return (
    <Card
      title="Moteur d'analyse"
      action={
        <button
          type="button"
          onClick={toggle}
          disabled={busy || !status?.vision_ready}
          className={`inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-50 ${
            running ? "border border-line bg-surface-raised hover:bg-line" : "bg-accent-strong hover:bg-accent"
          }`}
        >
          {busy ? <Loader2 aria-hidden className="size-4 animate-spin" /> : running ? <Square aria-hidden className="size-4" /> : <Play aria-hidden className="size-4" />}
          {running ? "Arrêter l'observation" : "Démarrer l'observation"}
        </button>
      }
    >
      <ul className="space-y-2 text-sm">
        <StatusLine ok={status?.vision_ready} label="Reconnaissance visuelle" okText="prête" koText="modèles absents" />
        <StatusLine
          ok={status ? status.game_window === "found" : undefined}
          label="Fenêtre du jeu"
          okText="détectée"
          koText={status?.game_window === "unsupported" ? "non supporté (Windows requis)" : "introuvable — lance Clash of Clans"}
        />
        <li className="flex items-center gap-2">
          {running ? <Loader2 aria-hidden className="size-4 animate-spin text-good" /> : <CircleOff aria-hidden className="size-4 text-ink-muted" />}
          <span className="text-ink-secondary">Observation :</span>
          <span>{running ? `en cours depuis ${formatDuration(elapsed)}` : "arrêtée"}</span>
        </li>
      </ul>

      {observer && observer.frames > 0 && (
        <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-1 border-t border-line pt-4 text-sm sm:grid-cols-4">
          <Metric label="Analyses">{formatNumber(observer.frames)}</Metric>
          <Metric label="Villages enregistrés">{formatNumber(observer.villages_saved)}</Metric>
          <Metric label="Écran actuel">{observer.last_screen ? SCREEN_LABELS[observer.last_screen] : "—"}</Metric>
          <Metric label="Durée d'une analyse">{observer.last_cycle_ms != null ? `${observer.last_cycle_ms} ms` : "—"}</Metric>
        </dl>
      )}

      {observer?.last_village && (
        <div className="mt-4 rounded-lg bg-surface-raised p-3 text-sm">
          <div className="mb-1 text-xs text-ink-muted">Dernier village · {formatTime(observer.last_village.analyzed_at)}</div>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
            <span className="tabular">
              {formatNumber(observer.last_village.gold)} or · {formatNumber(observer.last_village.elixir)} élixir ·{" "}
              {formatNumber(observer.last_village.dark_elixir)} noir
            </span>
            <span className="font-semibold">{observer.last_village.score}/100</span>
            <RecommendationBadge value={observer.last_village.recommendation} />
            <span className="text-ink-secondary">{observer.last_village.strategy}</span>
          </div>
        </div>
      )}

      {(actionError || observer?.last_error) && (
        <p className="mt-3 flex items-start gap-2 text-sm text-serious">
          <AlertTriangle aria-hidden className="mt-0.5 size-4 shrink-0" />
          {actionError ?? `Dernière erreur : ${observer?.last_error}`}
        </p>
      )}
    </Card>
  );
}

function StatusLine({ ok, label, okText, koText }: { ok: boolean | undefined; label: string; okText: string; koText: string }) {
  return (
    <li className="flex items-center gap-2">
      {ok ? <CheckCircle2 aria-hidden className="size-4 text-good" /> : <AlertTriangle aria-hidden className="size-4 text-warning" />}
      <span className="text-ink-secondary">{label} :</span>
      <span>{ok === undefined ? "…" : ok ? okText : koText}</span>
    </li>
  );
}

function Metric({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-ink-muted">{label}</dt>
      <dd className="tabular">{children}</dd>
    </div>
  );
}
