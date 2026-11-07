# OmniLog — Frontend Client

The frontend client for **OmniLog**, a comprehensive tracking platform for TV series and video games. Built using Next.js (App Router), TypeScript, and Tailwind CSS, this client communicates with the FastAPI backend to provide real-time library management, search, and personal tracking dashboards.

---

## Tech Stack & Core Libraries

- **Framework:** Next.js (App Router, React 19)
- **Language:** TypeScript
- **Styling:** Tailwind CSS (with `clsx` and `tailwind-merge` for clean utility management)
- **Icons:** `lucide-react`
- **Networking:** `axios` (configured for FastAPI endpoints)
- **Data Visualization:** `recharts` (for activity analytics and rating charts)

---

## Directory Architecture

```text
frontend/
├── src/
│   ├── proxy.ts           # Sends visitors without a login away from protected pages
│   ├── app/               # Next.js App Router (pages, layouts, routes)
│   │   ├── layout.tsx     # Global layout. Reads the logged-in user for the navbar
│   │   ├── error.tsx, loading.tsx, not-found.tsx   # Shared error and loading screens
│   │   ├── login/, register/, library/, friends/   # Pages
│   │   └── session-expired/   # Route that removes a refused session cookie
│   ├── components/        # UI elements: auth forms, navbar, library cards, empty/error/loading states
│   ├── lib/
│   │   ├── auth/          # Cookie name, token expiry and the list of protected paths
│   │   ├── server/        # Server-only code: backendFetch, session cookie and the functions
│   │   │                  # that read and change library, catalog, chapters, lists and diary
│   │   └── actions/       # Server Actions (login, register, logout)
│   └── types/             # Types of the backend answers (api.ts) and of screen states
├── tests/                 # Vitest tests. The folders follow src/. tests/security checks happy-dom
├── public/                # Static assets, logos, and vector illustrations
├── package.json           # Frontend dependency manifest
├── tsconfig.json          # TypeScript compilation configuration
└── next.config.ts         # Next.js environment & framework settings
```

## Login and data

The login token is kept in an httpOnly cookie, so scripts in the browser cannot read it. Pages and Server Actions call the backend on the server with `authedFetch` (`src/lib/server/authed.ts`). It sends the token and handles the failures in one place:

- No login: the user goes to `/login`.
- The backend answers 401: the user goes to `/session-expired`, which removes the cookie, and then to `/login`.
- Any other failure is shown by the page. `toErrorState` (`src/lib/server/error-state.ts`) turns it into a not-found, unavailable (503 or no answer) or error state.

A new protected page is added to `PROTECTED_PREFIXES` in `src/lib/auth/routes.ts`, and its link to `src/lib/navigation.ts`.

## Tests

```bash
npm test
```

The tests run with Vitest. Components run in happy-dom, and a test that needs plain Node starts with `// @vitest-environment node`. The settings that stop happy-dom from running code of a page are in `vitest.config.mts`. `tests/helpers/forms.ts` has the helpers to fill forms quickly.
