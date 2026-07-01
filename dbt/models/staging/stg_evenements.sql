-- Journal des opérations terrain : tassements et rotations.
select
    id            as evenement_id,
    site_id,
    type_dechet,
    evenement,
    fait_le
from {{ source('sotrema', 'historique_tassements') }}
