import { useEffect, useState } from "react";
import { getBennes } from "../api/client";
import SiteCard from "../components/SiteCard";
import SyncStatus from "../components/SyncStatus";
import { SkeletonSites } from "../components/Skeleton";
import EmptyState from "../components/EmptyState";
import { useAuth } from "../components/Auth";

export default function Dashboard() {
  const { isAdmin } = useAuth();
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
    (acc, { releve }) =>
      acc + (releve?.bennes?.filter((b) => b.taux >= (b.seuil_avertissement ?? 75)).length ?? 0),
    0
  );

  return (
    <div className="page">
      <div className="page-header">
        <h1>Tableau de bord - Bennes</h1>
        {isAdmin && <SyncStatus />}
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

      {error && <p className="error">{error}</p>}

      {loading ? (
        <SkeletonSites n={3} />
      ) : sites.length === 0 ? (
        <EmptyState
          icon="file-text"
          title="Aucun site à afficher"
          subtitle="Importez un premier relevé PDF pour alimenter le tableau de bord."
        />
      ) : (
        <div className="sites-list">
          {sites.map(({ site, releve }) => (
            <SiteCard key={site.id} site={site} releve={releve} onRefresh={refetch} />
          ))}
        </div>
      )}
    </div>
  );
}
