# Pulse

Pulse is the source-driven rebuild of the existing Community mobile application.

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
