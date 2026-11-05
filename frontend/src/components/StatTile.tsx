interface StatTileProps {
  label: string;
  value: string;
  hint?: string;
  /** Pastille d'identité (ex. couleur de la ressource) ; le texte reste neutre. */
  swatchClassName?: string;
}

/** Tuile de chiffre clé : libellé, valeur, précision. */
export function StatTile({ label, value, hint, swatchClassName }: StatTileProps) {
  return (
    <div className="rounded-xl border border-line bg-surface p-5">
      <div className="flex items-center gap-2 text-sm text-ink-secondary">
        {swatchClassName && <span aria-hidden className={`size-2.5 rounded-full ${swatchClassName}`} />}
        {label}
      </div>
      <div className="mt-2 text-3xl font-semibold text-ink">{value}</div>
      {hint && <div className="mt-1 text-xs text-ink-muted">{hint}</div>}
    </div>
  );
}
