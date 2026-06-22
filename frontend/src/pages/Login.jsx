import { useState } from "react";
import { useAuth } from "../components/Auth";
import Icon from "../components/Icon";

export default function Login() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username.trim(), password);
    } catch (err) {
      setError(err.response?.data?.detail || "Connexion impossible");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <div className="login-brand">
          <Icon name="truck" size={28} className="login-logo" />
          <div>
            <div className="login-title">SOTREMA</div>
            <div className="login-sub">Suivi des bennes</div>
          </div>
        </div>

        <label className="login-label">
          Identifiant
          <input
            type="text" autoComplete="username" value={username}
            onChange={(e) => setUsername(e.target.value)} autoFocus required
          />
        </label>
        <label className="login-label">
          Mot de passe
          <input
            type="password" autoComplete="current-password" value={password}
            onChange={(e) => setPassword(e.target.value)} required
          />
        </label>

        {error && <div className="login-error">{error}</div>}

        <button type="submit" className="login-btn" disabled={loading || !username || !password}>
          {loading ? "Connexion…" : "Se connecter"}
        </button>
      </form>
    </div>
  );
}
