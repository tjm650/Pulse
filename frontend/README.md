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

## Supabase environment variables

The frontend reads `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_PUBLISHABLE_KEY` directly using Expo's supported `process.env.EXPO_PUBLIC_*` substitution. They must be present when the JavaScript bundle is created.

For EAS Build/Update, define both variables in the Expo project's EAS environment (for example, the `development` and `production` environments). For GitHub Codespaces, define them as Codespaces secrets/environment variables so the Metro process receives them. EAS-hosted variables are not automatically injected into a separately running Codespace.

A local `frontend/.env` file is optional: it is a convenient way to provide the same values to local Metro. Copy `.env.example` to `.env` only if you are not supplying them through the platform environment. Never commit `.env`. The publishable key is designed for client use; database access must still be protected by Supabase Row Level Security. Never use the service-role key in the app.
