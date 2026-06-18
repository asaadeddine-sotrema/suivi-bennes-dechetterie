import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 30000,
});

export const getBennes = () => client.get("/bennes/").then((r) => r.data);
export const getHistoriqueSite = (siteId, jours = 30) =>
  client.get(`/bennes/${siteId}/historique`, { params: { jours } }).then((r) => r.data);
export const getAlertesActives = () => client.get("/alertes/actives").then((r) => r.data);
export const getAllertes = () => client.get("/alertes/").then((r) => r.data);
export const resoudreAlerte = (alerteId) =>
  client.patch(`/alertes/${alerteId}/resoudre`).then((r) => r.data);

export const uploadPdf = (file) => {
  const form = new FormData();
  form.append("file", file);
  return client
    .post("/upload/pdf", form, { headers: { "Content-Type": "multipart/form-data" } })
    .then((r) => r.data);
};
