-- Sites (déchèteries), renommés proprement.
select
    id            as site_id,
    code,
    nom,
    actif,
    created_at
from {{ source('sotrema', 'sites') }}
