import { Download, FolderOpen, ShieldCheck, Swords } from "lucide-react";
import type { ReactNode } from "react";
import changelog from "../../../CHANGELOG.md?raw";
import { Card } from "../components/Card";
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

        <Card title="Mises à jour">
          <p className="text-sm text-ink-secondary">
            La recherche et l'installation automatiques des mises à jour (signées, via GitHub Releases) arrivent avec
            l'application de bureau (phases 7 et 8).
          </p>
          <button type="button" disabled
            className="mt-4 inline-flex items-center gap-2 rounded-lg border border-line px-3 py-1.5 text-sm opacity-50">
            <Download aria-hidden className="size-4" /> Rechercher des mises à jour
          </button>
          <p className="mt-2 text-xs text-ink-muted">Bouton actif dans l'application installée.</p>
        </Card>
      </div>

      <Card title="Changelog">
        <Changelog markdown={changelog} />
      </Card>
    </div>
  );
}

/**
 * Affiche le CHANGELOG.md du projet (sous-ensemble Markdown : titres ## / ###,
 * listes « - », paragraphes). Pas de bibliothèque : le fichier est simple et maîtrisé.
 */
export function Changelog({ markdown }: { markdown: string }) {
  const blocks: ReactNode[] = [];
  let list: string[] = [];
  let paragraph: string[] = []; // lignes de texte consécutives = un seul paragraphe
  const flush = () => {
    if (paragraph.length) {
      blocks.push(<p key={`p${blocks.length}`} className="mb-2 text-sm text-ink-muted">{paragraph.join(" ")}</p>);
      paragraph = [];
    }
    if (list.length) {
      blocks.push(
        <ul key={`l${blocks.length}`} className="mb-3 list-disc space-y-1 pl-5 text-sm text-ink-secondary">
          {list.map((item) => <li key={item}>{item}</li>)}
        </ul>,
      );
      list = [];
    }
  };
  for (const raw of markdown.split(/\r?\n/)) {
    const line = raw.trim();
    if (line.startsWith("- ")) { list.push(line.slice(2)); continue; }
    if (line && !line.startsWith("#")) { paragraph.push(line); continue; }
    flush();
    if (!line || line.startsWith("# ")) continue; // le titre principal est déjà celui de la carte
    if (line.startsWith("## ")) blocks.push(<h3 key={blocks.length} className="mb-2 mt-4 text-base font-semibold first:mt-0">{line.slice(3)}</h3>);
    else if (line.startsWith("### ")) blocks.push(<h4 key={blocks.length} className="mb-1 mt-3 text-sm font-medium">{line.slice(4)}</h4>);
  }
  flush();
  return <div>{blocks}</div>;
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 sm:flex-row sm:justify-between sm:gap-4">
      <dt className="shrink-0 text-ink-muted">{label}</dt>
      <dd className="break-all text-right">{children}</dd>
    </div>
  );
}
