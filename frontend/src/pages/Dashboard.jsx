import { useEffect, useState } from "react";
import { getBennes } from "../api/client";
import SiteCard from "../components/SiteCard";
import SyncStatus from "../components/SyncStatus";
import { SkeletonSites } from "../components/Skeleton";
import EmptyState from "../components/EmptyState";
import { useAuth } from "../components/Auth";
import { secteurSite } from "../theme";

export default function Dashboard() {
  const { isAdmin } = useAuth();
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [secteur, setSecteur] = useState("est");

  const refetch = () => {
    getBennes().then(setSites).catch(() => setError("Impossible de charger les données"));
  };

  useEffect(() => {
    getBennes()
      .then(setSites)
      .catch(() => setError("Impossible de charger les données"))
      .finally(() => setLoading(false));
  }, []);

  // Rafraîchissement automatique silencieux : la page reflète les synchros API
  // (import des PDF Kizeo) sans rechargement manuel. Pas de spinner ni de bandeau
  // d'erreur sur un incident réseau passager, et on ne sollicite pas l'API quand
  // l'onglet est en arrière-plan.
  useEffect(() => {
    const POLL_MS = 60000;
    const id = setInterval(() => {
      if (document.visibilityState !== "visible") return;
      getBennes().then(setSites).catch(() => {});
    }, POLL_MS);
    return () => clearInterval(id);
  }, []);

  const sitesEst = sites.filter((s) => secteurSite(s.site) === "est");
  const sitesOuest = sites.filter((s) => secteurSite(s.site) === "ouest");

  // Criticité d'un site = taux de remplissage le plus élevé parmi ses bennes.
  // Les sites les plus pleins (donc les plus urgents) remontent en tête.
  const scoreSite = ({ releve }) => {
    const bs = releve?.bennes ?? [];
    return bs.length ? Math.max(...bs.map((b) => b.taux)) : -1;
  };
  const visibles = [...(secteur === "est" ? sitesEst : sitesOuest)].sort(
    (a, b) => scoreSite(b) - scoreSite(a)
  );

  const compteAlertes = (liste) =>
    liste.reduce(
      (acc, { releve }) =>
        acc + (releve?.bennes?.filter((b) => b.taux >= (b.seuil_avertissement ?? 75)).length ?? 0),
      0
    );
  const totalAlertes = compteAlertes(visibles);
  const enAttente = visibles.reduce(
    (acc, { releve }) => acc + (releve?.bennes?.filter((b) => b.tassement_demande).length ?? 0),
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
          <span className="kpi-value">{visibles.length}</span>
          <span className="kpi-label">Sites · secteur {secteur === "est" ? "Est" : "Ouest"}</span>
        </div>
        <div className="kpi">
          <span className="kpi-value kpi-alerte">{totalAlertes}</span>
          <span className="kpi-label">Alertes du secteur</span>
        </div>
        <div className="kpi">
          <span className="kpi-value">{enAttente}</span>
          <span className="kpi-label">Tassements en attente</span>
        </div>
      </div>

      <div className="secteur-tabs" role="tablist">
        <button
          role="tab"
          aria-selected={secteur === "est"}
          className={`secteur-tab${secteur === "est" ? " active" : ""}`}
          onClick={() => setSecteur("est")}
        >
          Secteur Est <span className="secteur-tab-count">{sitesEst.length}</span>
        </button>
        <button
          role="tab"
          aria-selected={secteur === "ouest"}
          className={`secteur-tab${secteur === "ouest" ? " active" : ""}`}
          onClick={() => setSecteur("ouest")}
        >
          Secteur Ouest <span className="secteur-tab-count">{sitesOuest.length}</span>
        </button>
      </div>

      <div className="dashboard-toolbar">
        <div className="legende">
          <span className="legende-item"><span className="legende-pastille" style={{ background: "var(--c-ok)" }} /> Normal</span>
          <span className="legende-item"><span className="legende-pastille" style={{ background: "var(--c-warning)" }} /> Avertissement</span>
          <span className="legende-item"><span className="legende-pastille" style={{ background: "var(--c-critical)" }} /> Critique</span>
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
      ) : visibles.length === 0 ? (
        <EmptyState
          icon="file-text"
          title={`Aucun site dans le secteur ${secteur === "est" ? "Est" : "Ouest"}`}
          subtitle="Les relevés de ce secteur apparaîtront ici une fois importés."
        />
      ) : (
        <div className="sites-grid">
          {visibles.map(({ site, releve }) => (
            <SiteCard key={site.id} site={site} releve={releve} onRefresh={refetch} />
          ))}
        </div>
      )}
    </div>
  );
}
