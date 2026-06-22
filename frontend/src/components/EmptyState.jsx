import Icon from "./Icon";

/** État vide illustré : icône + titre + sous-titre optionnel. */
export default function EmptyState({ icon = "inbox", title, subtitle, tone = "neutral" }) {
  return (
    <div className={`empty-state empty-${tone}`}>
      <Icon name={icon} size={40} className="empty-icon" strokeWidth={1.5} />
      <p className="empty-title">{title}</p>
      {subtitle && <p className="empty-subtitle">{subtitle}</p>}
    </div>
  );
}
