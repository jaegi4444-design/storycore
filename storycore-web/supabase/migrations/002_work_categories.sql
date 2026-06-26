-- Work categories (rank, job, affiliation) and character field split

alter table public.works
  add column if not exists ranks jsonb not null default '[]',
  add column if not exists jobs jsonb not null default '[]',
  add column if not exists affiliations jsonb not null default '[]';

alter table public.characters
  add column if not exists rank text not null default '',
  add column if not exists job text not null default '',
  add column if not exists affiliation_detail text not null default '';

update public.characters
set rank = coalesce(nullif(rank, ''), rank_or_job)
where rank_or_job is not null and rank_or_job <> '';

alter table public.characters
  drop column if exists rank_or_job;
