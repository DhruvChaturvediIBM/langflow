"""IBM Db2 Retrieval Coordinator Component for Langflow.

This component orchestrates query execution between DB2 SQL and DB2 Vector nodes,
combining structured filtering with semantic search capabilities.
"""

import asyncio
import json
from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import BoolInput, DropdownInput, HandleInput, IntInput, MessageTextInput
from lfx.io import Output
from lfx.schema.data import Data


class DB2RetrievalCoordinatorComponent(Component):
    """Orchestrates query execution between DB2 SQL and DB2 Vector nodes.

    This component accepts natural language queries and intelligently routes them to:
    - DB2 SQL node for structured filtering
    - DB2 Vector node for semantic similarity search

    It supports multiple execution strategies and combines results intelligently.
    """

    display_name = "DB2 Retrieval Coordinator"
    description = "Orchestrate SQL and Vector search for hybrid DB2 retrieval"
    documentation = "https://www.ibm.com/docs/en/db2/11.5"
    icon = "DB2"
    name = "DB2RetrievalCoordinator"

    inputs = [
        # Query Input
        HandleInput(
            name="query",
            display_name="Natural Language Query",
            input_types=["Message", "Text", "Data"],
            required=True,
            info="Natural language query to process (e.g., 'Find recent orders for customer John with high value')",
        ),
        # LLM for Query Analysis
        HandleInput(
            name="llm",
            display_name="Language Model",
            input_types=["LanguageModel"],
            required=True,
            info="LLM to analyze query and extract SQL filters and semantic intent",
        ),
        # SQL Node Connection
        HandleInput(
            name="sql_results",
            display_name="SQL Results (Optional)",
            input_types=["Data"],
            is_list=True,
            required=False,
            info="Connect to DB2 SQL node output for structured filtering",
        ),
        # Vector Node Connection
        HandleInput(
            name="vector_results",
            display_name="Vector Results (Optional)",
            input_types=["Data"],
            is_list=True,
            required=False,
            info="Connect to DB2 Vector node output for semantic search",
        ),
        # Execution Strategy
        DropdownInput(
            name="execution_strategy",
            display_name="Execution Strategy",
            options=[
                "SQL First (Filter then Rank)",
                "Parallel (Execute Both)",
                "Vector First (Search then Filter)",
                "Auto (LLM Decides)",
            ],
            value="Auto (LLM Decides)",
            info="How to coordinate SQL and Vector execution",
        ),
        # Result Configuration
        IntInput(
            name="max_results",
            display_name="Max Results",
            value=10,
            info="Maximum number of results to return",
        ),
        # Ranking Configuration
        DropdownInput(
            name="ranking_method",
            display_name="Ranking Method",
            options=[
                "Reciprocal Rank Fusion",
                "Weighted Score",
                "SQL Priority",
                "Vector Priority",
            ],
            value="Reciprocal Rank Fusion",
            info="Method to combine and rank results from SQL and Vector searches",
        ),
        # Weights for scoring
        IntInput(
            name="sql_weight",
            display_name="SQL Weight",
            value=50,
            advanced=True,
            info="Weight for SQL results (0-100, used in Weighted Score method)",
        ),
        IntInput(
            name="vector_weight",
            display_name="Vector Weight",
            value=50,
            advanced=True,
            info="Weight for Vector results (0-100, used in Weighted Score method)",
        ),
        # Schema Context (optional)
        MessageTextInput(
            name="schema_context",
            display_name="Database Schema Context",
            required=False,
            advanced=True,
            info="Optional: Provide database schema information to help LLM generate better SQL queries",
        ),
        # Enable detailed logging
        BoolInput(
            name="enable_logging",
            display_name="Enable Detailed Logging",
            value=True,
            advanced=True,
            info="Log query analysis and execution details",
        ),
    ]

    outputs = [
        Output(display_name="Combined Results", name="results", method="coordinate_retrieval"),
        Output(display_name="Query Analysis", name="analysis", method="get_query_analysis"),
        Output(display_name="Execution Plan", name="plan", method="get_execution_plan"),
    ]

    def __init__(self, **kwargs):
        """Initialize the coordinator."""
        super().__init__(**kwargs)
        self._query_analysis = None
        self._execution_plan = None
        self._sql_results_cache = None
        self._vector_results_cache = None

    def _extract_text(self, input_data: Any) -> str:
        """Extract text from various input types."""
        if isinstance(input_data, str):
            return input_data
        if hasattr(input_data, "text"):
            return input_data.text
        if isinstance(input_data, Data):
            if hasattr(input_data, "text_data"):
                return input_data.text_data
            return str(input_data.data)
        return str(input_data)

    async def _analyze_query_with_llm(self, query_text: str) -> dict[str, Any]:
        """Use LLM to analyze the query and extract structured and semantic components.

        Returns:
            dict with keys:
                - has_structured_filters: bool
                - has_semantic_intent: bool
                - sql_filters: str (SQL WHERE clause or full query)
                - semantic_query: str (semantic search query)
                - recommended_strategy: str
                - confidence: float
        """
        # Build the analysis prompt
        schema_info = f"\n\nDatabase Schema:\n{self.schema_context}" if self.schema_context else ""

        analysis_prompt = f"""Analyze the following natural language query and extract:
1. Whether it contains structured filters (dates, numbers, exact matches, conditions)
2. Whether it contains semantic intent (concepts, meanings, similarity)
3. SQL filters or WHERE clause for structured filtering
4. Semantic search query for vector similarity
5. Recommended execution strategy
6. Confidence level (0-1)

Query: "{query_text}"{schema_info}

Respond in JSON format:
{{
    "has_structured_filters": true/false,
    "has_semantic_intent": true/false,
    "sql_filters": "SQL WHERE clause or empty string",
    "semantic_query": "semantic search query or empty string",
    "recommended_strategy": "sql_first|parallel|vector_first|sql_only|vector_only",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}"""

        try:
            # Invoke LLM
            if hasattr(self.llm, "invoke"):
                response = await asyncio.to_thread(self.llm.invoke, analysis_prompt)
            else:
                response = await asyncio.to_thread(self.llm, analysis_prompt)

            # Extract text from response
            response_text = self._extract_text(response)

            # Parse JSON response
            # Try to find JSON in the response
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback: assume it's all semantic
                analysis = {
                    "has_structured_filters": False,
                    "has_semantic_intent": True,
                    "sql_filters": "",
                    "semantic_query": query_text,
                    "recommended_strategy": "vector_only",
                    "confidence": 0.5,
                    "reasoning": "Could not parse LLM response, defaulting to vector search",
                }

            return analysis

        except Exception as e:
            self.log(f"Error analyzing query with LLM: {e}")
            # Fallback: treat as semantic query
            return {
                "has_structured_filters": False,
                "has_semantic_intent": True,
                "sql_filters": "",
                "semantic_query": query_text,
                "recommended_strategy": "vector_only",
                "confidence": 0.3,
                "reasoning": f"LLM analysis failed: {e!s}",
            }

    def _determine_execution_strategy(self, analysis: dict[str, Any]) -> str:
        """Determine the execution strategy based on query analysis and user preference.

        Returns:
            One of: "sql_first", "parallel", "vector_first", "sql_only", "vector_only"
        """
        user_strategy = self.execution_strategy

        # If user chose Auto, use LLM recommendation
        if user_strategy == "Auto (LLM Decides)":
            return analysis.get("recommended_strategy", "parallel")

        # Map user choice to strategy
        strategy_map = {
            "SQL First (Filter then Rank)": "sql_first",
            "Parallel (Execute Both)": "parallel",
            "Vector First (Search then Filter)": "vector_first",
        }

        return strategy_map.get(user_strategy, "parallel")

    def _rank_results_rrf(self, sql_results: list[Data], vector_results: list[Data], k: int = 60) -> list[Data]:
        """Rank results using Reciprocal Rank Fusion (RRF).

        RRF formula: score(d) = Σ 1/(k + rank(d))
        where k is a constant (typically 60) and rank(d) is the rank of document d in each list.
        """
        # Create a score dictionary
        scores = {}
        result_map = {}

        # Score SQL results
        for rank, result in enumerate(sql_results, start=1):
            result_id = id(result)
            scores[result_id] = scores.get(result_id, 0) + 1 / (k + rank)
            result_map[result_id] = result

        # Score Vector results
        for rank, result in enumerate(vector_results, start=1):
            result_id = id(result)
            scores[result_id] = scores.get(result_id, 0) + 1 / (k + rank)
            result_map[result_id] = result

        # Sort by score
        ranked_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        # Return ranked results with scores
        ranked_results = []
        for result_id in ranked_ids[: self.max_results]:
            result = result_map[result_id]
            # Add ranking metadata
            if isinstance(result.data, dict):
                result.data["_rrf_score"] = scores[result_id]
            ranked_results.append(result)

        return ranked_results

    def _rank_results_weighted(self, sql_results: list[Data], vector_results: list[Data]) -> list[Data]:
        """Rank results using weighted scoring."""
        sql_w = self.sql_weight / 100.0
        vector_w = self.vector_weight / 100.0

        scores = {}
        result_map = {}

        # Normalize and score SQL results
        sql_max = len(sql_results)
        for rank, result in enumerate(sql_results, start=1):
            result_id = id(result)
            normalized_score = (sql_max - rank + 1) / sql_max
            scores[result_id] = scores.get(result_id, 0) + (normalized_score * sql_w)
            result_map[result_id] = result

        # Normalize and score Vector results
        vector_max = len(vector_results)
        for rank, result in enumerate(vector_results, start=1):
            result_id = id(result)
            normalized_score = (vector_max - rank + 1) / vector_max
            scores[result_id] = scores.get(result_id, 0) + (normalized_score * vector_w)
            result_map[result_id] = result

        # Sort by score
        ranked_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        # Return ranked results
        ranked_results = []
        for result_id in ranked_ids[: self.max_results]:
            result = result_map[result_id]
            if isinstance(result.data, dict):
                result.data["_weighted_score"] = scores[result_id]
            ranked_results.append(result)

        return ranked_results

    def _combine_results(self, sql_results: list[Data], vector_results: list[Data]) -> list[Data]:
        """Combine and rank results based on the selected ranking method."""
        if not sql_results and not vector_results:
            return []

        if not sql_results:
            return vector_results[: self.max_results]

        if not vector_results:
            return sql_results[: self.max_results]

        # Apply ranking method
        if self.ranking_method == "Reciprocal Rank Fusion":
            return self._rank_results_rrf(sql_results, vector_results)
        if self.ranking_method == "Weighted Score":
            return self._rank_results_weighted(sql_results, vector_results)
        if self.ranking_method == "SQL Priority":
            # SQL results first, then vector
            combined = sql_results + [v for v in vector_results if v not in sql_results]
            return combined[: self.max_results]
        if self.ranking_method == "Vector Priority":
            # Vector results first, then SQL
            combined = vector_results + [s for s in sql_results if s not in vector_results]
            return combined[: self.max_results]

        # Default: interleave results
        combined = []
        for i in range(max(len(sql_results), len(vector_results))):
            if i < len(sql_results):
                combined.append(sql_results[i])
            if i < len(vector_results) and vector_results[i] not in combined:
                combined.append(vector_results[i])

        return combined[: self.max_results]

    async def coordinate_retrieval(self) -> list[Data]:
        """Main coordination method that orchestrates SQL and Vector retrieval."""
        # Extract query text
        query_text = self._extract_text(self.query)

        if self.enable_logging:
            self.log(f"Processing query: {query_text}")

        # Analyze query with LLM
        self._query_analysis = await self._analyze_query_with_llm(query_text)

        if self.enable_logging:
            self.log(f"Query analysis: {json.dumps(self._query_analysis, indent=2)}")

        # Determine execution strategy
        strategy = self._determine_execution_strategy(self._query_analysis)
        self._execution_plan = {
            "strategy": strategy,
            "has_sql_results": bool(self.sql_results),
            "has_vector_results": bool(self.vector_results),
            "query_analysis": self._query_analysis,
        }

        if self.enable_logging:
            self.log(f"Execution strategy: {strategy}")

        # Get results based on strategy
        sql_results = []
        vector_results = []

        if strategy == "sql_only":
            sql_results = self.sql_results if self.sql_results else []
        elif strategy == "vector_only":
            vector_results = self.vector_results if self.vector_results else []
        elif strategy == "sql_first":
            # SQL first, then use results to filter vector search
            sql_results = self.sql_results if self.sql_results else []
            vector_results = self.vector_results if self.vector_results else []
        elif strategy == "vector_first":
            # Vector first, then use results to filter SQL
            vector_results = self.vector_results if self.vector_results else []
            sql_results = self.sql_results if self.sql_results else []
        else:  # parallel
            # Execute both in parallel (results already available from connections)
            sql_results = self.sql_results if self.sql_results else []
            vector_results = self.vector_results if self.vector_results else []

        # Cache results
        self._sql_results_cache = sql_results
        self._vector_results_cache = vector_results

        if self.enable_logging:
            self.log(f"SQL results: {len(sql_results)}, Vector results: {len(vector_results)}")

        # Combine and rank results
        combined_results = self._combine_results(sql_results, vector_results)

        if self.enable_logging:
            self.log(f"Returning {len(combined_results)} combined results")

        self.status = f"Retrieved {len(combined_results)} results using {strategy} strategy"

        return combined_results

    def get_query_analysis(self) -> Data:
        """Return the query analysis as a Data object."""
        if self._query_analysis is None:
            return Data(data={"error": "No query has been analyzed yet"})

        return Data(data=self._query_analysis)

    def get_execution_plan(self) -> Data:
        """Return the execution plan as a Data object."""
        if self._execution_plan is None:
            return Data(data={"error": "No execution plan has been created yet"})

        return Data(data=self._execution_plan)


# Made with Bob
