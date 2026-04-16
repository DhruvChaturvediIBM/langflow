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
            display_name="Collection Name",
            required=True,
            info="Name of the vector collection/table",
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
            input_types=["Data"],
            is_list=True,
            info="Documents to ingest into the vector store (connect from text splitters or file loaders)",
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
            options=["COSINE", "EUCLIDEAN", "DOT_PRODUCT"],
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
            "EUCLIDEAN": DistanceStrategy.EUCLIDEAN,
            "DOT_PRODUCT": DistanceStrategy.DOT_PRODUCT,
        }

        # Build vector store
        vector_store = DB2VS(
            connection=connection,
            embedding=self.embedding,
            collection_name=self.collection_name,
            distance_strategy=distance_strategy_map.get(self.distance_strategy, DistanceStrategy.COSINE),
        )

        # Add documents if provided
        if self.ingest_data:
            from langchain_core.documents import Document

            documents = []
            for data in self.ingest_data:
                if isinstance(data, Data):
                    doc = data.to_lc_document()
                    documents.append(doc)
                elif isinstance(data, Document):
                    documents.append(data)

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
        """Build the component - returns vector store or search results."""
        if self.search_query:
            return self.search_documents()
        return self.build_vector_store()


# Made with Bob
