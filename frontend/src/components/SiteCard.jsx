import { useState } from "react";
import BenneRow from "./BenneRow";

export default function SiteCard({ site, releve, onRefresh }) {
  const [ouvert, setOuvert] = useState(false);
  const bennes = releve?.bennes ?? [];
  const nbAlertes = bennes.filter((b) => b.taux >= (b.seuil_avertissement ?? 75)).length;

  return (
    <div className="site-card">
      <div className="site-card-header" onClick={() => setOuvert(!ouvert)}>
        <div>
          <h3>{site.nom}</h3>
          <small>{site.code}</small>
        </div>
        <div className="site-card-meta">
          {releve ? (
            <span className="date-releve">
              {new Date(releve.date_releve).toLocaleDateString("fr-FR")}
            </span>
          ) : (
            <span className="no-data">Aucun relevé</span>
          )}
          {nbAlertes > 0 && (
            <span className="alerte-count">{nbAlertes} alerte{nbAlertes > 1 ? "s" : ""}</span>
          )}
          <span className="chevron">{ouvert ? "▲" : "▼"}</span>
        </div>
      </div>

      {ouvert && (
        <div className="site-card-body">
          {bennes.length === 0 ? (
            <p className="no-data">Aucune benne enregistrée</p>
          ) : (
            bennes.map((b) => (
              <BenneRow key={b.id} benne={b} siteId={site.id} onRefresh={onRefresh} />
            ))
          )}
        </div>
      )}
    </div>
  );
}
