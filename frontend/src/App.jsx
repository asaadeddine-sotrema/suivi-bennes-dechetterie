import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Alertes from "./pages/Alertes";
import Historique from "./pages/Historique";
import Parametrage from "./pages/Parametrage";
import "./index.css";

const PAGES = { dashboard: Dashboard, upload: Upload, alertes: Alertes, historique: Historique, parametrage: Parametrage };

export default function App() {
  const [page, setPage] = useState("upload");
  const [dashboardKey, setDashboardKey] = useState(0);

  function handleImport() {
    setDashboardKey((k) => k + 1);
    setTimeout(() => setPage("dashboard"), 1000);
  }

  const Page = PAGES[page];

  return (
    <div className="app">
      <nav className="navbar">
        <span className="navbar-brand">SOTREMA - Bennes Déchetteries</span>
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
          <button className={page === "parametrage" ? "nav-link active" : "nav-link"} onClick={() => setPage("parametrage")}>
            Paramétrage
          </button>
        </div>
      </nav>
      <main className="main-content">
        {page === "upload" && <Upload onImport={handleImport} />}
        {page === "dashboard" && <Dashboard key={dashboardKey} />}
        {page === "alertes" && <Alertes />}
        {page === "historique" && <Historique />}
        {page === "parametrage" && <Parametrage />}
      </main>
    </div>
  );
}
