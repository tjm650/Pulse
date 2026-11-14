# Pulse

Pulse is the new application repository for the source-driven rebuild of the existing Community mobile application.

## Project direction

- **Product name:** Pulse
- **Source of truth:** [tjm650/Community](https://github.com/tjm650/Community), branch `main`
- **Target repository:** [tjm650/Pulse](https://github.com/tjm650/Pulse), branch `main`
- **Mobile frontend:** Preserve the existing React Native / Expo application, navigation, Zustand state responsibilities, screens, assets, and interaction design.
- **Backend and API:** Preserve the existing Django backend structure and workflows from Community.
- **Database:** Supabase PostgreSQL, integrated with the existing Django backend. Use Supabase Auth, Storage, Row Level Security, and Realtime only where required by the original application and the approved architecture.

## Non-negotiable rebuild rule

This is a source-code-driven replication, not a redesign. Do not invent screens, features, workflows, copy, visual elements, data relationships, or business rules. Record incomplete or uncertain source behaviour rather than filling gaps with assumptions.

The requested product-name change to **Pulse** is the explicit identity change. Existing visual design, layouts, colours, typography, icon sources, assets, and behaviour remain governed by the original source unless the owner explicitly approves a change.

## Current status

The target repository was confirmed empty at project kickoff. The source-driven rebuild will preserve the Community repository structure, with the explicitly approved changes: rename the application to Pulse and use Supabase as the database platform. No secrets or environment-file values are to be copied.

See [docs/source-audit/phase-1-initial-findings.md](docs/source-audit/phase-1-initial-findings.md) for verified kickoff findings and audit risks.
