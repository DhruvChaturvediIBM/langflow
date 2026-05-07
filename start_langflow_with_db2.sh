#!/bin/bash

echo "🚀 Starting Langflow with DB2 Components"
echo "========================================"

# Navigate to langflow directory
cd "$(dirname "$0")"

# Activate virtual environment
source .venv/bin/activate

# Set auto-login to bypass authentication
export LANGFLOW_AUTO_LOGIN=true

# Remove old database to start fresh
if [ -f "langflow.db" ]; then
    echo "🗑️  Removing old database..."
    rm -f langflow.db
fi

# Ensure frontend is built
if [ ! -d "src/backend/base/langflow/frontend" ]; then
    echo "🏗️  Frontend not found. Building..."
    cd src/frontend
    npm install
    npm run build
    cd ../..
    cp -r src/frontend/build src/backend/base/langflow/frontend
    echo "✅ Frontend built successfully"
fi

echo ""
echo "🎯 Starting Langflow..."
echo "📍 URL: http://localhost:7863"
echo "🔍 Search for 'DB2' in the component panel"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run Langflow (NOT in backend-only mode)
langflow run

# Made with Bob
