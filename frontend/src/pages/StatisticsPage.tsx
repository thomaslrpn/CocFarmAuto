import { AlertTriangle, FlaskConical } from "lucide-react";
import { Card } from "../components/Card";
import { HorizontalBarChart, SimpleBarChart, SimpleLineChart } from "../components/charts";
import { usePolling } from "../hooks/usePolling";
import { api } from "../services/api";
import type { SimulationResult, StatisticsOverview } from "../types/api";
import { formatCompact, formatNumber } from "../utils/format";
import { dayLabel, goldShare, scoreHistogram } from "./statisticsData";

const HISTOGRAM_VILLAGES = 500;

export function StatisticsPage() {
  const statistics = usePolling(api.statistics, 30000);
  const villages = usePolling(() => api.villages({ limit: HISTOGRAM_VILLAGES, sort: "date" }), 30000);
  const comparison = usePolling(api.compareStrategies, 60000);

  const stats = statistics.data;
  const days = stats?.days ?? [];
  const error = statistics.error ?? villages.error ?? comparison.error;
  const oneDay = days.length === 1;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Statistiques</h1>
      {error && (
        <p className="flex items-center gap-2 rounded-lg border border-serious/40 bg-serious/10 px-3 py-2 text-sm text-serious">
          <AlertTriangle aria-hidden className="size-4" /> {error.message}
        </p>
      )}
      {oneDay && (
        <p className="text-sm text-ink-muted">
          Une seule journée de données pour l'instant : les courbes d'évolution se rempliront au fil des sessions.
        </p>
      )}

      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Villages analysés par jour">
          <SimpleBarChart data={days.map((d) => ({ label: dayLabel(d.day), value: d.villages_count }))}
            unit="villages" ariaLabel="Nombre de villages analysés par jour" />
        </Card>
        <Card title="Rentabilité moyenne par jour (score /100)">
          <SimpleLineChart data={days.map((d) => ({ label: dayLabel(d.day), value: Math.round(d.average_score) }))}
            domain={[0, 100]} unit="/ 100" ariaLabel="Score moyen de rentabilité par jour" />
        </Card>
      </div>

      <Card title="Butin identifié par jour">
        {/* Petits multiples : l'élixir noir a une autre échelle (x100) -> un graphique par ressource. */}
        <div className="grid gap-6 lg:grid-cols-3">
          {([
            ["Or", "total_gold", "var(--color-gold)"],
            ["Élixir", "total_elixir", "var(--color-elixir)"],
            ["Élixir noir", "total_dark_elixir", "var(--color-dark-elixir)"],
          ] as const).map(([label, key, color]) => (
            <div key={key}>
              <h3 className="mb-2 text-xs font-medium text-ink-secondary">{label}</h3>
              <SimpleBarChart data={days.map((d) => ({ label: dayLabel(d.day), value: d[key] }))} color={color}
                format={formatCompact} height={180} ariaLabel={`${label} identifié par jour`} />
            </div>
          ))}
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Répartition or / élixir du butin identifié">
          {stats ? <ResourceSplit stats={stats} /> : <Loading />}
        </Card>
        <Card title={`Répartition des scores (${villages.data?.items.length ?? 0} derniers villages)`}>
          <SimpleBarChart data={scoreHistogram((villages.data?.items ?? []).map((v) => v.profitability_score))}
            unit="villages" height={200} allTicks ariaLabel="Nombre de villages par tranche de score" />
        </Card>
      </div>

      <Card title="Comparaison des stratégies (simulation théorique)">
        {comparison.data ? (
          comparison.data.results.length === 0 ? (
            <p className="text-sm text-ink-muted">Aucun village enregistré : rien à simuler.</p>
          ) : (
            <StrategyComparisonView results={comparison.data.results} assumptions={comparison.data.assumptions}
              armyConfigured={comparison.data.army_cost_configured} />
          )
        ) : (
          <Loading />
        )}
      </Card>
    </div>
  );
}

/** Barre 100 % à deux segments, libellés directs + légende (identité jamais par la couleur seule). */
function ResourceSplit({ stats }: { stats: StatisticsOverview }) {
  const share = goldShare(stats.total_gold, stats.total_elixir);
  const segments = [
    { label: "Or", value: stats.total_gold, share, className: "bg-gold" },
    { label: "Élixir", value: stats.total_elixir, share: 1 - share, className: "bg-elixir" },
  ];
  return (
    <div>
      <div className="flex h-10 gap-0.5 overflow-hidden rounded-lg" role="img"
        aria-label={`Or ${Math.round(share * 100)} %, élixir ${Math.round((1 - share) * 100)} %`}>
        {segments.map((s) => s.share > 0 && (
          <div key={s.label} className={`${s.className} flex items-center px-3 text-sm font-semibold text-white`}
            style={{ width: `${s.share * 100}%` }} title={`${s.label} : ${formatNumber(s.value)}`}>
            {s.share >= 0.12 && `${Math.round(s.share * 100)} %`}
          </div>
        ))}
      </div>
      <ul className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-sm">
        {segments.map((s) => (
          <li key={s.label} className="flex items-center gap-2">
            <span aria-hidden className={`size-2.5 rounded-full ${s.className}`} />
            <span className="text-ink-secondary">{s.label}</span>
            <span className="tabular">{formatNumber(s.value)}</span>
          </li>
        ))}
        <li className="flex items-center gap-2">
          <span aria-hidden className="size-2.5 rounded-full bg-dark-elixir" />
          <span className="text-ink-secondary">Élixir noir (autre échelle)</span>
          <span className="tabular">{formatNumber(stats.total_dark_elixir)}</span>
        </li>
      </ul>
    </div>
  );
}

function StrategyComparisonView({ results, assumptions, armyConfigured }: {
  results: SimulationResult[]; assumptions: string[]; armyConfigured: boolean;
}) {
  return (
    <div className="space-y-5">
      <div>
        <h3 className="mb-2 text-xs font-medium text-ink-secondary">
          Rendement : valeur du butin net par heure (points/h, même échelle que le score)
        </h3>
        <HorizontalBarChart data={results.map((r) => ({ label: r.strategy.label, value: Math.round(r.points_per_hour) }))}
          format={formatNumber} unit="pts/h" ariaLabel="Points par heure de chaque stratégie" />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line text-left text-xs text-ink-muted">
              <th className="py-2 pr-3 font-medium">Stratégie</th>
              <th className="py-2 pr-3 text-right font-medium">Attaques</th>
              <th className="py-2 pr-3 text-right font-medium">Villages passés</th>
              <th className="py-2 pr-3 text-right font-medium">Or net/h</th>
              <th className="py-2 pr-3 text-right font-medium">Élixir net/h</th>
              <th className="py-2 pr-3 text-right font-medium">Noir net/h</th>
              <th className="py-2 text-right font-medium">Points/h</th>
            </tr>
          </thead>
          <tbody className="tabular">
            {results.map((r) => (
              <tr key={r.strategy.key} className="border-b border-line/60 last:border-0" title={r.strategy.description}>
                <td className="py-2 pr-3">{r.strategy.label}</td>
                <td className="py-2 pr-3 text-right">{r.attacks}/{r.villages_seen}</td>
                <td className="py-2 pr-3 text-right">{Math.round(r.skip_rate * 100)} %</td>
                <td className="py-2 pr-3 text-right">{formatNumber(r.net_per_hour.gold)}</td>
                <td className="py-2 pr-3 text-right">{formatNumber(r.net_per_hour.elixir)}</td>
                <td className="py-2 pr-3 text-right">{formatNumber(r.net_per_hour.dark_elixir)}</td>
                <td className="py-2 text-right font-semibold">{formatNumber(r.points_per_hour)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="rounded-lg bg-surface-raised p-3 text-xs text-ink-secondary">
        <div className="mb-1 flex items-center gap-1.5 font-medium text-ink">
          <FlaskConical aria-hidden className="size-4" /> Hypothèses de la simulation (réglables dans Paramètres)
        </div>
        <ul className="space-y-0.5">
          {assumptions.map((a) => <li key={a}>{a}</li>)}
          {!armyConfigured && <li className="text-warning">[non configuré] coût de l'armée = 0 : butin net surestimé</li>}
        </ul>
      </div>
    </div>
  );
}

function Loading() {
  return <p className="py-6 text-center text-sm text-ink-muted">Chargement…</p>;
}
