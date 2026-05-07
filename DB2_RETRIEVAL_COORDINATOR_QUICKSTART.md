# DB2 Retrieval Coordinator - Quick Start Guide

## What You've Built

You now have a powerful **DB2 Retrieval Coordinator** component that:

✅ **Orchestrates hybrid retrieval** - Combines SQL filtering with vector semantic search
✅ **Uses LLM intelligence** - Automatically analyzes queries and chooses optimal strategies
✅ **Supports multiple ranking methods** - RRF, Weighted Score, SQL/Vector Priority
✅ **Modular and extensible** - Coordinates existing DB2 SQL and Vector nodes
✅ **Production-ready** - Comprehensive error handling and logging

## Quick Start in 5 Minutes

### Step 1: Verify Installation

The component is already installed and registered. Verify it:

```bash
cd langflow
source .venv/bin/activate
python -c "from src.lfx.src.lfx.components.db2 import DB2RetrievalCoordinatorComponent; print('✅ Ready to use!')"
```

### Step 2: Start Langflow

```bash
cd langflow
source .venv/bin/activate
langflow run
```

### Step 3: Create Your First Hybrid Retrieval Flow

1. **Open Langflow UI** at `http://localhost:7860`

2. **Add Components** (drag from sidebar):
   - Chat Input
   - Ollama Model (or OpenAI)
   - DB2 SQL
   - Ollama Embeddings
   - DB2 Vector Store
   - **DB2 Retrieval Coordinator** ⭐
   - Chat Output

3. **Connect the Flow**:
   ```
   Chat Input ──┬──> DB2 Retrieval Coordinator ──> Chat Output
                │         ▲  ▲  ▲
                │         │  │  │
                ├─────────┘  │  │
                │            │  │
   Ollama Model ────────────┘  │
                │               │
   DB2 SQL ────────────────────┤
                │               │
   DB2 Vector ─────────────────┘
   (with Ollama Embeddings)
   ```

4. **Configure Connections**:
   - **Query**: Chat Input → Coordinator
   - **LLM**: Ollama Model → Coordinator
   - **SQL Results**: DB2 SQL → Coordinator
   - **Vector Results**: DB2 Vector → Coordinator

### Step 4: Configure the Coordinator

**Basic Settings**:
- **Execution Strategy**: `Auto (LLM Decides)` (recommended for first use)
- **Ranking Method**: `Reciprocal Rank Fusion`
- **Max Results**: `10`

**Advanced Settings** (optional):
- **SQL Weight**: `50` (for Weighted Score method)
- **Vector Weight**: `50` (for Weighted Score method)
- **Database Schema Context**: Provide your schema for better SQL generation
- **Enable Detailed Logging**: `true` (helpful for debugging)

### Step 5: Test with Example Queries

Try these queries to see different strategies in action:

#### Query 1: Hybrid (SQL + Vector)
```
"Find wireless headphones under $100 with good battery life"
```
**Expected**: Parallel execution, combines price filtering with semantic search

#### Query 2: SQL-Heavy
```
"Show all orders from last month where total > $500"
```
**Expected**: SQL First strategy, structured filtering dominates

#### Query 3: Vector-Heavy
```
"Find products similar to noise-cancelling headphones"
```
**Expected**: Vector First strategy, semantic similarity dominates

## Understanding the Output

The coordinator provides **3 outputs**:

### 1. Combined Results (Main Output)
Ranked list of results combining SQL and Vector searches:
```json
[
  {
    "id": 123,
    "name": "Wireless Headphones Pro",
    "price": 89.99,
    "_rrf_score": 0.0325
  },
  ...
]
```

### 2. Query Analysis
LLM's understanding of your query:
```json
{
  "has_structured_filters": true,
  "has_semantic_intent": true,
  "sql_filters": "price < 100",
  "semantic_query": "wireless headphones good battery",
  "recommended_strategy": "parallel",
  "confidence": 0.95,
  "reasoning": "Query contains both price constraint and semantic intent"
}
```

### 3. Execution Plan
Details about how the query was executed:
```json
{
  "strategy": "parallel",
  "has_sql_results": true,
  "has_vector_results": true,
  "query_analysis": {...}
}
```

## Common Use Cases

### Use Case 1: E-commerce Product Search
**Scenario**: Customer searches for products with specific attributes and semantic similarity

**Flow**:
```
User Query: "gaming laptops under $1500 with good graphics"
├─> SQL: price < 1500 AND category = 'laptops'
├─> Vector: "gaming good graphics performance"
└─> Coordinator: Combines and ranks by relevance
```

### Use Case 2: Document Retrieval
**Scenario**: Find documents by metadata and content similarity

**Flow**:
```
User Query: "technical docs about authentication from last year"
├─> SQL: doc_type = 'technical' AND year = 2024
├─> Vector: "authentication security login"
└─> Coordinator: Merges results with RRF
```

### Use Case 3: Customer Support
**Scenario**: Find relevant tickets by status and semantic content

**Flow**:
```
User Query: "urgent tickets about login problems"
├─> SQL: priority = 'urgent' AND status = 'open'
├─> Vector: "login problems authentication issues"
└─> Coordinator: Prioritizes urgent tickets with semantic relevance
```

## Troubleshooting

### Issue: Component not showing in UI

**Solution**:
```bash
# Restart Langflow
cd langflow
source .venv/bin/activate
langflow run --reload
```

### Issue: LLM analysis fails

**Check**:
1. LLM node is properly configured
2. API keys are valid (for OpenAI)
3. Ollama is running (for local models)

**Test LLM separately**:
```bash
# For Ollama
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2",
  "prompt": "Hello"
}'
```

### Issue: No results returned

**Debug steps**:
1. Check "Execution Plan" output to see strategy used
2. Verify SQL and Vector nodes return results individually
3. Enable detailed logging in coordinator settings
4. Check Langflow logs for errors

### Issue: Results not ranked as expected

**Try**:
1. Switch ranking method (try RRF vs Weighted)
2. Adjust SQL/Vector weights
3. Review query analysis to understand LLM interpretation
4. Provide schema context for better SQL generation

## Performance Tips

### 1. Optimize SQL Queries
- Add indexes on frequently filtered columns
- Use SQL First strategy when filters are highly selective
- Limit max_rows in SQL node

### 2. Optimize Vector Search
- Use appropriate embedding model for your domain
- Adjust number_of_results in Vector node
- Consider using MMR for diversity

### 3. Choose Right Strategy
| Data Size | Filter Selectivity | Recommended Strategy |
|-----------|-------------------|---------------------|
| Large | High (>80% reduction) | SQL First |
| Large | Low (<20% reduction) | Vector First |
| Medium | Balanced | Parallel |
| Any | Unknown | Auto |

### 4. Tune Ranking
- **RRF**: Best for balanced results, no tuning needed
- **Weighted**: Tune weights based on importance (SQL vs Vector)
- **SQL Priority**: When exact matches matter most
- **Vector Priority**: When semantic similarity matters most

## Next Steps

### 1. Customize for Your Domain
- Add domain-specific schema context
- Tune weights based on your data
- Create custom ranking methods if needed

### 2. Monitor Performance
- Track query analysis accuracy
- Measure result relevance
- Monitor execution times

### 3. Extend Functionality
- Add query rewriting
- Implement result caching
- Add custom filters
- Create domain-specific strategies

### 4. Production Deployment
- Set up proper error handling
- Configure logging and monitoring
- Implement rate limiting
- Add authentication

## Example Flows

### Flow 1: Simple Hybrid Search
```
Chat Input → DB2 Retrieval Coordinator → Chat Output
              ↑         ↑         ↑
              |         |         |
         LLM  |    SQL  |   Vector|
```

### Flow 2: Advanced with Analysis
```
Chat Input → DB2 Retrieval Coordinator ─┬─> Chat Output (Results)
              ↑         ↑         ↑      ├─> Text Output (Analysis)
              |         |         |      └─> Text Output (Plan)
         LLM  |    SQL  |   Vector|
```

### Flow 3: Multi-Stage Pipeline
```
Chat Input → Query Rewriter → DB2 Retrieval Coordinator → Result Ranker → Chat Output
                                ↑         ↑         ↑
                                |         |         |
                           LLM  |    SQL  |   Vector|
```

## Resources

- **Full Documentation**: [DB2_RETRIEVAL_COORDINATOR.md](DB2_RETRIEVAL_COORDINATOR.md)
- **Example Flow**: [DB2_RETRIEVAL_COORDINATOR_EXAMPLE.json](DB2_RETRIEVAL_COORDINATOR_EXAMPLE.json)
- **DB2 Integration Guide**: [DB2_INTEGRATION.md](DB2_INTEGRATION.md)
- **Component Code**: `langflow/src/lfx/src/lfx/components/db2/db2_retrieval_coordinator.py`

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the full documentation
3. Check Langflow logs: `langflow/logs/`
4. Open an issue on GitHub

---

**Made with Bob** 🤖

Happy hybrid retrieval! 🚀