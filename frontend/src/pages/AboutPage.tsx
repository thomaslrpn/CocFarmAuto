import { FolderOpen, ShieldCheck, Swords } from "lucide-react";
import type { ReactNode } from "react";
import changelog from "../../../CHANGELOG.md?raw";
import { Card } from "../components/Card";
import { Changelog } from "../components/Changelog";
import { UpdateCard } from "../components/UpdateCard";
import { usePolling } from "../hooks/usePolling";
import { api } from "../services/api";

export function AboutPage() {
  const status = usePolling(api.status, 60_000);
  const s = status.data;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">À propos</h1>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card>
          <div className="flex items-center gap-3">
            <Swords aria-hidden className="size-10 text-accent" />
            <div>
              <div className="text-xl font-semibold">CoC AutoFarm</div>
              <div className="text-sm text-ink-secondary">Version {s?.version ?? "…"}</div>
            </div>
          </div>
          <p className="mt-4 text-sm text-ink-secondary">
            Assistant d'analyse et d'aide à la décision pour le farm sur Clash of Clans (Google Play Games, Windows).
          </p>
          <p className="mt-3 flex items-start gap-2 text-sm text-ink-secondary">
            <ShieldCheck aria-hidden className="mt-0.5 size-4 shrink-0 text-good" />
            Outil d'observation en lecture seule : il n'envoie aucune action au jeu, n'automatise aucun combat et ne
            contourne aucune protection.
          </p>
          <dl className="mt-5 space-y-2 border-t border-line pt-4 text-sm">
            <Row label="Données (base, captures, logs)">{s?.data_dir ?? "…"}</Row>
            <Row label="Base de données">{s?.database ?? "…"}</Row>
            <Row label="Villages enregistrés">{s?.villages_count ?? "…"}</Row>
            <Row label="Licence">non définie pour l'instant</Row>
          </dl>
          <p className="mt-3 flex items-center gap-2 text-xs text-ink-muted">
            <FolderOpen aria-hidden className="size-3.5" />
            Tes données restent sur ce PC et ne sont jamais écrasées par une mise à jour.
          </p>
        </Card>

        <UpdateCard />
      </div>

      <Card title="Changelog">
        <Changelog markdown={changelog} />
      </Card>
    </div>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 sm:flex-row sm:justify-between sm:gap-4">
      <dt className="shrink-0 text-ink-muted">{label}</dt>
      <dd className="break-all text-right">{children}</dd>
    </div>
  );
}
