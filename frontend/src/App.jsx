import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Alertes from "./pages/Alertes";
import Historique from "./pages/Historique";
import "./index.css";

const PAGES = { dashboard: Dashboard, upload: Upload, alertes: Alertes, historique: Historique };

export default function App() {
  const [page, setPage] = useState("upload");
  // Clé pour forcer le rechargement du dashboard après un import
  const [dashboardKey, setDashboardKey] = useState(0);

  function handleImport() {
    setDashboardKey((k) => k + 1);
    // Basculer sur le dashboard 1 seconde après l'import pour voir le résultat
    setTimeout(() => setPage("dashboard"), 1000);
  }

  const Page = PAGES[page];

  return (
    <div className="app">
      <nav className="navbar">
        <span className="navbar-brand">SOTREMA — Bennes</span>
        <div className="navbar-links">
          <button className={page === "upload" ? "nav-link active" : "nav-link"} onClick={() => setPage("upload")}>
            Importer PDF
          </button>
          <button className={page === "dashboard" ? "nav-link active" : "nav-link"} onClick={() => setPage("dashboard")}>
            Tableau de bord
          </button>
          <button className={page === "alertes" ? "nav-link active" : "nav-link"} onClick={() => setPage("alertes")}>
            Alertes
          </button>
          <button className={page === "historique" ? "nav-link active" : "nav-link"} onClick={() => setPage("historique")}>
            Historique
          </button>
        </div>
      </nav>
      <main className="main-content">
        {page === "upload" && <Upload onImport={handleImport} />}
        {page === "dashboard" && <Dashboard key={dashboardKey} />}
        {page === "alertes" && <Alertes />}
        {page === "historique" && <Historique />}
      </main>
    </div>
  );
}
