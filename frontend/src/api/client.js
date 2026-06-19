import axios from "axios";

const client = axios.create({
  baseURL: "/api",
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

export const getSyncStatus = () => client.get("/sync/status").then((r) => r.data);
export const syncManual = () => client.post("/sync/manual").then((r) => r.data);

export const setTassement = (siteId, typeDechet, tassee) =>
  client.patch(`/bennes/${siteId}/tassement`, { type_dechet: typeDechet, tassee }).then((r) => r.data);

export const rotationBenne = (siteId, typeDechet) =>
  client.post(`/bennes/${siteId}/rotation`, { type_dechet: typeDechet }).then((r) => r.data);
