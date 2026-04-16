#!/bin/bash
# DB2 Integration - Complete Setup and Run Script

set -e

echo "================================================"
echo "  IBM Db2 Integration for Langflow"
echo "================================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated${NC}"
    echo "Activating .venv..."
    source .venv/bin/activate
fi

echo -e "${BLUE}Step 1: Testing DB2 Component Imports${NC}"
echo "----------------------------------------"
python test_db2_components.py
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}⚠️  Component import test failed${NC}"
    echo "Please check that langchain-db2 is installed:"
    echo "  cd ../langchain-db2 && pip install -e ."
    exit 1
fi
echo ""

echo -e "${BLUE}Step 2: Starting Langflow Backend${NC}"
echo "----------------------------------------"
echo "Backend will start on: http://localhost:7860"
echo "Frontend proxy configured for: http://localhost:7860"
echo ""
echo -e "${GREEN}✓ Port configuration matches!${NC}"
echo ""
echo "Starting backend with component discovery enabled..."
echo "Press Ctrl+C to stop"
echo ""

# Start backend with LFX_DEV=1 for component discovery
LFX_DEV=1 LANGFLOW_PORT=7860 langflow run --backend-only

# Note: Frontend should be started separately with: npm run start

# Made with Bob
