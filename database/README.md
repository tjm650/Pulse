# Pulse database

Pulse uses Supabase PostgreSQL as its database.

Django remains responsible for the application models, database access, and schema migrations. The authoritative migrations are kept with their Django apps under `backend/<app>/migrations/` and are applied using Django's normal migration workflow.

The Django database connection reads `DATABASE_URL` from the environment. Supabase connection details are intentionally not committed to this repository.

Do not create a second, independently maintained schema that duplicates the Django models and migrations.
