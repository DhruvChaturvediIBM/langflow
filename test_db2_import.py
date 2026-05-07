"""Test script to verify DB2 components can be imported."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    src_path = Path(__file__).parent / "src" / "lfx" / "src"
    sys.path.insert(0, str(src_path))

    from lfx.components import DB2SQLComponent as DynamicSQL
    from lfx.components import DB2VectorStoreComponent as DynamicVector
    from lfx.components import db2
    from lfx.components.db2 import DB2SQLComponent
    from lfx.components.db2 import DB2VectorStoreComponent

    assert db2.__all__ == ["DB2SQLComponent", "DB2VectorStoreComponent"]
    assert DB2SQLComponent.display_name == "IBM Db2 SQL"
    assert DB2VectorStoreComponent.display_name == "IBM Db2 Vector Store"
    assert DynamicSQL is DB2SQLComponent
    assert DynamicVector is DB2VectorStoreComponent

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Made with Bob
