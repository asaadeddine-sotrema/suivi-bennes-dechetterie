import { useState } from "react";
import AlerteBadge from "./AlerteBadge";
import { setTassement, rotationBenne } from "../api/client";

const SEUIL_ROTATION = 75;

export default function BenneRow({ benne, siteId, onRefresh }) {
  const { type_dechet, taux, a_compacteur, tassee } = benne;
  const couleur = taux >= 90 ? "#e53e3e" : taux >= 75 ? "#dd6b20" : "#38a169";
  const [loading, setLoading] = useState(false);

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
      onRefresh();
    } finally {
      setLoading(false);
    }
  };

  return (
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
      <AlerteBadge taux={taux} />
      <button
        className={`btn-tassement${tassee ? " tassee-active" : ""}`}
        onClick={handleTassement}
        disabled={loading}
        title={tassee ? "Retirer le tassement" : "Marquer comme tassée"}
      >
        {tassee ? "Tassée ✓" : "Tasser"}
      </button>
      {tassee && taux >= SEUIL_ROTATION && (
        <button
          className="btn-rotation"
          onClick={handleRotation}
          disabled={loading}
          title="Rotation : vider la benne et réinitialiser le tassement"
        >
          Rotation
        </button>
      )}
    </div>
  );
}
