import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis, type TooltipContentProps } from "recharts";
import type { VillageSummary } from "../types/api";
import { formatDateTime, formatNumber } from "../utils/format";

/*
 * Une seule série (le score) : une seule couleur, pas de légende (le titre la nomme).
 * Barres fines à coins arrondis côté valeur, quadrillage discret, survol par barre.
 */
const COLORS = {
  bar: "var(--color-accent)",
  grid: "var(--color-line)",
  axis: "var(--color-ink-muted)",
  hover: "rgba(240, 239, 236, 0.06)",
};

interface Point {
  label: string;
  score: number;
  village: VillageSummary;
}

export function ScoreChart({ villages }: { villages: VillageSummary[] }) {
  // L'API renvoie du plus récent au plus ancien : on remet dans l'ordre chronologique.
  const data: Point[] = [...villages]
    .reverse()
    .map((v) => ({ label: formatDateTime(v.analyzed_at), score: v.profitability_score, village: v }));

  if (data.length === 0) {
    return <p className="py-10 text-center text-sm text-ink-muted">Aucun village analysé pour l'instant.</p>;
  }
  return (
    <div className="h-64" role="img" aria-label={`Scores de rentabilité des ${data.length} derniers villages`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -16 }} barCategoryGap={2}>
          <CartesianGrid vertical={false} stroke={COLORS.grid} />
          <XAxis
            dataKey="label"
            tick={{ fill: COLORS.axis, fontSize: 11 }}
            tickLine={false}
            axisLine={{ stroke: "var(--color-axis)" }}
            interval="preserveStartEnd"
            minTickGap={24}
          />
          <YAxis
            domain={[0, 100]}
            ticks={[0, 25, 50, 75, 100]}
            tick={{ fill: COLORS.axis, fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            className="tabular"
          />
          <Tooltip cursor={{ fill: COLORS.hover }} content={<ScoreTooltip />} />
          {/* Pas d'animation : les données se rafraîchissent en continu, elle se rejouerait sans cesse. */}
          <Bar dataKey="score" fill={COLORS.bar} radius={[4, 4, 0, 0]} maxBarSize={22} activeBar={{ fillOpacity: 0.8 }}
            isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function ScoreTooltip({ active, payload }: Partial<TooltipContentProps<number, string>>) {
  const point = payload?.[0]?.payload as Point | undefined;
  if (!active || !point) return null;
  const v = point.village;
  return (
    <div className="rounded-lg border border-line bg-surface-raised px-3 py-2 text-xs shadow-lg">
      <div className="mb-1 text-ink-muted">{point.label}</div>
      <div className="text-sm font-semibold text-ink">
        {v.profitability_score}/100 · {v.recommendation}
      </div>
      <div className="tabular mt-1 text-ink-secondary">
        {formatNumber(v.gold)} or · {formatNumber(v.elixir)} élixir · {formatNumber(v.dark_elixir)} noir
      </div>
    </div>
  );
}
