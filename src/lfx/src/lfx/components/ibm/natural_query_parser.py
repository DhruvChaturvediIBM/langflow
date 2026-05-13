"""Natural Language Query Parser for Hybrid Search.

Parses natural language queries into:
1. Semantic search query (descriptive terms)
2. Metadata filters (structured constraints)

WITHOUT using LLMs - pure rule-based parsing with:
- Regex patterns
- Keyword extraction
- Comparator detection
- Schema mapping
- Tokenization

Example:
Input: "nike blue shoes with price less than 200 and ratings greater than 3"
Output: {
    "query": "blue shoes",
    "filters": {"brand": "Nike", "price_lt": 200, "rating_gt": 3}
}
"""

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class SchemaField:
    """Represents a database schema field."""

    name: str
    type: str  # 'numeric', 'string', 'boolean'
    aliases: list[str]  # Alternative names for this field


class SchemaMapper:
    """Maps natural language terms to database schema fields."""

    def __init__(self, schema_fields: list[SchemaField]):
        """Initialize with database schema.

        Args:
            schema_fields: List of SchemaField objects describing the database
        """
        self.fields = schema_fields
        self._build_lookup_maps()

    def _build_lookup_maps(self):
        """Build efficient lookup maps for field matching."""
        self.field_map = {}  # term -> SchemaField
        self.type_map = {}  # field_name -> type

        for field in self.fields:
            # Map field name
            self.field_map[field.name.lower()] = field
            self.type_map[field.name.lower()] = field.type

            # Map aliases
            for alias in field.aliases:
                self.field_map[alias.lower()] = field

    def find_field(self, term: str) -> SchemaField | None:
        """Find schema field matching the given term."""
        return self.field_map.get(term.lower())

    @classmethod
    def from_metadata_sample(cls, metadata_dict: dict[str, Any]) -> "SchemaMapper":
        """Auto-detect schema from a metadata sample.

        Args:
            metadata_dict: Sample metadata dictionary

        Returns:
            SchemaMapper instance
        """
        fields = []

        for key, value in metadata_dict.items():
            # Detect type
            if isinstance(value, (int, float)):
                field_type = "numeric"
            elif isinstance(value, bool):
                field_type = "boolean"
            else:
                field_type = "string"

            # Generate aliases
            aliases = cls._generate_aliases(key)

            fields.append(SchemaField(name=key, type=field_type, aliases=aliases))

        return cls(fields)

    @staticmethod
    def _generate_aliases(field_name: str) -> list[str]:
        """Generate common aliases for a field name."""
        aliases = []

        # Common patterns
        patterns = {
            "price": ["cost", "amount", "value"],
            "rating": ["score", "stars", "review"],
            "brand": ["manufacturer", "maker", "company"],
            "color": ["colour", "shade"],
            "size": ["dimension"],
            "stock": ["inventory", "available", "availability"],
            "category": ["type", "class", "group"],
        }

        field_lower = field_name.lower()
        for key, alias_list in patterns.items():
            if key in field_lower:
                aliases.extend(alias_list)

        # Add variations
        if "_" in field_name:
            aliases.append(field_name.replace("_", " "))
            aliases.append(field_name.replace("_", ""))

        return aliases


class NaturalQueryParser:
    """Parse natural language queries into semantic query + filters."""

    # Comparison operators
    COMPARATORS = {
        "less than": "_lt",
        "lesser than": "_lt",
        "below": "_lt",
        "under": "_lt",
        "<": "_lt",
        "less than or equal": "_lte",
        "less than or equal to": "_lte",
        "<=": "_lte",
        "greater than": "_gt",
        "more than": "_gt",
        "above": "_gt",
        "over": "_gt",
        ">": "_gt",
        "greater than or equal": "_gte",
        "greater than or equal to": "_gte",
        ">=": "_gte",
        "equal": "",
        "equals": "",
        "is": "",
        "=": "",
        "==": "",
    }

    # Stop words to remove from semantic query
    STOP_WORDS = {
        "with",
        "and",
        "or",
        "the",
        "a",
        "an",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "by",
        "from",
        "as",
        "that",
        "which",
        "than",
        "equal",
        "equals",
        "is",
        "are",
        "was",
        "were",
        "less",
        "greater",
        "more",
        "below",
        "above",
        "under",
        "over",
    }

    def __init__(self, schema_mapper: SchemaMapper):
        """Initialize parser with schema mapper.

        Args:
            schema_mapper: SchemaMapper instance for field detection
        """
        self.schema = schema_mapper
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        # Pattern for numeric comparisons
        # Matches: "price less than 200", "rating > 3", etc.
        self.numeric_pattern = re.compile(
            r"(\w+)\s*"  # field name
            r"(less than or equal to|greater than or equal to|less than|greater than|"
            r"below|above|under|over|<=|>=|<|>|=|==|is|equals?)\s*"  # comparator
            r"(\d+\.?\d*)",  # numeric value
            re.IGNORECASE,
        )

        # Pattern for string equality
        # Matches: "brand nike", "color blue", etc.
        self.string_pattern = re.compile(
            r"(\w+)\s+"  # field name
            r"(is|equals?|=|==)?\s*"  # optional comparator
            r"([a-zA-Z][a-zA-Z0-9\s]*?)(?=\s+(?:and|or|with|less|greater|below|above|$))",
            re.IGNORECASE,
        )

        # Pattern for boolean values
        self.boolean_pattern = re.compile(
            r"(\w+)\s+"  # field name
            r"(is|equals?|=|==)?\s*"  # optional comparator
            r"(true|false|yes|no)",
            re.IGNORECASE,
        )

    def parse(self, query: str) -> dict[str, Any]:
        """Parse natural language query into semantic query + filters.

        Args:
            query: Natural language query string

        Returns:
            Dictionary with 'query' and 'filters' keys
        """
        filters = {}
        extracted_terms = set()

        # Extract numeric filters
        for match in self.numeric_pattern.finditer(query):
            field_term, comparator, value = match.groups()

            # Find matching schema field
            field = self.schema.find_field(field_term)
            if field and field.type == "numeric":
                # Map comparator
                operator = self._map_comparator(comparator)
                filter_key = f"{field.name}{operator}"
                filters[filter_key] = float(value)

                # Mark terms as extracted
                extracted_terms.add(field_term.lower())
                extracted_terms.add(comparator.lower())
                extracted_terms.add(value)

        # Extract boolean filters
        for match in self.boolean_pattern.finditer(query):
            field_term, _, bool_value = match.groups()

            field = self.schema.find_field(field_term)
            if field and field.type == "boolean":
                filters[field.name] = bool_value.lower() in ("true", "yes")
                extracted_terms.add(field_term.lower())
                extracted_terms.add(bool_value.lower())

        # Extract string filters (brand names, colors, etc.)
        for match in self.string_pattern.finditer(query):
            field_term, _, value = match.groups()

            field = self.schema.find_field(field_term)
            if field and field.type == "string":
                # Clean value
                value = value.strip()
                if value and len(value) > 1:
                    filters[field.name] = value.title()  # Capitalize
                    extracted_terms.add(field_term.lower())
                    extracted_terms.add(value.lower())

        # Build semantic query by removing extracted terms
        semantic_query = self._build_semantic_query(query, extracted_terms)

        return {"query": semantic_query, "filters": filters}

    def _map_comparator(self, comparator: str) -> str:
        """Map natural language comparator to filter suffix."""
        comparator_lower = comparator.lower().strip()
        return self.COMPARATORS.get(comparator_lower, "")

    def _build_semantic_query(self, original_query: str, extracted_terms: set) -> str:
        """Build semantic search query by removing filter terms.

        Args:
            original_query: Original query string
            extracted_terms: Set of terms that were extracted as filters

        Returns:
            Cleaned semantic query string
        """
        # Tokenize
        tokens = re.findall(r"\w+", original_query.lower())

        # Remove extracted terms and stop words
        semantic_tokens = [
            token
            for token in tokens
            if token not in extracted_terms and token not in self.STOP_WORDS and not token.isdigit()
        ]

        return " ".join(semantic_tokens)


# Made with Bob
