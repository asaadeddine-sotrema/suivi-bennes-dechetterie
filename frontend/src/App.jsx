import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Upload from "./pages/Upload";
import Historique from "./pages/Historique";
import Statistiques from "./pages/Statistiques";
import Parametrage from "./pages/Parametrage";
import Utilisateurs from "./pages/Utilisateurs";
import Login from "./pages/Login";
import Icon from "./components/Icon";
import { useAuth } from "./components/Auth";
import "./index.css";

const NAV = [
  { id: "dashboard", label: "Tableau de bord", icon: "dashboard" },
  { id: "historique", label: "Historique", icon: "activity" },
  { id: "statistiques", label: "Statistiques", icon: "bar-chart" },
  { id: "upload", label: "Importer PDF", icon: "upload" },
  { id: "parametrage", label: "Paramétrage", icon: "sliders", admin: true },
  { id: "utilisateurs", label: "Utilisateurs", icon: "inbox", admin: true },
];

export default function App() {
  const { user, loading, logout, isAdmin } = useAuth();
  const [page, setPage] = useState("dashboard");
  const [dashboardKey, setDashboardKey] = useState(0);

  function handleImport() {
    setDashboardKey((k) => k + 1);
    setTimeout(() => setPage("dashboard"), 1000);
  }

  if (loading) {
    return <div className="app-splash">Chargement…</div>;
  }

  if (!user) {
    return <Login />;
  }

  const items = NAV.filter((item) => !item.admin || isAdmin);
  const current = items.some((i) => i.id === page) ? page : "dashboard";

  return (
    <div className="app">
      <nav className="navbar">
        <span className="navbar-brand">
          <Icon name="truck" size={20} className="navbar-logo" />
          <span>SOTREMA <span className="navbar-brand-sub">· Suivi des bennes</span></span>
        </span>
        <div className="navbar-links">
          {items.map((item) => (
            <button
              key={item.id}
              className={current === item.id ? "nav-link active" : "nav-link"}
              onClick={() => setPage(item.id)}
            >
              <Icon name={item.icon} size={15} />
              <span>{item.label}</span>
            </button>
          ))}
        </div>
        <div className="navbar-user">
          <span className="navbar-username" title={`Rôle : ${user.role}`}>
            {user.username}
            <span className="navbar-role">{user.role === "admin" ? "Admin" : "Opérateur"}</span>
          </span>
          <button className="nav-link" onClick={logout} title="Se déconnecter">
            <Icon name="x" size={15} />
            <span>Déconnexion</span>
          </button>
        </div>
      </nav>
      <main className={current === "dashboard" ? "main-content main-content--wide" : "main-content"}>
        {current === "upload" && <Upload onImport={handleImport} />}
        {current === "dashboard" && <Dashboard key={dashboardKey} />}
        {current === "historique" && <Historique />}
        {current === "statistiques" && <Statistiques />}
        {current === "parametrage" && <Parametrage />}
        {current === "utilisateurs" && <Utilisateurs />}
      </main>
    </div>
  );
}
