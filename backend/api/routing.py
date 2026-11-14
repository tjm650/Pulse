"""Django Channels is intentionally not used by Pulse.

Realtime subscriptions are managed by Supabase Realtime from the mobile client.
Keep this module free of Channels imports so normal Django deployments do not
require Channels or Daphne.
"""

websocket_urlpatterns = []
