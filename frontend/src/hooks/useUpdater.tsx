/**
 * État des mises à jour, partagé par toute l'application (menu + page À propos).
 *
 * Vérification automatique (si activée dans Paramètres) : peu après le démarrage puis
 * toutes les 6 heures, sur le canal choisi (stable ou bêta).
 * Une vérification automatique qui échoue reste discrète (pas d'alerte) ;
 * une vérification manuelle affiche le message d'erreur.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { api } from "../services/api";
import { isDesktopApp } from "../services/desktop";
import {
  checkForUpdate,
  describeUpdateError,
  installUpdate,
  restartApp,
  type DownloadProgress,
  type InstallStep,
  type Update,
} from "../services/updater";
import type { UpdateChannel } from "../types/api";

const FIRST_CHECK_DELAY_MS = 15_000;
const CHECK_INTERVAL_MS = 6 * 60 * 60 * 1000;

export type UpdaterStatus =
  | "unsupported" // navigateur : pas de mises à jour (développement)
  | "idle"
  | "checking"
  | "up-to-date"
  | "available"
  | "installing"
  | "error" // la vérification a échoué
  | "install-error"; // l'installation a échoué

export interface UpdaterState {
  status: UpdaterStatus;
  update?: Update;
  error?: string;
  /** Le moteur a déjà été arrêté : il faut relancer l'application. */
  needsRestart: boolean;
  step?: InstallStep;
  progress?: DownloadProgress;
  lastCheck?: Date;
  /** Canal utilisé à la dernière vérification (réglage dans Paramètres). */
  channel: UpdateChannel;
  check: () => Promise<void>;
  install: () => Promise<void>;
  restart: () => Promise<void>;
}

const UpdaterContext = createContext<UpdaterState | null>(null);

export function UpdaterProvider({ children }: { children: ReactNode }) {
  const supported = isDesktopApp();
  const [status, setStatus] = useState<UpdaterStatus>(supported ? "idle" : "unsupported");
  const [update, setUpdate] = useState<Update>();
  const [error, setError] = useState<string>();
  const [step, setStep] = useState<InstallStep>();
  const [progress, setProgress] = useState<DownloadProgress>();
  const [lastCheck, setLastCheck] = useState<Date>();
  const [needsRestart, setNeedsRestart] = useState(false);
  const [channel, setChannel] = useState<UpdateChannel>("stable");
  const busy = useRef(false); // évite deux vérifications / installations simultanées

  const runCheck = useCallback(async (manual: boolean) => {
    if (!supported || busy.current) return;
    busy.current = true;
    try {
      // Réglages relus à chaque fois : un changement de canal s'applique sans redémarrer.
      const { app } = await api.settings();
      setChannel(app.update_channel);
      if (!manual && !app.auto_check_updates) return; // vérification automatique désactivée
      if (manual) setStatus("checking");
      const found = await checkForUpdate(app.update_channel);
      setUpdate(found ?? undefined);
      setError(undefined);
      setStatus(found ? "available" : "up-to-date");
    } catch (err) {
      setError(describeUpdateError(err));
      // Échec silencieux en automatique, sauf si une mise à jour était déjà connue.
      setStatus((current) => (manual ? "error" : current === "checking" ? "idle" : current));
    } finally {
      busy.current = false;
    }
    setLastCheck(new Date());
  }, [supported]);

  useEffect(() => {
    if (!supported) return;
    const first = setTimeout(() => void runCheck(false), FIRST_CHECK_DELAY_MS);
    const periodic = setInterval(() => void runCheck(false), CHECK_INTERVAL_MS);
    return () => {
      clearTimeout(first);
      clearInterval(periodic);
    };
  }, [supported, runCheck]);

  const install = useCallback(async () => {
    if (!update || busy.current) return;
    busy.current = true;
    setStatus("installing");
    setError(undefined);
    let currentStep: InstallStep | undefined;
    try {
      await installUpdate(update, (s) => { currentStep = s; setStep(s); }, setProgress);
    } catch (err) {
      setError(describeUpdateError(err));
      // Après l'arrêt du moteur, l'application ne peut plus fonctionner sans redémarrage.
      setNeedsRestart(currentStep === "stop-engine" || currentStep === "install");
      setStatus("install-error");
    } finally {
      busy.current = false;
    }
  }, [update]);

  const value = useMemo<UpdaterState>(() => ({
    status, update, error, needsRestart, step, progress, lastCheck, channel,
    check: () => runCheck(true),
    install,
    restart: restartApp,
  }), [status, update, error, needsRestart, step, progress, lastCheck, channel, runCheck, install]);

  return <UpdaterContext.Provider value={value}>{children}</UpdaterContext.Provider>;
}

export function useUpdater(): UpdaterState {
  const value = useContext(UpdaterContext);
  if (!value) throw new Error("useUpdater doit être utilisé dans <UpdaterProvider>");
  return value;
}
