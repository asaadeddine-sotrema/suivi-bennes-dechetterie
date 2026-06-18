import { useRef, useState } from "react";
import { uploadPdf } from "../api/client";

export default function UploadZone({ onSuccess }) {
  const [drag, setDrag] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  async function handleFile(file) {
    if (!file || file.type !== "application/pdf") {
      setError("Veuillez déposer un fichier PDF");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await uploadPdf(file);
      onSuccess?.(result);
    } catch (e) {
      setError(e.response?.data?.detail || "Erreur lors de l'import");
    } finally {
      setLoading(false);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDrag(false);
    handleFile(e.dataTransfer.files[0]);
  }

  return (
    <div
      className={`upload-zone ${drag ? "drag-over" : ""} ${loading ? "uploading" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      onClick={() => !loading && inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        style={{ display: "none" }}
        onChange={(e) => handleFile(e.target.files[0])}
      />
      {loading ? (
        <div className="upload-inner">
          <div className="upload-spinner" />
          <p>Analyse en cours...</p>
        </div>
      ) : (
        <div className="upload-inner">
          <span className="upload-icon">📄</span>
          <p className="upload-label">Déposez un PDF Kizeo ici</p>
          <p className="upload-hint">ou cliquez pour parcourir</p>
        </div>
      )}
      {error && <p className="upload-error">{error}</p>}
    </div>
  );
}
