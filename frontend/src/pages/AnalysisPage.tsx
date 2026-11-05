import { AlertTriangle, ArrowLeft, ExternalLink, ImageOff, Radio } from "lucide-react";
import type { ReactNode } from "react";
import { Link, useParams } from "react-router";
import { AttackRecap, attackDuration } from "../components/AttackRecap";
import { Card } from "../components/Card";
import { FarmScoreBadge, RecommendationBadge } from "../components/RecommendationBadge";
import { ScoreBreakdown } from "../components/ScoreBreakdown";
import { StatTile } from "../components/StatTile";
import { PRIORITY_LABELS } from "../constants/strategies";
import { usePolling } from "../hooks/usePolling";
import { api, villageImageUrl } from "../services/api";
import type { ScoringPreferences, VillageDetail } from "../types/api";
import { formatDateTime, formatNumber } from "../utils/format";

/**
 * Fiche d'un village.
 * - #/analyse/12 : le village n°12 ;
 * - #/analyse    : le DERNIER village observé, mis à jour en direct pendant l'observation.
 */
export function AnalysisPage() {
  const { id } = useParams();
  const live = id === undefined;
  const requestedId = live ? undefined : Number(id);

  // Mode direct : on suit l'identifiant du village le plus récent.
  const latest = usePolling(
    () => (live ? api.villages({ limit: 1, sort: "date" }) : Promise.resolve(undefined)),
    live ? 3000 : 3_600_000,
    String(live),
  );
  const villageId = live ? latest.data?.items[0]?.id : requestedId;

  const detail = usePolling(
    () => (villageId === undefined || Number.isNaN(villageId) ? Promise.resolve(undefined) : api.village(villageId)),
    60_000,
    String(villageId),
  );
  const village = detail.data && detail.data.id === villageId ? detail.data : undefined;
  const error = detail.error ?? latest.error;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <Link to="/historique" className="mb-1 inline-flex items-center gap-1 text-sm text-ink-secondary hover:text-ink">
            <ArrowLeft aria-hidden className="size-4" /> Historique
          </Link>
          <h1 className="text-2xl font-semibold">
            Analyse{village ? ` — village du ${formatDateTime(village.analyzed_at)}` : ""}
          </h1>
        </div>
        {live && (
          <span className="inline-flex items-center gap-2 rounded-full border border-line px-3 py-1 text-xs text-ink-secondary">
            <Radio aria-hidden className="size-3.5 text-good" /> Dernier village observé (mise à jour automatique)
          </span>
        )}
      </div>

      {error && (
        <p className="flex items-center gap-2 rounded-lg border border-serious/40 bg-serious/10 px-3 py-2 text-sm text-serious">
          <AlertTriangle aria-hidden className="size-4" /> {error.message}
        </p>
      )}

      {!village ? (
        <Card>
          <p className="py-6 text-center text-sm text-ink-muted">
            {live && latest.data?.items.length === 0
              ? "Aucun village analysé pour l'instant : démarre l'observation depuis le Dashboard."
              : "Chargement…"}
          </p>
        </Card>
      ) : (
        <VillageView village={village} />
      )}
    </div>
  );
}

function VillageView({ village: v }: { village: VillageDetail }) {
  return (
    <>
      <div className="grid gap-6 xl:grid-cols-5">
        <Card className="xl:col-span-3" title="Capture" action={v.has_image && (
          <a href={villageImageUrl(v.id)} target="_blank" rel="noreferrer"
            className="inline-flex items-center gap-1 text-xs text-ink-secondary hover:text-ink">
            Taille réelle <ExternalLink aria-hidden className="size-3.5" />
          </a>
        )}>
          {v.has_image ? (
            <img src={villageImageUrl(v.id)} alt={`Capture du village analysé le ${formatDateTime(v.analyzed_at)}`}
              className="w-full rounded-lg" />
          ) : (
            <div className="flex aspect-video items-center justify-center gap-2 rounded-lg bg-surface-raised text-sm text-ink-muted">
              <ImageOff aria-hidden className="size-5" /> Capture indisponible
            </div>
          )}
        </Card>

        <Card className="xl:col-span-2" title="Verdict">
          <div className="flex items-baseline gap-2">
            <span className="text-5xl font-semibold">{v.profitability_score}</span>
            <span className="text-ink-muted">/100</span>
          </div>
          <div className="mt-2"><RecommendationBadge value={v.recommendation} /></div>
          <dl className="mt-5 space-y-2 text-sm">
            <Row label="Stratégie recommandée">{v.recommended_strategy_label}</Row>
            <Row label="Meilleur que">
              {v.relative_rank == null ? "— (premier village)" : `${Math.round(v.relative_rank)} % des villages vus`}
            </Row>
            <Row label="Confiance de lecture">{Math.round(v.detection_confidence * 100)} %</Row>
            <Row label="Hôtel de ville">{v.town_hall_level ?? "non détecté (à venir)"}</Row>
            <Row label="Difficulté">{v.estimated_difficulty ?? "non mesurée (à venir)"}</Row>
          </dl>
        </Card>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatTile label="Or disponible" value={formatNumber(v.gold)} swatchClassName="bg-gold" />
        <StatTile label="Élixir disponible" value={formatNumber(v.elixir)} swatchClassName="bg-elixir" />
        <StatTile label="Élixir noir disponible" value={formatNumber(v.dark_elixir)} swatchClassName="bg-dark-elixir" />
      </div>

      {v.attack && (
        <Card
          title={`Résultat de l'attaque · ${attackDuration(v.attack)}`}
          action={v.attack.farm_score !== null && v.attack.farm_rating !== null
            ? <FarmScoreBadge score={v.attack.farm_score} rating={v.attack.farm_rating} /> : undefined}
        >
          <AttackRecap attack={v.attack} />
          <p className="mt-3 text-xs text-ink-muted">
            Butin récupéré sur le butin disponible, lu sur l'écran du combat (« Butin disponible » restant à la fin).
            La note du farm applique au butin récupéré le même calcul que le score d'un village (ressource
            prioritaire, butin visé, coût de l'armée).
          </p>
        </Card>
      )}

      <div className="grid gap-6 xl:grid-cols-5">
        <Card className="xl:col-span-3" title="Détail du calcul">
          {v.factors.length > 0 ? <ScoreBreakdown factors={v.factors} warnings={v.warnings} />
            : <p className="text-sm text-ink-muted">Détail indisponible pour ce village.</p>}
        </Card>
        <Card className="xl:col-span-2" title="Préférences utilisées pour ce score">
          {v.preferences_used ? <PreferencesSummary prefs={v.preferences_used} />
            : <p className="text-sm text-ink-muted">Non enregistrées.</p>}
        </Card>
      </div>
    </>
  );
}

function PreferencesSummary({ prefs }: { prefs: ScoringPreferences }) {
  const loot = (l: ScoringPreferences["target_loot"]) =>
    `${formatNumber(l.gold)} or · ${formatNumber(l.elixir)} élixir · ${formatNumber(l.dark_elixir)} noir`;
  const armyConfigured = prefs.army_cost.gold + prefs.army_cost.elixir + prefs.army_cost.dark_elixir > 0;
  return (
    <dl className="space-y-2 text-sm">
      <Row label="Ressource prioritaire">{PRIORITY_LABELS[prefs.priority]}</Row>
      <Row label="Butin visé"><span className="tabular">{loot(prefs.target_loot)}</span></Row>
      <Row label="Coût de l'armée">{armyConfigured ? <span className="tabular">{loot(prefs.army_cost)}</span> : "non configuré"}</Row>
      <Row label="Importance élixir noir">× {prefs.dark_elixir_importance}</Row>
      <Row label="Seuils">
        <span className="tabular">très intéressant ≥ {prefs.very_good_threshold} · intéressant ≥ {prefs.good_threshold} · moyen ≥ {prefs.average_threshold}</span>
      </Row>
      <p className="pt-2 text-xs text-ink-muted">
        Le score est calculé avec les préférences du moment de l'analyse ; elles se modifient dans Paramètres.
      </p>
    </dl>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 sm:flex-row sm:justify-between sm:gap-4">
      <dt className="text-ink-muted">{label}</dt>
      <dd className="text-right sm:max-w-[65%]">{children}</dd>
    </div>
  );
}
