"""IBM Db2 components for Langflow."""

from .db2_sql import DB2SQLComponent
from .db2_vector import DB2VectorStoreComponent

__all__ = ["DB2SQLComponent", "DB2VectorStoreComponent"]

# Dynamic imports mapping for component discovery
_dynamic_imports = {
    "DB2SQLComponent": "db2_sql",
    "DB2VectorStoreComponent": "db2_vector",
}

# Made with Bob
