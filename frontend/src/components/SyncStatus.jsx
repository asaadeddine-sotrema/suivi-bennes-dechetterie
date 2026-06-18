import { useState } from "react";
import { getSyncStatus, syncManual } from "../api/client";

export default function SyncStatus() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSync() {
    setLoading(true);
    setError(null);
    try {
      await syncManual();
      const s = await getSyncStatus();
      setStatus(s);
    } catch (e) {
      setError(e.response?.data?.detail || "Erreur lors de la synchronisation");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="sync-status">
      <button className="btn-sync" onClick={handleSync} disabled={loading}>
        {loading ? "Synchronisation..." : "Synchroniser maintenant"}
      </button>
      {status?.derniere_synchro && (
        <span className="sync-info">
          Dernière synchro : {new Date(status.derniere_synchro).toLocaleString("fr-FR")}
          {status.stats && (
            <> · {status.stats.traites} traité(s), {status.stats.alertes} alerte(s)</>
          )}
        </span>
      )}
      {error && <span className="sync-error">{error}</span>}
    </div>
  );
}
