import { useEffect, useState } from "react";
import { getBennes } from "../api/client";
import SiteCard from "../components/SiteCard";
import SyncStatus from "../components/SyncStatus";

export default function Dashboard() {
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refetch = () => {
    getBennes().then(setSites).catch(() => setError("Impossible de charger les données"));
  };

  useEffect(() => {
    getBennes()
      .then(setSites)
      .catch(() => setError("Impossible de charger les données"))
      .finally(() => setLoading(false));
  }, []);

  const totalAlertes = sites.reduce(
    (acc, { releve }) => acc + (releve?.bennes?.filter((b) => b.taux >= 75).length ?? 0),
    0
  );

  return (
    <div className="page">
      <div className="page-header">
        <h1>Tableau de bord - Bennes</h1>
        <SyncStatus />
      </div>

      <div className="kpi-bar">
        <div className="kpi">
          <span className="kpi-value">{sites.length}</span>
          <span className="kpi-label">Sites actifs</span>
        </div>
        <div className="kpi">
          <span className="kpi-value kpi-alerte">{totalAlertes}</span>
          <span className="kpi-label">Alertes en cours</span>
        </div>
      </div>

      {loading && <p className="loading">Chargement...</p>}
      {error && <p className="error">{error}</p>}

      <div className="sites-list">
        {sites.map(({ site, releve }) => (
          <SiteCard key={site.id} site={site} releve={releve} onRefresh={refetch} />
        ))}
      </div>
    </div>
  );
}
