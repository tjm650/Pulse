# Phase 1 — Initial source inspection

**Status:** In progress  
**Source repository:** https://github.com/tjm650/Community  
**Source branch:** `main`  
**Target repository:** https://github.com/tjm650/Pulse  
**Target branch:** `main`

## 1. Repository verification

| Item | Verified finding |
|---|---|
| Source repository | `tjm650/Community` |
| Source default branch | `main` |
| Target repository | `tjm650/Pulse` |
| Target default branch | `main` |
| Target state at kickoff | Empty repository |
| Source tree entries | 1,095 |
| Frontend tree entries | 592 |
| Backend tree entries | 490 |
| Frontend screen source files | 305 |
| Backend Django model modules | 13 |

The source tree was retrieved recursively and was not reported as truncated.

## 2. Verified frontend architecture

The source `frontend/package.json` identifies a React Native / Expo application using:

- Expo `^54.0.32`
- React `^19.2.3`
- React Native `^0.83.1`
- Expo Router `^6.0.22`
- React Navigation 7
- Zustand `^4.5.7`
- React Native Paper `^5.14.5`
- Supabase JS `^2.91.0`
- Axios `^1.13.2`
- Expo Image, Image Picker, Blur, Linear Gradient, Reanimated, SVG, and Video packages

Verified entry composition in `frontend/App.js`:

- `SafeAreaProvider`
- `StatusBarManager`
- `ScreenWraper`
- `PaperProvider`
- `StackNavigation`

Verified navigation sources include:

- `frontend/components/navigation/StackNavigation.js`
- `frontend/components/navigation/Drawer.js`
- `frontend/components/navigation/BottomNav.js`
- `frontend/components/StackScreens/AuthenticationStack.js`
- `frontend/components/StackScreens/CheckSignUp.js`
- `frontend/components/StackScreens/DrawerStack.js`
- `frontend/components/StackScreens/SplashStack.js`

The inspected stack flow checks initialisation, authentication, signup completion, and then loads the drawer application. The inspected bottom navigation actively registers Home, Notifications, and Search. Community and monetisation tab definitions are commented out in the inspected file; they must not be reactivated merely because related screens exist.

## 3. Verified state and theme sources

- Global Zustand store: `frontend/assets/core/useGlobal.js`
- Theme definitions: `frontend/constants/DarkColor/` and `frontend/constants/LightColor/`
- Supabase client stub: `frontend/services/supabase.js`
- Supabase connector: `frontend/services/supabaseConnector.js`

The inspected Zustand store contains state and handlers for authentication, search, profile management, messaging, communities, monetisation, notifications, posts, blogs, connections, and Quercus AI.

The global theme files confirm separate light and dark colour definitions. The exact values in the source files, not approximations in planning notes, remain authoritative.

## 4. Verified Django backend to preserve

The source backend is currently Django, not FastAPI:

- `backend/requirements.txt` includes Django 5.2.8, Django REST Framework 3.15.2, Channels-related ASGI support, PostgreSQL driver, and Django-specific test/runtime packages.
- `backend/manage.py` invokes Django management commands.
- The source contains 13 Django model modules across feature apps, including blogs, follows, messages, monetisation, service notifications, core API, official app notifications, search, user notifications, posts, communities, consumer views, and Quercus.
- The backend project settings file is `backend/backend/settings.py`.

**Owner's confirmed decision:** Keep Django as the backend and API framework. The rebuilt application must follow the existing Community Django project and app structure. Do not replace Django with FastAPI or introduce a new backend architecture. Supabase is the database platform for the rebuilt application; integrate it with Django while preserving existing models, API routes, serializers, views, authentication flow, and realtime behaviour wherever compatible with the approved Supabase change.

The inspected frontend Supabase client currently contains placeholder URL and anonymous-key strings. No live Supabase configuration was verified in the inspected file. Do not infer or reuse a Supabase project from placeholders. Do not add configuration files or environment-variable conventions beyond what is necessary and explicitly approved for the Supabase integration.

## 5. Security and repository hygiene risks

The source tree contains tracked environment files at:

- `.env`
- `backend/.env`
- `frontend/.env`

Their contents have deliberately **not** been copied into this repository or reproduced in this report. Their presence in Git history is a security review item. The owner should verify whether any real credentials were committed and rotate exposed credentials where necessary. Removing a file from the latest commit alone does not remove it from Git history.

The source tree also contains 154 tracked paths associated with Python `__pycache__` directories or `.pyc` bytecode files. These are generated artifacts and should not be copied into the rebuilt repository.

No secrets, environment-file values, database credentials, or private keys have been added to Pulse.

## 6. Branding decision

The new product name is **Pulse**, as explicitly requested by the owner. The source prompt otherwise requires strict preservation of the original UI and assets. The working rule is therefore:

- Change the product/application name where the app identity is presented or configured.
- Preserve original logo and image assets pending explicit direction or source evidence that an asset itself contains editable branding.
- Preserve all other visual styling, copy, navigation, and workflows.

## 7. Remaining Phase 1 work

The initial inspection is not a complete source audit. Remaining work includes:

1. Enumerate every registered screen and navigation route.
2. Inventory reusable UI components and their source dependencies.
3. Extract complete theme values, typography, icon callsites, and asset references.
4. Trace every frontend API call to its legacy Django route and response shape.
5. Inspect all Django models, migrations, serializers, views, URL configurations, and WebSocket consumers.
6. Map media upload/display flows and Supabase Realtime/socket usage.
7. Identify implemented, partially implemented, disconnected, and incomplete features.
8. Record source evidence and unresolved questions while retaining the existing Django route and app structure; make only the database changes needed for Supabase.

No redesign or additional configuration should be introduced. Preserve the existing Django API contract and source structure; change only what is necessary to connect the application to Supabase.
