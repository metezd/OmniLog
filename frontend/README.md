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
│   ├── app/               # Next.js App Router (pages, layouts, routes)
│   │   ├── layout.tsx     # Global layout and shell structure
│   │   ├── page.tsx       # Landing and dashboard root view
│   │   └── globals.css    # Global stylesheet and Tailwind setup
│   ├── components/        # Reusable UI elements (cards, buttons, modals)
│   ├── lib/               # Shared utilities, Axios API client instances
│   └── types/             # Domain and API response type definitions
├── public/                # Static assets, logos, and vector illustrations
├── package.json           # Frontend dependency manifest
├── tsconfig.json          # TypeScript compilation configuration
└── next.config.ts         # Next.js environment & framework settings
