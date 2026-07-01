-- Relevés journaliers (un PDF Kizeo = un relevé).
select
    id            as releve_id,
    site_id,
    date_releve,
    agent,
    recu_at
from {{ source('sotrema', 'releves') }}
