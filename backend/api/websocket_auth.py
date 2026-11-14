"""Authenticate WebSocket connections with Supabase access tokens."""
from urllib.parse import parse_qs

import jwt
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

from api.authentication import _jwks_client
from api.models import User


@database_sync_to_async
def _get_active_user(subject):
    try:
        user = User.objects.get(pk=subject)
    except (User.DoesNotExist, ValueError, TypeError):
        return AnonymousUser()
    if not user.is_active or user.is_suspended_now:
        return AnonymousUser()
    return user


class SupabaseJWTWebSocketMiddleware:
    """Validate a short-lived Supabase JWT before accepting a socket."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode("utf-8"))
        tokens = query.get("token", [])
        user = AnonymousUser()
        if len(tokens) == 1 and tokens[0]:
            try:
                token = tokens[0]
                key = _jwks_client().get_signing_key_from_jwt(token).key
                claims = jwt.decode(
                    token,
                    key,
                    algorithms=["ES256", "RS256"],
                    audience="authenticated",
                    issuer=f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
                    options={"require": ["exp", "iat", "sub", "iss", "aud"]},
                )
                user = await _get_active_user(claims["sub"])
            except Exception:
                user = AnonymousUser()

        authenticated_scope = dict(scope)
        authenticated_scope["user"] = user
        return await self.inner(authenticated_scope, receive, send)
