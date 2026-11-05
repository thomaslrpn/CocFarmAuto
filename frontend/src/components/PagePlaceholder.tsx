import { Construction } from "lucide-react";
import { Card } from "./Card";

/** Page pas encore développée (étapes 6.2 / 6.3). */
export function PagePlaceholder({ title, step }: { title: string; step: string }) {
  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold">{title}</h1>
      <Card>
        <div className="flex items-center gap-3 text-ink-secondary">
          <Construction aria-hidden className="size-5" />
          Cette page arrive à l'étape {step}.
        </div>
      </Card>
    </div>
  );
}
