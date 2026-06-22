import { useEffect, useState } from "react";
import { getSeuils, updateSeuil } from "../api/client";

export default function Parametrage() {
  const [seuils, setSeuils] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState({});
  const [edits, setEdits] = useState({});
  const [saved, setSaved] = useState({});

  useEffect(() => {
    getSeuils()
      .then((data) => {
        setSeuils(data);
        const initial = {};
        data.forEach((s) => {
          const key = `${s.site_id}__${s.type_dechet}`;
          initial[key] = { avert: s.seuil_avertissement, critique: s.seuil_critique };
        });
        setEdits(initial);
      })
      .catch(() => setError("Impossible de charger les paramètres"))
      .finally(() => setLoading(false));
  }, []);

  const handleChange = (siteId, typeDechet, field, value) => {
    const key = `${siteId}__${typeDechet}`;
    setEdits((prev) => ({ ...prev, [key]: { ...prev[key], [field]: Number(value) } }));
    setSaved((prev) => ({ ...prev, [key]: false }));
  };

  const handleSave = async (siteId, typeDechet) => {
    const key = `${siteId}__${typeDechet}`;
    const { avert, critique } = edits[key] || {};
    if (!avert || !critique) return;
    if (avert >= critique) {
      alert("Le seuil d'avertissement doit être inférieur au seuil critique");
      return;
    }
    setSaving((prev) => ({ ...prev, [key]: true }));
    try {
      await updateSeuil(siteId, typeDechet, { seuil_avertissement: avert, seuil_critique: critique });
      setSaved((prev) => ({ ...prev, [key]: true }));
      setSeuils((prev) =>
        prev.map((s) =>
          s.site_id === siteId && s.type_dechet === typeDechet
            ? { ...s, seuil_avertissement: avert, seuil_critique: critique }
            : s
        )
      );
    } catch {
      alert("Erreur lors de la sauvegarde");
    } finally {
      setSaving((prev) => ({ ...prev, [key]: false }));
    }
  };

  // Grouper par site
  const bySite = seuils.reduce((acc, s) => {
    if (!acc[s.site_id]) acc[s.site_id] = { nom: s.site_nom, bennes: [] };
    acc[s.site_id].bennes.push(s);
    return acc;
  }, {});

  return (
    <div className="page">
      <div className="page-header">
        <h1>Paramétrage des seuils</h1>
      </div>
      <p className="page-subtitle">
        Configurez les seuils d'alerte par benne. Les seuils s'appliquent à l'import de PDFs et à l'affichage du tableau de bord.
      </p>

      {loading && <p className="loading">Chargement...</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && Object.keys(bySite).length === 0 && (
        <p className="no-data">Aucune benne trouvée — importez d'abord un PDF pour voir les bennes disponibles.</p>
      )}

      <div className="param-sites">
        {Object.entries(bySite).map(([siteId, { nom, bennes }]) => (
          <div key={siteId} className="param-site-block">
            <h2>{nom}</h2>
            <table className="param-table">
              <thead>
                <tr>
                  <th>Type de déchet</th>
                  <th>Seuil avertissement (%)</th>
                  <th>Seuil critique (%)</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {bennes.map((s) => {
                  const key = `${s.site_id}__${s.type_dechet}`;
                  const edit = edits[key] || { avert: s.seuil_avertissement, critique: s.seuil_critique };
                  const isSaving = saving[key];
                  const isSaved = saved[key];
                  const dirty =
                    edit.avert !== s.seuil_avertissement || edit.critique !== s.seuil_critique;
                  return (
                    <tr key={s.type_dechet}>
                      <td className="param-type">{s.type_dechet}</td>
                      <td>
                        <div className="param-seuil-cell">
                          <input
                            type="number"
                            min={1}
                            max={99}
                            value={edit.avert}
                            onChange={(e) => handleChange(s.site_id, s.type_dechet, "avert", e.target.value)}
                            className="param-input param-input-avert"
                          />
                          <span className="param-preview-bar">
                            <span
                              className="param-preview-fill"
                              style={{ width: `${edit.avert}%`, background: "#dd6b20" }}
                            />
                          </span>
                        </div>
                      </td>
                      <td>
                        <div className="param-seuil-cell">
                          <input
                            type="number"
                            min={1}
                            max={100}
                            value={edit.critique}
                            onChange={(e) => handleChange(s.site_id, s.type_dechet, "critique", e.target.value)}
                            className="param-input param-input-critique"
                          />
                          <span className="param-preview-bar">
                            <span
                              className="param-preview-fill"
                              style={{ width: `${edit.critique}%`, background: "#e53e3e" }}
                            />
                          </span>
                        </div>
                      </td>
                      <td>
                        <button
                          className={`btn-param-save${isSaved && !dirty ? " saved" : ""}`}
                          onClick={() => handleSave(s.site_id, s.type_dechet)}
                          disabled={isSaving || (!dirty && !isSaved)}
                        >
                          {isSaving ? "..." : isSaved && !dirty ? "Enregistré" : "Enregistrer"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ))}
      </div>
    </div>
  );
}
