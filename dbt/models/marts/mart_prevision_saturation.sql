-- Prévision de saturation par benne : tendance linéaire du taux sur 30 jours
-- (régression en SQL via regr_slope) et estimation des jours avant 100 %.
with f as (
    select site_id, type_dechet, date_releve, taux
    from {{ ref('fct_releve_benne') }}
    where date_releve >= current_date - interval '30 days'
),

-- Pente de la droite taux = f(jour), en points de % par jour.
tendance as (
    select
        site_id,
        type_dechet,
        count(*)                                                        as n_points,
        regr_slope(taux, extract(epoch from date_releve) / 86400.0)     as pente_pct_jour
    from f
    group by site_id, type_dechet
),

-- Dernier taux connu de chaque benne.
dernier as (
    select distinct on (site_id, type_dechet)
        site_id, type_dechet, taux as taux_actuel, date_releve as derniere_date
    from f
    order by site_id, type_dechet, date_releve desc
)

select
    t.site_id,
    ds.nom        as site_nom,
    t.type_dechet,
    d.taux_actuel,
    d.derniere_date,
    t.n_points,
    round(t.pente_pct_jour::numeric, 2)                                 as pente_pct_jour,
    case
        when t.n_points < 2 or t.pente_pct_jour is null or t.pente_pct_jour <= 0 then null
        else ceil((100 - d.taux_actuel) / t.pente_pct_jour)
    end                                                                 as jours_avant_saturation,
    case
        when t.n_points < 2 then 'insuffisant'
        when t.pente_pct_jour is null or t.pente_pct_jour <= 0 then 'stable'
        when d.taux_actuel >= 100 then 'saturee'
        else 'en_hausse'
    end                                                                 as tendance
from tendance t
inner join dernier d  on d.site_id = t.site_id and d.type_dechet = t.type_dechet
inner join {{ ref('dim_site') }} ds on ds.site_id = t.site_id
