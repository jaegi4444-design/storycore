-- StoryCore initial schema

create extension if not exists "pgcrypto";

-- Works
create table public.works (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  genre text not null default '',
  one_line_summary text not null default '',
  synopsis text not null default '',
  author_note text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Characters
create table public.characters (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  work_id uuid not null references public.works(id) on delete cascade,
  name text not null,
  alias text not null default '',
  age text not null default '',
  gender text not null default '',
  affiliation text not null default '',
  role text not null default '',
  rank_or_job text not null default '',
  abilities text not null default '',
  personality text not null default '',
  appearance text not null default '',
  first_appearance_episode integer,
  current_status text not null default 'active'
    check (current_status in ('active', 'dead', 'missing', 'unknown')),
  public_info text not null default '',
  secret_info text not null default '',
  memo text not null default '',
  image_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Episodes
create table public.episodes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  work_id uuid not null references public.works(id) on delete cascade,
  episode_number integer not null,
  title text not null,
  summary text not null default '',
  character_ids uuid[] not null default '{}',
  locations text[] not null default '{}',
  revealed_settings text not null default '',
  foreshadows text not null default '',
  resolved_foreshadows text not null default '',
  draft text not null default '',
  author_note text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (work_id, episode_number)
);

-- World settings
create table public.world_settings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  work_id uuid not null references public.works(id) on delete cascade,
  name text not null,
  category text not null
    check (category in ('term', 'organization', 'location', 'item', 'ability', 'monster', 'event', 'rankSystem')),
  description text not null default '',
  related_character_ids uuid[] not null default '{}',
  related_episode_ids uuid[] not null default '{}',
  memo text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- User preferences
create table public.user_preferences (
  user_id uuid primary key references auth.users(id) on delete cascade,
  selected_work_id uuid references public.works(id) on delete set null,
  updated_at timestamptz not null default now()
);

-- Indexes
create index works_user_id_idx on public.works(user_id);
create index characters_work_id_idx on public.characters(work_id);
create index characters_user_id_idx on public.characters(user_id);
create index episodes_work_id_idx on public.episodes(work_id);
create index world_settings_work_id_idx on public.world_settings(work_id);

-- RLS
alter table public.works enable row level security;
alter table public.characters enable row level security;
alter table public.episodes enable row level security;
alter table public.world_settings enable row level security;
alter table public.user_preferences enable row level security;

create policy "works_select_own" on public.works for select using (auth.uid() = user_id);
create policy "works_insert_own" on public.works for insert with check (auth.uid() = user_id);
create policy "works_update_own" on public.works for update using (auth.uid() = user_id);
create policy "works_delete_own" on public.works for delete using (auth.uid() = user_id);

create policy "characters_select_own" on public.characters for select using (auth.uid() = user_id);
create policy "characters_insert_own" on public.characters for insert with check (auth.uid() = user_id);
create policy "characters_update_own" on public.characters for update using (auth.uid() = user_id);
create policy "characters_delete_own" on public.characters for delete using (auth.uid() = user_id);

create policy "episodes_select_own" on public.episodes for select using (auth.uid() = user_id);
create policy "episodes_insert_own" on public.episodes for insert with check (auth.uid() = user_id);
create policy "episodes_update_own" on public.episodes for update using (auth.uid() = user_id);
create policy "episodes_delete_own" on public.episodes for delete using (auth.uid() = user_id);

create policy "world_settings_select_own" on public.world_settings for select using (auth.uid() = user_id);
create policy "world_settings_insert_own" on public.world_settings for insert with check (auth.uid() = user_id);
create policy "world_settings_update_own" on public.world_settings for update using (auth.uid() = user_id);
create policy "world_settings_delete_own" on public.world_settings for delete using (auth.uid() = user_id);

create policy "user_preferences_select_own" on public.user_preferences for select using (auth.uid() = user_id);
create policy "user_preferences_insert_own" on public.user_preferences for insert with check (auth.uid() = user_id);
create policy "user_preferences_update_own" on public.user_preferences for update using (auth.uid() = user_id);
create policy "user_preferences_delete_own" on public.user_preferences for delete using (auth.uid() = user_id);

-- Storage bucket for character images
insert into storage.buckets (id, name, public)
values ('character-images', 'character-images', true)
on conflict (id) do nothing;

create policy "character_images_select"
  on storage.objects for select
  using (bucket_id = 'character-images');

create policy "character_images_insert"
  on storage.objects for insert
  with check (
    bucket_id = 'character-images'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

create policy "character_images_update"
  on storage.objects for update
  using (
    bucket_id = 'character-images'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

create policy "character_images_delete"
  on storage.objects for delete
  using (
    bucket_id = 'character-images'
    and auth.uid()::text = (storage.foldername(name))[1]
  );
