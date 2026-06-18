import { useEffect, useState } from "react";
import { getBennes, getHistoriqueSite } from "../api/client";

export default function Historique() {
  const [sites, setSites] = useState([]);
  const [siteId, setSiteId] = useState(null);
  const [jours, setJours] = useState(30);
  const [releves, setReleves] = useState([]);
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
    getHistoriqueSite(siteId, jours)
      .then(setReleves)
      .finally(() => setLoading(false));
  }, [siteId, jours]);

  return (
    <div className="page">
      <h1>Historique des relevés</h1>

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
      </div>

      {loading && <p className="loading">Chargement...</p>}

      {releves.map((releve) => (
        <div key={releve.id} className="releve-block">
          <h4>
            {new Date(releve.date_releve).toLocaleDateString("fr-FR")}
            {releve.agent && <span className="agent"> — {releve.agent}</span>}
          </h4>
          <div className="bennes-mini">
            {releve.bennes?.map((b) => (
              <span
                key={b.id}
                className="benne-mini-tag"
                style={{ backgroundColor: b.taux >= 75 ? "#fed7aa" : "#c6f6d5" }}
              >
                {b.type_dechet} {b.taux}%
              </span>
            ))}
          </div>
        </div>
      ))}

      {!loading && releves.length === 0 && (
        <p className="no-data">Aucun relevé sur cette période</p>
      )}
    </div>
  );
}
