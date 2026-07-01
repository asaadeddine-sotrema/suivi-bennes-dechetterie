-- Test singulier : le taux de remplissage doit rester entre 0 et 100 %.
-- Le test échoue si cette requête renvoie au moins une ligne.
select benne_id, taux
from {{ ref('fct_releve_benne') }}
where taux < 0 or taux > 100
