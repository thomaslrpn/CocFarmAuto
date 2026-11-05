/** Calculs de la page Statistiques (fonctions pures, testées). */
import type { Datum } from "../components/charts";

/** Répartition des scores en 10 tranches : 0–9, 10–19, ..., 90–100. */
export function scoreHistogram(scores: number[]): Datum[] {
  const bins = Array.from({ length: 10 }, (_, i) => ({ label: i === 9 ? "90–100" : `${i * 10}–${i * 10 + 9}`, value: 0 }));
  for (const score of scores) {
    const index = Math.min(9, Math.max(0, Math.floor(score / 10)));
    bins[index]!.value += 1;
  }
  return bins;
}

/** « 2026-11-05 » -> « 05/11 » */
export function dayLabel(day: string): string {
  const [, month, date] = day.split("-");
  return `${date}/${month}`;
}

/** Part de l'or dans (or + élixir), entre 0 et 1 (0.5 si aucun butin). */
export function goldShare(gold: number, elixir: number): number {
  const total = gold + elixir;
  return total > 0 ? gold / total : 0.5;
}
