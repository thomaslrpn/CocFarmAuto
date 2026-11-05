import type { VillageSummary } from "../types/api";
import { formatDateTime, formatNumber } from "../utils/format";
import { RecommendationBadge } from "./RecommendationBadge";

/** Tableau des derniers villages (sert aussi de « vue tableau » du graphique). */
export function RecentVillagesTable({ villages }: { villages: VillageSummary[] }) {
  if (villages.length === 0) {
    return <p className="py-6 text-center text-sm text-ink-muted">Aucun village pour l'instant.</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line text-left text-xs text-ink-muted">
            <th className="py-2 pr-3 font-medium">Date</th>
            <th className="py-2 pr-3 text-right font-medium">Or</th>
            <th className="py-2 pr-3 text-right font-medium">Élixir</th>
            <th className="py-2 pr-3 text-right font-medium">Élixir noir</th>
            <th className="py-2 pr-3 text-right font-medium">Score</th>
            <th className="py-2 pr-3 text-right font-medium" title="Part des autres villages vus que celui-ci dépasse">
              Meilleur que
            </th>
            <th className="py-2 pr-3 font-medium">Recommandation</th>
            <th className="py-2 font-medium">Stratégie</th>
          </tr>
        </thead>
        <tbody className="tabular">
          {villages.map((v) => (
            <tr key={v.id} className="border-b border-line/60 last:border-0 hover:bg-surface-raised">
              <td className="py-2 pr-3 text-ink-secondary">{formatDateTime(v.analyzed_at)}</td>
              <td className="py-2 pr-3 text-right">{formatNumber(v.gold)}</td>
              <td className="py-2 pr-3 text-right">{formatNumber(v.elixir)}</td>
              <td className="py-2 pr-3 text-right">{formatNumber(v.dark_elixir)}</td>
              <td className="py-2 pr-3 text-right font-semibold">{v.profitability_score}</td>
              <td className="py-2 pr-3 text-right text-ink-secondary">
                {v.relative_rank == null ? "—" : `${Math.round(v.relative_rank)} %`}
              </td>
              <td className="py-2 pr-3">
                <RecommendationBadge value={v.recommendation} />
              </td>
              <td className="py-2 text-ink-secondary">{v.recommended_strategy_label}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
