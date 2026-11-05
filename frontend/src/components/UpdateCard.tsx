import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Download, FlaskConical, Loader2, RefreshCw, RotateCcw, Sparkles } from "lucide-react";
import { useUpdater, type UpdaterState } from "../hooks/useUpdater";
import type { InstallStep } from "../services/updater";
import { Card } from "./Card";
import { Changelog } from "./Changelog";

const STEP_LABELS: Record<InstallStep, string> = {
  download: "Téléchargement…",
  backup: "Sauvegarde de la base de données…",
  "stop-engine": "Arrêt du moteur d'analyse…",
  install: "Installation : l'application va redémarrer…",
};

const BUTTON = "inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm disabled:opacity-50";

/** Carte « Mises à jour » de la page À propos. */
export function UpdateCard() {
  const updater = useUpdater();
  const { status, lastCheck, channel } = updater;

  if (status === "unsupported") {
    return (
      <Card title="Mises à jour">
        <p className="text-sm text-ink-secondary">
          Les mises à jour automatiques fonctionnent dans l'application installée, pas dans le navigateur.
        </p>
      </Card>
    );
  }

  const busy = status === "checking" || status === "installing";
  return (
    <Card
      title="Mises à jour"
      action={
        <button type="button" onClick={() => void updater.check()} disabled={busy}
          className={`${BUTTON} border border-line hover:bg-surface-raised`}>
          <RefreshCw aria-hidden className={`size-4 ${status === "checking" ? "animate-spin" : ""}`} />
          Rechercher des mises à jour
        </button>
      }
    >
      <UpdateStatus updater={updater} />
      {lastCheck && (
        <p className="mt-3 text-xs text-ink-muted">
          Dernière vérification : {lastCheck.toLocaleString("fr-FR")} · canal {channel === "beta" ? "bêta" : "stable"} (modifiable dans Paramètres).
        </p>
      )}
    </Card>
  );
}

function UpdateStatus({ updater }: { updater: UpdaterState }) {
  const { status, update, error, step, progress, needsRestart } = updater;

  switch (status) {
    case "idle":
      return <p className="text-sm text-ink-secondary">Vérification automatique peu après le démarrage.</p>;
    case "checking":
      return <Line icon={<Loader2 className="size-4 animate-spin text-accent" />}>Recherche en cours…</Line>;
    case "up-to-date":
      return <Line icon={<CheckCircle2 className="size-4 text-good" />}>CoC AutoFarm est à jour.</Line>;
    case "error":
      return <Line icon={<AlertTriangle className="size-4 text-warning" />}>Vérification impossible : {error}</Line>;
    case "installing": {
      const percent = progress?.total ? Math.min(100, Math.round((progress.downloaded / progress.total) * 100)) : undefined;
      return (
        <div>
          <Line icon={<Loader2 className="size-4 animate-spin text-accent" />}>
            {step ? STEP_LABELS[step] : "Préparation…"}
            {step === "download" && percent !== undefined && ` ${percent} %`}
          </Line>
          {step === "download" && (
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface-raised" role="progressbar"
              aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent} aria-label="Téléchargement de la mise à jour">
              <div className="h-full rounded-full bg-accent transition-[width]" style={{ width: `${percent ?? 5}%` }} />
            </div>
          )}
        </div>
      );
    }
    case "install-error":
      return (
        <div>
          <Line icon={<AlertTriangle className="size-4 text-critical" />}>Échec de la mise à jour : {error}</Line>
          <p className="mt-2 text-sm text-ink-secondary">
            Tes données ne sont pas touchées (une sauvegarde de la base a été faite avant l'installation).
          </p>
          {needsRestart ? (
            <button type="button" onClick={() => void updater.restart()}
              className={`${BUTTON} mt-3 bg-accent-strong font-medium hover:bg-accent`}>
              <RotateCcw aria-hidden className="size-4" /> Redémarrer l'application
            </button>
          ) : (
            <button type="button" onClick={() => void updater.install()}
              className={`${BUTTON} mt-3 border border-line hover:bg-surface-raised`}>
              <Download aria-hidden className="size-4" /> Réessayer
            </button>
          )}
        </div>
      );
    case "available":
      if (!update) return null;
      return (
        <div>
          <Line icon={<Sparkles className="size-4 text-accent" />}>
            Version <strong>{update.version}</strong> disponible (installée : {update.currentVersion}).
          </Line>
          {isBetaVersion(update.version) && (
            <Line icon={<FlaskConical className="size-4 text-warning" />}>
              <span className="text-ink-secondary">
                Version bêta : nouveautés en avant-première, elle peut contenir des bugs.
              </span>
            </Line>
          )}
          {update.body && (
            <div className="mt-3 max-h-60 overflow-y-auto rounded-lg border border-line bg-page p-3">
              <Changelog markdown={update.body} />
            </div>
          )}
          <button type="button" onClick={() => void updater.install()}
            className={`${BUTTON} mt-4 bg-accent-strong font-medium hover:bg-accent`}>
            <Download aria-hidden className="size-4" /> Installer et redémarrer
          </button>
          <p className="mt-2 text-xs text-ink-muted">
            Fichier signé et vérifié avant installation. Ta base est sauvegardée automatiquement.
          </p>
        </div>
      );
  }
}

function Line({ icon, children }: { icon: ReactNode; children: ReactNode }) {
  return (
    <p className="flex items-start gap-2 text-sm">
      <span aria-hidden className="mt-0.5 shrink-0">{icon}</span>
      <span>{children}</span>
    </p>
  );
}

/** « 0.3.0-beta.1 » : une version SemVer avec suffixe est une pré-version (bêta). */
export function isBetaVersion(version: string): boolean {
  return /^\d+\.\d+\.\d+-/.test(version);
}
