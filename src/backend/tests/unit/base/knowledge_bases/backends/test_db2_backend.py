"""Tests for DB2Backend knowledge base integration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

if TYPE_CHECKING:
    from pathlib import Path

import pytest
from lfx.base.knowledge_bases.backends import BackendType, DB2Backend, create_backend


class TestDB2Backend:
    """Test suite for DB2Backend."""

    @pytest.fixture
    def mock_db2_connection(self):
        """Mock DB2 connection."""
        connection = MagicMock()
        cursor = MagicMock()
        cursor.fetchone.return_value = (10,)  # Mock count result
        cursor.fetchall.return_value = []
        connection.cursor.return_value = cursor
        return connection

    @pytest.fixture
    def backend_config(self):
        """Default backend config for testing."""
        return {
            "database_variable": "DB2_DATABASE",
            "hostname_variable": "DB2_HOSTNAME",
            "port": 50000,
            "username_variable": "DB2_USERNAME",
            "password_variable": "DB2_PASSWORD",  # pragma: allowlist secret
            "table_name": "TEST_VECTORS",
            "use_ssl": False,
            "distance_strategy": "COSINE",
        }

    def test_backend_type(self):
        """Test that DB2Backend has correct backend type."""
        assert DB2Backend.backend_type == BackendType.DB2

    def test_create_backend_db2(self, tmp_path: Path, backend_config):
        """Test creating a DB2Backend via the factory."""
        backend = create_backend(
            backend_type=BackendType.DB2,
            kb_name="test_kb",
            kb_path=tmp_path,
            backend_config=backend_config,
        )
        assert isinstance(backend, DB2Backend)
        assert backend.kb_name == "test_kb"
        assert backend.kb_path == tmp_path
        assert backend.backend_config == backend_config

    def test_create_backend_db2_string(self, tmp_path: Path, backend_config):
        """Test creating a DB2Backend via string identifier."""
        backend = create_backend(
            backend_type="db2",
            kb_name="test_kb",
            kb_path=tmp_path,
            backend_config=backend_config,
        )
        assert isinstance(backend, DB2Backend)

    @pytest.mark.asyncio
    async def test_resolve_secrets(self, tmp_path: Path, backend_config):
        """Test secret resolution."""
        backend = DB2Backend(
            kb_name="test_kb",
            kb_path=tmp_path,
            backend_config=backend_config,
        )

        # Mock the resolve_required_secret method
        with patch.object(backend, "resolve_required_secret", new_callable=AsyncMock) as mock_resolve:
            mock_resolve.side_effect = lambda var: f"resolved_{var}"

            await backend._resolve_secrets()

            assert backend._resolved_database == "resolved_DB2_DATABASE"
            assert backend._resolved_hostname == "resolved_DB2_HOSTNAME"
            assert backend._resolved_username == "resolved_DB2_USERNAME"
            assert backend._resolved_password == "resolved_DB2_PASSWORD"  # noqa: S105  # pragma: allowlist secret
            assert backend._resolved_use_ssl is False

    @pytest.mark.asyncio
    async def test_count(self, tmp_path: Path, backend_config, mock_db2_connection):
        """Test document count."""
        backend = DB2Backend(
            kb_name="test_kb",
            kb_path=tmp_path,
            backend_config=backend_config,
        )

        # Mock the connection
        backend._db2_connection = mock_db2_connection
        backend._db2_table_name = "TEST_VECTORS"

        count = await backend.count()
        assert count == 10
        mock_db2_connection.cursor.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_error_handling(self, tmp_path: Path, backend_config):
        """Test count error handling."""
        backend = DB2Backend(
            kb_name="test_kb",
            kb_path=tmp_path,
            backend_config=backend_config,
        )

        # Mock connection that raises an error
        mock_connection = MagicMock()
        mock_connection.cursor.side_effect = Exception("Connection failed")
        backend._db2_connection = mock_connection
        backend._db2_table_name = "TEST_VECTORS"

        count = await backend.count()
        assert count == 0  # Should return 0 on error

    @pytest.mark.asyncio
    async def test_test_connection_success(self, tmp_path: Path, backend_config):
        """Test successful connection test."""
        backend = DB2Backend(
            kb_name="test_kb",
            kb_path=tmp_path,
            backend_config=backend_config,
        )

        # Mock successful secret resolution and connection
        with (
            patch.object(backend, "_resolve_secrets", new_callable=AsyncMock),
            patch.object(backend, "_build_vector_store"),
        ):
            backend._resolved_database = "testdb"
            backend._resolved_hostname = "localhost"
            backend._resolved_port = 50000
            backend._resolved_username = "testuser"
            backend._resolved_password = "testpass"  # noqa: S105  # pragma: allowlist secret

            # Mock ibm_db_dbi.connect
            with patch("ibm_db_dbi.connect") as mock_connect:
                mock_connection = MagicMock()
                mock_cursor = MagicMock()
                mock_cursor.fetchone.return_value = (1,)
                mock_connection.cursor.return_value = mock_cursor
                mock_connect.return_value = mock_connection

                result = await backend.test_connection()

                assert result.ok is True
            assert "testdb" in result.message
            assert "localhost" in result.message

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, tmp_path: Path, backend_config):
        """Test failed connection test."""
        backend = DB2Backend(
            kb_name="test_kb",
            kb_path=tmp_path,
            backend_config=backend_config,
        )

        # Mock failed secret resolution
        with patch.object(backend, "_resolve_secrets", new_callable=AsyncMock) as mock_resolve:
            mock_resolve.side_effect = ValueError("Missing credentials")

            result = await backend.test_connection()

            assert result.ok is False
            assert "Missing credentials" in result.message

    @pytest.mark.asyncio
    async def test_teardown(self, tmp_path: Path, backend_config, mock_db2_connection):
        """Test backend teardown."""
        backend = DB2Backend(
            kb_name="test_kb",
            kb_path=tmp_path,
            backend_config=backend_config,
        )

        backend._db2_connection = mock_db2_connection
        backend._vector_store = MagicMock()

        await backend.teardown()

        assert backend._db2_connection is None
        assert backend._vector_store is None

    def test_required_config_validation(self, tmp_path: Path):
        """Test that missing required config raises error."""
        backend = DB2Backend(
            kb_name="test_kb",
            kb_path=tmp_path,
            backend_config={},  # Empty config
        )

        with pytest.raises(ValueError, match="requires"):
            backend._required("table_name")

    @pytest.mark.asyncio
    async def test_storage_size_bytes(self, tmp_path: Path, backend_config):
        """Test storage size calculation (returns 0 for DB2)."""
        backend = DB2Backend(
            kb_name="test_kb",
            kb_path=tmp_path,
            backend_config=backend_config,
        )

        size = await backend.storage_size_bytes()
        assert size == 0  # DB2 backend returns 0 as placeholder


# Made with Bob
