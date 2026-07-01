import { useEffect, useState } from "react";
import { getStats, exporterRelevesCsv } from "../api/client";
import Icon from "../components/Icon";
import Skeleton from "../components/Skeleton";
import EmptyState from "../components/EmptyState";
import { useToast } from "../components/Toast";

export default function Statistiques() {
  const notify = useToast();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    getStats()
      .then(setStats)
      .catch(() => setError("Impossible de charger les statistiques"))
      .finally(() => setLoading(false));
  }, []);

  const handleExport = async () => {
    setExporting(true);
    try {
      await exporterRelevesCsv();
      notify("Export CSV téléchargé");
    } catch {
      notify("Échec de l'export", "error");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Statistiques & export</h1>
        <button className="login-btn" style={{ width: "auto", padding: "9px 16px" }} onClick={handleExport} disabled={exporting}>
          <Icon name="download" size={15} /> {exporting ? "Export…" : "Exporter en CSV"}
        </button>
      </div>
      <p className="page-subtitle">
        Synthèse de l'activité par déchèterie et téléchargement des relevés pour vos rapports.
      </p>

      {loading && <Skeleton height={200} />}
      {error && <p className="error">{error}</p>}

      {!loading && !error && stats && (
        <>
          <div className="kpi-bar">
            <div className="kpi">
              <span className="kpi-value">{stats.totaux.tassements}</span>
              <span className="kpi-label">Tassements (total)</span>
            </div>
            <div className="kpi">
              <span className="kpi-value">{stats.totaux.rotations}</span>
              <span className="kpi-label">Rotations (total)</span>
            </div>
            <div className="kpi">
              <span className="kpi-value">{stats.sites.length}</span>
              <span className="kpi-label">Sites suivis</span>
            </div>
          </div>

          <h2>Par déchèterie</h2>
          {stats.sites.length === 0 ? (
            <EmptyState icon="file-text" title="Aucune donnée" subtitle="Importez des relevés pour alimenter les statistiques." />
          ) : (
            <table className="param-table" style={{ marginBottom: 28 }}>
              <thead>
                <tr>
                  <th>Déchèterie</th>
                  <th>Bennes</th>
                  <th>Taux moyen</th>
                  <th>Dernier relevé</th>
                  <th>Tassements</th>
                  <th>Rotations</th>
                </tr>
              </thead>
              <tbody>
                {stats.sites.map((s) => (
                  <tr key={s.site_id}>
                    <td>{s.site_nom}</td>
                    <td>{s.nb_bennes}</td>
                    <td>{s.taux_moyen != null ? `${s.taux_moyen}%` : "—"}</td>
                    <td>{s.derniere_date ? new Date(s.derniere_date).toLocaleDateString("fr-FR") : "—"}</td>
                    <td>{s.nb_tassements}</td>
                    <td>{s.nb_rotations}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {stats.activite_mensuelle.length > 0 && (
            <>
              <h2>Activité mensuelle</h2>
              <table className="param-table">
                <thead>
                  <tr><th>Mois</th><th>Tassements</th><th>Rotations</th></tr>
                </thead>
                <tbody>
                  {stats.activite_mensuelle.map((m) => (
                    <tr key={m.mois}>
                      <td>{m.mois}</td>
                      <td>{m.tassements}</td>
                      <td>{m.rotations}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </>
      )}
    </div>
  );
}
