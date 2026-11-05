import { useId } from "react";

interface Props {
  label: string;
  value: number | null;
  onChange: (value: number | null) => void;
  min?: number;
  max?: number;
  step?: number;
  suffix?: string;
  help?: string;
  /** Champ vide autorisé (valeur null) : ex. « mesuré automatiquement ». */
  nullable?: boolean;
  placeholder?: string;
  invalid?: boolean;
}

/** Champ numérique libellé, avec unité et aide. */
export function NumberField({ label, value, onChange, min, max, step = 1, suffix, help, nullable, placeholder, invalid }: Props) {
  const id = useId();
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-xs text-ink-muted">{label}</label>
      <div className={`flex items-center rounded-lg border bg-page focus-within:border-accent ${invalid ? "border-critical" : "border-line"}`}>
        <input
          id={id}
          type="number"
          inputMode="decimal"
          value={value ?? ""}
          min={min}
          max={max}
          step={step}
          placeholder={placeholder}
          aria-invalid={invalid || undefined}
          onChange={(e) => {
            if (e.target.value === "") onChange(nullable ? null : 0);
            else onChange(Number(e.target.value));
          }}
          className="tabular w-full min-w-0 bg-transparent px-2.5 py-1.5 text-sm outline-none"
        />
        {suffix && <span className="pr-2.5 text-xs text-ink-muted">{suffix}</span>}
      </div>
      {help && <p className="text-xs text-ink-muted">{help}</p>}
    </div>
  );
}
