#!/bin/bash

################################################################################
# Cleanup Script - Remove Unnecessary/Outdated Files
################################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}  Cleaning Up Unnecessary Files${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo

# Files to remove from root
ROOT_FILES=(
    "csv_parser_component.py"
    "restart_langflow_clean.sh"
    "test_db2_vector_format.py"
    "debug_db2_embeddings.py"
    "drop_db2_table.py"
    "test_column_detection.py"
    "test_db2_embedding_generation.py"
    "test_db2_empty_embeddings.py"
    "test_db2_fix.py"
)

# Files to remove from langflow directory
LANGFLOW_FILES=(
    "check_db2_api.sh"
    "diagnose_db2.sh"
    "run_db2_integration.sh"
    "start_langflow_with_db2.sh"
    "start_with_db2.sh"
    "test_component_directly.py"
    "test_csv_ingestion.py"
    "test_db2_components.py"
    "test_db2_connection.py"
    "test_db2_direct_ingestion.py"
    "test_db2_import.py"
    "test_db2_in_ui.py"
    "test_db2_vector_debug.py"
    "debug_api_response.js"
    "check_db2_detail.js"
)

# Remove files from root
echo -e "${GREEN}Cleaning root directory...${NC}"
for file in "${ROOT_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo -e "  ${GREEN}✓${NC} Removed: $file"
    fi
done

# Remove files from langflow directory
echo
echo -e "${GREEN}Cleaning langflow directory...${NC}"
cd langflow
for file in "${LANGFLOW_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo -e "  ${GREEN}✓${NC} Removed: $file"
    fi
done
cd ..

echo
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Cleanup Complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo
echo -e "${YELLOW}Kept files:${NC}"
echo -e "  • start.sh (main setup script)"
echo -e "  • test_vector_ingestion_hybrid_retrieval.py (working test)"
echo -e "  • README.md (documentation)"
echo -e "  • All documentation files"
echo

# Made with Bob
