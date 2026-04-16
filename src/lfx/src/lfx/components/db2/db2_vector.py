"""IBM Db2 Vector Store Component for Langflow."""

import ibm_db_dbi
from langchain_community.vectorstores.utils import DistanceStrategy
from langchain_db2.db2vs import DB2VS

from lfx.base.vectorstores.model import LCVectorStoreComponent, check_cached_vector_store
from lfx.helpers.data import docs_to_data
from lfx.inputs.inputs import BoolInput, DropdownInput, HandleInput, IntInput, SecretStrInput, StrInput
from lfx.schema.data import Data


class DB2VectorStoreComponent(LCVectorStoreComponent):
    """IBM Db2 Vector Store with search capabilities."""

    display_name: str = "IBM Db2 Vector Store"
    description: str = "IBM Db2 Vector Store with similarity search capabilities"
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
        StrInput(
            name="search_query",
            display_name="Search Query",
            info="Query text for similarity search",
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

    @check_cached_vector_store
    def build_vector_store(self) -> DB2VS:
        """Build and return the DB2 vector store instance."""
        # Create connection string
        conn_str = (
            f"DATABASE={self.database};"
            f"HOSTNAME={self.hostname};"
            f"PORT={self.port};"
            f"PROTOCOL=TCPIP;"
            f"UID={self.username};"
            f"PWD={self.password};"
        )

        # Create connection
        connection = ibm_db_dbi.connect(conn_str, "", "")

        # Map distance strategy
        distance_strategy_map = {
            "COSINE": DistanceStrategy.COSINE,
            "EUCLIDEAN_DISTANCE": DistanceStrategy.EUCLIDEAN_DISTANCE,
            "DOT_PRODUCT": DistanceStrategy.DOT_PRODUCT,
        }

        # Build vector store
        vector_store = DB2VS(
            client=connection,
            embedding_function=self.embedding,
            table_name=self.collection_name,
            distance_strategy=distance_strategy_map.get(self.distance_strategy, DistanceStrategy.COSINE),
        )

        # Add documents if provided
        if self.ingest_data:
            from langchain_core.documents import Document
            import json
            import pandas as pd

            documents = []
            for data in self.ingest_data:
                if isinstance(data, Data):
                    doc = data.to_lc_document()
                    # Ensure metadata is a simple dict
                    doc.metadata = {}
                    documents.append(doc)
                elif isinstance(data, Document):
                    # Clear metadata to avoid serialization issues
                    data.metadata = {}
                    documents.append(data)
                elif isinstance(data, pd.DataFrame):
                    # Handle pandas DataFrame - convert each row to a document
                    for _, row in data.iterrows():
                        text_parts = []
                        for val in row.values:
                            try:
                                if pd.notna(val):
                                    text_parts.append(str(val))
                            except (ValueError, TypeError):
                                # Handle arrays or other non-scalar values
                                text_parts.append(str(val))
                        text = ' '.join(text_parts)
                        doc = Document(page_content=text, metadata={})
                        documents.append(doc)
                elif isinstance(data, pd.Series):
                    # Handle pandas Series - convert each value to a document
                    for val in data:
                        try:
                            if pd.notna(val):
                                doc = Document(page_content=str(val), metadata={})
                                documents.append(doc)
                        except (ValueError, TypeError):
                            # Handle arrays or other non-scalar values
                            doc = Document(page_content=str(val), metadata={})
                            documents.append(doc)
                elif isinstance(data, dict):
                    # Handle JSON/dict objects
                    text = json.dumps(data) if not isinstance(data.get('text'), str) else data.get('text', json.dumps(data))
                    doc = Document(page_content=text, metadata={})
                    documents.append(doc)
                elif hasattr(data, 'text'):
                    # Handle Message or any object with text attribute
                    doc = Document(page_content=data.text, metadata={})
                    documents.append(doc)
                elif isinstance(data, str):
                    # Handle plain strings
                    doc = Document(page_content=data, metadata={})
                    documents.append(doc)

            if documents:
                vector_store.add_documents(documents)

        return vector_store

    def search_documents(self) -> list[Data]:
        """Perform similarity search and return results."""
        vector_store = self.build_vector_store()

        if not self.search_query:
            return []

        if self.search_type == "Similarity":
            docs = vector_store.similarity_search(
                query=self.search_query,
                k=self.number_of_results,
            )
        else:  # MMR
            docs = vector_store.max_marginal_relevance_search(
                query=self.search_query,
                k=self.number_of_results,
            )

        return docs_to_data(docs)

    def build(self) -> DB2VS | list[Data]:
        """Build the component and return either the vector store or search results."""
        if self.search_query:
            return self.search_documents()
        return self.build_vector_store()

# Made with Bob
