# 🔧 DB2 Connection Troubleshooting Guide

## 🚨 Common Issues & Solutions

---

# Issue 1: Components Not Showing in UI

## ❓ Problem:
DB2 SQL and DB2 Vector Store nodes don't appear in Langflow sidebar

## ✅ Solution:

### Step 1: Start with `LFX_DEV=1`
```bash
cd langflow
source .venv/bin/activate
export LFX_DEV=1
export LANGFLOW_AUTO_LOGIN=true
langflow run --port 7863
```

### Step 2: Check if components load
```bash
curl -s http://localhost:7863/api/v1/components | python3 -c "
import sys, json
data = json.load(sys.stdin)
db2 = [k for k in data.keys() if 'db2' in k.lower() or 'DB2' in k]
print('DB2 components:', db2 if db2 else 'NONE FOUND')
print('Total components:', len(data))
"
```

**Expected:** Should show DB2SQLComponent and DB2VectorStoreComponent

---

# Issue 2: Connection Failed

## ❓ Problem:
"Connection to DB2 failed" or timeout errors

## ✅ Solutions:

### Check 1: Verify DB2 is Running
```bash
# Test connection with db2cli
db2cli validate -dsn <your_dsn>

# Or test with Python
python3 << 'EOF'
import ibm_db_dbi

conn_str = "DATABASE=TESTDB;HOSTNAME=localhost;PORT=50000;PROTOCOL=TCPIP;UID=db2inst1;PWD=password;"
try:
    conn = ibm_db_dbi.connect(conn_str, "", "")
    print("✅ Connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
EOF
```

### Check 2: Verify Connection Parameters

| Parameter | Common Values | How to Check |
|-----------|--------------|--------------|
| **Hostname** | localhost, 127.0.0.1, IP | `ping <hostname>` |
| **Port** | 50000 (default) | `netstat -an \| grep 50000` |
| **Database** | TESTDB, SAMPLE | `db2 list db directory` |
| **Username** | db2inst1 | Check with DBA |
| **Password** | (secret) | Verify with DBA |

### Check 3: Firewall/Network
```bash
# Test if port is accessible
telnet <hostname> 50000

# Or use nc
nc -zv <hostname> 50000
```

---

# Issue 3: Import Errors

## ❓ Problem:
```
ModuleNotFoundError: No module named 'ibm_db_dbi'
ModuleNotFoundError: No module named 'langchain_db2'
```

## ✅ Solution:

### Install Required Packages
```bash
# Activate Langflow venv
cd langflow
source .venv/bin/activate

# Install ibm_db
pip install ibm_db

# Install langchain-db2 (your custom package)
cd ../langchain-db2
pip install -e .

# Verify installation
python3 -c "import ibm_db_dbi; print('✅ ibm_db_dbi installed')"
python3 -c "import langchain_db2; print('✅ langchain_db2 installed')"
```

---

# Issue 4: Dimension Mismatch Error

## ❓ Problem:
```
ValueError: Embedding dimension mismatch detected
VECTOR cannot be CAST
```

## ✅ Solution:

### Option 1: Drop and Recreate Table
```sql
-- Connect to DB2
db2 connect to TESTDB

-- Drop existing table
DROP TABLE LANGFLOW_VECTORS;

-- Disconnect
db2 disconnect all
```

### Option 2: Use Different Table Name
In Langflow UI:
- Change "Table Name" from `LANGFLOW_VECTORS` to `LANGFLOW_VECTORS_V2`

### Option 3: Check Embedding Dimensions
```python
# Test your embedding model
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()
test_vector = embeddings.embed_query("test")
print(f"Embedding dimension: {len(test_vector)}")
```

---

# Issue 5: SSL/TLS Errors

## ❓ Problem:
```
SSL connection error
Certificate verification failed
```

## ✅ Solution:

### Option 1: Disable SSL (Development Only)
```python
conn_str = (
    f"DATABASE={database};"
    f"HOSTNAME={hostname};"
    f"PORT={port};"
    f"PROTOCOL=TCPIP;"
    f"UID={username};"
    f"PWD={password};"
    f"SECURITY=SSL;"  # Add this
    f"SSLServerCertificate=<path_to_cert>;"  # Add this
)
```

### Option 2: Use Non-SSL Port
- Default SSL port: 50001
- Default non-SSL port: 50000

---

# Issue 6: Permission Denied

## ❓ Problem:
```
SQL0551N  "USER" does not have the required authorization
```

## ✅ Solution:

### Grant Required Permissions
```sql
-- Connect as admin
db2 connect to TESTDB user db2admin

-- Grant permissions
GRANT CREATETAB ON DATABASE TO USER db2inst1;
GRANT CREATE ON SCHEMA LANGFLOW TO USER db2inst1;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE LANGFLOW_VECTORS TO USER db2inst1;

-- Disconnect
db2 disconnect all
```

---

# Issue 7: Table Already Exists

## ❓ Problem:
```
SQL0601N  The name of the object to be created is identical to the existing name
```

## ✅ Solution:

### Option 1: Use Existing Table
- Just continue - the component will use the existing table

### Option 2: Drop and Recreate
```sql
DROP TABLE LANGFLOW_VECTORS;
```

### Option 3: Use Different Name
- Change table name in Langflow UI

---

# Issue 8: Slow Performance

## ❓ Problem:
Vector search is very slow

## ✅ Solutions:

### Check 1: Create Index
```sql
-- Check if index exists
SELECT * FROM SYSCAT.INDEXES WHERE TABNAME = 'LANGFLOW_VECTORS';

-- If not, DB2VS should create it automatically
-- But you can verify with:
SELECT * FROM SYSCAT.INDEXES WHERE TABNAME = 'LANGFLOW_VECTORS' AND INDEXTYPE = 'VECT';
```

### Check 2: Check Table Size
```sql
SELECT
    CARD as row_count,
    NPAGES as num_pages,
    FPAGES as formatted_pages
FROM SYSCAT.TABLES
WHERE TABNAME = 'LANGFLOW_VECTORS';
```

### Check 3: Optimize Query
- Reduce `number_of_results` (default: 4)
- Use appropriate distance strategy
- Consider batch operations

---

# Issue 9: Memory Errors

## ❓ Problem:
```
MemoryError: Unable to allocate array
Out of memory
```

## ✅ Solutions:

### Solution 1: Batch Processing
- Don't ingest all documents at once
- Process in batches of 100-1000 documents

### Solution 2: Increase Memory
```bash
# Increase Python memory limit
export PYTHONMALLOC=malloc
ulimit -v unlimited
```

---

# Issue 10: Encoding Errors

## ❓ Problem:
```
UnicodeDecodeError: 'utf-8' codec can't decode
```

## ✅ Solution:

### Ensure UTF-8 Encoding
```python
# When reading files
with open('file.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# When creating documents
from langchain_core.documents import Document
doc = Document(page_content=content.encode('utf-8').decode('utf-8'))
```

---

# 🔍 Diagnostic Commands

## Check Langflow Status
```bash
# Check if Langflow is running
curl http://localhost:7863/health

# Check component count
curl -s http://localhost:7863/api/v1/components | python3 -c "import sys, json; print(len(json.load(sys.stdin)))"
```

## Check DB2 Status
```bash
# Check DB2 instance
db2pd -inst

# Check database status
db2 list active databases

# Check connections
db2 list applications
```

## Check Python Environment
```bash
# Check installed packages
pip list | grep -E "ibm|langchain"

# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"
```

---

# 📞 Getting Help

## 1. Check Logs
```bash
# Langflow logs
tail -f ~/.langflow/logs/langflow.log

# DB2 logs
db2diag -h
```

## 2. Enable Debug Mode
```bash
export LANGFLOW_LOG_LEVEL=DEBUG
langflow run --port 7863
```

## 3. Ask Community
- Langflow Discord: [link]
- GitHub Issues: [link]
- Stack Overflow: tag `langflow` + `db2`

---

# ✅ Quick Checklist

Before asking for help, verify:

- [ ] DB2 is running and accessible
- [ ] Connection parameters are correct
- [ ] `ibm_db` and `langchain_db2` are installed
- [ ] `LFX_DEV=1` is set
- [ ] Langflow is running on correct port
- [ ] No firewall blocking connection
- [ ] User has required permissions
- [ ] Table name doesn't conflict
- [ ] Embedding dimensions match

---

# 🎯 Most Common Fix

**90% of issues are solved by:**

```bash
# 1. Kill everything
lsof -ti:7863,3000 | xargs kill -9 2>/dev/null

# 2. Start with LFX_DEV=1
cd langflow
source .venv/bin/activate
export LFX_DEV=1
export LANGFLOW_AUTO_LOGIN=true
langflow run --port 7863

# 3. Open http://localhost:7863
# 4. Search for "DB2"
```

If components still don't show, check the API:
```bash
curl -s http://localhost:7863/api/v1/components | grep -i db2
```

---

**Last Updated:** 2026-04-21