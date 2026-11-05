import { ChevronsUp, ChevronUp, Minus, X, type LucideIcon } from "lucide-react";
import type { Recommendation } from "../types/api";

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
