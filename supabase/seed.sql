-- Optional seed data for the first voice model
insert into public.voice_models (name, description, voice_bank_path, speaker, backend_url, is_active)
values (
  'Default DiffSinger Voice',
  'Starter voice model entry for local DiffSinger backend integration',
  '',
  '',
  'http://127.0.0.1:8000',
  true
)
on conflict do nothing;
