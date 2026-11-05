import type { AttackSummary } from "../types/api";
import { formatNumber } from "../utils/format";

type Resource = "gold" | "elixir" | "dark_elixir";

const ROWS: { key: Resource; label: string; color: string }[] = [
  { key: "gold", label: "Or", color: "bg-gold" },
  { key: "elixir", label: "Élixir", color: "bg-elixir" },
  { key: "dark_elixir", label: "Élixir noir", color: "bg-dark-elixir" },
];

export interface RecapRow {
  key: Resource;
  gained: number | null;
  available: number;
  percent: number | null; // null : non lu, ou rien de disponible
}

/** Lignes du récapitulatif (récupéré / disponible / pourcentage) ; testé séparément. */
export function recapRows(attack: AttackSummary): RecapRow[] {
  return ROWS.map(({ key }) => {
    const gained = attack[`gained_${key}`];
    const available = attack[`available_${key}`];
    const percent = gained !== null && available > 0 ? Math.min(100, Math.round((gained / available) * 100)) : null;
    return { key, gained, available, percent };
  });
}

/** Durée d'une attaque, ex. « 2 min 41 s ». */
export function attackDuration(attack: AttackSummary): string {
  const seconds = Math.max(0, Math.round((Date.parse(attack.ended_at) - Date.parse(attack.started_at)) / 1000));
  const minutes = Math.floor(seconds / 60);
  return minutes > 0 ? `${minutes} min ${seconds % 60} s` : `${seconds} s`;
}

/**
 * Récapitulatif d'une attaque : butin récupéré sur butin disponible, par ressource.
 * La couleur ne sert qu'à identifier la ressource (pastille + jauge) ; les chiffres restent en texte.
 */
export function AttackRecap({ attack, compact = false }: { attack: AttackSummary; compact?: boolean }) {
  return (
    <ul className={compact ? "space-y-1.5" : "space-y-3"}>
      {recapRows(attack).map((row) => {
        const meta = ROWS.find((r) => r.key === row.key)!;
        return (
          <li key={row.key}>
            <div className="flex items-baseline justify-between gap-2 text-sm">
              <span className="flex items-center gap-2 text-ink-secondary">
                <span aria-hidden className={`size-2 rounded-full ${meta.color}`} /> {meta.label}
              </span>
              <span className="tabular-nums">
                {row.gained === null ? (
                  <span className="text-ink-muted">non lu</span>
                ) : (
                  <>
                    <span className="font-medium text-ink">{formatNumber(row.gained)}</span>
                    <span className="text-ink-muted"> / {formatNumber(row.available)}</span>
                    {row.percent !== null && <span className="ml-1.5 text-ink-secondary">{row.percent} %</span>}
                  </>
                )}
              </span>
            </div>
            {!compact && row.percent !== null && (
              <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-surface-raised" role="meter"
                aria-valuemin={0} aria-valuemax={100} aria-valuenow={row.percent} aria-label={`${meta.label} récupéré`}>
                <div className={`h-full rounded-full ${meta.color}`} style={{ width: `${row.percent}%` }} />
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}
