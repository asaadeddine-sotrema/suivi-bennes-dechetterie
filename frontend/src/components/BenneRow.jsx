import { useState } from "react";
import AlerteBadge from "./AlerteBadge";
import { setTassement, rotationBenne, getHistoriqueTassements } from "../api/client";

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" })
    + " à "
    + d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

export default function BenneRow({ benne, siteId, onRefresh }) {
  const { type_dechet, taux, a_compacteur, tassee, tassee_at, seuil_avertissement = 75, seuil_critique = 90 } = benne;
  const couleur = taux >= seuil_critique ? "#e53e3e" : taux >= seuil_avertissement ? "#dd6b20" : "#38a169";

  const [loading, setLoading] = useState(false);
  const [historique, setHistorique] = useState(null);
  const [loadingHisto, setLoadingHisto] = useState(false);

  const handleTassement = async () => {
    setLoading(true);
    try {
      await setTassement(siteId, type_dechet, !tassee);
      onRefresh();
    } finally {
      setLoading(false);
    }
  };

  const handleRotation = async () => {
    if (!window.confirm(`Confirmer la rotation de "${type_dechet}" ?`)) return;
    setLoading(true);
    try {
      await rotationBenne(siteId, type_dechet);
      setHistorique(null);
      onRefresh();
    } finally {
      setLoading(false);
    }
  };

  const toggleHistorique = async () => {
    if (historique !== null) {
      setHistorique(null);
      return;
    }
    setLoadingHisto(true);
    try {
      const data = await getHistoriqueTassements(siteId, type_dechet);
      setHistorique(data);
    } finally {
      setLoadingHisto(false);
    }
  };

  return (
    <div className="benne-row-wrapper">
      <div className="benne-row">
        <span className="benne-type">
          {type_dechet}
          {a_compacteur && <span className="compacteur-tag"> C</span>}
        </span>
        <div className="barre-container">
          <div
            className="barre-remplissage"
            style={{ width: `${taux}%`, backgroundColor: couleur }}
          />
        </div>
        <AlerteBadge taux={taux} seuilAvertissement={seuil_avertissement} seuilCritique={seuil_critique} />
        <button
          className={`btn-tassement${tassee ? " tassee-active" : ""}`}
          onClick={handleTassement}
          disabled={loading}
          title={tassee ? "Retirer le tassement" : "Marquer comme tassée"}
        >
          {tassee ? "Tassée ✓" : "Tasser"}
        </button>
        {tassee && taux >= seuil_avertissement && (
          <button
            className="btn-rotation"
            onClick={handleRotation}
            disabled={loading}
            title="Rotation : vider la benne et réinitialiser le tassement"
          >
            Rotation
          </button>
        )}
        <button
          className="btn-historique"
          onClick={toggleHistorique}
          disabled={loadingHisto}
          title="Voir l'historique des tassements et rotations"
        >
          {loadingHisto ? "..." : historique !== null ? "▲" : "▼"}
        </button>
      </div>

      {tassee && tassee_at && (
        <div className="tassee-since">
          Tassée depuis le {formatDate(tassee_at)}
        </div>
      )}

      {historique !== null && (
        <div className="historique-tassements">
          {historique.length === 0 ? (
            <span className="histo-vide">Aucun événement enregistré</span>
          ) : (
            historique.map((ev) => (
              <div key={ev.id} className={`histo-ligne histo-${ev.evenement}`}>
                <span className="histo-badge">{ev.evenement === "rotation" ? "Rotation" : "Tassement"}</span>
                <span className="histo-date">{formatDate(ev.fait_le)}</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
