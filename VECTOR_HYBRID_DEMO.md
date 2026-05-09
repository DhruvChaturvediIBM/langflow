# Vector Ingestion & Hybrid Retrieval Demo

## Overview

This demo implements a complete **Vector Ingestion and Hybrid Retrieval Pipeline** using IBM DB2 with vector support. It demonstrates:

1. **Ingestion Pipeline**: JSON → Embeddings → DB2 Storage
2. **Pure Vector Search**: Query → Embedding → Similarity Search
3. **Hybrid Search**: Query → Embedding + SQL Filters → Filtered Results

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INGESTION PIPELINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  JSON Product Data                                              │
│         ↓                                                       │
│  Extract Description                                            │
│         ↓                                                       │
│  Embedding Model (SentenceTransformer)                          │
│         ↓                                                       │
│  Generate Embedding Vector                                      │
│         ↓                                                       │
│  Attach to Product ID                                           │
│         ↓                                                       │
│  Insert into DB2                                                │
│         ↓                                                       │
│  ┌──────────────────────────────────────────┐                  │
│  │ DB2 Table: PRODUCTS                      │                  │
│  ├──────────────────────────────────────────┤                  │
│  │ PRODUCT_ID    | INTEGER                  │                  │
│  │ PRICE         | DECIMAL(10,2)            │                  │
│  │ DESCRIPTION   | VARCHAR(5000)            │                  │
│  │ EMBEDDING_VECTOR | VECTOR(384)           │                  │
│  └──────────────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                  PURE VECTOR SEARCH                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Query: "audio equipment for music"                        │
│         ↓                                                       │
│  Embedding Model                                                │
│         ↓                                                       │
│  Query Embedding Vector                                         │
│         ↓                                                       │
│  DB2 Vector Similarity Search                                   │
│  (COSINE distance)                                              │
│         ↓                                                       │
│  Top-K Results (ranked by similarity)                           │
│         ↓                                                       │
│  Return Product Metadata                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              HYBRID SEARCH (Vector + SQL)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Query: "health and fitness device"                        │
│  SQL Filters: price >= 200 AND price < 500                      │
│         ↓                                                       │
│  Embedding Model                                                │
│         ↓                                                       │
│  Query Embedding Vector                                         │
│         ↓                                                       │
│  DB2 Hybrid Query:                                              │
│    ├── Vector Similarity Search (COSINE)                        │
│    └── SQL WHERE Clause (price filters)                         │
│         ↓                                                       │
│  Filtered Top-K Results                                         │
│  (matching both vector similarity AND SQL filters)              │
│         ↓                                                       │
│  Return Filtered Product Metadata                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

1. **Python 3.10+** installed
2. **DB2 database** with vector support enabled
3. **DB2 credentials** in `db2_config.json`

### Installation & Run

```bash
# First, set up Langflow (one-time setup)
./start.sh

# Then run the demo
./run_demo.sh
```

The `start.sh` script will:
- ✅ Check prerequisites
- ✅ Create virtual environment
- ✅ Install all dependencies (Langflow, langchain-db2, ibm-db, sentence-transformers)

The `run_demo.sh` script will:
- ✅ Run the vector hybrid search demonstration
- ✅ Show ingestion, vector search, and hybrid search in action

### Manual Run (if venv already exists)

```bash
source .venv/bin/activate
python vector_hybrid_search_demo.py
```

## Demo Flow

### Part 1: Ingestion Pipeline

The demo ingests 3 sample products:

```json
{
  "product_id": 1,
  "price": 100,
  "description": "High-quality wireless headphones with noise cancellation..."
}
```

**Process:**
1. Extract product description
2. Generate embedding using SentenceTransformer (all-MiniLM-L6-v2)
3. Store in DB2 with vector column

**DB2 Storage:**
```sql
INSERT INTO PRODUCTS (
    PRODUCT_ID,
    PRICE,
    DESCRIPTION,
    EMBEDDING_VECTOR
)
VALUES (
    1,
    100,
    'High-quality wireless headphones...',
    VECTOR('[1.00, 2.00, 3.00, ...]')
);
```

### Part 2: Pure Vector Search

**Query:** "audio equipment for music"

**Process:**
1. Generate query embedding
2. Search DB2 using COSINE distance
3. Return top-K most similar products

**SQL Query:**
```sql
SELECT 
    PRODUCT_ID,
    PRICE,
    DESCRIPTION,
    VECTOR_DISTANCE(EMBEDDING_VECTOR, VECTOR(?), COSINE) AS DISTANCE
FROM PRODUCTS
ORDER BY DISTANCE
FETCH FIRST 3 ROWS ONLY;
```

**Expected Result:**
- Product 1 (headphones) - highest similarity
- Other products ranked by semantic similarity

### Part 3: Hybrid Search

**Query:** "health and fitness device"  
**Filters:** `price >= 200 AND price < 500`

**Process:**
1. Generate query embedding
2. Search DB2 with BOTH vector similarity AND SQL filters
3. Return filtered top-K results

**SQL Query:**
```sql
SELECT 
    PRODUCT_ID,
    PRICE,
    DESCRIPTION,
    VECTOR_DISTANCE(EMBEDDING_VECTOR, VECTOR(?), COSINE) AS DISTANCE
FROM PRODUCTS
WHERE PRICE >= 200 AND PRICE < 500
ORDER BY DISTANCE
FETCH FIRST 3 ROWS ONLY;
```

**Expected Result:**
- Only products matching BOTH semantic similarity AND price range
- Product 3 (fitness tracker, $400) - matches both criteria
- Product 2 (laptop stand, $200) - matches price but lower similarity

## Key Features

### 1. Semantic Search
- Uses SentenceTransformer embeddings (384 dimensions)
- COSINE distance for similarity measurement
- Finds semantically similar products regardless of exact keyword matches

### 2. Hybrid Filtering
- Combines vector similarity with SQL predicates
- Supports complex WHERE clauses (price ranges, categories, etc.)
- Efficient filtering at database level

### 3. Production-Ready Code
- Proper error handling
- Connection management
- Configurable parameters
- Clean architecture with separation of concerns

## Code Structure

```
vector_hybrid_search_demo.py
├── DB2Config              # Configuration management
├── DB2Connection          # Database connection handling
├── EmbeddingModel         # Text embedding generation
├── SchemaManager          # Table creation and schema
├── IngestionPipeline      # Data ingestion logic
├── RetrievalPipeline      # Search logic (vector + hybrid)
└── VectorHybridDemo       # Main orchestrator
```

## Configuration

### db2_config.json

```json
{
  "database": "YOUR_DATABASE",
  "hostname": "your-db2-host.com",
  "port": 50000,
  "username": "your_username",
  "password": "your_password"
}
```

## Customization

### Change Embedding Model

```python
embedder = EmbeddingModel(model_name="all-mpnet-base-v2")  # Larger, more accurate
```

### Adjust Top-K Results

```python
results = retrieval.vector_search(query, top_k=5)  # Return top 5 instead of 3
```

### Add More Filters

```python
results = retrieval.hybrid_search(
    query_text="laptop",
    price_gte=500,
    price_lt=2000,
    top_k=10
)
```

## Troubleshooting

### Issue: "sentence-transformers not installed"

**Solution:**
```bash
pip install sentence-transformers
```

### Issue: "DB2 connection failed"

**Solutions:**
1. Verify `db2_config.json` exists and has correct credentials
2. Check DB2 server is accessible
3. Verify network connectivity and firewall rules

### Issue: "Table already exists"

**Solution:**
The demo automatically drops and recreates the table. If you see errors, manually drop:
```sql
DROP TABLE PRODUCTS;
```

### Issue: Vector dimension mismatch

**Solution:**
Ensure the table's vector dimension matches the embedding model:
- `all-MiniLM-L6-v2`: 384 dimensions
- `all-mpnet-base-v2`: 768 dimensions

## Performance Considerations

### Embedding Generation
- **Speed**: ~100-500 products/second (CPU)
- **GPU**: 10x faster with CUDA-enabled GPU
- **Batch Processing**: Use `encode_batch()` for multiple texts

### Vector Search
- **Index**: Create vector index for large datasets (>10K products)
- **Distance Metric**: COSINE is standard for normalized embeddings
- **Top-K**: Limit results to improve query speed

### Hybrid Search
- **Filter First**: SQL filters reduce vector search space
- **Indexing**: Create indexes on frequently filtered columns (price, category)
- **Query Optimization**: Use EXPLAIN to analyze query plans

## Next Steps

1. **Scale Up**: Test with larger datasets (10K+ products)
2. **Add Indexes**: Create vector and SQL indexes for performance
3. **Integrate with Langflow**: Use the DB2 Vector Store component
4. **Production Deployment**: Add monitoring, logging, and error recovery

## Resources

- [IBM DB2 Vector Documentation](https://www.ibm.com/docs/en/db2)
- [SentenceTransformers Documentation](https://www.sbert.net/)
- [Langflow Documentation](https://docs.langflow.org/)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the main README.md
3. Check DB2 connection logs
4. Verify embedding model is loaded correctly

---

**Made with ❤️ for IBM DB2 Vector Integration**