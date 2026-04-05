# Next.js Sustainability Dashboard

Modern React/Next.js dashboard for the sports scheduling optimizer.

## Stack

- Next.js + TypeScript
- shadcn-style UI primitives
- React Aria (`react-aria-components`) for accessible tabs
- Motion for React animations
- Recharts for analytics charts
- MapLibre GL JS (token-free) for travel map + emissions heat layer
- TanStack Query for server-state fetching
- Zustand for client-side filter state
- react-hot-toast notifications

## Run

```bash
cd dashboard-next
cp .env.example .env.local
npm install
npm run dev
```

Ensure backend API is running at `http://127.0.0.1:8000` (or update `NEXT_PUBLIC_SCHEDULER_API_BASE`).
