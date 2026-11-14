# Pulse backend

This directory preserves the original Community Django backend structure and application responsibilities. The Django project, apps, models, serializers, views, URL routes, authentication, and realtime handlers belong here.

The source of truth is `tjm650/Community` on `main`. Keep Django; do not introduce FastAPI. Preserve existing behaviour while integrating Supabase as the database platform.

## Supabase authentication and database integration

Supabase Auth owns registration, password verification, access tokens, refresh tokens, and session revocation. Django accepts Supabase bearer access tokens, resolves the matching `public.profiles` row, and continues to serve the existing application API.

The auth-user database trigger provisions the corresponding profile, private profile data, preferences, and analytics rows. Django does not store or verify account passwords.

Required backend environment:
- `DATABASE_URL`: Supabase PostgreSQL connection string (use the Supabase session pooler for an IPv4-only backend host)
- `SECRET_KEY`: Django secret key
- `ALLOWED_HOSTS`: comma-separated Django hostnames
- `CORS_ALLOWED_ORIGINS`: comma-separated frontend origins

`SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` default to the Pulse Supabase project values and can be overridden through environment variables. Do not put the database password or any service-role key in the frontend.
