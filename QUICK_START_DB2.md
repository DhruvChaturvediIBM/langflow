# Quick Start: IBM Db2 Integration

## File Structure

```
langflow/
├── src/
│   ├── backend/base/langflow/components/db2/     # Backend components
│   │   ├── __init__.py
│   │   ├── db2_sql.py                            # SQL executor
│   │   └── db2_vector.py                         # Vector store
│   └── frontend/src/icons/
│       ├── IBM/
│       │   ├── db2/DB2.tsx                       # DB2 icon
│       │   └── index.tsx                         # Icon exports
│       ├── lazyIconImports.ts                    # Lazy icon loading
│       └── eagerIconImports.ts                   # Eager icon loading
└── langchain-db2/                                # Your DB2 implementation
    └── langchain_db2/
        └── db2vs.py                              # Vector store logic
```

## Installation

### 1. Install Dependencies

```bash
# Install IBM Db2 drivers
pip install ibm_db ibm_db_dbi

# Install langchain-db2 (your implementation)
cd langchain-db2
pip install -e .
```

### 2. Start Langflow

```bash
cd langflow

# Start backend
make backend

# In another terminal, start frontend
make frontend
```

### 3. Access Langflow

Open browser: `http://localhost:3000`

## Using DB2 Components

### SQL Component

1. **Find Component:** Search "DB2 SQL" in sidebar
2. **Drag to Canvas**
3. **Configure:**
   - Database: `your_db`
   - Hostname: `localhost`
   - Port: `50000`
   - Username: `db2user`
   - Password: `********`
   - SQL Query: `SELECT * FROM table LIMIT 10`
4. **Run Flow**

### Vector Store Component

1. **Find Component:** Search "DB2 Vector" in sidebar
2. **Drag to Canvas**
3. **Configure Connection** (same as SQL)
4. **Add:**
   - Table Name: `langflow_vectors`
   - Distance Strategy: `COSINE`
   - Embedding Model: Connect an embeddings node
5. **Use it in two ways:**
   - Ingest: Connect File/Text/Data/Table → component using the ingest input
   - Search: Enter query in "Search Query" or connect another node to it
6. **Optional SQL alongside vector flow:**
   - Use [`DB2 SQL`](langflow/src/lfx/src/lfx/components/db2/db2_sql.py:11) as a separate node when you want exact SQL execution in the same flow
   - Keep [`DB2 Vector Store`](langflow/src/lfx/src/lfx/components/db2/db2_vector.py:13) for embedding-based ingestion and semantic retrieval

## Example Flow: RAG with DB2

```
┌──────────────┐
│ File Loader  │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Text Splitter│
└──────┬───────┘
       │
       ↓
┌──────────────────┐
│ OpenAI Embeddings│
└──────┬───────────┘
       │
       ↓
┌──────────────────┐
│ DB2 Vector Store │ ← Ingestion
└──────────────────┘

┌──────────────┐
│ Chat Input   │
└──────┬───────┘
       │
       ↓
┌──────────────────┐
│ DB2 Vector Store │ ← Search
└──────┬───────────┘
       │
       ↓
┌──────────────┐
│ Prompt       │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ OpenAI LLM   │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│ Chat Output  │
└──────────────┘
```

## Optional SQL + Vector Flow

```text
Chat Input ───────────────► DB2 Vector Store ───────► Chat Output
              query              semantic results

SQL Text/Input ───────────► DB2 SQL ────────────────► downstream node
                           exact SQL results
```

Use [`DB2 Vector Store`](langflow/src/lfx/src/lfx/components/db2/db2_vector.py:13) for semantic retrieval and [`DB2 SQL`](langflow/src/lfx/src/lfx/components/db2/db2_sql.py:11) when you want exact SQL queries in the same project.

## How It Works

### Backend

1. **Component Discovery:**
   - Langflow scans `lfx/components/db2/`
   - Finds `DB2SQLComponent` and `DB2VectorStoreComponent`
   - Registers them automatically

2. **Execution:**
   - User configures component in UI
   - Backend calls `execute_query()` or `build_vector_store()`
   - Uses your `langchain-db2` implementation
   - Returns results to flow

### Frontend

1. **Icon Loading:**
   - `DB2Icon` registered in `lazyIconImports.ts`
   - Loaded when component appears in sidebar
   - Shows IBM-styled DB2 icon

2. **UI Rendering:**
   - Backend sends component metadata (inputs/outputs)
   - Frontend renders configuration form
   - User fills connection details
   - Values sent to backend on execution

## Data Flow

```
User Input
    ↓
Frontend (React)
    ↓
Backend (Python Component)
    ↓
langchain-db2 (Your Implementation)
    ↓
IBM Db2 Database
    ↓
Results back through chain
    ↓
Display in UI
```

## Troubleshooting

### Components Not Showing

```bash
# Restart Langflow
pkill -f langflow
make backend
make frontend
```

### Import Errors

```bash
# Verify langchain-db2 installed
pip list | grep langchain-db2

# Reinstall if needed
cd langchain-db2
pip install -e .
```

### Connection Errors

```bash
# Test Db2 connection
db2 connect to your_db user db2user

# Check port is open
telnet localhost 50000
```

## Next Steps

- Read full documentation: `DB2_INTEGRATION.md`
- Explore example flows in Langflow UI
- Customize components in `lfx/components/db2/`
- Add tests in `tests/unit/components/db2/`

## Support

- Langflow Docs: https://docs.langflow.org
- IBM Db2 Docs: https://www.ibm.com/docs/en/db2/11.5