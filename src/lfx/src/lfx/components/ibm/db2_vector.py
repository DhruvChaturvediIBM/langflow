"""IBM Db2 Vector Store Component for Langflow."""

import ibm_db_dbi
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_core.embeddings import Embeddings
from langchain_db2.db2vs import DB2VS

from lfx.base.vectorstores.model import LCVectorStoreComponent
from lfx.helpers.data import docs_to_data
from lfx.inputs.inputs import BoolInput, DropdownInput, HandleInput, IntInput, SecretStrInput, StrInput
from lfx.schema.data import Data


class DB2VectorStoreComponent(LCVectorStoreComponent):
    """IBM Db2 Vector Store with search capabilities."""

    display_name: str = "IBM Db2 Vector Store"
    description: str = "IBM Db2 Vector Store with hybrid SQL-backed vector retrieval capabilities"
    documentation: str = "https://www.ibm.com/docs/en/db2/11.5"
    name = "DB2VectorStore"
    icon = "DB2"

    inputs = [
        StrInput(
            name="database",
            display_name="Database Name",
            required=True,
            info="Name of the Db2 database",
        ),
        StrInput(
            name="hostname",
            display_name="Hostname",
            required=True,
            info="Db2 server hostname or IP address",
        ),
        IntInput(
            name="port",
            display_name="Port",
            value=50000,
            required=True,
            info="Db2 server port (default: 50000)",
        ),
        StrInput(
            name="username",
            display_name="Username",
            required=True,
            info="Db2 database username",
        ),
        SecretStrInput(
            name="password",
            display_name="Password",
            required=True,
            info="Db2 database password",
        ),
        StrInput(
            name="collection_name",
            display_name="Table Name",
            value="LANGFLOW_VECTORS",
            required=True,
            info="Name of the DB2 table to store vectors (will be created if it doesn't exist)",
        ),
        HandleInput(
            name="embedding",
            display_name="Embedding Model",
            input_types=["Embeddings"],
            required=True,
            info="Embedding model to use for vectorization",
        ),
        HandleInput(
            name="ingest_data",
            display_name="Ingest Data",
            input_types=["Data", "Document", "Message", "Text", "Table"],
            is_list=True,
            info="Documents to ingest into the vector store (accepts Data, Documents, Messages, Tables, JSON, or text)",
        ),
        HandleInput(
            name="search_query",
            display_name="Search Query",
            input_types=["Message", "Text", "Data"],
            required=False,
            info="Query text for similarity search (can be connected from other nodes or typed directly)",
        ),
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            value=4,
            info="Number of results to return from search",
        ),
        DropdownInput(
            name="search_type",
            display_name="Search Type",
            options=["Similarity", "MMR"],
            value="Similarity",
            info="Type of search to perform",
        ),
        DropdownInput(
            name="retrieval_mode",
            display_name="Retrieval Mode",
            options=["Vector", "Hybrid"],
            value="Vector",
            info="Choose between pure vector search and hybrid SQL + vector retrieval",
        ),
        HandleInput(
            name="metadata_filters",
            display_name="Metadata Filters",
            input_types=["Data", "dict", "Message", "str"],
            required=False,
            info="Metadata filters as JSON string, dict, Message, or Data (e.g., {'brand': 'Nike', 'price_lt': 200})",
        ),
        DropdownInput(
            name="distance_strategy",
            display_name="Distance Strategy",
            options=["COSINE", "EUCLIDEAN_DISTANCE", "DOT_PRODUCT"],
            value="COSINE",
            info="Distance calculation strategy",
        ),
        BoolInput(
            name="allow_dangerous_deserialization",
            display_name="Allow Dangerous Deserialization",
            value=False,
            advanced=True,
            info="Allow deserialization of pickled data (use with caution)",
        ),
    ]

    def build_vector_store(self) -> DB2VS:
        """Build and return the DB2 vector store instance."""
        self.log("=" * 60)
        self.log("🔧 BUILD_VECTOR_STORE CALLED")
        self.log(f"ingest_data type: {type(self.ingest_data)}")
        self.log(f"ingest_data value: {self.ingest_data}")
        self.log(f"ingest_data is None: {self.ingest_data is None}")
        self.log(f"ingest_data length: {len(self.ingest_data) if self.ingest_data else 0}")
        self.log("=" * 60)

        # Validate inputs first
        if not self.database or not self.hostname or not self.username or not self.password:
            msg = (
                "Missing required connection parameters. Please provide:\n"
                "- Database Name\n"
                "- Hostname\n"
                "- Username\n"
                "- Password"
            )
            raise ValueError(msg)

        # Create connection string
        conn_str = (
            f"DATABASE={self.database};"
            f"HOSTNAME={self.hostname};"
            f"PORT={self.port};"
            f"PROTOCOL=TCPIP;"
            f"UID={self.username};"
            f"PWD={self.password};"
        )

        # Create connection with better error handling
        try:
            connection = ibm_db_dbi.connect(conn_str, "", "")
        except Exception as e:
            error_msg = str(e)

            # Provide helpful error messages
            if "SQL30081N" in error_msg or "communication error" in error_msg.lower():
                msg = (
                    f"❌ Cannot connect to DB2 server at {self.hostname}:{self.port}\n\n"
                    f"Possible causes:\n"
                    f"1. DB2 server is not running\n"
                    f"2. Hostname/IP is incorrect (current: {self.hostname})\n"
                    f"3. Port is incorrect (current: {self.port})\n"
                    f"4. Firewall blocking connection\n"
                    f"5. Network connectivity issue\n\n"
                    f"To test connection, run:\n"
                    f"  telnet {self.hostname} {self.port}\n"
                    f"  or: nc -zv {self.hostname} {self.port}\n\n"
                    f"Original error: {error_msg}"
                )
                raise ConnectionError(msg) from e
            if "SQL1336N" in error_msg or "not found" in error_msg.lower():
                msg = (
                    f"❌ Cannot resolve hostname: {self.hostname}\n\n"
                    f"Possible causes:\n"
                    f"1. Hostname is misspelled\n"
                    f"2. DNS cannot resolve the hostname\n"
                    f"3. Use IP address instead of hostname\n\n"
                    f"Try using:\n"
                    f"  - localhost (if DB2 is on same machine)\n"
                    f"  - 127.0.0.1 (if DB2 is on same machine)\n"
                    f"  - Actual IP address of DB2 server\n\n"
                    f"Original error: {error_msg}"
                )
                raise ConnectionError(msg) from e
            if "SQL30082N" in error_msg or "security" in error_msg.lower():
                msg = (
                    f"❌ Authentication failed\n\n"
                    f"Possible causes:\n"
                    f"1. Username is incorrect (current: {self.username})\n"
                    f"2. Password is incorrect\n"
                    f"3. User doesn't have access to database: {self.database}\n\n"
                    f"Original error: {error_msg}"
                )
                raise ConnectionError(msg) from e
            msg = (
                f"❌ DB2 Connection Error\n\n"
                f"Database: {self.database}\n"
                f"Hostname: {self.hostname}\n"
                f"Port: {self.port}\n"
                f"Username: {self.username}\n\n"
                f"Error: {error_msg}"
            )
            raise ConnectionError(msg) from e

        # Map distance strategy
        distance_strategy_map = {
            "COSINE": DistanceStrategy.COSINE,
            "EUCLIDEAN_DISTANCE": DistanceStrategy.EUCLIDEAN_DISTANCE,
            "DOT_PRODUCT": DistanceStrategy.DOT_PRODUCT,
        }

        try:
            # Validate embedding model is provided
            if not self.embedding:
                msg = (
                    "❌ Embedding Model Required\n\n"
                    "Please connect an embedding model to the 'Embedding Model' input.\n"
                    "This is required to generate embeddings for your data."
                )
                raise ValueError(msg)

            # Build vector store (will automatically generate embeddings for existing empty rows)
            self.log(f"Connecting to DB2 table: {self.collection_name}...")
            vector_store = DB2VS(
                client=connection,
                embedding_function=self.embedding,
                table_name=self.collection_name,
                distance_strategy=distance_strategy_map.get(self.distance_strategy, DistanceStrategy.COSINE),
            )

            self.log(f"✓ Connected to DB2 table: {self.collection_name}")
            self.log("Note: If table had empty embeddings, they have been automatically generated")

            # Add documents if provided
            if self.ingest_data:
                import json

                import pandas as pd
                from langchain_core.documents import Document

                self.log(f"📥 Starting data ingestion... ({len(self.ingest_data)} data items)")
                documents = []
                for idx, data in enumerate(self.ingest_data):
                    self.log(f"Processing data item {idx + 1}/{len(self.ingest_data)}: {type(data).__name__}")
                    if isinstance(data, Data):
                        doc = data.to_lc_document()
                        # Preserve metadata for hybrid retrieval
                        documents.append(doc)
                    elif isinstance(data, Document):
                        # Preserve existing metadata
                        documents.append(data)
                    elif isinstance(data, pd.DataFrame):
                        # Handle pandas DataFrame - extract metadata from columns
                        for _, row in data.iterrows():
                            # Separate text content from metadata fields
                            metadata = {}
                            text_parts = []

                            for col_name, val in row.items():
                                # Common metadata fields to extract
                                if col_name.lower() in ["brand", "category", "price", "product_id", "tenant_id", "id"]:
                                    if pd.notna(val):
                                        metadata[col_name] = val
                                elif col_name.lower() in ["description", "text", "content"]:
                                    # These are text content fields
                                    if pd.notna(val):
                                        text_parts.append(str(val))
                                else:
                                    # Other fields go to text
                                    try:
                                        if pd.notna(val):
                                            text_parts.append(str(val))
                                    except (ValueError, TypeError):
                                        text_parts.append(str(val))

                            text = " ".join(text_parts) if text_parts else ""
                            doc = Document(page_content=text, metadata=metadata)
                            documents.append(doc)
                    elif isinstance(data, pd.Series):
                        # Handle pandas Series - convert each value to a document
                        for val in data:
                            try:
                                if pd.notna(val):
                                    doc = Document(page_content=str(val), metadata={})
                                    documents.append(doc)
                            except (ValueError, TypeError):
                                doc = Document(page_content=str(val), metadata={})
                                documents.append(doc)
                    elif isinstance(data, dict):
                        # Handle JSON/dict objects - extract metadata intelligently
                        metadata = {}
                        text_content = None

                        # Extract known metadata fields
                        for key in ["brand", "category", "price", "product_id", "tenant_id", "id"]:
                            if key in data:
                                metadata[key] = data[key]

                        # Extract text content
                        if "description" in data:
                            text_content = data["description"]
                        elif "text" in data:
                            text_content = data["text"]
                        elif "content" in data:
                            text_content = data["content"]
                        else:
                            # Use entire dict as text if no specific text field
                            text_content = json.dumps(data)

                        doc = Document(page_content=text_content, metadata=metadata)
                        documents.append(doc)
                    elif hasattr(data, "text"):
                        # Handle Message or any object with text attribute
                        metadata = {}
                        if hasattr(data, "metadata") and isinstance(data.metadata, dict):
                            metadata = data.metadata
                        doc = Document(page_content=data.text, metadata=metadata)
                        documents.append(doc)
                    elif isinstance(data, str):
                        # Check if it's CSV content
                        if "," in data and "\n" in data:
                            # Likely CSV - try to parse it
                            try:
                                import io

                                df = pd.read_csv(io.StringIO(data))
                                self.log(f"Detected CSV format with {len(df)} rows")

                                # Process as DataFrame
                                for _, row in df.iterrows():
                                    metadata = {}
                                    text_parts = []

                                    for col_name, val in row.items():
                                        if col_name.lower() in [
                                            "brand",
                                            "category",
                                            "price",
                                            "product_id",
                                            "tenant_id",
                                            "id",
                                        ]:
                                            if pd.notna(val):
                                                metadata[col_name] = val
                                        elif col_name.lower() in ["description", "text", "content"]:
                                            if pd.notna(val):
                                                text_parts.append(str(val))
                                        # Other fields go to text
                                        elif pd.notna(val):
                                            text_parts.append(str(val))

                                    text = " ".join(text_parts) if text_parts else ""
                                    doc = Document(page_content=text, metadata=metadata)
                                    documents.append(doc)
                            except (ValueError, pd.errors.ParserError) as e:
                                self.log(f"Failed to parse as CSV: {e}, treating as plain text")
                                doc = Document(page_content=data, metadata={})
                                documents.append(doc)
                        else:
                            # Handle plain strings
                            doc = Document(page_content=data, metadata={})
                            documents.append(doc)

                if documents:
                    self.log(f"📝 Prepared {len(documents)} documents for ingestion")
                    self.log("Sample document metadata: " + str(documents[0].metadata if documents else {}))

                    try:
                        self.log(f"🔄 Adding {len(documents)} documents to DB2 table '{self.collection_name}'...")
                        vector_store.add_documents(documents)
                        self.log(f"✅ Successfully ingested {len(documents)} documents into DB2!")
                    except ValueError as e:
                        error_msg = str(e)
                        if "dimension mismatch" in error_msg.lower():
                            # Provide clear guidance on dimension mismatch
                            msg = (
                                f"Embedding dimension mismatch detected. {error_msg}\n\n"
                                f"To fix this issue:\n"
                                f"1. Drop the existing table: DROP TABLE {self.collection_name};\n"
                                f"2. Or use a different table name\n"
                                f"3. Or ensure your embedding model produces the same dimension as the table"
                            )
                            raise ValueError(msg) from e
                        raise
                    except RuntimeError as e:
                        error_msg = str(e)
                        if "VECTOR" in error_msg and "cannot be CAST" in error_msg:
                            # DB2 vector dimension mismatch error
                            msg = (
                                f"DB2 vector dimension mismatch: {error_msg}\n\n"
                                f"The table '{self.collection_name}' was created with a different vector dimension.\n"
                                f"To fix: DROP TABLE {self.collection_name}; and try again."
                            )
                            raise ValueError(msg) from e
                        raise
                else:
                    self.log("⚠️ No documents to add - ingest_data was empty or could not be processed")
        except Exception:
            # Ensure connection is closed on error
            connection.close()
            raise

        return vector_store

    def _build_filter_clause(self, filters: dict) -> tuple[str, list]:
        """Build SQL WHERE clause from metadata filters.

        Args:
            filters: Dictionary of filter conditions

        Returns:
            Tuple of (WHERE clause string, list of parameter values)

        Supported filter formats:
            - field_name: value (equality)
            - field_name_lt: value (less than)
            - field_name_lte: value (less than or equal)
            - field_name_gt: value (greater than)
            - field_name_gte: value (greater than or equal)
        """
        if not filters:
            return "", []

        where_clauses = []
        params = []

        for key, value in filters.items():
            # Parse filter key for operators
            if key.endswith("_lt"):
                field = key[:-3]
                where_clauses.append(f"{field} < ?")
                params.append(value)
            elif key.endswith("_lte"):
                field = key[:-4]
                where_clauses.append(f"{field} <= ?")
                params.append(value)
            elif key.endswith("_gt"):
                field = key[:-3]
                where_clauses.append(f"{field} > ?")
                params.append(value)
            elif key.endswith("_gte"):
                field = key[:-4]
                where_clauses.append(f"{field} >= ?")
                params.append(value)
            else:
                # Default to equality
                where_clauses.append(f"{key} = ?")
                params.append(value)

        where_sql = " AND ".join(where_clauses)
        return where_sql, params

    def hybrid_search(self, query_text: str, filters: dict, k: int = 5) -> list[Data]:
        """Perform hybrid search combining vector similarity and SQL filtering.

        Args:
            query_text: The search query text
            filters: Dictionary of metadata filters
            k: Number of results to return

        Returns:
            List of Data objects with search results
        """
        from langchain_core.documents import Document

        self.log("Running hybrid retrieval...")

        # Get vector store and connection
        vector_store = self.build_vector_store()
        connection = vector_store.client

        # Generate query embedding
        self.log(f"Generating embedding for query: {query_text[:50]}...")
        # Use the public embedding function instead of private method
        if isinstance(vector_store.embedding_function, Embeddings):
            query_embedding = vector_store.embedding_function.embed_query(query_text)
        else:
            query_embedding = vector_store.embedding_function(query_text)
        embedding_dim = len(query_embedding)

        # Build WHERE clause from filters
        where_sql, filter_params = self._build_filter_clause(filters)

        if where_sql:
            self.log(f"Generated WHERE clause: {where_sql}")
            self.log(f"Filter parameters: {filter_params}")
        else:
            self.log("No filters provided - using pure vector search")

        # Get distance function
        distance_func_map = {
            "COSINE": "COSINE",
            "EUCLIDEAN_DISTANCE": "EUCLIDEAN",
            "DOT_PRODUCT": "DOT",
        }
        distance_func = distance_func_map.get(self.distance_strategy, "COSINE")

        # Build SQL query
        # Note: column_names are validated by DB2VS, not user input
        column_names = vector_store.column_names

        # S608: column_names from DB2VS are validated, not direct user input
        base_query = f"""
        SELECT {column_names["id"]},
               {column_names["text"]},
               {column_names["metadata"]},
               VECTOR_DISTANCE(
                   {column_names["embedding"]},
                   VECTOR(?, {embedding_dim}, FLOAT32),
                   {distance_func}
               ) as distance
        FROM {vector_store.table_name}
        """  # noqa: S608

        if where_sql:
            base_query += f"\nWHERE {where_sql}"

        base_query += f"\nORDER BY distance\nFETCH FIRST {k} ROWS ONLY"

        self.log("Executing hybrid search query...")

        # Execute query
        cursor = connection.cursor()
        try:
            # Prepare parameters: embedding string first, then filter params
            query_params = [str(query_embedding), *filter_params]

            cursor.execute(base_query, query_params)
            results = cursor.fetchall()

            self.log(f"Retrieved {len(results)} documents")

            # Convert results to Documents
            documents = []
            for result in results:
                # Handle metadata - convert memoryview/bytes to dict if needed
                meta_raw = result[2]
                if meta_raw is None:
                    metadata = {}
                elif isinstance(meta_raw, (bytes, memoryview)):
                    import json

                    metadata = json.loads(bytes(meta_raw).decode("utf-8"))
                elif isinstance(meta_raw, str):
                    import json

                    metadata = json.loads(meta_raw)
                else:
                    metadata = {}

                # Add similarity score to metadata
                metadata["similarity_score"] = float(result[3])

                doc = Document(
                    page_content=(result[1] if result[1] is not None else ""),
                    metadata=metadata,
                )
                documents.append(doc)

            return docs_to_data(documents)

        finally:
            cursor.close()

    def search_documents(self) -> list[Data]:
        """Perform similarity search and return results.

        Supports two retrieval modes:
        - Vector: Pure vector similarity search (backward compatible)
        - Hybrid: Combined vector similarity + SQL metadata filtering
        """
        if not self.search_query:
            return []

        # Extract text from search_query (handle Message, Data, or string)
        query_text = self.search_query
        if hasattr(self.search_query, "text"):
            # Handle Message objects
            query_text = self.search_query.text
        elif isinstance(self.search_query, Data):
            # Handle Data objects
            query_text = self.search_query.text_data
        elif not isinstance(self.search_query, str):
            # Convert any other type to string
            query_text = str(self.search_query)

        # Check retrieval mode
        retrieval_mode = getattr(self, "retrieval_mode", "Vector")

        if retrieval_mode == "Hybrid":
            # Hybrid retrieval with metadata filtering
            self.log("Using Hybrid retrieval mode")

            # Extract filters from various input types
            filters = {}
            if self.metadata_filters:
                import json

                if isinstance(self.metadata_filters, dict):
                    # Direct dict input
                    filters = self.metadata_filters
                elif isinstance(self.metadata_filters, str):
                    # JSON string input
                    try:
                        filters = json.loads(self.metadata_filters)
                        self.log(f"Parsed JSON string filters: {filters}")
                    except json.JSONDecodeError as e:
                        self.log(f"Warning: Failed to parse JSON string: {e}")
                elif isinstance(self.metadata_filters, Data):
                    # Data object input
                    if hasattr(self.metadata_filters, "data") and isinstance(self.metadata_filters.data, dict):
                        filters = self.metadata_filters.data
                    else:
                        self.log("Warning: metadata_filters is Data but couldn't extract dict")
                elif hasattr(self.metadata_filters, "text"):
                    # Message object input
                    try:
                        filters = json.loads(self.metadata_filters.text)
                        self.log(f"Parsed Message text as JSON: {filters}")
                    except json.JSONDecodeError as e:
                        self.log(f"Warning: Failed to parse Message text as JSON: {e}")
                else:
                    self.log(f"Warning: metadata_filters type {type(self.metadata_filters)} not supported")

            if filters:
                self.log(f"Applying filters: {filters}")
                return self.hybrid_search(query_text=query_text, filters=filters, k=self.number_of_results)
            self.log("No filters provided, falling back to vector search")

        # Vector retrieval (default, backward compatible)
        self.log("Using Vector retrieval mode")
        vector_store = self.build_vector_store()

        if self.search_type == "Similarity":
            docs = vector_store.similarity_search(
                query=query_text,
                k=self.number_of_results,
            )
        else:  # MMR
            docs = vector_store.max_marginal_relevance_search(
                query=query_text,
                k=self.number_of_results,
            )

        return docs_to_data(docs)

    def build(self) -> DB2VS | list[Data]:
        """Build the component and return either the vector store or search results."""
        if self.search_query:
            return self.search_documents()
        return self.build_vector_store()


# Made with Bob
