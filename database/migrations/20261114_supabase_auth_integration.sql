-- Supabase Auth owns account credentials and token lifecycle.
-- The public profile row remains linked to auth.users through profiles.id.

alter table public.profiles
  add column if not exists email text not null default '',
  add column if not exists is_active boolean not null default true,
  add column if not exists is_staff boolean not null default false,
  add column if not exists cell text not null default '',
  add column if not exists is_superuser boolean not null default false,
  add column if not exists password varchar(128) not null default '!',
  add column if not exists last_login timestamptz;

create unique index if not exists profiles_username_unique_idx
  on public.profiles (lower(username));

create unique index if not exists profiles_email_unique_idx
  on public.profiles (lower(email))
  where email <> '';

create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  metadata jsonb := coalesce(new.raw_user_meta_data, '{}'::jsonb);
  chosen_username text;
begin
  chosen_username := coalesce(
    nullif(metadata ->> 'username', ''),
    split_part(coalesce(new.email, ''), '@', 1),
    'user-' || left(new.id::text, 8)
  );

  insert into public.profiles (
    id, username, email, first_name, last_name, directory_status1,
    bio, profession, prof_initial, program, service_name, location,
    website, verified, theme_preference, language, timezone,
    agreement, market_agreement, is_active
  )
  values (
    new.id,
    chosen_username,
    coalesce(new.email, ''),
    coalesce(metadata ->> 'first_name', ''),
    coalesce(metadata ->> 'last_name', ''),
    coalesce(metadata ->> 'directory_status1', ''),
    coalesce(metadata ->> 'bio', ''),
    coalesce(metadata ->> 'profession', ''),
    coalesce(metadata ->> 'prof_initial', ''),
    coalesce(metadata ->> 'program', ''),
    coalesce(metadata ->> 'service_name', ''),
    coalesce(metadata ->> 'location', ''),
    coalesce(metadata ->> 'website', ''),
    false,
    'auto',
    'en',
    'UTC',
    false,
    false,
    true
  );

  insert into public.profile_private_data (user_id)
  values (new.id)
  on conflict (user_id) do nothing;

  insert into public.user_preferences (user_id)
  values (new.id)
  on conflict (user_id) do nothing;

  insert into public.user_analytics (user_id)
  values (new.id)
  on conflict (user_id) do nothing;

  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure public.handle_new_auth_user();
