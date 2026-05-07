# Run Langflow Frontend & Backend Separately (Development Mode)

## Why This Works Better

In development mode:
- ✅ Frontend hot-reloads with all new files (including DB2 icon)
- ✅ No need to rebuild frontend
- ✅ DB2 components will appear immediately
- ✅ Changes reflect instantly

---

## Terminal 1: Backend

```bash
cd langflow
source .venv/bin/activate
export LANGFLOW_AUTO_LOGIN=true
langflow run --backend-only --port 7863
```

**Expected output:**
```
╭───────────────────────────────────────────────────╮
│ Welcome to ⛓ Langflow                           │
│                                                   │
│ Access http://127.0.0.1:7863                     │
│ Collaborate, and contribute at our GitHub Repo 🌟│
╰───────────────────────────────────────────────────╯
```

Keep this terminal running!

---

## Terminal 2: Frontend

```bash
cd langflow/src/frontend
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

Keep this terminal running!

---

## Access Langflow

Open your browser to:
```
http://localhost:3000
```

**NOT** http://localhost:7863 (that's backend only)

---

## Verify DB2 Components

1. Open http://localhost:3000
2. Click "New Flow" or open existing flow
3. In the left sidebar, search for "DB2"
4. You should see:
   - **IBM Db2 SQL** (with DB2 icon)
   - **IBM Db2 Vector Store** (with DB2 icon)

---

## How It Works

```
Frontend (Port 3000)
    ↓
  Proxy
    ↓
Backend (Port 7863)
```

The frontend dev server proxies API requests to backend on port 7863.

Proxy is configured in:
`src/frontend/src/customization/config-constants.ts`

```typescript
export const PROXY_TARGET = "http://127.0.0.1:7863";
```

---

## Troubleshooting

### Backend won't start
```bash
# Kill any existing Langflow processes
lsof -ti:7863 | xargs kill -9 2>/dev/null

# Try again
cd langflow
source .venv/bin/activate
export LANGFLOW_AUTO_LOGIN=true
langflow run --backend-only --port 7863
```

### Frontend won't start
```bash
# Kill any existing frontend processes
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Clean and reinstall
cd langflow/src/frontend
rm -rf node_modules/.cache
npm install
npm run dev
```

### DB2 components still not showing

Check if icon files exist:
```bash
ls -la langflow/src/frontend/src/icons/IBM/db2/DB2.tsx
ls -la langflow/src/frontend/src/icons/IBM/index.tsx
```

Both should exist. If not, the files weren't created properly.

---

## Stop Everything

### Stop Backend (Terminal 1)
Press `Ctrl+C`

### Stop Frontend (Terminal 2)
Press `Ctrl+C`

Or kill all:
```bash
lsof -ti:3000,7863 | xargs kill -9 2>/dev/null
```

---

## Production Mode (After Development)

Once you're happy with the changes, build for production:

```bash
cd langflow/src/frontend
npm run build
cd ../..
rm -rf src/backend/base/langflow/frontend
cp -r src/frontend/build src/backend/base/langflow/frontend

# Run normally
source .venv/bin/activate
langflow run --port 7863
```

Then access: http://localhost:7863

---

## Summary

**Development Mode (Recommended Now):**
- Terminal 1: `langflow run --backend-only --port 7863`
- Terminal 2: `npm run dev` (in src/frontend)
- Access: http://localhost:3000
- DB2 components will appear immediately!

**Production Mode (Later):**
- Build frontend: `npm run build`
- Copy to backend
- Run: `langflow run --port 7863`
- Access: http://localhost:7863