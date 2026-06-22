/** Bloc de chargement animé (placeholder). */
export default function Skeleton({ width = "100%", height = 14, radius = 6, style = {} }) {
  return <span className="skeleton" style={{ width, height, borderRadius: radius, ...style }} />;
}

/** Cartes de site en chargement (Tableau de bord). */
export function SkeletonSites({ n = 3 }) {
  return (
    <div className="sites-list">
      {Array.from({ length: n }).map((_, i) => (
        <div key={i} className="site-card" style={{ padding: "14px 20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <Skeleton width={160} height={15} />
              <Skeleton width={70} height={11} />
            </div>
            <Skeleton width={90} height={20} radius={99} />
          </div>
        </div>
      ))}
    </div>
  );
}

/** Lignes de tableau en chargement. */
export function SkeletonRows({ rows = 4, cols = 6 }) {
  return (
    <tbody>
      {Array.from({ length: rows }).map((_, r) => (
        <tr key={r}>
          {Array.from({ length: cols }).map((__, c) => (
            <td key={c}><Skeleton height={12} /></td>
          ))}
        </tr>
      ))}
    </tbody>
  );
}

/** Cartes de courbes en chargement (Historique). */
export function SkeletonCharts({ n = 4 }) {
  return (
    <div className="evo-grid">
      {Array.from({ length: n }).map((_, i) => (
        <div key={i} className="evo-row">
          <div className="evo-head">
            <Skeleton width={110} height={13} />
            <Skeleton width={48} height={16} style={{ marginLeft: "auto" }} />
          </div>
          <Skeleton height={70} radius={8} style={{ marginTop: 8, display: "block" }} />
        </div>
      ))}
    </div>
  );
}
