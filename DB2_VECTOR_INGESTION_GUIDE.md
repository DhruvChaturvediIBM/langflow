# IBM Db2 Vector Store Ingestion Guide

## Scope

This guide reflects the current DB2 component setup in this project:

- [`DB2VectorStoreComponent`](src/lfx/src/lfx/components/db2/db2_vector.py:13)
- [`DB2SQLComponent`](src/lfx/src/lfx/components/db2/db2_sql.py:11)

The old retrieval coordinator has been removed from component registration in [`src/lfx/src/lfx/components/db2/__init__.py`](src/lfx/src/lfx/components/db2/__init__.py).

---

## Components You Now Keep

You only need these two DB2 components:

- [`IBM Db2 Vector Store`](src/lfx/src/lfx/components/db2/db2_vector.py:13)
- [`IBM Db2 SQL`](src/lfx/src/lfx/components/db2/db2_sql.py:11)

Their roles are different:

- Use [`IBM Db2 Vector Store`](src/lfx/src/lfx/components/db2/db2_vector.py:13) for:
  - ingestion of text into vector storage
  - embedding-based semantic retrieval
  - similarity search and MMR search

- Use [`IBM Db2 SQL`](src/lfx/src/lfx/components/db2/db2_sql.py:11) for:
  - exact SQL execution
  - inspection of tables
  - debugging stored vector rows
  - custom validation queries

---

## Important Validation: Is Vector Retrieval Still SQL?

Yes. In this implementation, DB2 vector retrieval is still executed through SQL inside Db2.

### What happens during vector search

At a high level:

1. Your query text is embedded in Python.
2. The embedding is sent to Db2.
3. Db2 executes SQL using native vector functions.
4. Db2 returns the ranked rows.

### Exact proof from code

The Langflow vector node calls vector store search from [`search_documents()`](src/lfx/src/lfx/components/db2/db2_vector.py:295):

- Similarity search call: [`vector_store.similarity_search(...)`](src/lfx/src/lfx/components/db2/db2_vector.py:315)
- MMR search call: [`vector_store.max_marginal_relevance_search(...)`](src/lfx/src/lfx/components/db2/db2_vector.py:320)

Those methods are implemented in [`langchain-db2/langchain_db2/db2vs.py`](../langchain-db2/langchain_db2/db2vs.py):

- Query embedding generation: [`embed_query(query)`](../langchain-db2/langchain_db2/db2vs.py:393)
- SQL search entry point: [`similarity_search_by_vector_with_relevance_scores()`](../langchain-db2/langchain_db2/db2vs.py:427)
- Native SQL distance expression: [`vector_distance(embedding, VECTOR(...)) as distance`](../langchain-db2/langchain_db2/db2vs.py:441)
- SQL ordering: [`ORDER BY distance`](../langchain-db2/langchain_db2/db2vs.py:444)
- Row limit: [`FETCH FIRST {k} ROWS ONLY`](../langchain-db2/langchain_db2/db2vs.py:445)
- SQL execution: [`cursor.execute(query)`](../langchain-db2/langchain_db2/db2vs.py:453)

### Exact retrieval SQL shape

The current retrieval path uses SQL shaped like this:

```sql
SELECT id,
  text,
  SYSTOOLS.BSON2JSON(metadata),
  vector_distance(embedding, VECTOR('<query_embedding>', <dim>, FLOAT32),
  <distance_function>) as distance
FROM <table_name>
ORDER BY distance
FETCH FIRST <k> ROWS ONLY
```

Source: [`langchain-db2/langchain_db2/db2vs.py:437`](../langchain-db2/langchain_db2/db2vs.py:437)

So the answer is:

- yes, vector retrieval in the vector node is still SQL-based in Db2
- it is not doing similarity ranking purely in Python
- Python generates embeddings, but Db2 performs the main vector comparison

---

## How Ingestion Works

The vector node accepts input documents through the [`ingest_data`](src/lfx/src/lfx/components/db2/db2_vector.py:68) input.

Supported input types are defined in [`DB2VectorStoreComponent.inputs`](src/lfx/src/lfx/components/db2/db2_vector.py:22):

- [`Data`](src/lfx/src/lfx/components/db2/db2_vector.py:71)
- [`Document`](src/lfx/src/lfx/components/db2/db2_vector.py:71)
- [`Message`](src/lfx/src/lfx/components/db2/db2_vector.py:71)
- [`Text`](src/lfx/src/lfx/components/db2/db2_vector.py:71)
- [`Table`](src/lfx/src/lfx/components/db2/db2_vector.py:71)

### Ingestion flow inside the node

When data is provided:

1. Langflow builds a Db2 connection in [`build_vector_store()`](src/lfx/src/lfx/components/db2/db2_vector.py:112)
2. It creates a [`DB2VS`](../langchain-db2/langchain_db2/db2vs.py:153) instance
3. It converts incoming inputs into LangChain documents
4. It calls [`vector_store.add_documents(documents)`](src/lfx/src/lfx/components/db2/db2_vector.py:261)

### Input conversion behavior

Inside [`build_vector_store()`](src/lfx/src/lfx/components/db2/db2_vector.py:112), the node converts different input types:

- [`Data.to_lc_document()`](src/lfx/src/lfx/components/db2/db2_vector.py:212)
- direct [`Document`](src/lfx/src/lfx/components/db2/db2_vector.py:216)
- pandas DataFrame rows become joined text rows at [`data.iterrows()`](src/lfx/src/lfx/components/db2/db2_vector.py:222)
- dict/JSON objects are converted with [`json.dumps(...)`](src/lfx/src/lfx/components/db2/db2_vector.py:247)
- objects with `.text` are converted from [`data.text`](src/lfx/src/lfx/components/db2/db2_vector.py:252)
- plain strings are wrapped directly at [`Document(page_content=data, metadata={})`](src/lfx/src/lfx/components/db2/db2_vector.py:256)

### Embeddings during ingestion

During ingestion, text embeddings are generated in the app layer:

- document embeddings: [`self._embed_documents(texts)`](../langchain-db2/langchain_db2/db2vs.py:347)

The embedding model used is whatever you connect into:

- [`embedding`](src/lfx/src/lfx/components/db2/db2_vector.py:61)

That embedding handle is passed into DB2VS here:

- [`embedding_function=self.embedding`](src/lfx/src/lfx/components/db2/db2_vector.py:198)

---

## How Data Is Stored in Db2

The vector table is created in [`_create_table()`](../langchain-db2/langchain_db2/db2vs.py:103).

### Storage schema

Important columns:

- text column: [`"text": "CLOB"`](../langchain-db2/langchain_db2/db2vs.py:107)
- metadata column: [`"metadata": "BLOB"`](../langchain-db2/langchain_db2/db2vs.py:108)
- embedding column: [`"embedding": f"vector({embedding_dim}, FLOAT32)"`](../langchain-db2/langchain_db2/db2vs.py:109)

### Insert SQL used for ingestion

The current insert SQL is:

```sql
INSERT INTO <table_name> (id, embedding, metadata, text)
VALUES (?, VECTOR(?, <embeddingLen>, FLOAT32), SYSTOOLS.JSON2BSON(?), ?)
```

Source: [`SQL_INSERT`](../langchain-db2/langchain_db2/db2vs.py:364)

Execution happens at:

- [`cursor.executemany(SQL_INSERT, docs)`](../langchain-db2/langchain_db2/db2vs.py:371)

So ingestion is also SQL-driven when writing vectors into Db2.

---

## Recommended First Ingestion Test

If your goal is to validate vector capability first, use a very small and very controlled dataset.

### Suggested sample dataset

Use 5 to 10 short rows like:

- `blue t shirt cotton casual wear`
- `red t shirt sports fabric`
- `formal black leather shoes`
- `wireless bluetooth headphones`
- `gaming mechanical keyboard`

Do not start with large mixed paragraphs. Short, focused product-like text makes validation easier.

### Why this helps

Because current retrieval returns the nearest `k` rows even without a relevance threshold:

- [`ORDER BY distance`](../langchain-db2/langchain_db2/db2vs.py:444)
- [`FETCH FIRST {k} ROWS ONLY`](../langchain-db2/langchain_db2/db2vs.py:445)

That means if your dataset is noisy, you may still get irrelevant nearest neighbors.

---

## Step-by-Step: First Vector Ingestion in Langflow

### 1. Start Langflow

Use the working commands you already confirmed:

Backend:
```bash
cd /Users/dhruv_insights/Documents/Langflow_POC_with_Db2_Support/langflow
source .venv/bin/activate
uv pip install -e ../langchain-db2
export LANGFLOW_AUTO_LOGIN=true
export LFX_DEV=1
export PYTHONPATH="$(pwd)/src/lfx/src:$PYTHONPATH"
langflow run --host 127.0.0.1 --port 7863 --backend-only
```

Frontend:
```bash
cd /Users/dhruv_insights/Documents/Langflow_POC_with_Db2_Support/langflow/src/frontend
npm run start
```

### 2. Add these nodes

For a basic ingestion + search validation flow, use:

- a text source node or chat/text input node
- an embeddings node
- [`IBM Db2 Vector Store`](src/lfx/src/lfx/components/db2/db2_vector.py:13)
- optionally a chat/text output node

### 3. Configure the vector node

Set these fields in [`DB2VectorStoreComponent.inputs`](src/lfx/src/lfx/components/db2/db2_vector.py:22):

- [`database`](src/lfx/src/lfx/components/db2/db2_vector.py:24)
- [`hostname`](src/lfx/src/lfx/components/db2/db2_vector.py:30)
- [`port`](src/lfx/src/lfx/components/db2/db2_vector.py:36)
- [`username`](src/lfx/src/lfx/components/db2/db2_vector.py:42)
- [`password`](src/lfx/src/lfx/components/db2/db2_vector.py:48)
- [`collection_name`](src/lfx/src/lfx/components/db2/db2_vector.py:55)
- [`embedding`](src/lfx/src/lfx/components/db2/db2_vector.py:62)

Recommended first values:

- table name: `LANGFLOW_VECTORS_TEST`
- distance strategy: `COSINE`
- number of results: `3`

### 4. Ingest data

Connect your test text/documents into:

- [`ingest_data`](src/lfx/src/lfx/components/db2/db2_vector.py:69)

Then run the flow.

If the table does not exist, Db2VS will create it based on the embedding dimension.

### 5. Query the vector store

Provide a search string through:

- [`search_query`](src/lfx/src/lfx/components/db2/db2_vector.py:76)

Example:
- `blue tshirts`
- `wireless audio`
- `formal shoes`

The node will return data through:

- [`docs_to_data(docs)`](src/lfx/src/lfx/components/db2/db2_vector.py:325)

### 6. Switch search mode if needed

The vector node supports:

- [`Similarity`](src/lfx/src/lfx/components/db2/db2_vector.py:91)
- [`MMR`](src/lfx/src/lfx/components/db2/db2_vector.py:91)

Execution branch:
- similarity path: [`vector_store.similarity_search(...)`](src/lfx/src/lfx/components/db2/db2_vector.py:315)
- MMR path: [`vector_store.max_marginal_relevance_search(...)`](src/lfx/src/lfx/components/db2/db2_vector.py:320)

---

## How To Validate What Was Actually Inserted

Use the separate [`IBM Db2 SQL`](src/lfx/src/lfx/components/db2/db2_sql.py:11) node to inspect your vector table.

Example validation SQL:

```sql
SELECT id, text
FROM LANGFLOW_VECTORS_TEST
FETCH FIRST 10 ROWS ONLY
```

Run that in [`DB2SQLComponent.execute_query()`](src/lfx/src/lfx/components/db2/db2_sql.py:72).

This helps you verify:

- rows were inserted
- the text content is what you expected
- your ingestion input produced the correct chunks/rows

---

## Recommended Validation Workflow

### Phase 1: Prove ingestion works

1. insert 5 to 10 known rows
2. inspect them with [`IBM Db2 SQL`](src/lfx/src/lfx/components/db2/db2_sql.py:11)
3. confirm row count and stored text

Example:
```sql
SELECT COUNT(*) AS TOTAL_ROWS
FROM LANGFLOW_VECTORS_TEST
```

### Phase 2: Prove semantic retrieval works

Run searches like:

- `blue tshirt`
- `bluetooth headphones`
- `leather shoes`

Check whether the top rows are semantically close.

### Phase 3: Compare vector vs exact SQL

Use [`IBM Db2 SQL`](src/lfx/src/lfx/components/db2/db2_sql.py:11) for exact matching and [`IBM Db2 Vector Store`](src/lfx/src/lfx/components/db2/db2_vector.py:13) for semantic matching.

Example exact SQL:
```sql
SELECT id, text
FROM LANGFLOW_VECTORS_TEST
WHERE LOWER(text) LIKE '%blue%'
```

This comparison is useful because:

- SQL answers exact lexical conditions
- vector search answers semantic similarity conditions

---

## Important Limitation To Remember

Right now, retrieval does not apply a minimum relevance threshold.

Proof from current search SQL:

- [`ORDER BY distance`](../langchain-db2/langchain_db2/db2vs.py:444)
- [`FETCH FIRST {k} ROWS ONLY`](../langchain-db2/langchain_db2/db2vs.py:445)

So if you search for something like `blue tshirts`, Db2 will still return the top `k` nearest rows, even if some are weak matches.

This is why first validation should use:

- small dataset
- clean data
- clearly separated categories
- small `k` such as 2 or 3

---

## Dimension Mismatch Warning

If you ingest with one embedding model and later switch to another embedding model with a different dimension, you can hit dimension mismatch problems.

Relevant handling is in [`build_vector_store()`](src/lfx/src/lfx/components/db2/db2_vector.py:260).

The code explicitly warns that you may need to:

- drop the existing table
- use a new table name
- keep the same embedding model dimension

Reference:
- [`dimension mismatch detected`](src/lfx/src/lfx/components/db2/db2_vector.py:267)
- suggested fix: [`DROP TABLE {self.collection_name};`](src/lfx/src/lfx/components/db2/db2_vector.py:269)

---

## Best Practice For Your First Demo

For your first DB2 vector capability demo:

1. create a fresh table name, for example `LANGFLOW_VECTORS_DEMO_1`
2. use one embedding model only
3. ingest a tiny curated dataset
4. validate inserted rows with [`IBM Db2 SQL`](src/lfx/src/lfx/components/db2/db2_sql.py:11)
5. run 3 to 5 semantic queries
6. compare results against exact SQL queries
7. only then move to larger ingestion

---

## Final Confirmation

You asked whether, in the vector node also, Db2 retrieves the data as SQL.

Confirmed answer:

- yes, the vector node ultimately retrieves from Db2 through SQL
- the semantic ranking is executed with Db2 native [`vector_distance(...)`](../langchain-db2/langchain_db2/db2vs.py:441)
- ingestion is also persisted through SQL INSERT statements
- the vector node is not a separate non-SQL engine; it is a vector-enabled SQL retrieval path on Db2

That is the correct mental model for this implementation.