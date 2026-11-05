/** Mise en forme française des nombres et des dates. */

const integer = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });
const compact = new Intl.NumberFormat("fr-FR", { notation: "compact", maximumFractionDigits: 1 });

/** 1234567 -> « 1 234 567 » (espace insécable remplacée par une espace simple). */
export function formatNumber(value: number): string {
  return integer.format(value).replace(/ | /g, " ");
}

/** 1234567 -> « 1,2 M » (tuiles, axes). */
export function formatCompact(value: number): string {
  return compact.format(value).replace(/ | /g, " ");
}

/** ISO -> « 05/11 10:21 » */
export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${pad(d.getDate())}/${pad(d.getMonth() + 1)} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** ISO -> « 10:21:48 » */
export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

/** Durée en secondes -> « 2 min 05 s » / « 1 h 03 min ». */
export function formatDuration(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h > 0) return `${h} h ${String(m).padStart(2, "0")} min`;
  return `${m} min ${String(s % 60).padStart(2, "0")} s`;
}
