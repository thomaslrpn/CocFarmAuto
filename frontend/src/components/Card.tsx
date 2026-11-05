import type { ReactNode } from "react";

interface CardProps {
  title?: string;
  action?: ReactNode; // bouton ou lien en haut à droite
  children: ReactNode;
  className?: string;
}

/** Conteneur standard des pages : fond « surface », bord fin, titre optionnel. */
export function Card({ title, action, children, className = "" }: CardProps) {
  return (
    <section className={`rounded-xl border border-line bg-surface p-5 ${className}`}>
      {(title || action) && (
        <header className="mb-4 flex items-center justify-between gap-3">
          {title && <h2 className="text-sm font-semibold text-ink-secondary">{title}</h2>}
          {action}
        </header>
      )}
      {children}
    </section>
  );
}
