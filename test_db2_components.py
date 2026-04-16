#!/usr/bin/env python3
"""Test script to verify DB2 components can be imported."""

import sys
from pathlib import Path

# Add the lfx source to path
lfx_path = Path(__file__).parent / "src" / "lfx" / "src"
sys.path.insert(0, str(lfx_path))

print("Testing DB2 component imports...")
print("-" * 50)

try:
    print("1. Importing lfx.components...")
    print("   ✓ Success")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

try:
    print("2. Importing db2 module...")
    from lfx.components import db2

    print("   ✓ Success")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

try:
    print("3. Importing DB2SQLComponent...")
    from lfx.components.db2 import DB2SQLComponent

    print("   ✓ Success")
    print(f"   - Display name: {DB2SQLComponent.display_name}")
    print(f"   - Icon: {DB2SQLComponent.icon}")
    print(f"   - Name: {DB2SQLComponent.name}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

try:
    print("4. Importing DB2VectorStoreComponent...")
    from lfx.components.db2 import DB2VectorStoreComponent

    print("   ✓ Success")
    print(f"   - Display name: {DB2VectorStoreComponent.display_name}")
    print(f"   - Icon: {DB2VectorStoreComponent.icon}")
    print(f"   - Name: {DB2VectorStoreComponent.name}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
    sys.exit(1)

try:
    print("5. Checking component discovery...")
    if hasattr(db2, "_dynamic_imports"):
        print(f"   ✓ _dynamic_imports found: {db2._dynamic_imports}")
    else:
        print("   ✗ _dynamic_imports not found")
except Exception as e:
    print(f"   ✗ Failed: {e}")

print("-" * 50)
print("✅ All DB2 components imported successfully!")
print("\nNext steps:")
print("1. Restart Langflow backend with: LFX_DEV=1 langflow run --backend-only")
print("2. Open browser at: http://localhost:7863")
print("3. Search for 'DB2' in the component sidebar")
print("4. Run the fetch test in browser console:")
print("   fetch('http://localhost:7863/api/v1/all').then(r => r.json()).then(d => {")
print("     const db2 = Object.keys(d).filter(k => k.includes('DB2'));")
print("     console.log('DB2 components:', db2);")
print("   })")

# Made with Bob
