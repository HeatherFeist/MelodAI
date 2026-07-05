-- Supabase schema for MelodAI / DiffSinger integration
-- Paste this into the Supabase SQL Editor and run it.

create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- Drop existing objects so the script is safe to re-run in the SQL editor.
drop trigger if exists voice_models_touch on public.voice_models;
drop trigger if exists voice_profiles_touch on public.voice_profiles;
drop trigger if exists songs_touch on public.songs;
drop trigger if exists generation_jobs_touch on public.generation_jobs;
drop function if exists public.touch_updated_at() cascade;
drop policy if exists "Allow public read access to voice models" on public.voice_models;
drop policy if exists "Allow public write access to voice models" on public.voice_models;
drop policy if exists "Allow public read access to voice profiles" on public.voice_profiles;
drop policy if exists "Allow public write access to voice profiles" on public.voice_profiles;
drop policy if exists "Allow public read access to songs" on public.songs;
drop policy if exists "Allow public write access to songs" on public.songs;
drop policy if exists "Allow public read access to generation jobs" on public.generation_jobs;
drop policy if exists "Allow public write access to generation jobs" on public.generation_jobs;
drop policy if exists "Allow public read access to audio outputs" on storage.objects;
drop policy if exists "Allow public upload to audio outputs" on storage.objects;
drop policy if exists "Allow public update to audio outputs" on storage.objects;
drop policy if exists "Allow public delete from audio outputs" on storage.objects;

create table if not exists public.voice_models (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text,
  voice_bank_path text,
  speaker text,
  backend_url text default 'http://127.0.0.1:8000',
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.voice_profiles (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  tags text[] default '{}',
  appsdk_voice text,
  color text,
  samples jsonb default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.songs (
  id uuid primary key default gen_random_uuid(),
  title text not null default 'Untitled Song',
  lyrics text,
  style text,
  genre text,
  voice text,
  status text not null default 'draft',
  audio_url text,
  audio_storage_path text,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.generation_jobs (
  id uuid primary key default gen_random_uuid(),
  song_id uuid references public.songs(id) on delete cascade,
  voice_model_id uuid references public.voice_models(id) on delete set null,
  prompt text,
  status text not null default 'queued',
  error_message text,
  result_audio_url text,
  result_storage_path text,
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create or replace function public.touch_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger voice_models_touch
before update on public.voice_models
for each row execute function public.touch_updated_at();

create trigger voice_profiles_touch
before update on public.voice_profiles
for each row execute function public.touch_updated_at();

create trigger songs_touch
before update on public.songs
for each row execute function public.touch_updated_at();

create trigger generation_jobs_touch
before update on public.generation_jobs
for each row execute function public.touch_updated_at();

alter table public.voice_models enable row level security;
alter table public.voice_profiles enable row level security;
alter table public.songs enable row level security;
alter table public.generation_jobs enable row level security;

create policy "Allow public read access to voice models"
  on public.voice_models for select using (true);
create policy "Allow public insert access to voice models"
  on public.voice_models for insert with check (true);
create policy "Allow public update access to voice models"
  on public.voice_models for update using (true) with check (true);
create policy "Allow public delete access to voice models"
  on public.voice_models for delete using (true);

create policy "Allow public read access to voice profiles"
  on public.voice_profiles for select using (true);
create policy "Allow public insert access to voice profiles"
  on public.voice_profiles for insert with check (true);
create policy "Allow public update access to voice profiles"
  on public.voice_profiles for update using (true) with check (true);
create policy "Allow public delete access to voice profiles"
  on public.voice_profiles for delete using (true);

create policy "Allow public read access to songs"
  on public.songs for select using (true);
create policy "Allow public insert access to songs"
  on public.songs for insert with check (true);
create policy "Allow public update access to songs"
  on public.songs for update using (true) with check (true);
create policy "Allow public delete access to songs"
  on public.songs for delete using (true);

create policy "Allow public read access to generation jobs"
  on public.generation_jobs for select using (true);
create policy "Allow public insert access to generation jobs"
  on public.generation_jobs for insert with check (true);
create policy "Allow public update access to generation jobs"
  on public.generation_jobs for update using (true) with check (true);
create policy "Allow public delete access to generation jobs"
  on public.generation_jobs for delete using (true);

-- Create a public bucket for generated audio files
insert into storage.buckets (id, name, public)
values ('audio-outputs', 'audio-outputs', true)
on conflict (id) do nothing;

create policy "Allow public read access to audio outputs"
  on storage.objects for select using (bucket_id = 'audio-outputs');
create policy "Allow public upload to audio outputs"
  on storage.objects for insert with check (bucket_id = 'audio-outputs');
create policy "Allow public update to audio outputs"
  on storage.objects for update using (bucket_id = 'audio-outputs') with check (bucket_id = 'audio-outputs');
create policy "Allow public delete from audio outputs"
  on storage.objects for delete using (bucket_id = 'audio-outputs');
