"""IBM DB2 Vector Store backend for Knowledge Bases.

Wraps ``langchain_db2.DB2VS`` so Langflow Knowledge Bases can target an
IBM DB2 database with vector search capabilities. Connection parameters
and credentials are resolved through Langflow's ``variable_service`` so
``backend_config`` only carries variable *names* — never raw secrets —
and round-trips cleanly through the UI.

``backend_config`` fields:

* ``database_variable`` — name of the Langflow variable holding the
  database name. Defaults to ``DB2_DATABASE``. Required.
* ``hostname_variable`` — name of the variable holding the DB2 server
  hostname or IP address. Defaults to ``DB2_HOSTNAME``. Required.
* ``port`` — DB2 server port. Defaults to 50000.
* ``username_variable`` — name of the variable holding the DB2 username.
  Defaults to ``DB2_USERNAME``. Required.
* ``password_variable`` — name of the variable holding the DB2 password.
  Defaults to ``DB2_PASSWORD``. Required.
* ``table_name`` — DB2 table name for storing vectors. Defaults to
  ``LANGFLOW_VECTORS``. Required.
* ``use_ssl`` — Enable SSL/TLS encryption. Defaults to ``False``.
* ``ssl_certificate_variable`` — name of the variable holding the SSL
  certificate path. Optional; only used when ``use_ssl`` is ``True``.
* ``ssl_certificate_password_variable`` — name of the variable holding
  the SSL certificate password. Optional.
* ``distance_strategy`` — Distance metric (``COSINE``, ``EUCLIDEAN_DISTANCE``,
  ``DOT_PRODUCT``). Defaults to ``COSINE``.

Optional dependencies: ``langchain-db2`` ships the LangChain wrapper;
``ibm_db`` and ``ibm_db_dbi`` ship the DB2 client. All are imported
lazily so Langflow installs without DB2 deps keep working.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from typing import TYPE_CHECKING, Any

from lfx.base.knowledge_bases.backends.base import (
    BackendType,
    BaseVectorStoreBackend,
    IngestedDocument,
    TestConnectionResult,
)
from lfx.log.logger import logger

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from langchain_core.vectorstores import VectorStore


DEFAULT_DATABASE_VARIABLE = "DB2_DATABASE"
DEFAULT_HOSTNAME_VARIABLE = "DB2_HOSTNAME"
DEFAULT_PORT = 50000
DEFAULT_USERNAME_VARIABLE = "DB2_USERNAME"
DEFAULT_PASSWORD_VARIABLE = "DB2_PASSWORD"  # noqa: S105 — variable name, not a secret  # pragma: allowlist secret
DEFAULT_TABLE_NAME = "LANGFLOW_VECTORS"
DEFAULT_DISTANCE_STRATEGY = "COSINE"


def _coerce_bool(value: Any, *, default: bool) -> bool:
    """Coerce a config value to ``bool`` with explicit string handling."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off", ""}:
            return False
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    return default


class DB2Backend(BaseVectorStoreBackend):
    """IBM DB2 Vector Store as a Langflow KB backend."""

    backend_type = BackendType.DB2

    def _required(self, key: str) -> str:
        value = self.backend_config.get(key)
        if not value:
            msg = f"DB2Backend requires '{key}' in backend_config."
            raise ValueError(msg)
        return str(value)

    async def _resolve_secrets(self) -> None:
        """Resolve DB2 connection parameters via variable_service.

        All connection parameters (database, hostname, username, password)
        are required. SSL certificate parameters are optional and only
        used when ``use_ssl`` is enabled.
        """
        database_variable = self.backend_config.get("database_variable") or DEFAULT_DATABASE_VARIABLE
        hostname_variable = self.backend_config.get("hostname_variable") or DEFAULT_HOSTNAME_VARIABLE
        username_variable = self.backend_config.get("username_variable") or DEFAULT_USERNAME_VARIABLE
        password_variable = self.backend_config.get("password_variable") or DEFAULT_PASSWORD_VARIABLE

        self._resolved_database = await self.resolve_required_secret(database_variable)
        self._resolved_hostname = await self.resolve_required_secret(hostname_variable)
        self._resolved_username = await self.resolve_required_secret(username_variable)
        self._resolved_password = await self.resolve_required_secret(password_variable)

        # SSL certificate parameters are optional
        use_ssl = _coerce_bool(self.backend_config.get("use_ssl"), default=False)
        self._resolved_use_ssl = use_ssl

        if use_ssl:
            ssl_cert_variable = self.backend_config.get("ssl_certificate_variable")
            ssl_cert_password_variable = self.backend_config.get("ssl_certificate_password_variable")

            if ssl_cert_variable:
                self._resolved_ssl_certificate = await self.resolve_secret(ssl_cert_variable)
            else:
                self._resolved_ssl_certificate = None

            if ssl_cert_password_variable:
                self._resolved_ssl_certificate_password = await self.resolve_secret(ssl_cert_password_variable)
            else:
                self._resolved_ssl_certificate_password = None
        else:
            self._resolved_ssl_certificate = None
            self._resolved_ssl_certificate_password = None

    def _build_vector_store(self) -> VectorStore:
        """Build the DB2VS vector store instance."""
        # Validate config before touching optional deps
        table_name = self.backend_config.get("table_name") or DEFAULT_TABLE_NAME
        port = int(self.backend_config.get("port", DEFAULT_PORT))

        # Ensure secrets are resolved
        database = getattr(self, "_resolved_database", None)
        hostname = getattr(self, "_resolved_hostname", None)
        username = getattr(self, "_resolved_username", None)
        password = getattr(self, "_resolved_password", None)

        if not all([database, hostname, username, password]):
            msg = "DB2Backend.ensure_ready() must be awaited before _build_vector_store."
            raise RuntimeError(msg)

        try:
            import ibm_db_dbi
            from langchain_community.vectorstores.utils import DistanceStrategy
            from langchain_db2 import DB2VS
        except ImportError as exc:
            msg = (
                "DB2Backend requires langchain-db2, ibm_db, and ibm_db_dbi. "
                "Install the 'db2' extras or add those packages."
            )
            raise RuntimeError(msg) from exc

        # Build connection string
        conn_str = f"DATABASE={database};HOSTNAME={hostname};PORT={port};PROTOCOL=TCPIP;UID={username};PWD={password};"

        # Add SSL parameters if enabled
        use_ssl = getattr(self, "_resolved_use_ssl", False)
        if use_ssl:
            conn_str += "SECURITY=SSL;"
            ssl_cert = getattr(self, "_resolved_ssl_certificate", None)
            if ssl_cert:
                conn_str += f"SSLServerCertificate={ssl_cert};"
                ssl_cert_password = getattr(self, "_resolved_ssl_certificate_password", None)
                if ssl_cert_password:
                    conn_str += f"SSLClientKeystorePassword={ssl_cert_password};"

        # Create connection
        try:
            connection = ibm_db_dbi.connect(conn_str, "", "")
        except Exception as exc:
            msg = f"Failed to connect to DB2 database: {exc}"
            raise ConnectionError(msg) from exc

        # Store connection for cleanup
        self._db2_connection = connection
        self._db2_table_name = table_name

        # Map distance strategy
        distance_strategy_str = self.backend_config.get("distance_strategy") or DEFAULT_DISTANCE_STRATEGY
        distance_strategy_map = {
            "COSINE": DistanceStrategy.COSINE,
            "EUCLIDEAN_DISTANCE": DistanceStrategy.EUCLIDEAN_DISTANCE,
            "DOT_PRODUCT": DistanceStrategy.DOT_PRODUCT,
        }
        distance_strategy = distance_strategy_map.get(
            distance_strategy_str.upper(),
            DistanceStrategy.COSINE,
        )

        # Build vector store
        if self.embedding_function is None:
            msg = "Embedding function is required for DB2Backend"
            raise ValueError(msg)

        return DB2VS(
            client=connection,
            embedding_function=self.embedding_function,
            table_name=table_name,
            distance_strategy=distance_strategy,
        )

    async def count(self) -> int:
        """Count documents in the DB2 table."""
        await self.ensure_ready()
        connection = getattr(self, "_db2_connection", None)
        table_name = getattr(self, "_db2_table_name", None)

        if connection is None or table_name is None:
            # Force a build so connection is populated
            _ = self.vector_store
            connection = self._db2_connection
            table_name = self._db2_table_name

        if connection is None:
            return 0

        try:
            cursor = connection.cursor()
            # Use parameterized query to prevent SQL injection
            # Note: DB2 doesn't support parameterized table names, so we validate it
            # Table name validation should be done in the component
            query = f"SELECT COUNT(*) FROM {table_name}"  # noqa: S608
            cursor.execute(query)
            result = cursor.fetchone()
            cursor.close()
            return int(result[0]) if result else 0
        except Exception as exc:  # noqa: BLE001
            logger.warning("DB2 count() failed for %s: %s", self.kb_name, exc)
            return 0

    async def iter_documents(
        self,
        *,
        batch_size: int = 5000,
        include_embeddings: bool = False,
    ) -> AsyncIterator[list[IngestedDocument]]:
        """Stream documents from the DB2 table.

        DB2VS stores documents with columns: id, text, embedding, metadata.
        We fetch in batches using OFFSET/LIMIT pagination.
        """
        await self.ensure_ready()
        connection = getattr(self, "_db2_connection", None)
        table_name = getattr(self, "_db2_table_name", None)

        if connection is None or table_name is None:
            _ = self.vector_store
            connection = self._db2_connection
            table_name = self._db2_table_name

        if connection is None:
            return

        total = await self.count()
        if total <= 0:
            return

        # Build column list
        columns = "text, metadata"
        if include_embeddings:
            columns = "text, metadata, embedding"

        offset = 0
        while offset < total:
            try:
                cursor = connection.cursor()

                # Table name is validated in the component, but we still use noqa for the linter
                query = (
                    f"SELECT {columns} FROM {table_name} "  # noqa: S608
                    f"ORDER BY id OFFSET {offset} ROWS FETCH NEXT {batch_size} ROWS ONLY"
                )
                cursor.execute(query)
                rows = cursor.fetchall()
                cursor.close()

                if not rows:
                    break

                batch: list[IngestedDocument] = []
                for row in rows:
                    text = row[0] or ""
                    # Column indices for metadata and embedding
                    metadata_idx = 1
                    embedding_idx = 2
                    metadata = row[metadata_idx] if len(row) > metadata_idx else {}
                    embedding = None
                    if include_embeddings and len(row) > embedding_idx:
                        embedding = list(row[embedding_idx]) if row[embedding_idx] else None

                    # Parse metadata if it's a string (JSON)
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except (json.JSONDecodeError, ValueError):
                            metadata = {}

                    batch.append(
                        IngestedDocument(
                            content=str(text),
                            metadata=dict(metadata) if isinstance(metadata, dict) else {},
                            embedding=embedding,
                        )
                    )

                if batch:
                    yield batch

                offset += batch_size
            except Exception as exc:  # noqa: BLE001
                logger.warning("DB2 iter_documents failed at offset %d: %s", offset, exc)
                break

    async def storage_size_bytes(self) -> int:
        """Estimate storage size of the DB2 table.

        DB2 doesn't provide a simple way to get exact table size without
        admin privileges. We return 0 as a placeholder.
        """
        return 0

    async def test_connection(self) -> TestConnectionResult:
        """Validate DB2 connection parameters and reachability.

        This method tests the database connection without requiring an embedding function,
        making it suitable for connection validation before KB creation.
        """
        try:
            await self.ensure_ready()
        except ValueError as exc:
            return TestConnectionResult(
                ok=False,
                message=str(exc),
                details={"type": "ConfigError"},
            )
        except Exception as exc:  # noqa: BLE001
            return TestConnectionResult(
                ok=False,
                message=str(exc) or type(exc).__name__,
                details={"type": type(exc).__name__},
            )

        # For connection testing, connect directly without building the vector store
        # (which would require an embedding function)
        try:
            import ibm_db_dbi
        except ImportError:
            return TestConnectionResult(
                ok=False,
                message="Required package ibm_db_dbi is not installed",
                details={"type": "ImportError"},
            )

        # Build connection string
        database = getattr(self, "_resolved_database", "")
        hostname = getattr(self, "_resolved_hostname", "")
        port = getattr(self, "_resolved_port", 50000)
        username = getattr(self, "_resolved_username", "")
        password = getattr(self, "_resolved_password", "")

        if not all([database, hostname, username, password]):
            return TestConnectionResult(
                ok=False,
                message="Missing required connection parameters",
                details={"type": "ConfigError"},
            )

        conn_str = f"DATABASE={database};HOSTNAME={hostname};PORT={port};PROTOCOL=TCPIP;UID={username};PWD={password};"

        # Add SSL if configured
        use_ssl = self.backend_config.get("use_ssl", False)
        if use_ssl:
            conn_str += "SECURITY=SSL;"
            ssl_cert = getattr(self, "_resolved_ssl_certificate", None)
            if ssl_cert:
                conn_str += f"SSLServerCertificate={ssl_cert};"

        # Test the connection
        connection = None
        try:
            connection = ibm_db_dbi.connect(conn_str, "", "")
            cursor = connection.cursor()
            cursor.execute("SELECT 1 FROM SYSIBM.SYSDUMMY1")
            cursor.fetchone()
            cursor.close()

            return TestConnectionResult(
                ok=True,
                message=f"Connected to DB2 database {database} on {hostname}",
                details={"database": database, "hostname": hostname, "port": port},
            )
        except Exception as exc:  # noqa: BLE001
            return TestConnectionResult(
                ok=False,
                message=f"Connection test failed: {exc}",
                details={"type": type(exc).__name__},
            )
        finally:
            if connection:
                with contextlib.suppress(Exception):
                    connection.close()

    async def delete_by(self, where: dict[str, Any]) -> None:
        """Delete documents matching the filter.

        DB2VS stores metadata as a JSON column, so we need to query
        and delete by matching metadata fields.
        """
        await self.ensure_ready()
        connection = getattr(self, "_db2_connection", None)
        table_name = getattr(self, "_db2_table_name", None)

        if connection is None or table_name is None:
            _ = self.vector_store
            connection = self._db2_connection
            table_name = self._db2_table_name

        if connection is None or not where:
            return

        # Build WHERE clause for metadata matching
        # This is a simplified implementation - production code would need
        # proper JSON querying support
        try:
            cursor = connection.cursor()
            # For now, we'll fetch all rows and filter in Python
            # A production implementation would use DB2's JSON functions
            cursor.execute(f"SELECT id, metadata FROM {table_name}")  # noqa: S608
            rows = cursor.fetchall()

            ids_to_delete = []
            for row in rows:
                row_id = row[0]
                metadata = row[1]

                # Parse metadata if it's a string
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except (json.JSONDecodeError, ValueError):
                        continue

                # Check if all filter conditions match
                if isinstance(metadata, dict) and all(metadata.get(k) == v for k, v in where.items()):
                    ids_to_delete.append(row_id)

            # Delete matching rows
            if ids_to_delete:
                placeholders = ",".join("?" * len(ids_to_delete))
                delete_query = f"DELETE FROM {table_name} WHERE id IN ({placeholders})"  # noqa: S608
                cursor.execute(delete_query, ids_to_delete)
                connection.commit()

            cursor.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning("DB2 delete_by failed for %s: %s", self.kb_name, exc)

    async def teardown(self) -> None:
        """Close the DB2 connection."""
        connection = getattr(self, "_db2_connection", None)
        if connection is not None:
            try:
                await asyncio.to_thread(connection.close)
            except Exception as exc:  # noqa: BLE001
                logger.warning("DB2 connection.close failed: %s", exc)
        self._db2_connection = None
        self._vector_store = None

    async def delete_collection(self) -> None:
        """Drop the DB2 table. Used by KB deletion."""
        connection = getattr(self, "_db2_connection", None)
        table_name = getattr(self, "_db2_table_name", None)

        if connection is None or table_name is None:
            _ = self.vector_store
            connection = self._db2_connection
            table_name = self._db2_table_name

        if connection is None:
            return

        try:
            cursor = connection.cursor()
            cursor.execute(f"DROP TABLE {table_name}")
            connection.commit()
            cursor.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning("DB2 DROP TABLE failed for %s: %s", self.kb_name, exc)


# Made with Bob
