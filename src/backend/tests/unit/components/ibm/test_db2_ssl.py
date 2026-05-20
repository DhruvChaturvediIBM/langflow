"""Unit tests for DB2 SSL/TLS support."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from lfx.components.ibm.db2_sql import DB2SQLComponent
from lfx.components.ibm.db2_vector import DB2VectorStoreComponent


class TestDB2SSLSupport:
    """Test SSL/TLS support for DB2 components."""

    @pytest.fixture
    def sql_component(self):
        """Create a DB2SQLComponent instance with valid inputs."""
        comp = DB2SQLComponent()
        comp.database = "TESTDB"
        comp.hostname = "localhost"
        comp.port = 50000
        comp.username = "testuser"
        comp.password = "testpass"  # noqa: S105  # pragma: allowlist secret
        comp.sql_query = "SELECT * FROM users"
        comp.max_rows = 100
        comp.read_only_mode = True
        comp.query_timeout = 30
        comp.enable_ssl = True
        comp.ssl_certificate_path = ""
        return comp

    @pytest.fixture
    def vector_component(self):
        """Create a DB2VectorStoreComponent instance with valid inputs."""
        comp = DB2VectorStoreComponent()
        comp.collection_name = "test_vectors"
        comp.database = "TESTDB"
        comp.hostname = "localhost"
        comp.port = 50000
        comp.username = "testuser"
        comp.password = "testpass"  # noqa: S105  # pragma: allowlist secret
        comp.search_type = "Similarity"
        comp.number_of_results = 4
        comp.distance_strategy = "COSINE"
        comp.allow_duplicates = True
        comp.should_cache_vector_store = False
        comp.enable_ssl = True
        comp.ssl_certificate_path = ""
        return comp

    @pytest.fixture
    def mock_embedding(self):
        """Create a mock embedding model."""
        embedding = Mock()
        embedding.embed_documents = Mock(return_value=[[0.1, 0.2, 0.3]])
        embedding.embed_query = Mock(return_value=[0.1, 0.2, 0.3])
        return embedding

    def test_sql_component_ssl_disabled(self, sql_component):
        """Test SQL component with SSL explicitly disabled."""
        # Explicitly disable SSL for this test
        sql_component.enable_ssl = False

        mock_ibm_db_dbi = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchmany.return_value = []
        mock_cursor.description = []
        mock_conn.cursor.return_value = mock_cursor
        mock_ibm_db_dbi.connect.return_value = mock_conn

        with patch.dict("sys.modules", {"ibm_db_dbi": mock_ibm_db_dbi}):
            sql_component.execute_query()

            # Verify connection string does not contain SSL parameters
            conn_str = mock_ibm_db_dbi.connect.call_args[0][0]
            assert "SECURITY=SSL" not in conn_str
            assert "SSLServerCertificate" not in conn_str

    def test_sql_component_ssl_enabled_without_certificate(self, sql_component):
        """Test SQL component with SSL enabled but no certificate path."""
        sql_component.enable_ssl = True
        sql_component.ssl_certificate_path = ""

        mock_ibm_db_dbi = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchmany.return_value = []
        mock_cursor.description = []
        mock_conn.cursor.return_value = mock_cursor
        mock_ibm_db_dbi.connect.return_value = mock_conn

        with patch.dict("sys.modules", {"ibm_db_dbi": mock_ibm_db_dbi}):
            sql_component.execute_query()

            # Verify connection string contains SSL but no certificate
            conn_str = mock_ibm_db_dbi.connect.call_args[0][0]
            assert "SECURITY=SSL;" in conn_str
            assert "SSLServerCertificate" not in conn_str

    def test_sql_component_ssl_enabled_with_certificate(self, sql_component):
        """Test SQL component with SSL enabled and certificate path."""
        sql_component.enable_ssl = True
        sql_component.ssl_certificate_path = "/path/to/cert.arm"

        mock_ibm_db_dbi = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchmany.return_value = []
        mock_cursor.description = []
        mock_conn.cursor.return_value = mock_cursor
        mock_ibm_db_dbi.connect.return_value = mock_conn

        with patch.dict("sys.modules", {"ibm_db_dbi": mock_ibm_db_dbi}):
            sql_component.execute_query()

            # Verify connection string contains SSL and certificate
            conn_str = mock_ibm_db_dbi.connect.call_args[0][0]
            assert "SECURITY=SSL;" in conn_str
            assert "SSLServerCertificate=/path/to/cert.arm;" in conn_str

    def test_vector_component_ssl_disabled(self, vector_component, mock_embedding):
        """Test vector component with SSL explicitly disabled."""
        # Explicitly disable SSL for this test
        vector_component.enable_ssl = False
        vector_component.embedding = mock_embedding

        mock_ibm_db_dbi = MagicMock()
        mock_conn = MagicMock()
        mock_ibm_db_dbi.connect.return_value = mock_conn

        with (
            patch.dict("sys.modules", {"ibm_db_dbi": mock_ibm_db_dbi}),
            patch("lfx.components.ibm.db2vs.DB2VS") as mock_db2vs,
        ):
            mock_db2vs.return_value = MagicMock()
            vector_component.build_vector_store()

            # Verify connection string does not contain SSL parameters
            conn_str = mock_ibm_db_dbi.connect.call_args[0][0]
            assert "SECURITY=SSL" not in conn_str
            assert "SSLServerCertificate" not in conn_str

    def test_vector_component_ssl_enabled_without_certificate(self, vector_component, mock_embedding):
        """Test vector component with SSL enabled but no certificate path."""
        vector_component.embedding = mock_embedding
        vector_component.enable_ssl = True
        vector_component.ssl_certificate_path = ""

        mock_ibm_db_dbi = MagicMock()
        mock_conn = MagicMock()
        mock_ibm_db_dbi.connect.return_value = mock_conn

        with (
            patch.dict("sys.modules", {"ibm_db_dbi": mock_ibm_db_dbi}),
            patch("lfx.components.ibm.db2vs.DB2VS") as mock_db2vs,
        ):
            mock_db2vs.return_value = MagicMock()
            vector_component.build_vector_store()

            # Verify connection string contains SSL but no certificate
            conn_str = mock_ibm_db_dbi.connect.call_args[0][0]
            assert "SECURITY=SSL;" in conn_str
            assert "SSLServerCertificate" not in conn_str

    def test_vector_component_ssl_enabled_with_certificate(self, vector_component, mock_embedding):
        """Test vector component with SSL enabled and certificate path."""
        vector_component.embedding = mock_embedding
        vector_component.enable_ssl = True
        vector_component.ssl_certificate_path = "/path/to/cert.arm"

        mock_ibm_db_dbi = MagicMock()
        mock_conn = MagicMock()
        mock_ibm_db_dbi.connect.return_value = mock_conn

        with (
            patch.dict("sys.modules", {"ibm_db_dbi": mock_ibm_db_dbi}),
            patch("lfx.components.ibm.db2vs.DB2VS") as mock_db2vs,
        ):
            mock_db2vs.return_value = MagicMock()
            vector_component.build_vector_store()

            # Verify connection string contains SSL and certificate
            conn_str = mock_ibm_db_dbi.connect.call_args[0][0]
            assert "SECURITY=SSL;" in conn_str
            assert "SSLServerCertificate=/path/to/cert.arm;" in conn_str

    def test_ssl_connection_failure_handling(self, sql_component):
        """Test handling of SSL connection failures."""
        sql_component.enable_ssl = True
        sql_component.ssl_certificate_path = "/invalid/path/cert.arm"

        mock_ibm_db_dbi = MagicMock()
        # Create a proper exception class
        mock_ibm_db_dbi.DatabaseError = type("DatabaseError", (Exception,), {})
        mock_ibm_db_dbi.connect.side_effect = mock_ibm_db_dbi.DatabaseError("SSL certificate not found")

        with (
            patch.dict("sys.modules", {"ibm_db_dbi": mock_ibm_db_dbi}),
            pytest.raises(RuntimeError, match="Database operation failed"),
        ):
            sql_component.execute_query()

    def test_ssl_certificate_path_validation(self, sql_component):
        """Test that SSL certificate path is properly included in connection string."""
        test_paths = [
            "/path/to/cert.arm",
            "/usr/local/certs/db2cert.arm",
            "C:\\certs\\db2.arm",
            "./relative/path/cert.arm",
        ]

        for cert_path in test_paths:
            sql_component.enable_ssl = True
            sql_component.ssl_certificate_path = cert_path

            mock_ibm_db_dbi = MagicMock()
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.fetchmany.return_value = []
            mock_cursor.description = []
            mock_conn.cursor.return_value = mock_cursor
            mock_ibm_db_dbi.connect.return_value = mock_conn

            with patch.dict("sys.modules", {"ibm_db_dbi": mock_ibm_db_dbi}):
                sql_component.execute_query()

                # Verify certificate path is in connection string
                conn_str = mock_ibm_db_dbi.connect.call_args[0][0]
                assert f"SSLServerCertificate={cert_path};" in conn_str

    def test_ssl_with_all_connection_parameters(self, sql_component):
        """Test SSL works correctly with all connection parameters."""
        sql_component.enable_ssl = True
        sql_component.ssl_certificate_path = "/path/to/cert.arm"
        sql_component.database = "PRODDB"
        sql_component.hostname = "db2.example.com"
        sql_component.port = 50001
        sql_component.username = "produser"
        sql_component.password = "prodpass"  # noqa: S105  # pragma: allowlist secret

        mock_ibm_db_dbi = MagicMock()
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchmany.return_value = []
        mock_cursor.description = []
        mock_conn.cursor.return_value = mock_cursor
        mock_ibm_db_dbi.connect.return_value = mock_conn

        with patch.dict("sys.modules", {"ibm_db_dbi": mock_ibm_db_dbi}):
            sql_component.execute_query()

            # Verify all parameters are in connection string
            conn_str = mock_ibm_db_dbi.connect.call_args[0][0]
            assert "DATABASE=PRODDB;" in conn_str
            assert "HOSTNAME=db2.example.com;" in conn_str
            assert "PORT=50001;" in conn_str
            assert "PROTOCOL=TCPIP;" in conn_str
            assert "UID=produser;" in conn_str
            assert "PWD=prodpass;" in conn_str
            assert "SECURITY=SSL;" in conn_str
            assert "SSLServerCertificate=/path/to/cert.arm;" in conn_str


# Made with Bob
