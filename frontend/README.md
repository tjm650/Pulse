# Pulse frontend

This directory preserves the original Community React Native and Expo frontend structure, components, navigation, screens, assets, themes, state management, and workflows.

The source of truth is `tjm650/Community` on `main`. Preserve the existing design and functionality; change the application name to Pulse only where required.

## Runtime endpoints

Configure the Expo environment for the Pulse deployment:
- `EXPO_PUBLIC_API_URL`: full URL of the deployed Pulse Django API (HTTPS in production)
- `EXPO_PUBLIC_API_HOST`: API hostname used by the existing WebSocket connection
- `EXPO_PUBLIC_SUPABASE_URL`: Supabase project URL
- `EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY`: Supabase publishable key

The Supabase publishable key is intended for client applications. Never place a database password or Supabase service-role key in the frontend. The local API fallback is `http://localhost:8000`; set the deployed API URL before testing on a physical device or production build.

## Local development environment

For GitHub Codespaces or local development, create `frontend/.env` from `frontend/.env.example` and enter the Supabase project URL and publishable key. The `.env` file is ignored by Git and must not be committed. Alternatively, define the same `EXPO_PUBLIC_*` variables as Codespaces secrets/environment variables.

After setting them, restart Metro from `frontend/`:

```bash
npx expo start --dev-client --tunnel --clear
```

The app config maps the documented `EXPO_PUBLIC_*` names into Expo's runtime `extra` values and retains compatibility with the older `EXPO_SUPABASE_*` names.
