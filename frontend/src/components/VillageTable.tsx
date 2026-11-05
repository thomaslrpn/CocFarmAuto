import { ImageOff } from "lucide-react";
import { villageImageUrl } from "../services/api";
import type { VillageSummary } from "../types/api";
import { formatDateTime, formatNumber } from "../utils/format";
import { RecommendationBadge } from "./RecommendationBadge";

const THUMB_WIDTH = 160; // px demandés au backend (affichés en 80 px : net sur écran haute densité)

interface Props {
  villages: VillageSummary[];
  /** Ligne cliquable (ouvre la fiche du village). */
  onSelect?: (village: VillageSummary) => void;
  showThumbnails?: boolean;
  emptyMessage?: string;
}

/** Tableau de villages : dashboard (derniers villages) et historique (avec miniatures). */
export function VillageTable({ villages, onSelect, showThumbnails = false, emptyMessage = "Aucun village." }: Props) {
  if (villages.length === 0) {
    return <p className="py-6 text-center text-sm text-ink-muted">{emptyMessage}</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line text-left text-xs text-ink-muted">
            {showThumbnails && <th className="py-2 pr-3 font-medium">Capture</th>}
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
            <tr
              key={v.id}
              onClick={onSelect ? () => onSelect(v) : undefined}
              onKeyDown={onSelect ? (e) => e.key === "Enter" && onSelect(v) : undefined}
              tabIndex={onSelect ? 0 : undefined}
              className={`border-b border-line/60 last:border-0 hover:bg-surface-raised ${
                onSelect ? "cursor-pointer focus:bg-surface-raised focus:outline-none" : ""
              }`}
            >
              {showThumbnails && (
                <td className="py-1.5 pr-3">
                  {v.has_image ? (
                    <img
                      src={villageImageUrl(v.id, THUMB_WIDTH)}
                      alt=""
                      loading="lazy"
                      className="h-[45px] w-20 rounded object-cover"
                    />
                  ) : (
                    <div className="flex h-[45px] w-20 items-center justify-center rounded bg-surface-raised">
                      <ImageOff aria-label="pas de capture" className="size-4 text-ink-muted" />
                    </div>
                  )}
                </td>
              )}
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
