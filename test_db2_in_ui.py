"""Test if DB2 components are properly registered and can be loaded."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    sys.path.insert(0, str(Path(__file__).parent / "src" / "lfx" / "src"))

    from lfx.components import _dynamic_imports
    from lfx.components.db2 import DB2SQLComponent, DB2VectorStoreComponent

    assert DB2SQLComponent.display_name == "IBM Db2 SQL"
    assert DB2VectorStoreComponent.display_name == "IBM Db2 Vector Store"
    assert DB2SQLComponent.icon == "DB2"
    assert DB2VectorStoreComponent.icon == "DB2"
    assert "db2" in _dynamic_imports

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Made with Bob
