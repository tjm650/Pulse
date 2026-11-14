"""
Migration router for the Pulse database.

The public application schema is created and versioned through Supabase SQL
migrations. Django keeps its ORM models, but must not attempt to recreate or
alter those Supabase-managed application tables.
"""

SUPABASE_MANAGED_APPS = {
    "api",
    "ablog",
    "afollows",
    "amessages",
    "anotif",
    "amonetization",
    "app_notif",
    "asearch",
    "ausernotif",
    "auserpost",
    "community",
    "quercus",
    "rest_framework_simplejwt",
}


class SupabaseSchemaRouter:
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label in SUPABASE_MANAGED_APPS:
            return False
        return None
