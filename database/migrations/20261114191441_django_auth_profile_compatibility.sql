alter table public.profiles add column if not exists password varchar(128) not null default '!', add column if not exists last_login timestamptz;
