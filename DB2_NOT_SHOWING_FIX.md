# 🔍 ROOT CAUSE: DB2 Components Not Showing in UI

## The Problem

**API returns only 1 component instead of hundreds!**

```bash
curl http://localhost:7863/api/v1/components | python3 -c "import sys, json; print(len(json.load(sys.stdin)))"
# Output: 1  ← WRONG! Should be 200+
```

This means the backend is NOT loading components dynamically.

---

## Root Cause

**Missing `LFX_DEV=1` environment variable!**

Langflow has two modes:

### Production Mode (Default)
- Uses pre-built component index
- Fast startup
- Components must be in the index file
- **DB2 components are NOT in the index** (we just added them)

### Development Mode (`LFX_DEV=1`)
- Discovers components dynamically at runtime
- Slower startup
- Finds ALL components including new ones
- **This is what we need!**

---

## The Solution

### Option 1: Use the Startup Script (Easiest)

```bash
# Terminal 1: Start backend with LFX_DEV=1
./start_with_db2.sh

# Terminal 2: Start frontend
cd src/frontend
npm run dev

# Open: http://localhost:3000
```

The script automatically:
- Sets `LFX_DEV=1` for dynamic discovery
- Starts backend on port 7863
- Tests if DB2 components are loaded
- Shows clear status messages

### Option 2: Manual Start

```bash
# Terminal 1: Backend
cd langflow
source .venv/bin/activate
export LFX_DEV=1
export LANGFLOW_AUTO_LOGIN=true
langflow run --backend-only --port 7863

# Terminal 2: Frontend
cd langflow/src/frontend
npm run dev

# Open: http://localhost:3000
```

### Option 3: Build Component Index (Production)

If you want production mode, rebuild the component index:

```bash
cd langflow
source .venv/bin/activate
make build_component_index

# Then start normally
langflow run --port 7863
```

This creates a pre-built index including DB2 components.

---

## Verification

### Test 1: Check API Returns Many Components

```bash
curl -s http://localhost:7863/api/v1/components | python3 -c "import sys, json; print('Total:', len(json.load(sys.stdin)))"
```

**Expected:** `Total: 200+` (not 1!)

### Test 2: Check DB2 Components Exist

```bash
curl -s http://localhost:7863/api/v1/components | python3 -c "
import sys, json
data = json.load(sys.stdin)
db2 = [k for k in data.keys() if 'db2' in k.lower() or 'DB2' in k]
print('DB2 components:', db2 if db2 else 'NONE')
"
```

**Expected:** `DB2 components: ['DB2SQLComponent', 'DB2VectorStoreComponent']`

### Test 3: Check in UI

1. Open http://localhost:3000
2. Click "New Flow"
3. Search for "DB2" in left sidebar
4. Should see:
   - **IBM Db2 SQL** (with DB2 icon)
   - **IBM Db2 Vector Store** (with DB2 icon)

---

## Why This Happened

1. ✅ We created DB2 components correctly
2. ✅ We registered them in `__init__.py`
3. ✅ We added DB2 icon to frontend
4. ❌ **We started Langflow without `LFX_DEV=1`**
5. ❌ Langflow used old component index (no DB2)
6. ❌ API returned only 1 component
7. ❌ UI showed no DB2 components

---

## Technical Details

### Component Discovery Flow

```
LFX_DEV=1 set?
    ↓ YES
Dynamic Discovery
    ↓
Scan lfx/components/
    ↓
Find db2/__init__.py
    ↓
Load DB2SQLComponent
Load DB2VectorStoreComponent
    ↓
Add to API response
    ↓
Frontend shows components

    ↓ NO (Production)
Load pre-built index
    ↓
DB2 not in index
    ↓
Only 1 component loaded
    ↓
DB2 not in API
    ↓
UI doesn't show DB2
```

### Files Involved

**Backend:**
- `src/lfx/src/lfx/components/__init__.py` - Main registry (✓ has db2)
- `src/lfx/src/lfx/components/db2/__init__.py` - DB2 module (✓ exists)
- `src/lfx/src/lfx/components/db2/db2_sql.py` - SQL component (✓ exists)
- `src/lfx/src/lfx/components/db2/db2_vector.py` - Vector component (✓ exists)

**Frontend:**
- `src/frontend/src/icons/IBM/db2/DB2.tsx` - Icon component (✓ exists)
- `src/frontend/src/icons/IBM/index.tsx` - Icon export (✓ updated)
- `src/frontend/src/icons/lazyIconImports.ts` - Lazy loading (✓ updated)
- `src/frontend/src/icons/eagerIconImports.ts` - Eager loading (✓ updated)

**Everything is correct!** Just need `LFX_DEV=1` to enable discovery.

---

## Summary

**Problem:** Backend not loading components (API returns 1 instead of 200+)

**Cause:** Missing `LFX_DEV=1` environment variable

**Solution:** Start with `LFX_DEV=1` or rebuild component index

**Quick Fix:**
```bash
./start_with_db2.sh  # Terminal 1
cd src/frontend && npm run dev  # Terminal 2
# Open http://localhost:3000
```

DB2 components will appear immediately!