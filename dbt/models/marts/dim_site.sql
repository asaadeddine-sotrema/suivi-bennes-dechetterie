-- Dimension site : ajoute le secteur géographique (Est / Ouest), dérivé du nom.
-- Même règle que l'application front (liste fixe pour l'Est, le reste = Ouest).
with sites as (
    select * from {{ ref('stg_sites') }}
),

normalise as (
    select
        *,
        -- Majuscules + suppression des accents (sans extension Postgres).
        translate(upper(nom),
                  'ÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ',
                  'AAAEEEEIIOOUUUC') as nom_norm
    from sites
)

select
    site_id,
    code,
    nom,
    actif,
    case
        when nom_norm ~ 'ACHERES|CONFLANS|ORGEVAL|TRIEL|MUREAUX' then 'est'
        else 'ouest'
    end as secteur
from normalise
