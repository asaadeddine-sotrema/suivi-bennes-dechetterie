import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Alertes from "./pages/Alertes";
import Historique from "./pages/Historique";
import Parametrage from "./pages/Parametrage";
import Icon from "./components/Icon";
import "./index.css";

const NAV = [
  { id: "dashboard", label: "Tableau de bord", icon: "dashboard" },
  { id: "alertes", label: "Alertes", icon: "bell" },
  { id: "historique", label: "Historique", icon: "activity" },
  { id: "parametrage", label: "Paramétrage", icon: "sliders" },
  { id: "upload", label: "Importer PDF", icon: "upload" },
];

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [dashboardKey, setDashboardKey] = useState(0);

  function handleImport() {
    setDashboardKey((k) => k + 1);
    setTimeout(() => setPage("dashboard"), 1000);
  }

  return (
    <div className="app">
      <nav className="navbar">
        <span className="navbar-brand">
          <Icon name="truck" size={20} className="navbar-logo" />
          <span>SOTREMA <span className="navbar-brand-sub">· Suivi des bennes</span></span>
        </span>
        <div className="navbar-links">
          {NAV.map((item) => (
            <button
              key={item.id}
              className={page === item.id ? "nav-link active" : "nav-link"}
              onClick={() => setPage(item.id)}
            >
              <Icon name={item.icon} size={15} />
              <span>{item.label}</span>
            </button>
          ))}
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
