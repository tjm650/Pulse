alter table public.profiles add column if not exists is_superuser boolean not null default false;
