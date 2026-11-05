/**
 * Graphiques génériques à UNE série (une couleur, pas de légende : le titre la nomme).
 * Règles communes : marques fines, quadrillage discret, une seule échelle par graphique,
 * infobulle au survol, pas d'animation (les données se rafraîchissent en continu).
 */
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipContentProps,
} from "recharts";

export interface Datum {
  label: string;
  value: number;
}

const AXIS = { fill: "var(--color-ink-muted)", fontSize: 11 };
const GRID = "var(--color-line)";
const HOVER = "rgba(240, 239, 236, 0.06)";

type Format = (value: number) => string;

function makeTooltip(format: Format, unit?: string) {
  return function ChartTooltip({ active, payload }: Partial<TooltipContentProps<number, string>>) {
    const point = payload?.[0]?.payload as Datum | undefined;
    if (!active || !point) return null;
    return (
      <div className="rounded-lg border border-line bg-surface-raised px-3 py-2 text-xs shadow-lg">
        <div className="mb-0.5 text-ink-muted">{point.label}</div>
        <div className="tabular text-sm font-semibold text-ink">
          {format(point.value)}
          {unit ? ` ${unit}` : ""}
        </div>
      </div>
    );
  };
}

interface ChartProps {
  data: Datum[];
  color?: string;
  format?: Format;
  unit?: string; // ajouté dans l'infobulle (« villages », « pts/h »...)
  height?: number;
  domain?: [number, number];
  ariaLabel: string;
  /** Afficher toutes les étiquettes de l'axe X (peu de catégories, ex. tranches de score). */
  allTicks?: boolean;
}

/** Barres verticales (catégories ou jours en abscisse). */
export function SimpleBarChart({
  data, color = "var(--color-accent)", format = String, unit, height = 220, domain, ariaLabel, allTicks,
}: ChartProps) {
  const Content = makeTooltip(format, unit);
  return (
    <div style={{ height }} role="img" aria-label={ariaLabel}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }} barCategoryGap={2}>
          <CartesianGrid vertical={false} stroke={GRID} />
          <XAxis dataKey="label" tick={AXIS} tickLine={false} axisLine={{ stroke: "var(--color-axis)" }}
            interval={allTicks ? 0 : "preserveStartEnd"} minTickGap={allTicks ? 0 : 16} />
          <YAxis tick={AXIS} tickLine={false} axisLine={false} tickFormatter={format} domain={domain} width={56} />
          <Tooltip cursor={{ fill: HOVER }} content={<Content />} />
          <Bar dataKey="value" fill={color} radius={[4, 4, 0, 0]} maxBarSize={40} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Barres horizontales (libellés longs : noms de stratégies). */
export function HorizontalBarChart({ data, color = "var(--color-accent)", format = String, unit, ariaLabel }: ChartProps) {
  const Content = makeTooltip(format, unit);
  return (
    <div style={{ height: Math.max(120, data.length * 40) }} role="img" aria-label={ariaLabel}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 48, bottom: 0, left: 8 }} barCategoryGap={8}>
          <CartesianGrid horizontal={false} stroke={GRID} />
          <XAxis type="number" tick={AXIS} tickLine={false} axisLine={false} tickFormatter={format} />
          <YAxis type="category" dataKey="label" tick={{ ...AXIS, fill: "var(--color-ink-secondary)" }}
            tickLine={false} axisLine={{ stroke: "var(--color-axis)" }} width={150} />
          <Tooltip cursor={{ fill: HOVER }} content={<Content />} />
          <Bar dataKey="value" fill={color} radius={[0, 4, 4, 0]} maxBarSize={22} isAnimationActive={false}
            label={{ position: "right", fill: "var(--color-ink-secondary)", fontSize: 11, formatter: (v: unknown) => format(Number(v)) }} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

/** Courbe (évolution dans le temps). */
export function SimpleLineChart({ data, color = "var(--color-accent)", format = String, unit, height = 220, domain, ariaLabel }: ChartProps) {
  const Content = makeTooltip(format, unit);
  return (
    <div style={{ height }} role="img" aria-label={ariaLabel}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid vertical={false} stroke={GRID} />
          <XAxis dataKey="label" tick={AXIS} tickLine={false} axisLine={{ stroke: "var(--color-axis)" }}
            interval="preserveStartEnd" minTickGap={16} />
          <YAxis tick={AXIS} tickLine={false} axisLine={false} tickFormatter={format} domain={domain} width={56} />
          <Tooltip cursor={{ stroke: "var(--color-ink-muted)", strokeWidth: 1 }} content={<Content />} />
          <Line dataKey="value" stroke={color} strokeWidth={2} isAnimationActive={false}
            dot={{ r: 4, fill: color, stroke: "var(--color-surface)", strokeWidth: 2 }}
            activeDot={{ r: 5, stroke: "var(--color-surface)", strokeWidth: 2 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
