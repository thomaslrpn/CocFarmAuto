import { AlertTriangle, BellRing, CheckCircle2, Loader2, RotateCcw, Save } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { Card } from "../components/Card";
import { NumberField } from "../components/NumberField";
import { PRIORITY_LABELS } from "../constants/strategies";
import { ApiError, api } from "../services/api";
import type { AlertLevel, Loot, Priority, UpdateChannel, UserSettings, ValidationIssue } from "../types/api";

type Feedback = { kind: "ok"; message: string } | { kind: "error"; message: string; issues: ValidationIssue[] };

const RESOURCES: { key: keyof Loot; label: string }[] = [
  { key: "gold", label: "Or" },
  { key: "elixir", label: "Élixir" },
  { key: "dark_elixir", label: "Élixir noir" },
];

/** « preferences.target_loot.gold » à partir de l'emplacement d'une erreur 422. */
function issuePath(issue: ValidationIssue): string {
  return issue.loc.filter((part) => part !== "body").join(".");
}

export function SettingsPage() {
  const [saved, setSaved] = useState<UserSettings>();
  const [draft, setDraft] = useState<UserSettings>();
  const [loadError, setLoadError] = useState<string>();
  const [saving, setSaving] = useState(false);
  const [feedback, setFeedback] = useState<Feedback>();

  useEffect(() => {
    api.settings()
      .then((s) => { setSaved(s); setDraft(s); })
      .catch((e: unknown) => setLoadError(e instanceof Error ? e.message : String(e)));
  }, []);

  if (loadError) return <ErrorBox message={loadError} />;
  if (!draft || !saved) return <p className="text-sm text-ink-muted">Chargement…</p>;

  const dirty = JSON.stringify(draft) !== JSON.stringify(saved);
  const invalidPaths = new Set(feedback?.kind === "error" ? feedback.issues.map(issuePath) : []);
  // Champ en erreur : son chemin exact, ou un de ses sous-champs (ex. target_loot.gold pour target_loot).
  const isInvalid = (path: string) => [...invalidPaths].some((p) => p === path || p.startsWith(`${path}.`));

  // Mise à jour immuable d'un champ du brouillon.
  const setPrefs = (patch: Partial<UserSettings["preferences"]>) =>
    setDraft({ ...draft, preferences: { ...draft.preferences, ...patch } });
  const setSim = (patch: Partial<UserSettings["simulation"]>) =>
    setDraft({ ...draft, simulation: { ...draft.simulation, ...patch } });
  const setApp = (patch: Partial<UserSettings["app"]>) =>
    setDraft({ ...draft, app: { ...draft.app, ...patch } });

  const save = async () => {
    setSaving(true);
    setFeedback(undefined);
    try {
      const result = await api.updateSettings(draft);
      setSaved(result);
      setDraft(result);
      setFeedback({ kind: "ok", message: "Réglages enregistrés." });
    } catch (err) {
      const issues = err instanceof ApiError ? err.issues : [];
      setFeedback({ kind: "error", message: err instanceof Error ? err.message : String(err), issues });
    } finally {
      setSaving(false);
    }
  };

  const p = draft.preferences;
  const s = draft.simulation;

  return (
    <div className="space-y-6 pb-20">
      <h1 className="text-2xl font-semibold">Paramètres</h1>

      <Card title="Rentabilité">
        <p className="mb-4 text-sm text-ink-secondary">
          S'applique aux prochains villages analysés. Le rang relatif et la simulation sont recalculés immédiatement ;
          les scores déjà enregistrés gardent les réglages de leur analyse.
        </p>
        <div className="space-y-5">
          <Grid>
            <div className="flex flex-col gap-1">
              <label htmlFor="priority" className="text-xs text-ink-muted">Ressource prioritaire</label>
              <select id="priority" value={p.priority} onChange={(e) => setPrefs({ priority: e.target.value as Priority })}
                className="rounded-lg border border-line bg-page px-2.5 py-1.5 text-sm outline-none focus:border-accent">
                {(Object.keys(PRIORITY_LABELS) as Priority[]).map((key) => (
                  <option key={key} value={key}>{PRIORITY_LABELS[key]}</option>
                ))}
              </select>
              <span className="text-xs text-ink-muted">
                {p.priority === "balanced" ? "Or et élixir 40 % chacun, élixir noir 20 %." : "Cette ressource compte pour 80 % de la note, les autres 10 % chacune."}
              </span>
            </div>
            <NumberField label="Importance de l'élixir noir" value={p.dark_elixir_importance} step={0.1} min={0} max={5}
              suffix="×" onChange={(v) => setPrefs({ dark_elixir_importance: v ?? 0 })}
              invalid={isInvalid("preferences.dark_elixir_importance")} help="1 = poids normal, 0 = ignoré" />
            <NumberField label="Butin minimal (or + élixir)" value={p.min_gold_elixir} min={0} step={10000}
              onChange={(v) => setPrefs({ min_gold_elixir: v ?? 0 })} invalid={isInvalid("preferences.min_gold_elixir")}
              help="En dessous : toujours « à passer »" />
          </Grid>

          <Section title="Butin visé" help="Butin qui donne le maximum de points pour chaque ressource.">
            {RESOURCES.map((r) => (
              <NumberField key={r.key} label={r.label} value={p.target_loot[r.key]} min={1} step={r.key === "dark_elixir" ? 1000 : 50000}
                invalid={isInvalid(`preferences.target_loot.${r.key}`)}
                onChange={(v) => setPrefs({ target_loot: { ...p.target_loot, [r.key]: v ?? 0 } })} />
            ))}
          </Section>

          <Section title="Coût de ton armée" help="Déduit du butin pour une rentabilité nette (0 = non configuré).">
            {RESOURCES.map((r) => (
              <NumberField key={r.key} label={r.label} value={p.army_cost[r.key]} min={0} step={r.key === "dark_elixir" ? 100 : 10000}
                invalid={isInvalid(`preferences.army_cost.${r.key}`)}
                onChange={(v) => setPrefs({ army_cost: { ...p.army_cost, [r.key]: v ?? 0 } })} />
            ))}
          </Section>

          <Section title="Seuils de recommandation (score /100)">
            <NumberField label="Très intéressant à partir de" value={p.very_good_threshold} min={0} max={100}
              invalid={isInvalid("preferences")} onChange={(v) => setPrefs({ very_good_threshold: v ?? 0 })} />
            <NumberField label="Intéressant à partir de" value={p.good_threshold} min={0} max={100}
              invalid={isInvalid("preferences")} onChange={(v) => setPrefs({ good_threshold: v ?? 0 })} />
            <NumberField label="Moyen à partir de" value={p.average_threshold} min={0} max={100}
              invalid={isInvalid("preferences")} onChange={(v) => setPrefs({ average_threshold: v ?? 0 })} />
          </Section>
        </div>
      </Card>

      <Card title="Simulation des stratégies (hypothèses)">
        <p className="mb-4 text-sm text-ink-secondary">
          Valeurs supposées, utilisées uniquement par la comparaison des stratégies (page Statistiques).
        </p>
        <div className="space-y-5">
          <Section title="Part du butin récupérée lors d'une attaque">
            {RESOURCES.map((r) => (
              <NumberField key={r.key} label={r.label} value={Math.round(s.capture_rates[r.key] * 100)} min={0} max={100}
                suffix="%" invalid={isInvalid(`simulation.capture_rates.${r.key}`)}
                onChange={(v) => setSim({ capture_rates: { ...s.capture_rates, [r.key]: (v ?? 0) / 100 } })} />
            ))}
          </Section>
          <Grid>
            <NumberField label="Durée d'une attaque" value={s.attack_duration_s} min={1} suffix="s"
              invalid={isInvalid("simulation.attack_duration_s")} onChange={(v) => setSim({ attack_duration_s: v ?? 0 })} />
            <NumberField label="Attente entre deux attaques" value={s.army_ready_delay_s} min={0} suffix="s"
              help="Entraînement de l'armée ; 0 = armée boostée"
              invalid={isInvalid("simulation.army_ready_delay_s")} onChange={(v) => setSim({ army_ready_delay_s: v ?? 0 })} />
            <NumberField label="Coût d'une recherche" value={s.search_cost_gold} min={0} step={100} suffix="or"
              invalid={isInvalid("simulation.search_cost_gold")} onChange={(v) => setSim({ search_cost_gold: v ?? 0 })} />
            <NumberField label="Temps par village vu" value={s.search_time_s} min={0.1} step={0.5} suffix="s" nullable
              placeholder="mesuré automatiquement" help="Vide = mesuré sur tes observations"
              invalid={isInvalid("simulation.search_time_s")} onChange={(v) => setSim({ search_time_s: v })} />
          </Grid>
        </div>
      </Card>

      <Card title="Alertes">
        <p className="mb-4 text-sm text-ink-secondary">
          Préviens-toi quand un bon village apparaît pendant l'observation, même si CoC AutoFarm est caché
          derrière le jeu. S'applique immédiatement.
        </p>
        <Grid>
          <div className="flex flex-col gap-1">
            <label htmlFor="alert-level" className="text-xs text-ink-muted">Alerter pour</label>
            <select id="alert-level" value={draft.app.alert_level}
              onChange={(e) => setApp({ alert_level: e.target.value as AlertLevel })}
              className="rounded-lg border border-line bg-page px-2.5 py-1.5 text-sm outline-none focus:border-accent">
              <option value="very_interesting">Villages très intéressants</option>
              <option value="interesting">Villages intéressants ou mieux</option>
              <option value="off">Jamais (alertes désactivées)</option>
            </select>
          </div>
          <Checkbox label="Jouer un son" checked={draft.app.alert_sound}
            disabled={draft.app.alert_level === "off"} onChange={(v) => setApp({ alert_sound: v })} />
          <Checkbox label="Aussi une notification Windows" checked={draft.app.alert_notification}
            disabled={draft.app.alert_level === "off"} onChange={(v) => setApp({ alert_notification: v })}
            help="Peut être masquée par le mode « Ne pas déranger » de Windows pendant les jeux." />
        </Grid>
        <TestAlertButton disabled={dirty || draft.app.alert_level === "off"} unsaved={dirty} />
      </Card>

      <Card title="Application">
        <Grid>
          <NumberField label="Fréquence des analyses" value={draft.app.observe_interval_s} min={0.2} max={60} step={0.1} suffix="s"
            help="Délai entre deux analyses en mode observation (appliqué au prochain démarrage)"
            invalid={isInvalid("app.observe_interval_s")}
            onChange={(v) => setApp({ observe_interval_s: v ?? 0 })} />
          <div className="flex flex-col gap-1">
            <label htmlFor="update-channel" className="text-xs text-ink-muted">Canal des mises à jour</label>
            <select id="update-channel" value={draft.app.update_channel}
              onChange={(e) => setApp({ update_channel: e.target.value as UpdateChannel })}
              className="rounded-lg border border-line bg-page px-2.5 py-1.5 text-sm outline-none focus:border-accent">
              <option value="stable">Stable (recommandé)</option>
              <option value="beta">Bêta (versions de test)</option>
            </select>
            <span className="text-xs text-ink-muted">
              {draft.app.update_channel === "beta"
                ? "Reçoit les nouveautés en avant-première ; elles peuvent contenir des bugs."
                : "Uniquement les versions finalisées."}
            </span>
          </div>
          <Checkbox label="Rechercher les mises à jour automatiquement" checked={draft.app.auto_check_updates}
            onChange={(v) => setApp({ auto_check_updates: v })}
            help="Au démarrage puis toutes les 6 h. Sinon : bouton dans À propos." />
        </Grid>
        <dl className="mt-5 grid gap-x-6 gap-y-2 border-t border-line pt-4 text-sm sm:grid-cols-3">
          <Info label="Résolution de capture">automatique (taille de la fenêtre du jeu)</Info>
          <Info label="Reconnaissance">modèles intégrés (chiffres et écrans)</Info>
          <Info label="Thème">sombre</Info>
        </dl>
      </Card>

      {/* Barre d'actions fixe en bas : toujours visible pendant le défilement. */}
      <div className="fixed inset-x-0 bottom-0 z-10 border-t border-line bg-surface/95 px-6 py-3 backdrop-blur left-56">
        <div className="flex flex-wrap items-center justify-end gap-3">
          {feedback && (
            <span className={`mr-auto flex items-center gap-2 text-sm ${feedback.kind === "ok" ? "text-good" : "text-critical"}`}>
              {feedback.kind === "ok" ? <CheckCircle2 aria-hidden className="size-4" /> : <AlertTriangle aria-hidden className="size-4" />}
              {feedback.kind === "error" && feedback.issues.length > 0
                ? feedback.issues.map((i) => `${issuePath(i) || "réglages"} : ${i.msg}`).join(" · ")
                : feedback.message}
            </span>
          )}
          <button type="button" disabled={!dirty || saving} onClick={() => { setDraft(saved); setFeedback(undefined); }}
            className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-1.5 text-sm hover:bg-surface-raised disabled:opacity-40">
            <RotateCcw aria-hidden className="size-4" /> Annuler les modifications
          </button>
          <button type="button" disabled={!dirty || saving} onClick={save}
            className="inline-flex items-center gap-2 rounded-lg bg-accent-strong px-3 py-1.5 text-sm font-medium hover:bg-accent disabled:opacity-40">
            {saving ? <Loader2 aria-hidden className="size-4 animate-spin" /> : <Save aria-hidden className="size-4" />}
            Enregistrer
          </button>
        </div>
      </div>
    </div>
  );
}

function Grid({ children }: { children: ReactNode }) {
  return <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{children}</div>;
}

function Section({ title, help, children }: { title: string; help?: string; children: ReactNode }) {
  return (
    <fieldset>
      <legend className="mb-1 text-sm font-medium">{title}</legend>
      {help && <p className="mb-2 text-xs text-ink-muted">{help}</p>}
      <Grid>{children}</Grid>
    </fieldset>
  );
}

function Info({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-ink-muted">{label}</dt>
      <dd className="text-ink-secondary">{children}</dd>
    </div>
  );
}

function ErrorBox({ message }: { message: string }) {
  return (
    <p className="flex items-center gap-2 rounded-lg border border-serious/40 bg-serious/10 px-3 py-2 text-sm text-serious">
      <AlertTriangle aria-hidden className="size-4" /> {message}
    </p>
  );
}

function Checkbox({ label, checked, onChange, help, disabled = false }: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
  help?: string;
  disabled?: boolean;
}) {
  return (
    <label className={`flex items-start gap-2 self-center text-sm ${disabled ? "opacity-50" : ""}`}>
      <input type="checkbox" checked={checked} disabled={disabled} onChange={(e) => onChange(e.target.checked)}
        className="mt-0.5 size-4 accent-[var(--color-accent)]" />
      <span>
        {label}
        {help && <span className="block text-xs text-ink-muted">{help}</span>}
      </span>
    </label>
  );
}

/** Déclenche une alerte d'exemple avec les réglages ENREGISTRÉS (son + notification). */
function TestAlertButton({ disabled, unsaved }: { disabled: boolean; unsaved: boolean }) {
  const [result, setResult] = useState<string>();
  const run = async () => {
    try {
      const { sound, notification } = await api.testAlert();
      const parts = [sound && "son", notification && "notification"].filter(Boolean);
      setResult(parts.length ? `Alerte envoyée (${parts.join(" + ")}).` : "Son et notification sont désactivés.");
    } catch (err) {
      setResult(`Échec : ${err instanceof Error ? err.message : String(err)}`);
    }
  };
  return (
    <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-line pt-4">
      <button type="button" onClick={() => void run()} disabled={disabled}
        className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-1.5 text-sm hover:bg-surface-raised disabled:opacity-50">
        <BellRing aria-hidden className="size-4" /> Tester l'alerte
      </button>
      <span className="text-xs text-ink-muted">
        {unsaved ? "Enregistre tes réglages pour les tester." : result ?? "Joue le son et affiche une notification d'exemple."}
      </span>
    </div>
  );
}
