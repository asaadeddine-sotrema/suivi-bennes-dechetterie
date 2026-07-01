import { useState, useRef, useEffect } from "react";
import Icon from "./Icon";
import { useToast } from "./Toast";
import { couleurStatut } from "../theme";
import {
  demanderTassement,
  annulerDemandeTassement,
  rotationBenne,
  annulerRotationFaite,
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
function ActionPopover({ label, title, icon, className, onNow, onSchedule, disabled }) {
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
        {icon && <Icon name={icon} size={14} />}
        <span>{label}</span>
      </button>
      {open && (
        <div className="planif-popover">
          <div className="planif-popover-title">{title}</div>
          <button className="planif-option planif-option-confirm" onClick={() => pick(onNow)}>
            <Icon name="check" size={14} /> Maintenant
          </button>
          <div className="planif-popover-title planif-popover-subtitle">Planifier</div>
          <button className="planif-option" onClick={() => pick(onSchedule, quickDate(12, 0))}>
            <Icon name="clock" size={14} /> Ce matin (12h00)
          </button>
          <button className="planif-option" onClick={() => pick(onSchedule, quickDate(18, 0))}>
            <Icon name="clock" size={14} /> Cet après-midi (18h00)
          </button>
          <button className="planif-option" onClick={() => pick(onSchedule, quickDate(12, 1))}>
            <Icon name="clock" size={14} /> Demain (12h00)
          </button>
        </div>
      )}
    </div>
  );
}

export default function BenneRow({ benne, siteId, onRefresh }) {
  const {
    type_dechet, taux, a_compacteur,
    tassement_demande, tassement_demande_at, tassee, tassee_at, nb_tassements = 0,
    rotation_faite, rotation_faite_at,
    tassement_prevu_at, rotation_prevue_at,
    seuil_avertissement = 75, seuil_critique = 90,
  } = benne;

  const notify = useToast();
  const tassementPrevuFutur = isFutur(tassement_prevu_at);
  const rotationPrevueFutur = isFutur(rotation_prevue_at);

  const couleurChip = couleurStatut(taux, seuil_avertissement, seuil_critique);

  const suffixeN = nb_tassements > 1 ? ` ×${nb_tassements}` : "";

  // Indicateur d'état affiché en permanence (glanceable) à côté du taux.
  // Une demande en attente est prioritaire sur l'icône (même si déjà tassée N fois).
  let statut = null;
  if (rotationPrevueFutur) statut = { icon: "clock", cls: "prevu", title: `Rotation prévue le ${formatDate(rotation_prevue_at)}` };
  else if (tassementPrevuFutur) statut = { icon: "clock", cls: "prevu", title: `Tassement prévu le ${formatDate(tassement_prevu_at)}` };
  else if (tassement_demande) statut = { icon: "clock", cls: "demande", title: tassee ? `Tassée${suffixeN}, nouveau tassement demandé` : `Tassement demandé le ${formatDate(tassement_demande_at)}` };
  else if (rotation_faite) statut = { icon: "refresh", cls: "rotation", title: `Rotation effectuée le ${formatDate(rotation_faite_at)}` };
  else if (tassee) statut = { icon: "check", cls: "tassee", title: `Tassée${suffixeN} le ${formatDate(tassee_at)}` };

  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [historique, setHistorique] = useState(null);
  const [loadingHisto, setLoadingHisto] = useState(false);

  const handleDemanderTassement = async () => {
    setLoading(true);
    try {
      await demanderTassement(siteId, type_dechet);
      notify(`Demande de tassement enregistrée pour « ${type_dechet} »`);
      onRefresh();
    } catch {
      notify("Échec de l'opération", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleAnnulerDemandeTassement = async () => {
    setLoading(true);
    try {
      await annulerDemandeTassement(siteId, type_dechet);
      notify("Demande de tassement annulée");
      onRefresh();
    } catch {
      notify("Échec de l'opération", "error");
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
      notify(`Rotation de « ${type_dechet} » enregistrée`);
      onRefresh();
    } catch {
      notify("Échec de la rotation", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleAnnulerRotationFaite = async () => {
    setLoading(true);
    try {
      await annulerRotationFaite(siteId, type_dechet);
      notify("Rotation retirée");
      onRefresh();
    } catch {
      notify("Échec de l'opération", "error");
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

  const runPlanif = (apiCall, message) => async (arg) => {
    setLoading(true);
    try {
      await apiCall(siteId, type_dechet, arg);
      notify(message);
      onRefresh();
    } catch {
      notify("Échec de l'opération", "error");
    } finally {
      setLoading(false);
    }
  };

  const handlePlanifierTassement = runPlanif(planifierTassement, "Tassement planifié");
  const handleAnnulerTassement = runPlanif(annulerPlanification, "Planification annulée");
  const handlePlanifierRotation = runPlanif(planifierRotation, "Rotation planifiée");
  const handleAnnulerRotation = runPlanif(annulerPlanificationRotation, "Planification annulée");

  return (
    <div className={`benne-c${open ? " open" : ""}`}>
      <div
        className="benne-c-head"
        onClick={() => setOpen((o) => !o)}
        role="button"
        tabIndex={0}
        aria-expanded={open}
        title="Cliquer pour les actions"
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setOpen((o) => !o); }
        }}
      >
        <span className="benne-type">
          {a_compacteur ? type_dechet.replace(/^Compacteur\s+/i, "") : type_dechet}
          <span
            className={`badge-contenant ${a_compacteur ? "is-compacteur" : "is-benne"}`}
            title={a_compacteur ? "Équipée d'un compacteur" : "Benne simple (sans compacteur)"}
          >
            {a_compacteur ? "Compacteur" : "Benne"}
          </span>
        </span>
        <span className="benne-c-right">
          {statut && (
            <span className={`benne-c-statut statut-${statut.cls}`} title={statut.title}>
              <Icon name={statut.icon} size={12} />
            </span>
          )}
          <span className="taux-chip" style={{ backgroundColor: couleurChip }}>{taux}%</span>
          <Icon name={open ? "chevron-up" : "chevron-down"} size={14} />
        </span>
      </div>

      {open && (
        <div className="benne-c-body">
          <div className="benne-c-actions">
            {/* Tassement */}
            {tassementPrevuFutur ? (
              <button className="btn-annuler-planif" onClick={handleAnnulerTassement} disabled={loading} title="Annuler le tassement prévu">
                <Icon name="x" size={14} /> <span>Annuler le tassement</span>
              </button>
            ) : tassement_demande ? (
              <button className="btn-tassement tassement-demande-active" onClick={handleAnnulerDemandeTassement} disabled={loading} title="Annuler la demande de tassement">
                <Icon name="clock" size={14} /> <span>Tassement demandé{tassee ? ` (déjà tassée${suffixeN})` : ""}</span>
              </button>
            ) : tassee ? (
              <>
                <span className="btn-tassement tassee-active tassee-verrouille" title="Tassée — réinitialisée uniquement par une rotation">
                  <Icon name="check" size={14} /> <span>Tassée{suffixeN}</span>
                </span>
                <ActionPopover
                  label="Tasser à nouveau" title="Tasser à nouveau" icon="compress" className="btn-tassement"
                  onNow={handleDemanderTassement} onSchedule={handlePlanifierTassement} disabled={loading}
                />
              </>
            ) : (
              <ActionPopover
                label="Tasser" title="Tasser" icon="compress" className="btn-tassement"
                onNow={handleDemanderTassement} onSchedule={handlePlanifierTassement} disabled={loading}
              />
            )}

            {/* Rotation */}
            {rotationPrevueFutur ? (
              <button className="btn-annuler-planif" onClick={handleAnnulerRotation} disabled={loading} title="Annuler la rotation prévue">
                <Icon name="x" size={14} /> <span>Annuler la rotation</span>
              </button>
            ) : rotation_faite ? (
              <button className="btn-rotation rotation-faite-active" onClick={handleAnnulerRotationFaite} disabled={loading} title="Retirer l'état rotation effectuée">
                <Icon name="check" size={14} /> <span>Rotation effectuée</span>
              </button>
            ) : (
              <ActionPopover
                label="Rotation" title="Rotation" icon="refresh" className="btn-rotation"
                onNow={handleRotation} onSchedule={handlePlanifierRotation} disabled={loading}
              />
            )}

            <button className="btn-historique-txt" onClick={toggleHistorique} disabled={loadingHisto}>
              {loadingHisto ? "…" : historique !== null ? "Masquer l'historique" : "Historique"}
            </button>
          </div>

          {tassement_demande && tassement_demande_at && (
            <div className="tassee-since">
              {tassee ? `Déjà tassée${suffixeN}. ` : ""}Tassement demandé le {formatDate(tassement_demande_at)} · sera confirmé au prochain relevé en baisse
            </div>
          )}
          {tassee && !tassement_demande && tassee_at && (
            <div className="tassee-since">
              Tassée{suffixeN} (dernier : {formatDate(tassee_at)}) · réinitialisée uniquement par une rotation
            </div>
          )}
          {rotation_faite && rotation_faite_at && (
            <div className="tassee-since">
              Rotation effectuée le {formatDate(rotation_faite_at)} · maintenue jusqu'au prochain relevé en baisse
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
      )}
    </div>
  );
}
