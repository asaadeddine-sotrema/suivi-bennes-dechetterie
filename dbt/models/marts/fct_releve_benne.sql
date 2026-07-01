-- Table de faits : une ligne par benne et par relevé.
-- Grain = (releve_id, benne_id). C'est la base de toutes les analyses de remplissage.
with bennes as (
    select * from {{ ref('stg_bennes') }}
),

releves as (
    select * from {{ ref('stg_releves') }}
)

select
    b.benne_id,
    r.releve_id,
    r.site_id,
    r.date_releve,
    b.type_dechet,
    b.a_compacteur,
    case when b.a_compacteur then 'Compacteur' else 'Benne' end as type_contenant,
    b.taux,
    -- Statut selon les seuils par défaut (75 % / 90 %).
    case
        when b.taux >= 90 then 'critique'
        when b.taux >= 75 then 'avertissement'
        else 'normal'
    end as statut
from bennes b
inner join releves r on r.releve_id = b.releve_id
