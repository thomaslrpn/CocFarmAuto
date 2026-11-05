import {
  BarChart3,
  FileText,
  History,
  Info,
  LayoutDashboard,
  ScanSearch,
  Settings,
  Swords,
  type LucideIcon,
} from "lucide-react";
import { NavLink, Outlet } from "react-router";

interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/analyse", label: "Analyse", icon: ScanSearch },
  { to: "/historique", label: "Historique", icon: History },
  { to: "/statistiques", label: "Statistiques", icon: BarChart3 },
  { to: "/parametres", label: "Paramètres", icon: Settings },
  { to: "/logs", label: "Logs", icon: FileText },
  { to: "/a-propos", label: "À propos", icon: Info },
];

/** Structure commune : menu latéral + contenu de la page. */
export function Layout() {
  return (
    <div className="flex min-h-screen">
      <nav className="flex w-56 shrink-0 flex-col border-r border-line bg-surface px-3 py-5">
        <div className="mb-6 flex items-center gap-2 px-2">
          <Swords aria-hidden className="size-6 text-accent" />
          <span className="text-lg font-semibold">CoC AutoFarm</span>
        </div>
        <ul className="flex flex-col gap-1">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                    isActive ? "bg-accent/15 text-ink" : "text-ink-secondary hover:bg-surface-raised hover:text-ink"
                  }`
                }
              >
                <Icon aria-hidden className="size-4" />
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
        <p className="mt-auto px-2 text-xs text-ink-muted">Outil d'analyse — aucune action sur le jeu.</p>
      </nav>
      <main className="min-w-0 flex-1 p-6 lg:p-8">
        <Outlet />
      </main>
    </div>
  );
}
