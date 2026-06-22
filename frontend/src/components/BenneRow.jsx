import { useState, useRef, useEffect } from "react";
import AlerteBadge from "./AlerteBadge";
import {
  setTassement,
  rotationBenne,
  getHistoriqueTassements,
  planifierTassement,
  annulerPlanification,
  planifierRotation,
  annulerPlanificationRotation,
} from "../api/client";

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" })
    + " à "
    + d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

function isFutur(iso) {
  if (!iso) return false;
  return new Date(iso) > new Date();
}

function quickDate(heureHeure, joursPlus = 0) {
  const d = new Date();
  d.setDate(d.getDate() + joursPlus);
  d.setHours(heureHeure, 0, 0, 0);
  return d.toISOString();
}

/** Bouton d'action avec menu : exécuter maintenant ou planifier. */
function ActionPopover({ label, title, className, onNow, onSchedule, disabled }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const pick = (fn, arg) => {
    setOpen(false);
    fn(arg);
  };

  return (
    <div className="planif-wrapper" ref={ref}>
      <button className={className} onClick={() => setOpen((o) => !o)} disabled={disabled} title={title}>
        {label}
      </button>
      {open && (
        <div className="planif-popover">
          <div className="planif-popover-title">{title}</div>
          <button className="planif-option planif-option-confirm" onClick={() => pick(onNow)}>
            Maintenant
          </button>
          <div className="planif-popover-title planif-popover-subtitle">Planifier</div>
          <button className="planif-option" onClick={() => pick(onSchedule, quickDate(12, 0))}>
            Ce matin (12h00)
          </button>
          <button className="planif-option" onClick={() => pick(onSchedule, quickDate(18, 0))}>
            Cet après-midi (18h00)
          </button>
          <button className="planif-option" onClick={() => pick(onSchedule, quickDate(12, 1))}>
            Demain (12h00)
          </button>
        </div>
      )}
    </div>
  );
}

export default function BenneRow({ benne, siteId, onRefresh }) {
  const {
    type_dechet, taux, a_compacteur, tassee, tassee_at,
    tassement_prevu_at, rotation_prevue_at,
    seuil_avertissement = 75, seuil_critique = 90,
  } = benne;

  const tassementPrevuFutur = isFutur(tassement_prevu_at);
  const rotationPrevueFutur = isFutur(rotation_prevue_at);
  const prevuFutur = tassementPrevuFutur || rotationPrevueFutur;

  const couleur = prevuFutur
    ? "#6b7280"
    : taux >= seuil_critique ? "#e53e3e"
    : taux >= seuil_avertissement ? "#dd6b20"
    : "#38a169";

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
    if (historique !== null) { setHistorique(null); return; }
    setLoadingHisto(true);
    try {
      const data = await getHistoriqueTassements(siteId, type_dechet);
      setHistorique(data);
    } finally {
      setLoadingHisto(false);
    }
  };

  const runPlanif = (apiCall) => async (arg) => {
    setLoading(true);
    try {
      await apiCall(siteId, type_dechet, arg);
      onRefresh();
    } finally {
      setLoading(false);
    }
  };

  const handlePlanifierTassement = runPlanif(planifierTassement);
  const handleAnnulerTassement = runPlanif(annulerPlanification);
  const handlePlanifierRotation = runPlanif(planifierRotation);
  const handleAnnulerRotation = runPlanif(annulerPlanificationRotation);

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

        {/* Le taux est toujours affiché, même quand un tassement/rotation est prévu */}
        <AlerteBadge taux={taux} seuilAvertissement={seuil_avertissement} seuilCritique={seuil_critique} />
        {rotationPrevueFutur && (
          <span className="badge-planifie" title={`Rotation prévue le ${formatDate(rotation_prevue_at)}`}>
            Rotation prévue le {formatDate(rotation_prevue_at)}
          </span>
        )}
        {!rotationPrevueFutur && tassementPrevuFutur && (
          <span className="badge-planifie" title={`Tassement prévu le ${formatDate(tassement_prevu_at)}`}>
            Tassement prévu le {formatDate(tassement_prevu_at)}
          </span>
        )}

        {/* Tassement */}
        {tassementPrevuFutur ? (
          <button
            className="btn-annuler-planif"
            onClick={handleAnnulerTassement}
            disabled={loading}
            title="Annuler le tassement prévu"
          >
            Annuler le tassement prévu
          </button>
        ) : tassee ? (
          <button
            className="btn-tassement tassee-active"
            onClick={handleTassement}
            disabled={loading}
            title="Retirer le tassement"
          >
            Tassée
          </button>
        ) : (
          <ActionPopover
            label="Tasser"
            title="Tasser"
            className="btn-tassement"
            onNow={handleTassement}
            onSchedule={handlePlanifierTassement}
            disabled={loading}
          />
        )}

        {/* Rotation */}
        {rotationPrevueFutur ? (
          <button
            className="btn-annuler-planif"
            onClick={handleAnnulerRotation}
            disabled={loading}
            title="Annuler la rotation prévue"
          >
            Annuler la rotation prévue
          </button>
        ) : (
          <ActionPopover
            label="Rotation"
            title="Rotation"
            className="btn-rotation"
            onNow={handleRotation}
            onSchedule={handlePlanifierRotation}
            disabled={loading}
          />
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
