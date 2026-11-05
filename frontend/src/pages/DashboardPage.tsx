import { AlertTriangle } from "lucide-react";
import { useEffect } from "react";
import { useNavigate } from "react-router";
import { Card } from "../components/Card";
import { EngineStatusCard } from "../components/EngineStatusCard";
import { ScoreChart } from "../components/ScoreChart";
import { StatTile } from "../components/StatTile";
import { VillageTable } from "../components/VillageTable";
import { usePolling } from "../hooks/usePolling";
import { api } from "../services/api";
import { formatCompact, formatNumber } from "../utils/format";

const CHART_VILLAGES = 30;
const TABLE_VILLAGES = 8;

export function DashboardPage() {
  const navigate = useNavigate();
  const status = usePolling(api.status, 5000);
  const observer = usePolling(api.observer, 2000);
  const statistics = usePolling(api.statistics, 10000);
  const villages = usePolling(() => api.villages({ limit: CHART_VILLAGES, sort: "date" }), 10000);

  // Un nouveau village vient d'être enregistré : on rafraîchit tout de suite.
  const saved = observer.data?.villages_saved;
  const { refresh: refreshStats } = statistics;
  const { refresh: refreshVillages } = villages;
  useEffect(() => {
    if (saved) {
      void refreshStats();
      void refreshVillages();
    }
  }, [saved, refreshStats, refreshVillages]);

  const stats = statistics.data;
  const recent = villages.data?.items ?? [];
  const error = status.error ?? observer.error ?? statistics.error ?? villages.error;

  return (
    <div className="space-y-6">
      <div className="flex items-baseline justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        {status.data && <span className="text-xs text-ink-muted">Version {status.data.version}</span>}
      </div>

      {error && (
        <p className="flex items-center gap-2 rounded-lg border border-serious/40 bg-serious/10 px-3 py-2 text-sm text-serious">
          <AlertTriangle aria-hidden className="size-4" /> {error.message}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatTile label="Villages analysés" value={stats ? formatNumber(stats.villages_count) : "…"} />
        <StatTile
          label="Score moyen"
          value={stats?.average_score != null ? `${Math.round(stats.average_score)}/100` : "—"}
          hint="rentabilité selon tes préférences"
        />
        <StatTile label="Or identifié" value={stats ? formatCompact(stats.total_gold) : "…"} swatchClassName="bg-gold"
          hint={stats ? formatNumber(stats.total_gold) : undefined} />
        <StatTile label="Élixir identifié" value={stats ? formatCompact(stats.total_elixir) : "…"} swatchClassName="bg-elixir"
          hint={stats ? formatNumber(stats.total_elixir) : undefined} />
        <StatTile label="Élixir noir identifié" value={stats ? formatCompact(stats.total_dark_elixir) : "…"}
          swatchClassName="bg-dark-elixir" hint={stats ? formatNumber(stats.total_dark_elixir) : undefined} />
      </div>

      <EngineStatusCard
        status={status.data}
        observer={observer.data}
        onChange={async () => {
          await Promise.all([observer.refresh(), status.refresh()]);
        }}
      />

      <Card title={`Score de rentabilité des ${CHART_VILLAGES} derniers villages`}>
        <ScoreChart villages={recent} />
      </Card>

      <Card title="Historique récent">
        <VillageTable
          villages={recent.slice(0, TABLE_VILLAGES)}
          onSelect={(v) => navigate(`/analyse/${v.id}`)}
          emptyMessage="Aucun village pour l'instant : démarre l'observation."
        />
      </Card>
    </div>
  );
}
