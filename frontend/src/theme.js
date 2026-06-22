// Source unique des couleurs de statut, partagée par les composants qui
// colorent dynamiquement (barres, courbes). Les mêmes valeurs sont déclarées
// en variables CSS dans index.css (:root) pour le reste de l'interface.
export const STATUT = {
  ok: "#38a169",
  warning: "#dd6b20",
  critical: "#e53e3e",
  neutral: "#6b7280",
};

/** Couleur d'un taux selon les seuils paramétrés. */
export function couleurStatut(taux, seuilAvertissement = 75, seuilCritique = 90) {
  if (taux >= seuilCritique) return STATUT.critical;
  if (taux >= seuilAvertissement) return STATUT.warning;
  return STATUT.ok;
}
