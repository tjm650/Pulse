# Pulse database

Pulse uses the Supabase PostgreSQL project **Community** in `eu-west-2`.

The application tables are created and versioned through Supabase SQL migrations. Django remains the application ORM and API layer; it does not recreate or independently migrate the Supabase-managed application tables.

The database includes compatibility views that expose the table and column names expected by the preserved Community Django models while writing through to the corresponding Supabase tables. These views use PostgreSQL's `security_invoker` behavior so the underlying table security policies remain in effect.

Django connects through the `DATABASE_URL` environment variable. Use the Supabase session pooler connection string when the backend host requires IPv4. Connection credentials are not committed to this repository.

No legacy application data was imported. Supabase Auth is the identity provider, and the profile rows in `public.profiles` are linked to `auth.users`.
