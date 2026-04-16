#!/bin/bash
# Check which DB2 component is in the API

echo "Fetching DB2 components from API..."
curl -s http://localhost:7863/api/v1/all | python3 -c "
import sys, json
data = json.load(sys.stdin)
db2_components = {k: v for k, v in data.items() if 'db2' in k.lower()}
print(f'Found {len(db2_components)} DB2 component(s):')
for name, comp in db2_components.items():
    print(f'\nComponent: {name}')
    print(f'  display_name: {comp.get(\"display_name\", \"MISSING\")}')
    print(f'  description: {comp.get(\"description\", \"MISSING\")}')
    print(f'  icon: {comp.get(\"icon\", \"MISSING\")}')
"

# Made with Bob
