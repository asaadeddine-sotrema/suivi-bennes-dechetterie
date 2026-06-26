import { useEffect, useRef, useState } from "react";
import { getBennes, getHistoriqueSite, getSeuils, getPrevisions } from "../api/client";
import { couleurStatut, estCompacteur, nomContenant } from "../theme";
import { SkeletonCharts } from "../components/Skeleton";
import EmptyState from "../components/EmptyState";

// Types de bennes non suivis (verre, emballage, mobilier)
const TYPES_EXCLUS = ["Borne Verre", "Borne Emballage", "Mobilier"];
const estTypeExclu = (t) => TYPES_EXCLUS.some((e) => (t ?? "").startsWith(e));

const JOUR_MS = 86400000;
const joursEntre = (a, b) => Math.round((new Date(b) - new Date(a)) / JOUR_MS);
const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
const dateCourte = (d) => new Date(d).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" });
const dateLongue = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString("fr-FR", { weekday: "short", day: "2-digit", month: "2-digit", year: "numeric" });
const jourVersDate = (ref, j) => {
  const d = new Date(`${ref}T00:00:00`);
  d.setDate(d.getDate() + j);
  return d;
};

/** Courbe d'évolution + projection avec axes, et tooltip interactif au survol. */
function Sparkline({ points, projection, xMax, color, avert, crit, xticks }) {
  const W = 640, H = 110, mL = 30, mR = 12, mT = 10, mB = 26;
  const wrapRef = useRef(null);
  const [tip, setTip] = useState(null);
  if (!points.length) return null;
  const dom = Math.max(xMax, 1);
  const plotW = W - mL - mR, plotH = H - mT - mB;
  const x = (j) => mL + (j / dom) * plotW;
  const y = (v) => mT + (1 - v / 100) * plotH;

  const ligne = points.map((p, i) => `${i === 0 ? "M" : "L"}${x(p.jour).toFixed(1)},${y(p.taux).toFixed(1)}`).join(" ");
  const dernier = points[points.length - 1];
  const aire = `${ligne} L${x(dernier.jour).toFixed(1)},${y(0).toFixed(1)} L${x(points[0].jour).toFixed(1)},${y(0).toFixed(1)} Z`;

  const survol = (e, p) => {
    const c = e.target.getBoundingClientRect();
    const w = wrapRef.current.getBoundingClientRect();
    setTip({ left: c.left + c.width / 2 - w.left, top: c.top + c.height / 2 - w.top, date: p.date, taux: p.taux });
  };

  return (
    <div className="spark-wrap" ref={wrapRef}>
      <svg className="spark" viewBox={`0 0 ${W} ${H}`} role="img">
        {/* Axe Y : graduations 0 / 50 / 100 */}
        {[0, 50, 100].map((v) => (
          <g key={v}>
            <line x1={mL} y1={y(v)} x2={W - mR} y2={y(v)} stroke="#edf2f7" strokeWidth="1" />
            <text x={mL - 5} y={y(v) + 3} textAnchor="end" className="spark-axe">{v}</text>
          </g>
        ))}

        {/* Seuils paramétrés */}
        <line x1={mL} y1={y(avert)} x2={W - mR} y2={y(avert)} stroke="#dd6b20" strokeWidth="1" strokeDasharray="3 3" opacity="0.5" />
        <line x1={mL} y1={y(crit)} x2={W - mR} y2={y(crit)} stroke="#e53e3e" strokeWidth="1" strokeDasharray="3 3" opacity="0.5" />

        {/* Axe X : un repère vertical par relevé, dates seulement aux extrémités (le survol donne le reste) */}
        {xticks.map((t, i) => {
          const bord = i === 0 || i === xticks.length - 1;
          const ancre = i === 0 ? "start" : i === xticks.length - 1 ? "end" : "middle";
          const tx = i === 0 ? mL : i === xticks.length - 1 ? W - mR : x(t.jour);
          return (
            <g key={i}>
              <line x1={x(t.jour)} y1={mT} x2={x(t.jour)} y2={y(0)} stroke="#f0f4f8" strokeWidth="1" />
              {bord && <text x={tx} y={H - mB + 14} textAnchor={ancre} className="spark-axe">{t.label}</text>}
            </g>
          );
        })}
        <line x1={mL} y1={y(0)} x2={W - mR} y2={y(0)} stroke="#cbd5e0" strokeWidth="1" />

        {/* Données */}
        <path d={aire} fill={color} opacity="0.10" />
        <path d={ligne} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
        {projection && (
          <>
            <path
              d={`M${x(dernier.jour).toFixed(1)},${y(dernier.taux).toFixed(1)} L${x(projection.jour).toFixed(1)},${y(projection.taux).toFixed(1)}`}
              fill="none" stroke={color} strokeWidth="2" strokeDasharray="3 4" opacity="0.8"
            />
            <circle cx={x(projection.jour)} cy={y(projection.taux)} r="3.5" fill="none" stroke={color} strokeWidth="1.5" />
          </>
        )}
        {points.map((p, i) => (
          <circle key={i} cx={x(p.jour)} cy={y(p.taux)} r={i === points.length - 1 ? 4 : 2.5} fill={color} />
        ))}
        {/* Zones de survol (plus larges que les points pour faciliter le pointage) */}
        {points.map((p, i) => (
          <circle
            key={`hit-${i}`}
            cx={x(p.jour)} cy={y(p.taux)} r="11"
            fill="transparent" style={{ cursor: "pointer" }}
            onMouseEnter={(e) => survol(e, p)}
            onMouseLeave={() => setTip(null)}
          />
        ))}
      </svg>
      {tip && (
        <div className="spark-tip" style={{ left: tip.left, top: tip.top }}>
          <span className="spark-tip-date">{dateLongue(tip.date)}</span>
          <span className="spark-tip-val">{tip.taux}%</span>
        </div>
      )}
    </div>
  );
}

function badgePrevision(prev) {
  if (!prev) return null;
  if (prev.statut === "saturation") {
    const urgence = prev.jours_restants <= 7 ? "prev-urgent" : prev.jours_restants <= 30 ? "prev-proche" : "prev-loin";
    const fiable = prev.n_points >= 3 && prev.r2 >= 0.5;
    return {
      classe: urgence,
      texte: `Saturation ≈ ${dateCourte(prev.date_saturation)} (dans ${prev.jours_restants} j)`,
      titre: fiable ? `Tendance +${prev.pente} pts/j (R²=${prev.r2})` : `Estimation peu fiable — ${prev.n_points} relevés, R²=${prev.r2}`,
      fiable,
    };
  }
  if (prev.statut === "deja_saturee") return { classe: "prev-urgent", texte: "Déjà saturée", titre: "", fiable: true };
  if (prev.statut === "stable") return { classe: "prev-stable", texte: "Tendance stable", titre: `Pente ${prev.pente} pts/j`, fiable: true };
  return { classe: "prev-muet", texte: "Historique insuffisant", titre: "Au moins 2 relevés nécessaires", fiable: false };
}

/** Un repère par jour de relevé (les libellés ne sont posés qu'aux extrémités). */
function calculerXticks(points, dateRef) {
  const jours = [...new Set(points.map((p) => p.jour))].sort((a, b) => a - b);
  return jours.map((j) => ({ jour: j, label: dateCourte(jourVersDate(dateRef, j)) }));
}

export default function Historique() {
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState(null);
  const [jours, setJours] = useState(30);
  const [releves, setReleves] = useState([]);
  const [seuils, setSeuils] = useState({});
  const [previsions, setPrevisions] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getBennes().then((data) => {
      setSites(data.map((d) => d.site));
      if (data.length > 0) setSiteId(data[0].site.id);
    });
  }, []);

  useEffect(() => {
    if (!siteId) return;
    setLoading(true);
    Promise.all([getHistoriqueSite(siteId, jours), getSeuils(), getPrevisions(siteId, jours)])
      .then(([rel, seu, prev]) => {
        setReleves(rel);
        const mapSeuils = {};
        seu.filter((s) => s.site_id === siteId).forEach((s) => {
          mapSeuils[s.type_dechet] = { avert: s.seuil_avertissement, crit: s.seuil_critique };
        });
        setSeuils(mapSeuils);
        const mapPrev = {};
        prev.forEach((p) => { mapPrev[p.type_dechet] = p; });
        setPrevisions(mapPrev);
      })
      .finally(() => setLoading(false));
  }, [siteId, jours]);

  const ordreChrono = [...releves].sort((a, b) => new Date(a.date_releve) - new Date(b.date_releve));
  const dateRef = ordreChrono.length ? ordreChrono[0].date_releve : null;

  // Pivot : une série {jour, taux} par type de benne.
  const series = {};
  for (const r of ordreChrono) {
    const jour = joursEntre(dateRef, r.date_releve);
    for (const b of r.bennes ?? []) {
      if (estTypeExclu(b.type_dechet)) continue;
      (series[b.type_dechet] ??= []).push({ jour, taux: b.taux, date: r.date_releve });
    }
  }

  const bennes = Object.entries(series)
    .map(([type, points]) => {
      const cfg = seuils[type] ?? { avert: 75, crit: 90 };
      const prev = previsions[type] ?? null;
      const dernier = points[points.length - 1];
      const lastJour = dernier.jour;
      let projection = null;
      let xMax = Math.max(lastJour, 1);
      if (prev && prev.statut === "saturation" && prev.date_saturation) {
        const satJour = joursEntre(dateRef, prev.date_saturation);
        const horizon = lastJour + Math.min(satJour - lastJour, 60); // on étend de 60 j max
        const projTaux = clamp(dernier.taux + prev.pente * (horizon - lastJour), 0, 100);
        projection = { jour: horizon, taux: projTaux };
        xMax = horizon;
      }
      const xticks = calculerXticks(points, dateRef);
      return { type, points, actuel: dernier.taux, prev, projection, xMax, xticks, ...cfg };
    })
    .sort((a, b) => b.actuel - a.actuel);

  const periode = ordreChrono.length
    ? `${dateCourte(dateRef)} → ${dateCourte(ordreChrono[ordreChrono.length - 1].date_releve)} · ${ordreChrono.length} relevés`
    : null;

  return (
    <div className="page">
      <h1>Évolution &amp; prévision du remplissage</h1>

      <div className="filtre-bar">
        <select value={siteId ?? ""} onChange={(e) => setSiteId(Number(e.target.value))}>
          {sites.map((s) => (
            <option key={s.id} value={s.id}>{s.nom}</option>
          ))}
        </select>
        <select value={jours} onChange={(e) => setJours(Number(e.target.value))}>
          <option value={7}>7 jours</option>
          <option value={30}>30 jours</option>
          <option value={90}>90 jours</option>
        </select>
        {periode && <span className="evo-periode">{periode}</span>}
      </div>

      {loading && <SkeletonCharts n={4} />}

      {!loading && bennes.length > 0 && (
        <div className="evo-grid">
          {bennes.map((b) => {
            const couleur = couleurStatut(b.actuel, b.avert, b.crit);
            const badge = badgePrevision(b.prev);
            return (
              <div key={b.type} className="evo-row">
                <div className="evo-head">
                  <span className="evo-name">{nomContenant(b.type)}</span>
                  <span className={`badge-contenant ${estCompacteur(b.type) ? "is-compacteur" : "is-benne"}`}>
                    {estCompacteur(b.type) ? "Compacteur" : "Benne"}
                  </span>
                  {badge && (
                    <span className={`evo-prev ${badge.classe}`} title={badge.titre}>
                      {badge.texte}{!badge.fiable && " *"}
                    </span>
                  )}
                  <span className="evo-value" style={{ color: couleur }}>{b.actuel}%</span>
                </div>
                <Sparkline
                  points={b.points}
                  projection={b.projection}
                  xMax={b.xMax}
                  xticks={b.xticks}
                  color={couleur}
                  avert={b.avert}
                  crit={b.crit}
                />
              </div>
            );
          })}
        </div>
      )}

      {!loading && bennes.length === 0 && (
        <EmptyState
          icon="activity"
          title="Aucun relevé sur cette période"
          subtitle="Élargissez la période ou importez davantage de relevés pour voir les tendances."
        />
      )}

      {!loading && bennes.length > 0 && (
        <p className="evo-legende">
          Axe vertical : taux de remplissage (%). Axe horizontal : dates des relevés.
          Trait plein : relevés. Pointillés : projection linéaire jusqu'au seuil critique.
          « * » = estimation peu fiable (peu de relevés ou tendance irrégulière).
        </p>
      )}
    </div>
  );
}
