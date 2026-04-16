#!/bin/bash
# DB2 Integration Diagnostic Script

echo "================================================"
echo "  DB2 Integration Diagnostics"
echo "================================================"
echo ""

# Check if backend is running
echo "1. Checking if backend is running..."
if curl -s http://localhost:7860/health > /dev/null 2>&1; then
    echo "   ✓ Backend is running on port 7860"
elif curl -s http://localhost:7863/health > /dev/null 2>&1; then
    echo "   ⚠️  Backend is running on port 7863 (should be 7860)"
    echo "   Frontend expects port 7860!"
else
    echo "   ✗ Backend is NOT running"
    echo "   Please start with: ./run_db2_integration.sh"
fi
echo ""

# Check component files exist
echo "2. Checking component files..."
if [ -f "src/lfx/src/lfx/components/db2/__init__.py" ]; then
    echo "   ✓ db2/__init__.py exists"
else
    echo "   ✗ db2/__init__.py missing"
fi

if [ -f "src/lfx/src/lfx/components/db2/db2_sql.py" ]; then
    echo "   ✓ db2_sql.py exists"
else
    echo "   ✗ db2_sql.py missing"
fi

if [ -f "src/lfx/src/lfx/components/db2/db2_vector.py" ]; then
    echo "   ✓ db2_vector.py exists"
else
    echo "   ✗ db2_vector.py missing"
fi
echo ""

# Check Python imports
echo "3. Testing Python imports..."
source .venv/bin/activate 2>/dev/null
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("src/lfx/src")))

try:
    from lfx.components.db2 import DB2SQLComponent, DB2VectorStoreComponent
    print("   ✓ Components import successfully")
    print(f"   - DB2SQLComponent: {DB2SQLComponent.display_name}")
    print(f"   - DB2VectorStoreComponent: {DB2VectorStoreComponent.display_name}")
except Exception as e:
    print(f"   ✗ Import failed: {e}")
EOF
echo ""

# Check API endpoint
echo "4. Checking API for DB2 components..."
if curl -s http://localhost:7860/api/v1/all > /dev/null 2>&1; then
    DB2_COUNT=$(curl -s http://localhost:7860/api/v1/all | python3 -c "import sys, json; d=json.load(sys.stdin); print(len([k for k in d.keys() if 'db2' in k.lower()]))")
    if [ "$DB2_COUNT" -gt 0 ]; then
        echo "   ✓ Found $DB2_COUNT DB2 components in API"
    else
        echo "   ✗ No DB2 components found in API"
        echo "   Backend needs restart with: ./run_db2_integration.sh"
    fi
else
    echo "   ✗ Cannot reach API endpoint"
    echo "   Is backend running?"
fi
echo ""

echo "================================================"
echo "Summary:"
echo "================================================"
echo "If backend is NOT running or on wrong port:"
echo "  → Run: ./run_db2_integration.sh"
echo ""
echo "If components don't appear after backend restart:"
echo "  → Check backend logs for import errors"
echo "  → Verify langchain-db2 is installed: pip list | grep langchain-db2"
echo ""

# Made with Bob
