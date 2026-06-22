import { useEffect, useState } from "react";
import { getUsers, createUser, deleteUser } from "../api/client";
import { useToast } from "../components/Toast";
import { useAuth } from "../components/Auth";
import { SkeletonRows } from "../components/Skeleton";
import Icon from "../components/Icon";

export default function Utilisateurs() {
  const notify = useToast();
  const { user: courant } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ username: "", password: "", role: "operateur" });
  const [saving, setSaving] = useState(false);

  const charger = () => getUsers().then(setUsers).finally(() => setLoading(false));
  useEffect(() => { charger(); }, []);

  const ajouter = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await createUser(form);
      notify(`Compte « ${form.username} » créé`);
      setForm({ username: "", password: "", role: "operateur" });
      charger();
    } catch (err) {
      notify(err.response?.data?.detail || "Création impossible", "error");
    } finally {
      setSaving(false);
    }
  };

  const supprimer = async (u) => {
    if (!window.confirm(`Supprimer le compte « ${u.username} » ?`)) return;
    try {
      await deleteUser(u.id);
      notify("Compte supprimé");
      charger();
    } catch (err) {
      notify(err.response?.data?.detail || "Suppression impossible", "error");
    }
  };

  return (
    <div className="page">
      <h1>Utilisateurs</h1>
      <p className="page-subtitle">Gérez les comptes et leurs rôles (administrateur ou opérateur).</p>

      <form className="user-form" onSubmit={ajouter}>
        <input
          placeholder="Identifiant" value={form.username}
          onChange={(e) => setForm({ ...form, username: e.target.value })} required
        />
        <input
          type="password" placeholder="Mot de passe (min. 6)" value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={6}
        />
        <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
          <option value="operateur">Opérateur</option>
          <option value="admin">Administrateur</option>
        </select>
        <button type="submit" className="btn-param-save" disabled={saving}>
          <Icon name="check" size={14} /> Créer
        </button>
      </form>

      <table className="alertes-table">
        <thead>
          <tr><th>Identifiant</th><th>Rôle</th><th>Statut</th><th></th></tr>
        </thead>
        {loading ? (
          <SkeletonRows rows={3} cols={4} />
        ) : (
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.username}{u.id === courant?.id && " (vous)"}</td>
                <td><span className={`statut-badge ${u.role === "admin" ? "statut-envoye" : "statut-resolu"}`}>{u.role}</span></td>
                <td>{u.actif ? "Actif" : "Inactif"}</td>
                <td>
                  {u.id !== courant?.id && (
                    <button className="btn-resoudre" onClick={() => supprimer(u)}>Supprimer</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        )}
      </table>
    </div>
  );
}
