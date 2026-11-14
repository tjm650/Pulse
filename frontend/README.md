# Pulse frontend

This directory preserves the original Community React Native and Expo frontend structure, components, navigation, screens, assets, themes, state management, and workflows.

The source of truth is `tjm650/Community` on `main`. Preserve the existing design and functionality; change the application name to Pulse only where required.

## Runtime endpoints

Configure these environment variables for the Pulse deployment:

- `EXPO_API_URL`: full URL of the deployed Pulse Django API (HTTPS in production)
- `EXPO_PUBLIC_API_HOST`: API hostname used by the existing WebSocket connection
- `EXPO_SUPABASE_URL`: Supabase project URL
- `EXPO_SUPABASE_PUBLISHABLE_KEY`: Supabase publishable key

The Supabase publishable key is intended for client applications. Never place a database password or Supabase service-role key in the frontend. The local API fallback is `http://localhost:8000`; set the deployed API URL before testing on a physical device or production build.

## Local development environment

For GitHub Codespaces, no Supabase variables or production credentials are required just to launch the app. Supabase-dependent messaging and Realtime features remain unavailable until a Supabase URL and publishable key are configured in a trusted development environment. If live Supabase testing is needed, use a separate development Supabase project rather than production.

After setting them, restart Metro from `frontend/`:

```bash
npx expo start --dev-client --tunnel --clear
```

## Expo environment variables

The app config passes `EXPO_API_URL`, `EXPO_SUPABASE_URL`, and `EXPO_SUPABASE_PUBLISHABLE_KEY` into Expo runtime `extra` values. The API client and Supabase client read those runtime values. These names intentionally do not use the `EXPO_PUBLIC_` prefix.

For EAS Build/Update, define the required variables in the appropriate Expo project EAS environments (for example, `development` and `production`). EAS-hosted variables are not automatically injected into a separately running Codespace. Do not add production Supabase configuration to Codespaces.

A local `frontend/.env` file is optional and is only needed when testing Supabase-backed features locally. Without the Supabase variables, the app starts with Supabase disabled; Supabase-backed messaging and Realtime operations show a configuration error if invoked. Never commit `.env`. The publishable key is designed for client use; database access must still be protected by Supabase Row Level Security. Never use the service-role key in the app.
