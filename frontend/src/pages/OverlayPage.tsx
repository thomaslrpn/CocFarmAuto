import { Loader2, Play, Square } from "lucide-react";
import { useState, type ReactNode } from "react";
import { AttackRecap, attackDuration } from "../components/AttackRecap";
import { QuickSettings } from "../components/QuickSettings";
import { FarmScoreBadge, RecommendationBadge } from "../components/RecommendationBadge";
import { usePolling } from "../hooks/usePolling";
import { api } from "../services/api";
import type { AttackSummary, ObservedVillage, ObserverStatus } from "../types/api";
import { formatNumber, formatTime } from "../utils/format";

const RESOURCES: { key: "gold" | "elixir" | "dark_elixir"; label: string; dot: string }[] = [
  { key: "gold", label: "Or", dot: "bg-gold" },
  { key: "elixir", label: "Élixir", dot: "bg-elixir" },
  { key: "dark_elixir", label: "Élixir noir", dot: "bg-dark-elixir" },
];

/**
 * Mini-fenêtre « toujours au-dessus » du jeu : le dernier village analysé en un coup d'œil.
 * Affichage seulement : elle n'agit jamais sur le jeu.
 */
export function OverlayPage() {
  const observer = usePolling(api.observer, 1000);
  return (
    <OverlayView observer={observer.data} onChange={observer.refresh}
      quickSettings={<QuickSettings onChange={observer.refresh} />} />
  );
}

export function OverlayView({ observer, onChange, quickSettings }: {
  observer?: ObserverStatus;
  onChange: () => Promise<void>;
  quickSettings?: ReactNode; // priorité + butin visé, modifiables sans quitter le jeu
}) {
  const [busy, setBusy] = useState(false);
  const running = observer?.running ?? false;
  const village = observer?.last_village ?? null;
  const attack = observer?.last_attack ?? null;
  // Juste après un combat : le récapitulatif ; dès la recherche suivante : le nouveau village.
  const showAttack = attack !== null && (village === null || Date.parse(attack.ended_at) >= Date.parse(village.analyzed_at));

  const toggle = async () => {
    setBusy(true);
    try {
      await (running ? api.stopObserver() : api.startObserver());
      await onChange();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col gap-3 p-3 text-sm">
      <div className="flex items-center justify-between gap-2">
        <span className="flex items-center gap-2 text-xs text-ink-secondary">
          <span aria-hidden className={`size-2 rounded-full ${running ? "bg-good" : "bg-ink-muted"}`} />
          {running ? "Observation en cours" : "Observation arrêtée"}
        </span>
        <button type="button" onClick={() => void toggle()} disabled={busy || !observer}
          className="inline-flex items-center gap-1.5 rounded-md border border-line px-2 py-1 text-xs hover:bg-surface-raised disabled:opacity-50">
          {busy ? <Loader2 aria-hidden className="size-3.5 animate-spin" />
            : running ? <Square aria-hidden className="size-3.5" /> : <Play aria-hidden className="size-3.5" />}
          {running ? "Arrêter" : "Démarrer"}
        </button>
      </div>
      {quickSettings}
      {showAttack && attack ? <AttackSummaryCard attack={attack} /> : village ? <VillageSummary village={village} /> : (
        <p className="flex flex-1 items-center justify-center text-center text-ink-muted">
          {running ? "En attente d'un village… Lance une recherche dans le jeu." : "Démarre l'observation pour analyser les villages."}
        </p>
      )}
    </div>
  );
}

function VillageSummary({ village }: { village: ObservedVillage }) {
  const top = village.recommendation === "très intéressant";
  return (
    <div className={`flex flex-1 flex-col gap-2 rounded-lg border p-3 ${top ? "border-good/60 bg-good/10" : "border-line bg-surface"}`}>
      <div className="flex items-center justify-between gap-2">
        <span className="text-3xl font-semibold tabular-nums">
          {village.score}<span className="text-base text-ink-muted">/100</span>
        </span>
        <RecommendationBadge value={village.recommendation} />
      </div>
      <ul className="space-y-0.5">
        {RESOURCES.map(({ key, label, dot }) => (
          <li key={key} className="flex items-center justify-between gap-2">
            <span className="flex items-center gap-2 text-ink-secondary">
              <span aria-hidden className={`size-2 rounded-full ${dot}`} /> {label}
            </span>
            <span className="tabular-nums">{formatNumber(village[key])}</span>
          </li>
        ))}
      </ul>
      <p className="text-xs text-ink-muted">{village.strategy} · {formatTime(village.analyzed_at)}</p>
    </div>
  );
}

function AttackSummaryCard({ attack }: { attack: AttackSummary }) {
  return (
    <div className="flex flex-1 flex-col gap-2 rounded-lg border border-line bg-surface p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="font-semibold">Attaque terminée</span>
        {attack.farm_score !== null && attack.farm_rating !== null && (
          <FarmScoreBadge score={attack.farm_score} rating={attack.farm_rating} />
        )}
      </div>
      <AttackRecap attack={attack} compact />
      <p className="text-xs text-ink-muted">
        Récupéré / disponible · {attackDuration(attack)} · {formatTime(attack.ended_at)}
      </p>
    </div>
  );
}
