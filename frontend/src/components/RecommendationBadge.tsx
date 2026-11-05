import { ChevronsUp, ChevronUp, Minus, X, type LucideIcon } from "lucide-react";
import type { FarmRating, Recommendation } from "../types/api";

const STYLES: Record<Recommendation, { icon: LucideIcon; className: string }> = {
  "très intéressant": { icon: ChevronsUp, className: "text-good border-good/40 bg-good/10" },
  intéressant: { icon: ChevronUp, className: "text-good border-good/30 bg-good/5" },
  moyen: { icon: Minus, className: "text-warning border-warning/30 bg-warning/5" },
  "à passer": { icon: X, className: "text-critical border-critical/40 bg-critical/10" },
};

/** Recommandation : couleur de statut + icône + libellé (jamais la couleur seule). */
export function RecommendationBadge({ value }: { value: Recommendation }) {
  const { icon: Icon, className } = STYLES[value] ?? STYLES.moyen;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${className}`}>
      <Icon aria-hidden className="size-3.5" />
      {value}
    </span>
  );
}

// Note d'une attaque : même échelle de couleurs et d'icônes que les recommandations.
const FARM_STYLE: Record<FarmRating, Recommendation> = {
  excellent: "très intéressant",
  bon: "intéressant",
  moyen: "moyen",
  faible: "à passer",
};

/** Note du farm d'une attaque : « 72/100 · bon », avec icône (jamais la couleur seule). */
export function FarmScoreBadge({ score, rating }: { score: number; rating: FarmRating }) {
  const { icon: Icon, className } = STYLES[FARM_STYLE[rating]];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${className}`}>
      <Icon aria-hidden className="size-3.5" />
      <span className="tabular-nums">{score}/100</span> · {rating}
    </span>
  );
}
