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

// Découpage géographique des déchèteries. Le secteur Est est une liste fixe ;
// tout le reste est rattaché au secteur Ouest.
const SITES_EST = ["ACHERE", "CONFLANS", "ORGEVAL", "TRIEL", "MUREAUX"];

const sansAccent = (s) =>
  (s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toUpperCase();

/** Secteur d'un site : "est" ou "ouest" (par défaut). */
export function secteurSite(site) {
  const ref = `${sansAccent(site?.nom)} ${sansAccent(site?.code)}`;
  return SITES_EST.some((mot) => ref.includes(mot)) ? "est" : "ouest";
}

/** Vrai si le type de déchet correspond à un compacteur. */
export const estCompacteur = (type) => /^compacteur\s/i.test(type ?? "");

/** Nom d'affichage du contenant, sans le préfixe « Compacteur ». */
export const nomContenant = (type) => (type ?? "").replace(/^Compacteur\s+/i, "");
