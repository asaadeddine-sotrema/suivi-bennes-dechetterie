import { useState } from "react";
import BenneRow from "./BenneRow";
import Icon from "./Icon";

function dateRelative(dateStr) {
  if (!dateStr) return null;
  const jours = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86400000);
  const label = jours <= 0 ? "aujourd'hui" : jours === 1 ? "hier" : `il y a ${jours} j`;
  return { label, perime: jours > 2 };
}

export default function SiteCard({ site, releve, onRefresh }) {
  const [ouvert, setOuvert] = useState(true);
  const bennes = releve?.bennes ?? [];
  const nbAlertes = bennes.filter((b) => b.taux >= (b.seuil_avertissement ?? 75)).length;
  const rel = dateRelative(releve?.date_releve);

  // Bennes les plus pleines en premier.
  const bennesTriees = [...bennes].sort((a, b) => b.taux - a.taux);

  // Liseré coloré selon la benne la plus critique du site (rouge > orange > vert).
  const niveau = (b) =>
    b.taux >= (b.seuil_critique ?? 90) ? 3 : b.taux >= (b.seuil_avertissement ?? 75) ? 2 : 1;
  const pire = bennes.reduce((m, b) => Math.max(m, niveau(b)), 0);
  const lisere =
    pire === 3 ? "var(--c-critical)" : pire === 2 ? "var(--c-warning)" : pire === 1 ? "var(--c-ok)" : "transparent";

  return (
    <div className="site-card" style={{ borderLeft: `4px solid ${lisere}` }}>
      <div
        className="site-card-header"
        onClick={() => setOuvert(!ouvert)}
        role="button"
        tabIndex={0}
        aria-expanded={ouvert}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setOuvert((o) => !o); }
        }}
      >
        <div>
          <h3>{site.nom}</h3>
          <small>{site.code} · {bennes.length} benne{bennes.length > 1 ? "s" : ""}</small>
        </div>
        <div className="site-card-meta">
          {releve ? (
            <span
              className={`date-releve${rel?.perime ? " date-perimee" : ""}`}
              title={`Relevé du ${new Date(releve.date_releve).toLocaleDateString("fr-FR")}`}
            >
              {rel?.perime && <Icon name="clock" size={12} />} {rel?.label}
            </span>
          ) : (
            <span className="no-data">Aucun relevé</span>
          )}
          {nbAlertes > 0 && (
            <span className="alerte-count">{nbAlertes} alerte{nbAlertes > 1 ? "s" : ""}</span>
          )}
          <span className="chevron"><Icon name={ouvert ? "chevron-up" : "chevron-down"} size={16} /></span>
        </div>
      </div>

      {ouvert && (
        <div className="site-card-body">
          {bennes.length === 0 ? (
            <p className="no-data">Aucune benne enregistrée</p>
          ) : (
            bennesTriees.map((b) => (
              <BenneRow key={b.id} benne={b} siteId={site.id} onRefresh={onRefresh} />
            ))
          )}
        </div>
      )}
    </div>
  );
}
