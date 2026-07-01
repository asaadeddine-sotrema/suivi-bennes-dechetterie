import { describe, it, expect } from "vitest";
import { couleurStatut, secteurSite, STATUT, estCompacteur, nomContenant } from "./theme";

describe("couleurStatut", () => {
  it("vert sous le seuil d'avertissement", () => {
    expect(couleurStatut(50, 75, 90)).toBe(STATUT.ok);
  });
  it("orange entre avertissement et critique", () => {
    expect(couleurStatut(80, 75, 90)).toBe(STATUT.warning);
  });
  it("rouge au-delà du seuil critique", () => {
    expect(couleurStatut(95, 75, 90)).toBe(STATUT.critical);
  });
});

describe("secteurSite", () => {
  it("classe les déchèteries de l'Est (insensible casse/accents)", () => {
    expect(secteurSite({ nom: "Achères", code: "ACHERES" })).toBe("est");
    expect(secteurSite({ nom: "Les Mureaux", code: "LES MUREAUX" })).toBe("est");
    expect(secteurSite({ nom: "Conflans-Sainte-Honorine", code: "CONFLANS" })).toBe("est");
    expect(secteurSite({ nom: "Triel", code: "TRIEL" })).toBe("est");
    expect(secteurSite({ nom: "Orgeval", code: "ORGEVAL" })).toBe("est");
  });
  it("met le reste à l'Ouest", () => {
    expect(secteurSite({ nom: "Closeaux 1", code: "CLOSEAUX 1" })).toBe("ouest");
    expect(secteurSite({ nom: "Limay", code: "LIMAY" })).toBe("ouest");
  });
});

describe("contenant", () => {
  it("détecte un compacteur", () => {
    expect(estCompacteur("Compacteur Bois")).toBe(true);
    expect(estCompacteur("Bois")).toBe(false);
  });
  it("retire le préfixe « Compacteur » du nom", () => {
    expect(nomContenant("Compacteur Bois")).toBe("Bois");
    expect(nomContenant("Carton")).toBe("Carton");
  });
});
