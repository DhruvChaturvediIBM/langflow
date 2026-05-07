-- DB2 Table Cleanup Script
-- Run this to clean up test tables before testing vector store

-- Connect to database
CONNECT TO TESTDB USER mohit29;

-- List all vector tables
SELECT TABNAME, COLNAME, TYPENAME, LENGTH
FROM SYSCAT.COLUMNS
WHERE TYPENAME = 'VECTOR'
ORDER BY TABNAME;

-- Drop test tables (uncomment to execute)
-- DROP TABLE IF EXISTS LANGFLOW_VECTORS;
-- DROP TABLE IF EXISTS TEST_VECTORS;
-- DROP TABLE IF EXISTS VECTORS_384D;
-- DROP TABLE IF EXISTS VECTORS_768D;

-- Verify tables are dropped
-- SELECT COUNT(*) FROM LANGFLOW_VECTORS;  -- Should error if dropped

-- Commit changes
COMMIT;

-- Disconnect
CONNECT RESET;

-- Made with Bob
