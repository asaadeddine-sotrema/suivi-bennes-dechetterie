import axios from "axios";

const TOKEN_KEY = "sotrema_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t);
export const clearToken = () => localStorage.removeItem(TOKEN_KEY);

const client = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

// Ajoute le jeton à chaque requête
client.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Déconnexion automatique si le jeton est invalide/expiré
client.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401 && getToken()) {
      clearToken();
      window.dispatchEvent(new Event("auth:expired"));
    }
    return Promise.reject(error);
  }
);

// --- Authentification ---
export const login = (username, password) =>
  client.post("/auth/login", { username, password }).then((r) => r.data);
export const getMe = () => client.get("/auth/me").then((r) => r.data);
export const getUsers = () => client.get("/auth/users").then((r) => r.data);
export const createUser = (data) => client.post("/auth/users", data).then((r) => r.data);
export const deleteUser = (id) => client.delete(`/auth/users/${id}`).then((r) => r.data);

export const getBennes = () => client.get("/bennes/").then((r) => r.data);
export const getHistoriqueSite = (siteId, jours = 30) =>
  client.get(`/bennes/${siteId}/historique`, { params: { jours } }).then((r) => r.data);
export const getPrevisions = (siteId, jours = 30) =>
  client.get(`/bennes/${siteId}/prevision`, { params: { jours } }).then((r) => r.data);

export const uploadPdf = (file) => {
  const form = new FormData();
  form.append("file", file);
  return client
    .post("/upload/pdf", form, { headers: { "Content-Type": "multipart/form-data" } })
    .then((r) => r.data);
};

export const getStats = () => client.get("/reporting/stats").then((r) => r.data);

export const exporterRelevesCsv = async () => {
  const resp = await client.get("/reporting/releves.csv", { responseType: "blob" });
  const url = URL.createObjectURL(resp.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = "releves_bennes.csv";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

export const getSyncStatus = () => client.get("/sync/status").then((r) => r.data);
export const syncManual = () => client.post("/sync/manual").then((r) => r.data);

export const demanderTassement = (siteId, typeDechet) =>
  client.post(`/bennes/${siteId}/demander-tassement`, { type_dechet: typeDechet }).then((r) => r.data);

export const annulerDemandeTassement = (siteId, typeDechet) =>
  client.delete(`/bennes/${siteId}/${encodeURIComponent(typeDechet)}/demander-tassement`).then((r) => r.data);

export const rotationBenne = (siteId, typeDechet) =>
  client.post(`/bennes/${siteId}/rotation`, { type_dechet: typeDechet }).then((r) => r.data);

export const annulerRotationFaite = (siteId, typeDechet) =>
  client.delete(`/bennes/${siteId}/${encodeURIComponent(typeDechet)}/rotation-faite`).then((r) => r.data);

export const getHistoriqueTassements = (siteId, typeDechet) =>
  client.get(`/bennes/${siteId}/tassements/historique`, { params: { type_dechet: typeDechet } }).then((r) => r.data);

export const getSeuils = () => client.get("/parametrage/seuils").then((r) => r.data);
export const updateSeuil = (siteId, typeDechet, data) =>
  client.put(`/parametrage/seuils/${siteId}/${encodeURIComponent(typeDechet)}`, data).then((r) => r.data);

export const planifierTassement = (siteId, typeDechet, prevuAt) =>
  client.post(`/bennes/${siteId}/${encodeURIComponent(typeDechet)}/planifier-tassement`, { prevu_at: prevuAt }).then((r) => r.data);
export const annulerPlanification = (siteId, typeDechet) =>
  client.delete(`/bennes/${siteId}/${encodeURIComponent(typeDechet)}/planifier-tassement`).then((r) => r.data);

export const planifierRotation = (siteId, typeDechet, prevuAt) =>
  client.post(`/bennes/${siteId}/${encodeURIComponent(typeDechet)}/planifier-rotation`, { prevu_at: prevuAt }).then((r) => r.data);
export const annulerPlanificationRotation = (siteId, typeDechet) =>
  client.delete(`/bennes/${siteId}/${encodeURIComponent(typeDechet)}/planifier-rotation`).then((r) => r.data);
