import AlerteBadge from "./AlerteBadge";

export default function BenneRow({ benne }) {
  const { type_dechet, taux, a_compacteur } = benne;
  const couleur = taux >= 90 ? "#e53e3e" : taux >= 75 ? "#dd6b20" : "#38a169";

  return (
    <div className="benne-row">
      <span className="benne-type">
        {type_dechet}
        {a_compacteur && <span className="compacteur-tag"> C</span>}
      </span>
      <div className="barre-container">
        <div
          className="barre-remplissage"
          style={{ width: `${taux}%`, backgroundColor: couleur }}
        />
      </div>
      <AlerteBadge taux={taux} />
    </div>
  );
}
