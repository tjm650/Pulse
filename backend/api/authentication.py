import jwt
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import User


class SupabaseJWTAuthentication(BaseAuthentication):
    """Validate Supabase Auth access tokens and resolve their profile row."""

    keyword = b"bearer"

    def authenticate(self, request):
        parts = get_authorization_header(request).split()
        if not parts:
            return None
        if len(parts) != 2 or parts[0].lower() != self.keyword:
            raise AuthenticationFailed("Invalid Authorization header.")

        try:
            token = parts[1].decode("utf-8")
            jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
            signing_key = jwt.PyJWKClient(jwks_url).get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["ES256", "RS256"],
                audience="authenticated",
                issuer=f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1",
                options={"require": ["exp", "iat", "sub", "iss", "aud"]},
            )
        except Exception as exc:
            raise AuthenticationFailed("Invalid or expired Supabase access token.") from exc

        try:
            user = User.objects.get(pk=claims["sub"])
        except (ObjectDoesNotExist, ValueError, TypeError) as exc:
            raise AuthenticationFailed("The authenticated user profile was not found.") from exc

        if not user.is_active:
            raise AuthenticationFailed("This account is inactive.")
        if user.is_suspended_now:
            raise AuthenticationFailed("This account is suspended.")

        return user, claims

    def authenticate_header(self, request):
        return "Bearer"
