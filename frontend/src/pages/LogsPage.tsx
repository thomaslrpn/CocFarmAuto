import { AlertTriangle, Bug, Info, Pause, Play, Search, XCircle, type LucideIcon } from "lucide-react";
import { useMemo, useState } from "react";
import { Card } from "../components/Card";
import { usePolling } from "../hooks/usePolling";
import { api } from "../services/api";
import type { LogEntry, LogLevel } from "../types/api";
import { formatTime } from "../utils/format";

const LEVELS: Record<LogLevel, { rank: number; icon: LucideIcon; className: string; label: string }> = {
  DEBUG: { rank: 0, icon: Bug, className: "text-ink-muted", label: "Debug" },
  INFO: { rank: 1, icon: Info, className: "text-ink-secondary", label: "Info" },
  WARNING: { rank: 2, icon: AlertTriangle, className: "text-warning", label: "Alerte" },
  ERROR: { rank: 3, icon: XCircle, className: "text-critical", label: "Erreur" },
  CRITICAL: { rank: 4, icon: XCircle, className: "text-critical", label: "Critique" },
};

/** Catégories techniques -> libellés (les inconnues s'affichent telles quelles). */
const CATEGORY_LABELS: Record<string, string> = {
  observer_service: "observation",
  observer: "observation",
  capture: "capture",
  vision: "vision",
  database: "base de données",
  api: "api",
  main: "démarrage",
};

const FIELD = "rounded-lg border border-line bg-page px-2.5 py-1.5 text-sm outline-none focus:border-accent";

/** Filtre les événements (niveau minimal, catégorie, texte) ; plus récents en premier. */
export function filterLogs(entries: LogEntry[], minLevel: LogLevel, category: string, text: string): LogEntry[] {
  const needle = text.trim().toLowerCase();
  return entries
    .filter((e) => (LEVELS[e.level]?.rank ?? 1) >= LEVELS[minLevel].rank)
    .filter((e) => !category || categoryLabel(e.category) === category)
    .filter((e) => !needle || e.message.toLowerCase().includes(needle))
    .sort((a, b) => b.id - a.id);
}

function categoryLabel(category: string): string {
  return CATEGORY_LABELS[category] ?? category;
}

export function LogsPage() {
  const [paused, setPaused] = useState(false);
  const [minLevel, setMinLevel] = useState<LogLevel>("INFO");
  const [category, setCategory] = useState("");
  const [text, setText] = useState("");
  // En pause : on garde les données affichées (intervalle très long).
  const logs = usePolling(() => api.logs(0, "INFO"), paused ? 3_600_000 : 2000, String(paused));

  const entries = logs.data ?? [];
  const categories = useMemo(() => [...new Set(entries.map((e) => categoryLabel(e.category)))].sort(), [entries]);
  const visible = filterLogs(entries, minLevel, category, text);
  const counts = { warnings: entries.filter((e) => e.level === "WARNING").length,
    errors: entries.filter((e) => e.level === "ERROR" || e.level === "CRITICAL").length };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h1 className="text-2xl font-semibold">Logs</h1>
        <span className="text-xs text-ink-muted">
          {entries.length} événement(s) en mémoire · {counts.warnings} alerte(s) · {counts.errors} erreur(s) · journal complet :
          dossier logs\autofarm.log
        </span>
      </div>

      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-xs text-ink-muted">
            Niveau minimal
            <select className={FIELD} value={minLevel} onChange={(e) => setMinLevel(e.target.value as LogLevel)}>
              <option value="INFO">Tout</option>
              <option value="WARNING">Alertes et erreurs</option>
              <option value="ERROR">Erreurs seulement</option>
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs text-ink-muted">
            Module
            <select className={FIELD} value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">Tous</option>
              {categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </label>
          <label className="flex flex-1 flex-col gap-1 text-xs text-ink-muted">
            Rechercher
            <span className={`${FIELD} flex items-center gap-2`}>
              <Search aria-hidden className="size-4 text-ink-muted" />
              <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Texte du message"
                className="w-full bg-transparent outline-none" />
            </span>
          </label>
          <button type="button" onClick={() => setPaused(!paused)}
            className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-1.5 text-sm hover:bg-surface-raised">
            {paused ? <Play aria-hidden className="size-4" /> : <Pause aria-hidden className="size-4" />}
            {paused ? "Reprendre" : "Pause"}
          </button>
        </div>
      </Card>

      {logs.error && (
        <p className="flex items-center gap-2 rounded-lg border border-serious/40 bg-serious/10 px-3 py-2 text-sm text-serious">
          <AlertTriangle aria-hidden className="size-4" /> {logs.error.message}
        </p>
      )}

      <Card>
        {visible.length === 0 ? (
          <p className="py-6 text-center text-sm text-ink-muted">
            {entries.length === 0 ? "Aucun événement pour l'instant." : "Aucun événement ne correspond aux filtres."}
          </p>
        ) : (
          <ul className="divide-y divide-line/60 text-sm">
            {visible.map((e) => <LogLine key={e.id} entry={e} />)}
          </ul>
        )}
      </Card>
    </div>
  );
}

function LogLine({ entry: e }: { entry: LogEntry }) {
  const level = LEVELS[e.level] ?? LEVELS.INFO;
  const Icon = level.icon;
  const data = Object.entries(e.data);
  return (
    <li className="flex flex-wrap items-start gap-x-3 gap-y-1 py-2">
      <span className="tabular w-16 shrink-0 text-ink-muted">{formatTime(e.time)}</span>
      <span className={`inline-flex w-20 shrink-0 items-center gap-1 ${level.className}`}>
        <Icon aria-hidden className="size-3.5" /> {level.label}
      </span>
      <span className="w-28 shrink-0 text-ink-muted">{categoryLabel(e.category)}</span>
      <span className="min-w-0 flex-1 break-words">{e.message}</span>
      {data.length > 0 && (
        <span className="flex flex-wrap gap-1">
          {data.map(([k, v]) => (
            <span key={k} className="tabular rounded bg-surface-raised px-1.5 py-0.5 text-xs text-ink-secondary">
              {k === "duration_ms" ? `${v} ms` : `${k}: ${String(v)}`}
            </span>
          ))}
        </span>
      )}
    </li>
  );
}
