# IBM Db2 Integration for Langflow

This integration adds IBM Db2 support to Langflow with both SQL execution and vector search capabilities.

## Components

### 1. DB2 SQL Component
Execute SQL queries on IBM Db2 databases.

**Features:**
- Connect to Db2 databases
- Execute SELECT, INSERT, UPDATE, DELETE queries
- Return results as Data objects
- Configurable result limits

### 2. DB2 Vector Store Component
Store and search document embeddings using Db2's vector capabilities.

**Features:**
- Vector similarity search (Euclidean, Cosine, Dot Product)
- Document ingestion with embeddings
- MMR (Maximal Marginal Relevance) search
- Duplicate detection
- Integration with LangChain embeddings

## Installation

### Prerequisites

1. **IBM Db2 Database** (v11.5.2+ with vector support)
2. **Python packages:**
   ```bash
   pip install ibm_db ibm_db_dbi
   ```

3. **LangChain Db2 package:**
   Copy the `langchain-db2` directory to your Python path or install it:
   ```bash
   cd langchain-db2
   pip install -e .
   ```

### Setup Steps

1. **Copy DB2 components to Langflow:**
   The components are already in place at:
   ```
   langflow/src/lfx/src/lfx/components/db2/
   ├── __init__.py
   ├── db2_sql.py
   └── db2_vector.py
   ```

2. **Frontend icons are registered:**
   - Icon files: `langflow/src/frontend/src/icons/IBM/db2/DB2.tsx`
   - Registered in: `lazyIconImports.ts` and `eagerIconImports.ts`

3. **Restart Langflow:**
   ```bash
   cd langflow
   make backend
   # In another terminal
   make frontend
   ```

## Usage

### DB2 SQL Component

1. Add "IBM Db2 SQL" component to your flow
2. Configure connection:
   - Database Name
   - Hostname
   - Port (default: 50000)
   - Username
   - Password
3. Enter SQL query
4. Connect output to downstream components

**Example Flow:**
```
User Input → DB2 SQL → Text Output
```

### DB2 Vector Store Component

1. Add "IBM Db2 Vector Store" component to your flow
2. Configure connection (same as SQL component)
3. Set table name for vector storage
4. Choose distance strategy (EUCLIDEAN, COSINE, DOT_PRODUCT)
5. Connect embedding model
6. Add documents or search query

**Example Flow:**
```
File → Text Splitter → Embedding Model → DB2 Vector Store
                                              ↓
User Query → DB2 Vector Store (search) → LLM → Output
```

**RAG Flow Example:**
```
┌─────────────┐
│ User Input  │
└──────┬──────┘
       │
       ↓
┌─────────────────┐
│ DB2 Vector      │
│ (Search Mode)   │
└──────┬──────────┘
       │
       ↓
┌─────────────┐
│ LLM         │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ Output      │
└─────────────┘
```

## Configuration

### DB2 Connection Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| database | Database name | Required |
| hostname | Server hostname/IP | Required |
| port | Server port | 50000 |
| username | Database user | Required |
| password | Database password | Required |

### Vector Store Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| table_name | Vector table name | langflow_vectors |
| distance_strategy | Distance calculation | EUCLIDEAN |
| number_of_results | Search results count | 4 |
| search_type | Similarity or MMR | Similarity |
| allow_duplicates | Allow duplicate docs | True |

## Database Setup

### Create Vector-Enabled Table

The component automatically creates tables, but you can pre-create them:

```sql
CREATE TABLE langflow_vectors (
    id CHAR(16) PRIMARY KEY NOT NULL,
    text CLOB,
    metadata BLOB,
    embedding VECTOR(1536, FLOAT32)
);
```

**Note:** Adjust vector dimension (1536) based on your embedding model.

## Troubleshooting

### Connection Issues

1. **Verify Db2 is running:**
   ```bash
   db2 list active databases
   ```

2. **Check network connectivity:**
   ```bash
   telnet <hostname> <port>
   ```

3. **Verify credentials:**
   ```bash
   db2 connect to <database> user <username>
   ```

### Vector Search Issues

1. **Ensure Db2 version supports vectors** (11.5.2+)
2. **Check table exists:**
   ```sql
   SELECT * FROM SYSCAT.TABLES WHERE TABNAME = 'LANGFLOW_VECTORS';
   ```

3. **Verify vector dimension matches embedding model**

### Import Errors

If you see import errors for `langchain_db2`:

```bash
# Install from local directory
cd langchain-db2
pip install -e .

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/langchain-db2"
```

## Architecture

### Backend Flow

1. **Component Discovery:**
   - Langflow auto-discovers components in `lfx/components/db2/`
   - Components inherit from `Component` or `LCVectorStoreComponent`

2. **Execution:**
   - User configures component in UI
   - Component's `build_vector_store()` or `execute_query()` method runs
   - Results flow to connected components

### Frontend Flow

1. **Icon Loading:**
   - Icons registered in `lazyIconImports.ts`
   - Lazy-loaded when component appears in sidebar

2. **Component Rendering:**
   - Component metadata (inputs, outputs) sent from backend
   - UI dynamically renders configuration form
   - User fills in connection details and parameters

## Examples

### Example 1: Simple SQL Query

```python
# In Langflow UI:
# 1. Add DB2 SQL component
# 2. Configure connection
# 3. SQL Query: "SELECT * FROM employees LIMIT 10"
# 4. Connect to Table component to view results
```

### Example 2: Vector Search RAG

```python
# Ingestion Flow:
# File → Text Splitter → OpenAI Embeddings → DB2 Vector Store

# Query Flow:
# Chat Input → DB2 Vector Store (search) → Prompt → LLM → Chat Output
```

### Example 3: Hybrid Search

```python
# Combine SQL and Vector search:
# User Query → DB2 SQL (filter by metadata)
#           → DB2 Vector (semantic search)
#           → Merge Results → LLM → Output
```

## Performance Tips

1. **Use appropriate distance strategy:**
   - COSINE: Normalized vectors
   - EUCLIDEAN: Absolute distances
   - DOT_PRODUCT: Fast but sensitive to magnitude

2. **Optimize table:**
   ```sql
   RUNSTATS ON TABLE langflow_vectors;
   REORG TABLE langflow_vectors;
   ```

3. **Batch document ingestion:**
   - Process documents in batches of 100-1000
   - Use `allow_duplicates=False` to avoid redundant storage

4. **Index metadata fields:**
   ```sql
   -- If using JSON metadata queries
   CREATE INDEX idx_metadata ON langflow_vectors(metadata);
   ```

## API Reference

### DB2SQLComponent

**Methods:**
- `execute_query() -> list[Data]`: Execute SQL and return results

**Inputs:**
- database, hostname, port, username, password
- sql_query: SQL statement to execute
- max_rows: Maximum rows to return

**Outputs:**
- results: Query results as Data objects

### DB2VectorStoreComponent

**Methods:**
- `build_vector_store() -> DB2VS`: Create vector store instance
- `search_documents() -> list[Data]`: Search for similar documents

**Inputs:**
- database, hostname, port, username, password
- table_name: Vector table name
- distance_strategy: Distance calculation method
- embedding: Embedding model
- ingest_data: Documents to add
- search_query: Query for similarity search

**Outputs:**
- search_results: Similar documents
- dataframe: Results as table

## Contributing

To extend or modify the integration:

1. **Backend:** Edit files in `langflow/src/lfx/src/lfx/components/db2/`
2. **Frontend:** Modify icons in `langflow/src/frontend/src/icons/IBM/db2/`
3. **Test:** Add tests in `langflow/src/backend/tests/unit/components/db2/`

## License

This integration follows Langflow's license (MIT).

## Support

- Langflow Documentation: https://docs.langflow.org
- IBM Db2 Documentation: https://www.ibm.com/docs/en/db2/11.5
- Issues: Report in Langflow GitHub repository