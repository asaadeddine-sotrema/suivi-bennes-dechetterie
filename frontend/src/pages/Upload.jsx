import { useState } from "react";
import UploadZone from "../components/UploadZone";

export default function Upload({ onImport }) {
  const [resultats, setResultats] = useState([]);

  function handleSuccess(result) {
    setResultats((prev) => [result, ...prev]);
    onImport?.();
  }

  return (
    <div className="page">
      <h1>Importer un relevé PDF</h1>
      <p className="page-subtitle">
        Déposez un formulaire Kizeo Forms <em>«&nbsp;Etat des lieux des bennes&nbsp;»</em> pour alimenter le tableau de bord.
      </p>

      <UploadZone onSuccess={handleSuccess} />

      {resultats.length > 0 && (
        <div className="resultats">
          <h2>Imports de cette session</h2>
          {resultats.map((r, i) => (
            <div key={i} className="resultat-card">
              <div className="resultat-header">
                <strong>{r.site}</strong>
                <span className="resultat-date">
                  {new Date(r.date_releve).toLocaleDateString("fr-FR")}
                </span>
                {r.agent && <span className="resultat-agent">— {r.agent}</span>}
              </div>

              <div className="resultat-bennes">
                {r.bennes.map((b, j) => {
                  const alerte = r.alertes.some((a) => a.type_dechet === b.type_dechet);
                  return (
                    <span
                      key={j}
                      className="benne-mini-tag"
                      style={{ backgroundColor: alerte ? "#fed7aa" : "#c6f6d5" }}
                    >
                      {b.type_dechet} {b.taux}%
                    </span>
                  );
                })}
              </div>

              {r.alertes.length > 0 && (
                <div className="resultat-alertes">
                  ⚠️ {r.alertes.length} alerte{r.alertes.length > 1 ? "s" : ""} générée{r.alertes.length > 1 ? "s" : ""} :{" "}
                  {r.alertes.map((a) => `${a.type_dechet} (${a.taux}%)`).join(", ")}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
