import { HashRouter, Route, Routes } from "react-router";
import { Layout } from "./components/Layout";
import { PagePlaceholder } from "./components/PagePlaceholder";
import { TokenGate } from "./components/TokenGate";
import { AnalysisPage } from "./pages/AnalysisPage";
import { DashboardPage } from "./pages/DashboardPage";
import { HistoryPage } from "./pages/HistoryPage";

/**
 * HashRouter (#/historique...) : fonctionne aussi bien avec le serveur de dev
 * qu'une fois l'application embarquée dans Tauri (fichiers locaux, phase 7).
 */
export function App() {
  return (
    <TokenGate>
      <HashRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<DashboardPage />} />
            <Route path="analyse" element={<AnalysisPage />} />
            <Route path="analyse/:id" element={<AnalysisPage />} />
            <Route path="historique" element={<HistoryPage />} />
            <Route path="statistiques" element={<PagePlaceholder title="Statistiques" step="6.3" />} />
            <Route path="parametres" element={<PagePlaceholder title="Paramètres" step="6.3" />} />
            <Route path="logs" element={<PagePlaceholder title="Logs" step="6.3" />} />
            <Route path="a-propos" element={<PagePlaceholder title="À propos" step="6.3" />} />
            <Route path="*" element={<PagePlaceholder title="Page introuvable" step="—" />} />
          </Route>
        </Routes>
      </HashRouter>
    </TokenGate>
  );
}
