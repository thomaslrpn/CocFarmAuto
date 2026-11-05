import {
  BarChart3,
  FileText,
  History,
  Info,
  LayoutDashboard,
  ScanSearch,
  Settings,
  Sparkles,
  type LucideIcon,
} from "lucide-react";
import { Link, NavLink, Outlet } from "react-router";
import { useUpdater } from "../hooks/useUpdater";
import { AppLogo } from "./AppLogo";
import { compareVersions } from "../services/versions";

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
      {/* Menu fixe : collé en haut, hauteur de la fenêtre ; seul le contenu de droite défile. */}
      <nav className="sticky top-0 flex h-screen w-56 shrink-0 flex-col overflow-y-auto border-r border-line bg-surface px-3 py-5">
        <div className="mb-6 flex items-center gap-2 px-2">
          <AppLogo className="size-7" />
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
        <div className="mt-auto">
          <UpdateNotice />
          <p className="px-2 text-xs text-ink-muted">Outil d'analyse — aucune action sur le jeu.</p>
        </div>
      </nav>
      <main className="min-w-0 flex-1 p-6 lg:p-8">
        <Outlet />
      </main>
    </div>
  );
}

/** Signale dans le menu qu'une mise à jour est disponible (détails dans À propos). */
function UpdateNotice() {
  const { status, update } = useUpdater();
  if (status !== "available" || !update) return null;
  return (
    <Link to="/a-propos"
      className="mb-3 flex items-center gap-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-sm hover:bg-accent/20">
      <Sparkles aria-hidden className="size-4 shrink-0 text-accent" />
      <span>
        {compareVersions(update.version, update.currentVersion) < 0 ? "Version stable" : "Mise à jour"} {update.version} disponible
      </span>
    </Link>
  );
}
