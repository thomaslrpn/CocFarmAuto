import { useEffect, useState } from "react";
import { usePolling } from "../hooks/usePolling";
import { api } from "../services/api";
import type { Priority } from "../types/api";
import { formatNumber } from "../utils/format";

const OPTIONS: { value: Priority; label: string }[] = [
  { value: "balanced", label: "Équilibré" },
  { value: "gold", label: "Or" },
  { value: "elixir", label: "Élixir" },
  { value: "dark_elixir", label: "Noir" },
];

/**
 * Réglages rapides de la mini-fenêtre : ressource prioritaire et butin visé pour cette ressource.
 * Enregistrés comme dans la page Paramètres ; le village affiché est recalculé aussitôt.
 */
export function QuickSettings({ onChange }: { onChange: () => Promise<void> }) {
  const settings = usePolling(api.settings, 5000); // suit aussi les changements faits dans la fenêtre principale
  const prefs = settings.data?.preferences;
  const [target, setTarget] = useState("");
  const [error, setError] = useState<string>();
  const focused = prefs && prefs.priority !== "balanced" ? prefs.priority : null;
  const currentTarget = focused && prefs ? prefs.target_loot[focused] : null;

  useEffect(() => {
    setTarget(currentTarget === null ? "" : String(currentTarget));
  }, [currentTarget]);

  if (!prefs) return null;

  const save = async (update: Parameters<typeof api.updateSettings>[0]) => {
    setError(undefined);
    try {
      await api.updateSettings(update);
      await Promise.all([settings.refresh(), onChange()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const saveTarget = () => {
    const value = Number(target.replace(/\s/g, ""));
    if (!focused || !Number.isFinite(value) || value <= 0 || value === currentTarget) {
      setTarget(currentTarget === null ? "" : String(currentTarget));
      return;
    }
    void save({ preferences: { target_loot: { ...prefs.target_loot, [focused]: Math.round(value) } } });
  };

  return (
    <div className="space-y-1.5">
      <div role="group" aria-label="Ressource prioritaire" className="grid grid-cols-4 gap-1">
        {OPTIONS.map(({ value, label }) => (
          <button key={value} type="button" aria-pressed={prefs.priority === value}
            onClick={() => prefs.priority !== value && void save({ preferences: { priority: value } })}
            className={`rounded-md border px-1 py-0.5 text-xs ${prefs.priority === value
              ? "border-accent bg-accent/20 text-ink" : "border-line text-ink-secondary hover:bg-surface-raised"}`}>
            {label}
          </button>
        ))}
      </div>
      {focused && (
        <label className="flex items-center justify-between gap-2 text-xs text-ink-secondary">
          Butin visé ({OPTIONS.find((o) => o.value === focused)!.label.toLowerCase()})
          <input inputMode="numeric" value={target} onChange={(e) => setTarget(e.target.value)}
            onBlur={saveTarget} onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
            aria-label="Butin visé pour la ressource prioritaire"
            title={`Actuel : ${formatNumber(currentTarget ?? 0)}`}
            className="w-24 rounded-md border border-line bg-page px-1.5 py-0.5 text-right tabular-nums outline-none focus:border-accent" />
        </label>
      )}
      {error && <p className="text-xs text-critical">{error}</p>}
    </div>
  );
}
