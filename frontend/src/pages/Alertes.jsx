import { useEffect, useState } from "react";
import { getAllertes, resoudreAlerte } from "../api/client";

export default function Alertes() {
  const [alertes, setAlertes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtre, setFiltre] = useState("actives");

  useEffect(() => {
    getAllertes()
      .then(setAlertes)
      .finally(() => setLoading(false));
  }, []);

  const alertesFiltrees =
    filtre === "actives" ? alertes.filter((a) => a.statut === "envoye") : alertes;

  async function handleResoudre(id) {
    await resoudreAlerte(id);
    setAlertes((prev) =>
      prev.map((a) => (a.id === id ? { ...a, statut: "resolu" } : a))
    );
  }

  return (
    <div className="page">
      <h1>Alertes</h1>

      <div className="filtre-bar">
        <button
          className={filtre === "actives" ? "btn-filtre active" : "btn-filtre"}
          onClick={() => setFiltre("actives")}
        >
          Actives ({alertes.filter((a) => a.statut === "envoye").length})
        </button>
        <button
          className={filtre === "toutes" ? "btn-filtre active" : "btn-filtre"}
          onClick={() => setFiltre("toutes")}
        >
          Toutes ({alertes.length})
        </button>
      </div>

      {loading && <p className="loading">Chargement...</p>}

      <table className="alertes-table">
        <thead>
          <tr>
            <th>Site</th>
            <th>Benne</th>
            <th>Taux</th>
            <th>Destinataire</th>
            <th>Envoyée le</th>
            <th>Statut</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {alertesFiltrees.map((a) => (
            <tr key={a.id} className={a.statut === "resolu" ? "row-resolu" : ""}>
              <td>{a.site_nom || "—"}</td>
              <td>{a.type_dechet || `#${a.benne_id}`}</td>
              <td>{a.seuil_declenche}%</td>
              <td>{a.email_destinataire}</td>
              <td>{a.envoye_at ? new Date(a.envoye_at).toLocaleString("fr-FR") : "—"}</td>
              <td>
                <span className={`statut-badge statut-${a.statut}`}>{a.statut}</span>
              </td>
              <td>
                {a.statut === "envoye" && (
                  <button className="btn-resoudre" onClick={() => handleResoudre(a.id)}>
                    Résoudre
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
