import { AlertTriangle, ChevronLeft, ChevronRight, RotateCcw } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { Card } from "../components/Card";
import { VillageTable } from "../components/VillageTable";
import { STRATEGY_FILTERS } from "../constants/strategies";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { usePolling } from "../hooks/usePolling";
import { api } from "../services/api";
import {
  LOOT_FIELDS,
  MIN_SCORES,
  PAGE_SIZE,
  PERIODS,
  SORTS,
  currentPage,
  filtersToQuery,
} from "./historyFilters";

const FIELD = "rounded-lg border border-line bg-page px-2.5 py-1.5 text-sm outline-none focus:border-accent";

export function HistoryPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const query = filtersToQuery(params);
  const page = currentPage(params);
  const villages = usePolling(() => api.villages(query), 15000, JSON.stringify(query));

  /** Modifie un filtre (et revient à la page 1). */
  const setFilter = (name: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(name, value);
    else next.delete(name);
    if (name !== "page") next.delete("page");
    setParams(next, { replace: true });
  };

  const total = villages.data?.total ?? 0;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const first = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const last = Math.min(page * PAGE_SIZE, total);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Historique</h1>

      <Card>
        <div className="flex flex-wrap items-end gap-3">
          <Filter label="Période">
            <select className={FIELD} value={params.get("period") ?? ""} onChange={(e) => setFilter("period", e.target.value)}>
              {PERIODS.map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
            </select>
          </Filter>
          <Filter label="Score">
            <select className={FIELD} value={params.get("min_score") ?? ""} onChange={(e) => setFilter("min_score", e.target.value)}>
              {MIN_SCORES.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
            </select>
          </Filter>
          <Filter label="Stratégie recommandée">
            <select className={FIELD} value={params.get("strategy") ?? ""} onChange={(e) => setFilter("strategy", e.target.value)}>
              <option value="">Toutes</option>
              {STRATEGY_FILTERS.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
            </select>
          </Filter>
          {LOOT_FIELDS.map((f) => (
            <LootFilter key={f.param} label={f.label} swatch={f.swatch} value={params.get(f.param) ?? ""}
              onCommit={(value) => setFilter(f.param, value)} />
          ))}
          <Filter label="Tri">
            <select className={FIELD} value={params.get("sort") ?? "date"} onChange={(e) => setFilter("sort", e.target.value)}>
              {SORTS.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
            </select>
          </Filter>
          <button type="button" onClick={() => setParams(new URLSearchParams(), { replace: true })}
            className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-ink-secondary hover:bg-surface-raised hover:text-ink">
            <RotateCcw aria-hidden className="size-4" /> Réinitialiser
          </button>
        </div>
      </Card>

      {villages.error && (
        <p className="flex items-center gap-2 rounded-lg border border-serious/40 bg-serious/10 px-3 py-2 text-sm text-serious">
          <AlertTriangle aria-hidden className="size-4" /> {villages.error.message}
        </p>
      )}

      <Card
        title={villages.loading ? "Chargement…" : `${total} village${total > 1 ? "s" : ""}`}
        action={
          total > PAGE_SIZE && (
            <div className="flex items-center gap-2 text-sm text-ink-secondary">
              <span className="tabular">{first}–{last} sur {total}</span>
              <PageButton label="Page précédente" disabled={page <= 1} onClick={() => setFilter("page", String(page - 1))}>
                <ChevronLeft className="size-4" />
              </PageButton>
              <PageButton label="Page suivante" disabled={page >= pageCount} onClick={() => setFilter("page", String(page + 1))}>
                <ChevronRight className="size-4" />
              </PageButton>
            </div>
          )
        }
      >
        <VillageTable
          villages={villages.data?.items ?? []}
          showThumbnails
          onSelect={(v) => navigate(`/analyse/${v.id}`)}
          emptyMessage="Aucun village ne correspond à ces filtres."
        />
      </Card>
    </div>
  );
}

function Filter({ label, children }: { label: ReactNode; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1 text-xs text-ink-muted">
      {label}
      {children}
    </label>
  );
}

/** Champ numérique : la recherche part 400 ms après la dernière frappe. */
function LootFilter({ label, swatch, value, onCommit }: {
  label: string; swatch: string; value: string; onCommit: (value: string) => void;
}) {
  const [text, setText] = useState(value);
  const debounced = useDebouncedValue(text);
  useEffect(() => setText(value), [value]); // réinitialisation depuis l'extérieur
  useEffect(() => {
    const cleaned = debounced.replace(/\D/g, "");
    if (cleaned !== value) onCommit(cleaned);
  }, [debounced]); // volontairement : on ne réagit qu'à la saisie (pas aux changements de `value`)
  const title = (
    <span className="inline-flex items-center gap-1.5">
      <span aria-hidden className={`size-2 rounded-full ${swatch}`} />
      {label}
    </span>
  );
  return (
    <Filter label={title}>
      <input inputMode="numeric" placeholder="0" value={text} onChange={(e) => setText(e.target.value)} className={`${FIELD} w-28 tabular`} />
    </Filter>
  );
}

function PageButton({ label, disabled, onClick, children }: {
  label: string; disabled: boolean; onClick: () => void; children: ReactNode;
}) {
  return (
    <button type="button" aria-label={label} disabled={disabled} onClick={onClick}
      className="rounded-lg border border-line p-1 hover:bg-surface-raised disabled:opacity-40">
      {children}
    </button>
  );
}
