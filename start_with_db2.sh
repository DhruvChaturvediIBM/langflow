#!/bin/bash

# Kill any existing Langflow processes
echo "Stopping existing Langflow processes..."
lsof -ti:7863,3000 | xargs kill -9 2>/dev/null

# Set environment variables for component discovery
export LFX_DEV=1
export LANGFLOW_AUTO_LOGIN=true
export LANGFLOW_PORT=7863

echo "Starting Langflow with DB2 components..."
echo "LFX_DEV=$LFX_DEV (enables dynamic component discovery)"
echo "LANGFLOW_AUTO_LOGIN=$LANGFLOW_AUTO_LOGIN"
echo "LANGFLOW_PORT=$LANGFLOW_PORT"
echo ""

cd "$(dirname "$0")"
source .venv/bin/activate

# Start backend only
echo "Starting backend on port 7863..."
langflow run --backend-only --port 7863 &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✓ Backend started successfully (PID: $BACKEND_PID)"

    # Test if DB2 components are loaded
    echo ""
    echo "Testing DB2 component discovery..."
    COMPONENT_COUNT=$(curl -s http://localhost:7863/api/v1/components 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(len(data))" 2>/dev/null)
    echo "Total components loaded: $COMPONENT_COUNT"

    DB2_FOUND=$(curl -s http://localhost:7863/api/v1/components 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); db2 = [k for k in data.keys() if 'db2' in k.lower() or 'DB2' in k]; print('YES' if db2 else 'NO')" 2>/dev/null)

    if [ "$DB2_FOUND" = "YES" ]; then
        echo "✓ DB2 components found in API!"
    else
        echo "✗ DB2 components NOT found in API"
        echo "  This might be normal - components may load on first access"
    fi
else
    echo "✗ Backend failed to start"
    exit 1
fi

echo ""
echo "=========================================="
echo "Backend running on: http://localhost:7863"
echo "=========================================="
echo ""
echo "To start frontend in another terminal:"
echo "  cd src/frontend"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop backend"
echo ""

# Wait for backend process
wait $BACKEND_PID

# Made with Bob
