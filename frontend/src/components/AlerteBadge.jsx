export default function AlerteBadge({ taux, seuilCritique = 90, seuilAvertissement = 75 }) {
  if (taux >= seuilCritique) return <span className="badge badge-critical">{taux}%</span>;
  if (taux >= seuilAvertissement) return <span className="badge badge-warning">{taux}%</span>;
  return <span className="badge badge-ok">{taux}%</span>;
}
