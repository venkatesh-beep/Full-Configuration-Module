# Admin Logs Dashboard (React + Express + Supabase)

## Setup

1. Copy env file:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run app:
   ```bash
   npm run dev
   ```

Client runs at `http://localhost:5173` and backend at `http://localhost:4000`.

## Included features
- Admin-only login gate (backend validated).
- Logs table with latest-first ordering.
- Search + username/module/action/date filters.
- Pagination (10/20 per page).
- CSV export of current page and server-side full export.
- File download links.
- Loading + empty state + responsive table.
- Recent logs highlighting (24h) + total logs count.
