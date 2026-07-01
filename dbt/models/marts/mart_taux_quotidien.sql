-- Synthèse quotidienne par déchèterie : taux moyen/max, nombre de bennes en alerte.
with f as (
    select * from {{ ref('fct_releve_benne') }}
)

select
    f.site_id,
    s.nom        as site_nom,
    s.secteur,
    f.date_releve,
    count(*)                                          as nb_bennes,
    round(avg(f.taux))                                as taux_moyen,
    max(f.taux)                                       as taux_max,
    sum(case when f.taux >= 75 then 1 else 0 end)     as nb_en_alerte
from f
inner join {{ ref('dim_site') }} s on s.site_id = f.site_id
group by f.site_id, s.nom, s.secteur, f.date_releve
