# Admin Logs Dashboard (Integrated Login Fix)

## What this update does
- Adds a special admin login condition checked **before** normal login.
- If username=`Logs@BT` and password=`8684##` (trimmed, case-sensitive), login bypasses normal API and redirects to `/admin-logs`.
- Protects `/admin-logs` so only admin sees logs; others see **Access Denied**.
- Fetches logs directly from Supabase ordered by `created_at DESC`.

## Setup
```bash
npm install
npm run dev
```

## Required structure
- `src/services/supabaseClient.js`
- `src/services/logService.js`
- `src/pages/AdminLogs.js`
- `src/components/LogsTable.js`

## Features
- Search: username/module/action
- Filters: username/module/date range (+ action filter)
- Pagination: 10/20 rows
- CSV export for currently filtered table rows
- File download button per row
- Loading state + no-data state + responsive layout
- Debug console logs in login flow
