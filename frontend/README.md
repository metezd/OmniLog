# OmniLog — Frontend Client

The frontend client for **OmniLog**, a comprehensive tracking platform for TV series and video games. Built using Next.js (App Router), TypeScript, and Tailwind CSS, this client communicates with the FastAPI backend to provide real-time library management, search, and personal tracking dashboards.

---

## Tech Stack & Core Libraries

- **Framework:** Next.js (App Router, React 19)
- **Language:** TypeScript
- **Styling:** Tailwind CSS (with `clsx` and `tailwind-merge` for clean utility management)
- **Icons:** `lucide-react`
- **Backend calls:** `fetch` in the server code (`src/lib/server`, Server Components and Server Actions). The browser never calls the backend directly
- **Charts:** the statistics screen (`/stats`) draws its bars with plain HTML and Tailwind, without a chart library

---

## Directory Architecture

```text
frontend/
├── src/
│   ├── app/               # Next.js App Router (pages, layouts, routes)
│   │   ├── layout.tsx     # Global layout and shell structure
│   │   ├── page.tsx       # Landing and dashboard root view
│   │   └── globals.css    # Global stylesheet and Tailwind setup
│   ├── components/        # Reusable UI elements (cards, buttons, modals)
│   ├── lib/               # Shared utilities, server-side backend calls (lib/server)
│   └── types/             # Domain and API response type definitions
├── public/                # Static assets, logos, and vector illustrations
├── package.json           # Frontend dependency manifest
├── tsconfig.json          # TypeScript compilation configuration
└── next.config.ts         # Next.js environment & framework settings
