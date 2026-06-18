export default function AlerteBadge({ taux }) {
  if (taux >= 90) return <span className="badge badge-critical">{taux}%</span>;
  if (taux >= 75) return <span className="badge badge-warning">{taux}%</span>;
  return <span className="badge badge-ok">{taux}%</span>;
}
