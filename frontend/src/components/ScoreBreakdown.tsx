import { AlertTriangle, CircleDashed } from "lucide-react";
import type { ScoreFactor } from "../types/api";

/**
 * Détail du score : une ligne par critère.
 * Jauge = points obtenus / points possibles (une seule couleur : c'est une mesure,
 * pas une catégorie). Le calcul exact est écrit à côté, la jauge n'est qu'un repère.
 */
export function ScoreBreakdown({ factors, warnings }: { factors: ScoreFactor[]; warnings: string[] }) {
  const measured = factors.filter((f) => f.available);
  const missing = factors.filter((f) => !f.available);
  return (
    <div className="space-y-4">
      <ul className="space-y-3">
        {measured.map((f) => {
          const ratio = f.max_points > 0 ? Math.min(1, f.points / f.max_points) : 0;
          return (
            <li key={f.label}>
              <div className="flex items-baseline justify-between gap-3 text-sm">
                <span className="font-medium">{f.label}</span>
                <span className="tabular text-ink-secondary">
                  <span className="font-semibold text-ink">{f.points.toFixed(1)}</span> / {f.max_points.toFixed(1)} pts
                </span>
              </div>
              <div
                className="mt-1.5 h-2 overflow-hidden rounded-full bg-surface-raised"
                role="meter"
                aria-label={`${f.label} : ${f.points.toFixed(1)} points sur ${f.max_points.toFixed(1)}`}
                aria-valuenow={f.points}
                aria-valuemin={0}
                aria-valuemax={f.max_points}
              >
                <div className="h-full rounded-full bg-accent" style={{ width: `${ratio * 100}%` }} />
              </div>
              <p className="tabular mt-1 text-xs text-ink-muted">{f.detail}</p>
            </li>
          );
        })}
      </ul>

      {missing.length > 0 && (
        <ul className="space-y-1 border-t border-line pt-3 text-sm">
          {missing.map((f) => (
            <li key={f.label} className="flex items-center gap-2 text-ink-muted">
              <CircleDashed aria-hidden className="size-4" />
              <span className="text-ink-secondary">{f.label}</span> — non disponible ({f.detail})
            </li>
          ))}
        </ul>
      )}

      {warnings.length > 0 && (
        <ul className="space-y-1 text-sm text-warning">
          {warnings.map((w) => (
            <li key={w} className="flex items-start gap-2">
              <AlertTriangle aria-hidden className="mt-0.5 size-4 shrink-0" /> {w}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
