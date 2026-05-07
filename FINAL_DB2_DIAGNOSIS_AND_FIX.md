# DB2 Components Not Showing - Root Cause Analysis & Fix

## Current Situation

✅ **Backend**: DB2 components ARE installed and working
❌ **Frontend**: Components not appearing in UI
❌ **Workflows**: Lost due to database resets

---

## Root Cause

The issue is that **the frontend was built BEFORE we added the DB2 components**. The built frontend doesn't include the DB2 icon and component metadata.

### Evidence:
1. Components load perfectly in Python ✓
2. Components registered in backend ✓
3. Icon files exist ✓
4. **BUT** - Frontend was built before DB2 files were added

---

## The Fix

### Step 1: Rebuild Frontend with DB2 Components

```bash
cd langflow/src/frontend

# Clean old build
rm -rf build node_modules/.cache

# Rebuild
npm run build

# Copy to backend
cd ../..
rm -rf src/backend/base/langflow/frontend
cp -r src/frontend/build src/backend/base/langflow/frontend
```

### Step 2: Verify Icon is in Build

```bash
# Check if DB2 icon made it into the build
find src/backend/base/langflow/frontend -name "*DB2*" -o -name "*db2*"
```

If you see DB2-related files, the icon is included. If not, the frontend needs to be rebuilt.

---

## Why Your Workflows Are Gone

You deleted the database files:
- `rm -f langflow.db`
- `rm -rf .langflow`

This removed all your saved workflows. To prevent this in the future:

### Backup Database Before Changes
```bash
cp langflow.db langflow.db.backup
```

### Restore Workflows
If you have a backup:
```bash
cp langflow.db.backup langflow.db
```

---

## Complete Solution

### Option 1: Full Rebuild (Recommended)

```bash
cd langflow

# 1. Stop all Langflow instances
lsof -ti:7863,7865 | xargs kill -9 2>/dev/null

# 2. Backup database (if it exists)
[ -f langflow.db ] && cp langflow.db langflow.db.backup

# 3. Clean and rebuild frontend
cd src/frontend
rm -rf build node_modules/.cache
npm install
npm run build
cd ../..

# 4. Copy frontend to backend
rm -rf src/backend/base/langflow/frontend
cp -r src/frontend/build src/backend/base/langflow/frontend

# 5. Verify DB2 icon is in build
echo "Checking for DB2 in frontend build..."
find src/backend/base/langflow/frontend -name "*DB2*" -o -name "*db2*" | head -5

# 6. Start Langflow
source .venv/bin/activate
export LANGFLOW_AUTO_LOGIN=true
langflow run --port 7863
```

### Option 2: Quick Test (Development Mode)

```bash
cd langflow
source .venv/bin/activate

# Run frontend dev server (separate terminal)
cd src/frontend
npm run dev

# In another terminal, run backend
cd langflow
source .venv/bin/activate
export LANGFLOW_AUTO_LOGIN=true
langflow run --backend-only --port 7863

# Open http://localhost:3000 (frontend dev server)
```

In dev mode, the frontend will hot-reload and include all new files.

---

## Diagnostic Commands

### Check if Components Load in Backend
```bash
cd langflow
source .venv/bin/activate
python << 'EOF'
import sys
sys.path.insert(0, 'src/lfx/src')
from lfx.components.db2 import DB2SQLComponent, DB2VectorStoreComponent
print("✓ SQL:", DB2SQLComponent.display_name)
print("✓ Vector:", DB2VectorStoreComponent.display_name)
print("✓ SQL Icon:", DB2SQLComponent.icon)
print("✓ Vector Icon:", DB2VectorStoreComponent.icon)
EOF
```

Expected output:
```
✓ SQL: IBM Db2 SQL
✓ Vector: IBM Db2 Vector Store
✓ SQL Icon: DB2
✓ Vector Icon: DB2
```

### Check if Icon Files Exist
```bash
ls -la langflow/src/frontend/src/icons/IBM/db2/
ls -la langflow/src/frontend/src/icons/IBM/index.tsx
```

Should show:
- `DB2.tsx` (icon component)
- `index.tsx` exports DB2Icon

### Check if Icon is in Frontend Build
```bash
find langflow/src/backend/base/langflow/frontend -name "*DB2*" -o -name "*db2*"
```

If this returns nothing, the frontend wasn't rebuilt after adding DB2 files.

---

## The Real Problem

**Timeline of what happened:**

1. ✅ You added DB2 backend components
2. ✅ You added DB2 frontend icon files
3. ❌ Frontend was built BEFORE step 2
4. ❌ Old frontend (without DB2) was copied to backend
5. ❌ Langflow serves old frontend without DB2

**Solution:** Rebuild frontend AFTER adding all DB2 files.

---

## Prevention for Future

### Always rebuild frontend after adding components:
```bash
cd langflow/src/frontend
npm run build
cd ../..
cp -r src/frontend/build src/backend/base/langflow/frontend
```

### Or use development mode:
```bash
# Terminal 1: Frontend dev server
cd langflow/src/frontend
npm run dev

# Terminal 2: Backend
cd langflow
source .venv/bin/activate
langflow run --backend-only

# Open http://localhost:3000
```

---

## Summary

**Issue**: Frontend built before DB2 files were added
**Fix**: Rebuild frontend with DB2 files included
**Workflows**: Lost due to database deletion (restore from backup if available)

**Next Steps**:
1. Rebuild frontend (see Option 1 above)
2. Verify DB2 icon in build
3. Start Langflow
4. Components will appear in UI