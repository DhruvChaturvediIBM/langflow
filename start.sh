#!/bin/bash

################################################################################
# Langflow with DB2 Vector Support - Automated Setup & Start Script
################################################################################
# This script automates the complete setup and launch of Langflow with DB2
# vector store integration.
#
# Usage:
#   ./start.sh              # Full setup and start Langflow
#   ./start.sh --test       # Run test script instead of Langflow
#   ./start.sh --help       # Show help
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
LANGFLOW_DIR="$SCRIPT_DIR/langflow"
VENV_DIR="$LANGFLOW_DIR/.venv"

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

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "$1 is installed"
        return 0
    else
        print_error "$1 is not installed"
        return 1
    fi
}

################################################################################
# Main Functions
################################################################################

show_help() {
    cat << EOF
Langflow with DB2 Vector Support - Setup & Start Script

Usage:
    ./start.sh [OPTIONS]

Options:
    --help          Show this help message
    --clean         Clean install (remove existing venv)
    --skip-deps     Skip dependency installation
    --port PORT     Specify Langflow port (default: 7860)

Examples:
    ./start.sh                    # Full setup and start Langflow
    ./start.sh --clean            # Clean install and start
    ./start.sh --port 8080        # Start on port 8080

Requirements:
    - Python 3.10 or higher
    - Internet connection for package installation

For more information, see README.md
EOF
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local all_ok=true
    
    # Check Python
    if check_command python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_info "Python version: $PYTHON_VERSION"
        
        # Check if version is 3.10 or higher
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
            print_error "Python 3.10 or higher is required (found $PYTHON_VERSION)"
            all_ok=false
        fi
    else
        print_error "Python 3 is required but not found"
        all_ok=false
    fi
    
    # Check pip
    if ! check_command pip3; then
        print_error "pip3 is required but not found"
        all_ok=false
    fi
    
    # Check DB2 config
    if [ -f "$SCRIPT_DIR/db2_config.json" ]; then
        print_success "DB2 configuration file found"
    else
        print_warning "DB2 configuration file not found (db2_config.json)"
        print_info "You'll need to create it before running tests"
    fi
    
    if [ "$all_ok" = false ]; then
        print_error "Prerequisites check failed. Please install missing requirements."
        exit 1
    fi
    
    print_success "All prerequisites met"
    echo
}

create_venv() {
    print_header "Setting Up Virtual Environment"
    
    if [ -d "$VENV_DIR" ] && [ "$CLEAN_INSTALL" != "true" ]; then
        print_info "Virtual environment already exists"
        print_info "Use --clean flag to recreate it"
    else
        if [ -d "$VENV_DIR" ]; then
            print_info "Removing existing virtual environment..."
            rm -rf "$VENV_DIR"
        fi
        
        print_info "Creating virtual environment..."
        cd "$LANGFLOW_DIR"
        python3 -m venv .venv
        print_success "Virtual environment created"
    fi
    
    echo
}

install_dependencies() {
    print_header "Installing Dependencies"
    
    if [ "$SKIP_DEPS" = "true" ]; then
        print_info "Skipping dependency installation (--skip-deps flag)"
        echo
        return
    fi
    
    print_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    print_info "Upgrading pip..."
    pip install --upgrade pip > /dev/null 2>&1
    
    print_info "Installing Langflow and dependencies..."
    cd "$LANGFLOW_DIR"
    pip install -e . > /dev/null 2>&1
    
    print_info "Installing langchain-db2..."
    cd "$SCRIPT_DIR/langchain-db2"
    pip install -e . > /dev/null 2>&1
    
    print_info "Installing additional dependencies..."
    pip install ibm-db ibm-db-dbi sentence-transformers > /dev/null 2>&1
    
    print_success "All dependencies installed"
    echo
}

start_langflow() {
    print_header "Starting Langflow"
    
    source "$VENV_DIR/bin/activate"
    
    print_info "Starting Langflow on http://127.0.0.1:$PORT"
    print_info "Press Ctrl+C to stop"
    echo
    print_info "Access the UI at: ${GREEN}http://127.0.0.1:$PORT${NC}"
    print_info "Look for 'IBM Db2 Vector Store' component in the sidebar"
    echo
    
    cd "$LANGFLOW_DIR"
    langflow run --host 127.0.0.1 --port "$PORT"
}


show_banner() {
    cat << "EOF"
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║     ██╗      █████╗ ███╗   ██╗ ██████╗ ███████╗██╗      ██████╗    ║
║     ██║     ██╔══██╗████╗  ██║██╔════╝ ██╔════╝██║     ██╔═══██╗   ║
║     ██║     ███████║██╔██╗ ██║██║  ███╗█████╗  ██║     ██║   ██║   ║
║     ██║     ██╔══██║██║╚██╗██║██║   ██║██╔══╝  ██║     ██║   ██║   ║
║     ███████╗██║  ██║██║ ╚████║╚██████╔╝██║     ███████╗╚██████╔╝   ║
║     ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝     ╚══════╝ ╚═════╝    ║
║                                                                      ║
║                    with IBM DB2 Vector Support                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

EOF
}

################################################################################
# Main Script
################################################################################

# Default values
PORT=7860
CLEAN_INSTALL=false
SKIP_DEPS=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            exit 0
            ;;
        --clean)
            CLEAN_INSTALL=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Main execution
clear
show_banner

check_prerequisites
create_venv
install_dependencies
start_langflow

# Made with Bob
