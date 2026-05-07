# 🔄 DB2 Flow Examples

## Quick Reference

Both DB2 components now support **HandleInput** for queries, meaning you can:
- ✅ Type queries directly in the component
- ✅ Connect queries from other nodes (Chat Input, Text Input, etc.)
- ✅ Chain SQL → Vector Search → LLM flows

---

## Example 1: Simple SQL Query

```
Chat Input → DB2 SQL → Chat Output
```

**Setup:**
1. Add **Chat Input** component
2. Add **DB2 SQL** component
3. Connect Chat Input's output to DB2 SQL's "SQL Query" input
4. Fill DB2 connection details (database, hostname, port, username, password)
5. Add **Chat Output** and connect DB2 SQL's output

**User can type:**
```sql
SELECT * FROM EMPLOYEES LIMIT 10
```

---

## Example 2: Vector Search Only

```
Chat Input → DB2 Vector Store → Chat Output
```

**Setup:**
1. Add **Chat Input** component
2. Add **Embedding Model** (e.g., OpenAI Embeddings)
3. Add **DB2 Vector Store** component
4. Connect:
   - Embedding Model → DB2 Vector's "Embedding Model"
   - Chat Input → DB2 Vector's "Search Query"
5. Fill DB2 connection details
6. Add **Chat Output** and connect DB2 Vector's output

**User can type:**
```
Find documents about machine learning
```

---

## Example 3: SQL + Vector Search (Hybrid)

```
Chat Input → DB2 SQL → DB2 Vector Store → LLM → Chat Output
```

**Use Case:** Query database, then search similar documents

**Setup:**
1. **Chat Input** - User enters SQL query
2. **DB2 SQL** - Executes query, returns results
3. **DB2 Vector Store** - Searches for similar documents based on SQL results
4. **LLM** (e.g., OpenAI) - Generates answer combining both
5. **Chat Output** - Shows final result

**Flow:**
```
User: "SELECT product_name FROM products WHERE category='electronics'"
  ↓
DB2 SQL: Returns ["iPhone", "MacBook", "iPad"]
  ↓
DB2 Vector: Searches for documents about these products
  ↓
LLM: "Based on the electronics products and related documents..."
  ↓
Output: Comprehensive answer
```

---

## Example 4: RAG with DB2

```
File Upload → Text Splitter → DB2 Vector (Ingest)
                                    ↓
Chat Input → DB2 Vector (Search) → LLM → Chat Output
```

**Phase 1: Ingest Documents**
1. **File Upload** - Upload PDF/TXT files
2. **Text Splitter** - Split into chunks
3. **Embedding Model** - Create embeddings
4. **DB2 Vector Store** - Store in DB2
   - Connect File Upload → "Ingest Data"
   - Leave "Search Query" empty

**Phase 2: Query**
1. **Chat Input** - User question
2. **DB2 Vector Store** - Search similar chunks
   - Connect Chat Input → "Search Query"
3. **LLM** - Generate answer
4. **Chat Output** - Show result

---

## Example 5: Multi-Step Analysis

```
Chat Input → DB2 SQL (Get Data) → Python Code (Process) → DB2 Vector (Search) → LLM → Chat Output
```

**Use Case:** Complex analysis combining SQL, processing, and vector search

**Flow:**
1. User asks: "Analyze sales trends and find related market research"
2. DB2 SQL: Fetches sales data
3. Python Code: Calculates trends, creates summary
4. DB2 Vector: Searches for related market research documents
5. LLM: Combines everything into comprehensive analysis
6. Output: Final report

---

## Connection Parameters

Both components need these connection details:

| Parameter | Example | Notes |
|-----------|---------|-------|
| **Database** | `TESTDB` | Your DB2 database name |
| **Hostname** | `localhost` or `10.17.36.176` | Use IP if hostname fails |
| **Port** | `50000` | Default DB2 port |
| **Username** | `db2inst1` | Your DB2 username |
| **Password** | `********` | Your DB2 password |

---

## Vector Store Additional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| **Table Name** | `LANGFLOW_VECTORS` | Where vectors are stored |
| **Number of Results** | `4` | How many results to return |
| **Search Type** | `Similarity` | Or `MMR` for diversity |
| **Distance Strategy** | `COSINE` | Or `EUCLIDEAN_DISTANCE`, `DOT_PRODUCT` |

---

## Tips for Success

### ✅ DO:
- Use `localhost` or `127.0.0.1` if DB2 is on same machine
- Test connection with simple query first
- Use HandleInput to chain components
- Start with small datasets for testing

### ❌ DON'T:
- Don't use hostname if DNS fails (use IP instead)
- Don't forget to connect Embedding Model to Vector Store
- Don't mix different embedding dimensions in same table
- Don't use production credentials in testing

---

## Troubleshooting

### Error: "Cannot connect to DB2"
**Fix:** Check hostname, port, and firewall settings

### Error: "Hostname not found"
**Fix:** Use IP address instead of hostname

### Error: "Dimension mismatch"
**Fix:** Drop table or use different table name:
```sql
DROP TABLE LANGFLOW_VECTORS;
```

### Error: "SQL Query is required"
**Fix:** Either type query directly OR connect from another node

---

## Real-World Example: Customer Support Bot

```
┌─────────────┐
│ Chat Input  │ "Find customers who bought iPhone"
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  DB2 SQL    │ SELECT * FROM customers WHERE product='iPhone'
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ DB2 Vector  │ Search support tickets for these customers
└──────┬──────┘
       │
       ↓
┌─────────────┐
│     LLM     │ Analyze patterns and generate insights
└──────┬──────┘
       │
       ↓
┌─────────────┐
│Chat Output  │ "iPhone customers commonly report..."
└─────────────┘
```

---

## Next Steps

1. **Test Connection:** Use simple SQL query first
2. **Ingest Data:** Upload documents to vector store
3. **Build Flow:** Connect components as shown above
4. **Iterate:** Refine based on results

---

**Made with ❤️ for Langflow + DB2 Integration**