#!/bin/bash

################################################################################
# Vector Hybrid Search Demo Runner
################################################################################
# This script runs the vector ingestion and hybrid retrieval demonstration
#
# Usage:
#   ./run_demo.sh
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

################################################################################
# Main Script
################################################################################

clear

cat << "EOF"
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║          Vector Ingestion & Hybrid Retrieval Demo                   ║
║                                                                      ║
║                    IBM DB2 Vector Support                            ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

EOF

print_header "Running Vector Hybrid Search Demo"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    print_error "Virtual environment not found!"
    print_info "Please run ./start.sh first to set up the environment"
    exit 1
fi

# Check if DB2 config exists
if [ ! -f "$SCRIPT_DIR/db2_config.json" ]; then
    print_error "DB2 configuration file not found!"
    print_info "Please create db2_config.json with your DB2 credentials"
    print_info "You can use db2_config.example.json as a template"
    exit 1
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Check if demo script exists
if [ ! -f "$SCRIPT_DIR/vector_hybrid_search_demo.py" ]; then
    print_error "Demo script not found: vector_hybrid_search_demo.py"
    exit 1
fi

print_info "Starting demo..."
echo

# Run the demo
python "$SCRIPT_DIR/vector_hybrid_search_demo.py"

echo
print_success "Demo completed!"

# Made with Bob
