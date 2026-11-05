import { HashRouter, Route, Routes } from "react-router";
import { Layout } from "./components/Layout";
import { PagePlaceholder } from "./components/PagePlaceholder";
import { TokenGate } from "./components/TokenGate";
import { UpdaterProvider } from "./hooks/useUpdater";
import { isOverlayWindow } from "./services/desktop";
import { AboutPage } from "./pages/AboutPage";
import { AnalysisPage } from "./pages/AnalysisPage";
import { DashboardPage } from "./pages/DashboardPage";
import { HistoryPage } from "./pages/HistoryPage";
import { LogsPage } from "./pages/LogsPage";
import { OverlayPage } from "./pages/OverlayPage";
import { SettingsPage } from "./pages/SettingsPage";
import { StatisticsPage } from "./pages/StatisticsPage";

/**
 * HashRouter (#/historique...) : fonctionne aussi bien avec le serveur de dev
 * qu'une fois l'application embarquée dans Tauri (fichiers locaux, phase 7).
 */
export function App() {
  // Mini-fenêtre « toujours au-dessus » : sa propre page, sans menu ni vérification des mises à jour.
  if (isOverlayWindow()) {
    return (
      <TokenGate>
        <OverlayPage />
      </TokenGate>
    );
  }

  return (
    <TokenGate>
      <UpdaterProvider>
        <HashRouter>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<DashboardPage />} />
              <Route path="analyse" element={<AnalysisPage />} />
              <Route path="analyse/:id" element={<AnalysisPage />} />
              <Route path="historique" element={<HistoryPage />} />
              <Route path="statistiques" element={<StatisticsPage />} />
              <Route path="parametres" element={<SettingsPage />} />
              <Route path="logs" element={<LogsPage />} />
              <Route path="a-propos" element={<AboutPage />} />
              <Route path="*" element={<PagePlaceholder title="Page introuvable" step="—" />} />
            </Route>
          </Routes>
        </HashRouter>
      </UpdaterProvider>
    </TokenGate>
  );
}
