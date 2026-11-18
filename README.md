# Pulse

## Project structure

```text
Pulse/
├── backend/     # Django backend and API, following Community
├── database/    # Supabase PostgreSQL schema and migrations
└── frontend/    # React Native + Expo application, following Community
```

## Agreed technology

- **Frontend:** React Native + Expo
- **Backend and API:** Django
- **Database:** Supabase PostgreSQL

## Source and target

- **Original source:** https://github.com/tjm650/Community
- **Source branch:** `main`
- **Pulse repository:** https://github.com/tjm650/Pulse
- **Target branch:** `main`

## Implementation rules

- Preserve the Community source structure, application workflows, screens, navigation, components, assets, themes, and visual design.
- The product name changes from Community to **Pulse** where the application identity is presented.
- Keep Django as the backend. Do not introduce FastAPI.
- Use Supabase for the database integration.
- Do not add features, redesigns, or configurations that were not requested.
- Do not copy committed environment secrets, local database files, or generated Python bytecode into Pulse.


## Online Expo development with GitHub Codespaces

1. Open the repository on GitHub and choose **Code → Codespaces → Create codespace on main**.
2. Wait for the Codespace setup to finish. The dev container installs the exact frontend dependencies with `npm ci` and installs the Expo tunnel helper without changing the committed package manifest or lockfile.
3. In the Codespaces terminal, run:

   ```bash
   cd frontend
   npx expo start --dev-client --tunnel
   ```

4. Wait for Expo to display its QR code, then open the installed Pulse Android development build and scan the code (or use the development server entry if it appears).
5. Keep the Codespace running while testing. Stop the Codespace from GitHub when finished.

This Codespaces configuration is for development only. It does not change the Render Django service, production EAS build profile, production environment variables, or production deployment. No Supabase credentials are required to start the app in Codespaces. Supabase-backed messaging and Realtime features remain disabled until a trusted development Supabase configuration is supplied; do not add production Supabase values to Codespaces.
