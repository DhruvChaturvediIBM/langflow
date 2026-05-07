"""Debug-oriented smoke test for DB2 vector store functionality."""

from __future__ import annotations

import contextlib
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent / "src" / "lfx" / "src"))


def main() -> int:
    from langchain_community.vectorstores.utils import DistanceStrategy
    from langchain_core.documents import Document
    from langchain_core.embeddings import Embeddings
    from langchain_db2.db2vs import DB2VS
    import ibm_db_dbi

    conn_str = "DATABASE=TESTDB;HOSTNAME=9.30.183.217;PORT=50000;PROTOCOL=TCPIP;UID=mohit29;PWD=Goku@2907;"
    connection = ibm_db_dbi.connect(conn_str, "", "")

    class SimpleEmbeddings(Embeddings):
        """Simple embeddings for testing."""

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            return [[0.1] * 384 for _ in texts]

        def embed_query(self, _: str) -> list[float]:
            return [0.1] * 384

    vector_store = DB2VS(
        client=connection,
        embedding_function=SimpleEmbeddings(),
        table_name="TEST_VECTORS",
        distance_strategy=DistanceStrategy.COSINE,
    )

    test_docs = [
        Document(page_content="This is a test document about databases", metadata={}),
        Document(page_content="Vector stores are useful for similarity search", metadata={}),
        Document(page_content="DB2 is an enterprise database system", metadata={}),
    ]
    vector_store.add_documents(test_docs)

    results = vector_store.similarity_search(query="database systems", k=2)
    assert len(results) == 2

    results_with_scores = vector_store.similarity_search_with_score(query="database systems", k=2)
    assert len(results_with_scores) == 2

    mmr_results = vector_store.max_marginal_relevance_search(query="database systems", k=2)
    assert len(mmr_results) == 2

    cleanup_table(connection, vector_store.table_name)
    with contextlib.suppress(Exception):
        connection.close()
    return 0


def cleanup_table(connection: Any, table_name: str) -> None:
    cursor = connection.cursor()
    try:
        quoted_table_name = quote_identifier(table_name)
        cursor.execute(f"DROP TABLE {quoted_table_name}")  # noqa: S608
        cursor.execute("COMMIT")
    finally:
        cursor.close()


def quote_identifier(identifier: str) -> str:
    if not identifier.replace("_", "").isalnum():
        msg = f"Unsafe identifier: {identifier}"
        raise ValueError(msg)
    return identifier


if __name__ == "__main__":
    raise SystemExit(main())

# Made with Bob
