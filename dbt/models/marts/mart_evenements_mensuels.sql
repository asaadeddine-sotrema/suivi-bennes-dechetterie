-- Activité mensuelle par déchèterie : nombre de tassements et de rotations.
with e as (
    select * from {{ ref('stg_evenements') }}
)

select
    e.site_id,
    s.nom        as site_nom,
    s.secteur,
    date_trunc('month', e.fait_le)::date              as mois,
    sum(case when e.evenement = 'tassement' then 1 else 0 end) as nb_tassements,
    sum(case when e.evenement = 'rotation'  then 1 else 0 end) as nb_rotations
from e
inner join {{ ref('dim_site') }} s on s.site_id = e.site_id
group by e.site_id, s.nom, s.secteur, date_trunc('month', e.fait_le)
