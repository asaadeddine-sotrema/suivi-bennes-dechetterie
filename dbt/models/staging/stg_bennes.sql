-- Une ligne par benne mesurée dans un relevé (taux de remplissage).
select
    id            as benne_id,
    releve_id,
    type_dechet,
    taux,
    a_compacteur
from {{ source('sotrema', 'bennes') }}
