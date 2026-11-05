import { AlertTriangle, CheckCircle2, FlaskConical, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../services/api";
import { fetchReleases, visibleVersions, type PublishedVersion } from "../services/releases";
import { Card } from "./Card";
import { Changelog } from "./Changelog";

/** Versions publiées sur GitHub (canal choisi), avec la version installée repérée. */
export function ReleaseHistory({ installedVersion }: { installedVersion?: string }) {
  const [versions, setVersions] = useState<PublishedVersion[]>();
  const [error, setError] = useState<string>();

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchReleases(), api.settings()])
      .then(([releases, settings]) => {
        if (!cancelled) setVersions(visibleVersions(releases, settings.app.update_channel));
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      });
    return () => { cancelled = true; };
  }, []);

  return (
    <Card title="Historique des versions">
      {error && (
        <p className="flex items-center gap-2 text-sm text-ink-secondary">
          <AlertTriangle aria-hidden className="size-4 text-warning" />
          Historique indisponible (connexion internet ?) : {error}
        </p>
      )}
      {!error && !versions && (
        <p className="flex items-center gap-2 text-sm text-ink-muted">
          <Loader2 aria-hidden className="size-4 animate-spin" /> Chargement depuis GitHub…
        </p>
      )}
      {versions?.length === 0 && <p className="text-sm text-ink-muted">Aucune version publiée.</p>}
      {versions && versions.length > 0 && (
        <ul className="divide-y divide-line">
          {versions.map((v) => (
            <li key={v.version} className="py-2">
              <details>
                <summary className="flex cursor-pointer flex-wrap items-center gap-x-3 gap-y-1 text-sm">
                  <span className="font-medium">{v.version}</span>
                  {v.date && <span className="text-ink-muted">{new Date(v.date).toLocaleDateString("fr-FR")}</span>}
                  {v.beta && (
                    <span className="inline-flex items-center gap-1 rounded-full border border-line px-2 text-xs text-ink-secondary">
                      <FlaskConical aria-hidden className="size-3" /> bêta
                    </span>
                  )}
                  {v.version === installedVersion && (
                    <span className="inline-flex items-center gap-1 text-xs text-ink-secondary">
                      <CheckCircle2 aria-hidden className="size-3.5 text-good" /> installée
                    </span>
                  )}
                </summary>
                <div className="mt-2 pl-1">
                  {v.notes ? <Changelog markdown={v.notes} /> : <p className="text-sm text-ink-muted">Pas de notes.</p>}
                </div>
              </details>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
