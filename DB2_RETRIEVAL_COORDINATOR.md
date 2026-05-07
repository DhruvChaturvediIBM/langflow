# DB2 Retrieval Coordinator

## Overview

The **DB2 Retrieval Coordinator** is an advanced Langflow component that orchestrates hybrid retrieval by intelligently combining SQL-based structured filtering with vector-based semantic search. This component acts as a coordinator between the DB2 SQL and DB2 Vector Store nodes, enabling sophisticated query strategies that leverage both capabilities.

## Key Features

### 🎯 Intelligent Query Analysis
- Uses LLM to analyze natural language queries
- Automatically extracts structured filters (dates, numbers, conditions)
- Identifies semantic intent for similarity search
- Recommends optimal execution strategy

### 🔄 Multiple Execution Strategies
1. **SQL First (Filter then Rank)** - Apply SQL filters first, then rank with vector similarity
2. **Parallel (Execute Both)** - Run SQL and vector searches simultaneously
3. **Vector First (Search then Filter)** - Find similar items first, then apply SQL filters
4. **Auto (LLM Decides)** - Let the LLM choose the best strategy based on query analysis

### 📊 Advanced Result Ranking
- **Reciprocal Rank Fusion (RRF)** - Combines rankings from multiple sources
- **Weighted Score** - Customizable weights for SQL vs Vector results
- **SQL Priority** - Prioritize structured query results
- **Vector Priority** - Prioritize semantic similarity results

### 🔌 Modular Design
- Does not replace SQL or Vector nodes
- Coordinates existing nodes through connections
- Clear separation of concerns
- Extensible architecture

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  DB2 Retrieval Coordinator                   │
│                                                              │
│  ┌──────────────┐      ┌─────────────┐      ┌────────────┐ │
│  │   Natural    │─────▶│     LLM     │─────▶│  Execution │ │
│  │   Language   │      │   Query     │      │  Strategy  │ │
│  │    Query     │      │  Analysis   │      │  Selection │ │
│  └──────────────┘      └─────────────┘      └────────────┘ │
│                                                              │
│         ┌────────────────────┬────────────────────┐         │
│         ▼                    ▼                    ▼         │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐ │
│  │  SQL First  │      │  Parallel   │      │Vector First │ │
│  │  Strategy   │      │  Strategy   │      │  Strategy   │ │
│  └─────────────┘      └─────────────┘      └─────────────┘ │
│         │                    │                    │         │
│         └────────────────────┼────────────────────┘         │
│                              ▼                               │
│                    ┌──────────────────┐                     │
│                    │  Result Ranking  │                     │
│                    │   & Combination  │                     │
│                    └──────────────────┘                     │
│                              │                               │
│                              ▼                               │
│                    ┌──────────────────┐                     │
│                    │ Unified Results  │                     │
│                    └──────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
         │                                          │
         ▼                                          ▼
┌─────────────────┐                        ┌─────────────────┐
│  DB2 SQL Node   │                        │ DB2 Vector Node │
│                 │                        │                 │
│ • Structured    │                        │ • Semantic      │
│   Filtering     │                        │   Search        │
│ • Exact Matches │                        │ • Similarity    │
│ • Aggregations  │                        │ • Embeddings    │
└─────────────────┘                        └─────────────────┘
```

## Usage Examples

### Example 1: Basic Hybrid Search

**Scenario**: Find products similar to "wireless headphones" with price under $100

```
Flow Configuration:
1. Chat Input → "Find wireless headphones under $100"
2. DB2 SQL Node → SELECT * FROM products WHERE price < 100
3. DB2 Vector Node → Similarity search for "wireless headphones"
4. LLM (OpenAI/Ollama) → Query analysis
5. DB2 Retrieval Coordinator → Combines results
6. Chat Output → Display results
```

**Query Analysis**:
```json
{
  "has_structured_filters": true,
  "has_semantic_intent": true,
  "sql_filters": "price < 100",
  "semantic_query": "wireless headphones",
  "recommended_strategy": "parallel",
  "confidence": 0.95
}
```

### Example 2: SQL-First Strategy

**Scenario**: Find recent customer reviews (last 30 days) about "battery life"

```
Natural Language Query: "Show me recent reviews mentioning battery life issues"

Strategy: SQL First
1. SQL filters: created_date > CURRENT_DATE - 30 DAYS
2. Vector search: "battery life issues" on filtered results
3. Rank by relevance
```

### Example 3: Vector-First Strategy

**Scenario**: Find similar documents, then filter by category

```
Natural Language Query: "Find technical documentation similar to this, but only for enterprise products"

Strategy: Vector First
1. Vector search: Find semantically similar documents
2. SQL filter: category = 'enterprise'
3. Combine and rank results
```

### Example 4: Parallel Execution

**Scenario**: Complex query with both structured and semantic components

```
Natural Language Query: "Find high-value orders from last quarter with customer complaints"

Strategy: Parallel
1. SQL: order_value > 1000 AND order_date >= '2024-01-01'
2. Vector: "customer complaints"
3. Merge using Reciprocal Rank Fusion
```

## Configuration Guide

### Input Parameters

#### Required Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| **Natural Language Query** | Message/Text/Data | The user's query in natural language |
| **Language Model** | LanguageModel | LLM for query analysis (OpenAI, Ollama, etc.) |

#### Optional Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| **SQL Results** | Data[] | Connect from DB2 SQL node output |
| **Vector Results** | Data[] | Connect from DB2 Vector node output |

#### Configuration Options

| Parameter | Options | Default | Description |
|-----------|---------|---------|-------------|
| **Execution Strategy** | SQL First / Parallel / Vector First / Auto | Auto | How to coordinate execution |
| **Ranking Method** | RRF / Weighted / SQL Priority / Vector Priority | RRF | Result combination method |
| **Max Results** | Integer | 10 | Maximum results to return |
| **SQL Weight** | 0-100 | 50 | Weight for SQL results (Weighted method) |
| **Vector Weight** | 0-100 | 50 | Weight for Vector results (Weighted method) |

#### Advanced Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **Database Schema Context** | Text | - | Optional schema info for better SQL generation |
| **Enable Detailed Logging** | Boolean | true | Log query analysis and execution details |

### Output Ports

| Output | Type | Description |
|--------|------|-------------|
| **Combined Results** | Data[] | Ranked and combined results from both sources |
| **Query Analysis** | Data | LLM's analysis of the query structure |
| **Execution Plan** | Data | Details about the execution strategy used |

## Ranking Methods Explained

### 1. Reciprocal Rank Fusion (RRF)

**Formula**: `score(d) = Σ 1/(k + rank(d))`

**Best for**: Balanced combination of SQL and Vector results

**Example**:
```
SQL Results:     [Doc1, Doc2, Doc3]
Vector Results:  [Doc2, Doc1, Doc4]

RRF Scores:
- Doc1: 1/(60+1) + 1/(60+2) = 0.0164 + 0.0161 = 0.0325
- Doc2: 1/(60+2) + 1/(60+1) = 0.0161 + 0.0164 = 0.0325
- Doc3: 1/(60+3) = 0.0159
- Doc4: 1/(60+3) = 0.0159

Final Ranking: [Doc1, Doc2, Doc3, Doc4]
```

### 2. Weighted Score

**Formula**: `score(d) = (sql_weight × sql_score) + (vector_weight × vector_score)`

**Best for**: When you want to prioritize one source over another

**Example** (SQL Weight: 70, Vector Weight: 30):
```
Doc1: (0.7 × 0.9) + (0.3 × 0.6) = 0.81
Doc2: (0.7 × 0.7) + (0.3 × 0.9) = 0.76
```

### 3. SQL Priority

**Best for**: When structured filters are more important than semantic similarity

Returns SQL results first, then adds unique vector results.

### 4. Vector Priority

**Best for**: When semantic similarity is more important than exact matches

Returns vector results first, then adds unique SQL results.

## Best Practices

### 1. Query Design

✅ **Good Queries**:
- "Find products under $50 similar to 'running shoes'"
- "Show recent orders from last month with delivery issues"
- "Technical docs about authentication for enterprise customers"

❌ **Poor Queries**:
- "Show me everything" (too vague)
- "SELECT * FROM table" (use SQL node directly)
- Single-word queries without context

### 2. Strategy Selection

| Query Type | Recommended Strategy |
|------------|---------------------|
| Strong filters + semantic search | SQL First |
| Balanced structured + semantic | Parallel |
| Primarily semantic with light filtering | Vector First |
| Uncertain | Auto (LLM Decides) |

### 3. Performance Optimization

- **Use SQL First** when filters significantly reduce dataset size
- **Use Parallel** when both operations are fast
- **Use Vector First** when semantic search is highly selective
- **Provide schema context** for better SQL generation
- **Adjust max_results** based on your needs (lower = faster)

### 4. Schema Context

Providing database schema helps the LLM generate better SQL:

```
Example Schema Context:
Tables:
- products (id, name, price, category, description)
- orders (id, customer_id, product_id, order_date, status)
- reviews (id, product_id, rating, comment, created_date)
```

## Troubleshooting

### Issue: No results returned

**Possible Causes**:
1. SQL and Vector nodes not connected
2. Query doesn't match any data
3. Filters too restrictive

**Solution**:
- Check node connections
- Verify data exists in both SQL and Vector stores
- Try broader queries
- Check execution plan output

### Issue: LLM analysis fails

**Possible Causes**:
1. LLM not properly configured
2. Invalid API key
3. Network issues

**Solution**:
- Verify LLM node configuration
- Check API credentials
- Review LLM node logs
- Use simpler queries for testing

### Issue: Results not ranked as expected

**Possible Causes**:
1. Wrong ranking method selected
2. Weights not properly configured
3. Limited overlap between SQL and Vector results

**Solution**:
- Try different ranking methods
- Adjust SQL/Vector weights
- Review query analysis output
- Check individual SQL and Vector results

## Integration Examples

### Example Flow 1: E-commerce Product Search

```
┌─────────────┐
│ Chat Input  │
│ "wireless   │
│ headphones  │
│ under $100" │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ DB2 SQL Node        │
│ SELECT * FROM       │
│ products WHERE      │
│ price < 100         │
└──────┬──────────────┘
       │
       ├──────────────────────┐
       │                      │
       ▼                      ▼
┌─────────────────┐   ┌──────────────────┐
│ DB2 Vector Node │   │ OpenAI LLM       │
│ Search:         │   │ (Query Analysis) │
│ "wireless       │   └────────┬─────────┘
│  headphones"    │            │
└────────┬────────┘            │
         │                     │
         └──────────┬──────────┘
                    ▼
         ┌────────────────────────┐
         │ DB2 Retrieval          │
         │ Coordinator            │
         │ Strategy: Parallel     │
         │ Ranking: RRF           │
         └──────────┬─────────────┘
                    │
                    ▼
         ┌────────────────────────┐
         │ Chat Output            │
         │ Top 10 Results         │
         └────────────────────────┘
```

### Example Flow 2: Customer Support Ticket Analysis

```
┌─────────────┐
│ Chat Input  │
│ "urgent     │
│ tickets     │
│ about login"│
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ DB2 SQL Node        │
│ SELECT * FROM       │
│ tickets WHERE       │
│ priority='urgent'   │
└──────┬──────────────┘
       │
       ├──────────────────────┐
       │                      │
       ▼                      ▼
┌─────────────────┐   ┌──────────────────┐
│ DB2 Vector Node │   │ Ollama LLM       │
│ Search:         │   │ (Local Analysis) │
│ "login issues"  │   └────────┬─────────┘
└────────┬────────┘            │
         │                     │
         └──────────┬──────────┘
                    ▼
         ┌────────────────────────┐
         │ DB2 Retrieval          │
         │ Coordinator            │
         │ Strategy: SQL First    │
         │ Ranking: Weighted      │
         │ SQL Weight: 70         │
         └──────────┬─────────────┘
                    │
                    ▼
         ┌────────────────────────┐
         │ Prompt Template        │
         │ "Summarize these       │
         │  urgent tickets..."    │
         └──────────┬─────────────┘
                    │
                    ▼
         ┌────────────────────────┐
         │ LLM Response           │
         │ (Summary)              │
         └────────────────────────┘
```

## API Reference

### Main Method: `coordinate_retrieval()`

Orchestrates the hybrid retrieval process.

**Returns**: `list[Data]` - Combined and ranked results

**Process**:
1. Extract query text from input
2. Analyze query with LLM
3. Determine execution strategy
4. Retrieve SQL and Vector results
5. Combine and rank results
6. Return top N results

### Helper Methods

#### `get_query_analysis()`
Returns the LLM's analysis of the query.

**Returns**: `Data` - Query analysis details

#### `get_execution_plan()`
Returns the execution plan used.

**Returns**: `Data` - Execution strategy and metadata

## Performance Considerations

### Latency

| Strategy | Typical Latency | Best For |
|----------|----------------|----------|
| SQL First | Low-Medium | Large datasets with selective filters |
| Parallel | Medium | Balanced workloads |
| Vector First | Medium-High | Semantic-heavy queries |
| Auto | Variable | General purpose |

### Scalability

- **SQL Node**: Scales with database performance
- **Vector Node**: Scales with vector store size and embedding model
- **Coordinator**: Minimal overhead, primarily I/O bound

### Optimization Tips

1. **Index your SQL tables** for common filter columns
2. **Optimize vector store** with appropriate dimensions
3. **Use SQL First** when filters reduce dataset by >80%
4. **Cache LLM responses** for repeated queries
5. **Adjust max_results** to balance quality vs speed

## Future Enhancements

Planned features for future versions:

- [ ] Query rewriting and expansion
- [ ] Multi-stage retrieval pipelines
- [ ] Custom ranking functions
- [ ] Result caching and memoization
- [ ] A/B testing different strategies
- [ ] Performance metrics and monitoring
- [ ] Query optimization suggestions
- [ ] Support for multiple vector stores
- [ ] Federated search across databases

## Contributing

To extend the DB2 Retrieval Coordinator:

1. **Add new ranking methods**: Implement in `_rank_results_*` methods
2. **Add new strategies**: Extend `_determine_execution_strategy()`
3. **Improve query analysis**: Enhance LLM prompts
4. **Add metrics**: Track performance and accuracy

## Support

For issues, questions, or feature requests:
- Check the [DB2 Integration Guide](DB2_INTEGRATION.md)
- Review [Troubleshooting Guide](TROUBLESHOOTING.md)
- Open an issue on GitHub

---

**Made with Bob** 🤖