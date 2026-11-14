"""Authenticate WebSocket connections with Supabase access tokens."""
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

import jwt

from api.authentication import _jwks_client
from api.models import User


@sync_to_async
def _decode_access_token(token):
    signing_key = _jwks_client().get_signing_key_from_jwt(token).key
    return jwt.decode(
        token,
        signing_key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
        issuer=f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
        options={"require": ["exp", "iat", "sub", "iss", "aud"]},
    )


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
    """Validate a Supabase JWT from Authorization header (or legacy query token)."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        headers = dict(scope.get("headers", []))
        authorization = headers.get(b"authorization", b"").decode("latin1")
        bearer = authorization.split()
        token = bearer[1] if len(bearer) == 2 and bearer[0].lower() == "bearer" else None

        # Retain query-token support for older app builds during the transition.
        if token is None:
            from urllib.parse import parse_qs
            query = parse_qs(scope.get("query_string", b"").decode("utf-8"))
            tokens = query.get("token", [])
            if len(tokens) == 1:
                token = tokens[0]

        user = AnonymousUser()
        auth_exp = None
        if token:
            try:
                claims = await _decode_access_token(token)
                user = await _get_active_user(claims["sub"])
                auth_exp = claims["exp"]
            except Exception:
                user = AnonymousUser()

        authenticated_scope = dict(scope)
        authenticated_scope["user"] = user
        authenticated_scope["auth_exp"] = auth_exp
        return await self.inner(authenticated_scope, receive, send)
