"""IBM Db2 SQL Component for Langflow."""

import ibm_db_dbi

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import HandleInput, IntInput, SecretStrInput, StrInput
from lfx.io import Output
from lfx.schema.data import Data


class DB2SQLComponent(Component):
    """IBM Db2 SQL Executor Component."""

    display_name = "IBM Db2 SQL"
    description = "Execute SQL queries on IBM Db2 database"
    documentation = "https://www.ibm.com/docs/en/db2/11.5"
    icon = "DB2"
    name = "DB2SQL"

    inputs = [
        StrInput(
            name="database",
            display_name="Database Name",
            required=True,
            info="Name of the Db2 database",
        ),
        StrInput(
            name="hostname",
            display_name="Hostname",
            required=True,
            info="Db2 server hostname or IP address",
        ),
        IntInput(
            name="port",
            display_name="Port",
            value=50000,
            required=True,
            info="Db2 server port (default: 50000)",
        ),
        StrInput(
            name="username",
            display_name="Username",
            required=True,
            info="Db2 database username",
        ),
        SecretStrInput(
            name="password",
            display_name="Password",
            required=True,
            info="Db2 database password",
        ),
        HandleInput(
            name="sql_query",
            display_name="SQL Query",
            input_types=["Message", "Text", "Data"],
            required=False,
            info="SQL query to execute (can be connected from other nodes or typed directly)",
        ),
        IntInput(
            name="max_rows",
            display_name="Max Rows",
            value=100,
            info="Maximum number of rows to return",
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="Results", name="results", method="execute_query"),
    ]

    def execute_query(self) -> list[Data]:
        """Execute SQL query on Db2 database."""
        # Validate inputs
        if not self.database or not self.hostname or not self.username or not self.password:
            msg = (
                "❌ Missing required connection parameters. Please provide:\n"
                "- Database Name\n"
                "- Hostname\n"
                "- Username\n"
                "- Password"
            )
            raise ValueError(msg)

        if not self.sql_query:
            msg = "❌ SQL Query is required\n\nPlease provide a SQL query to execute."
            raise ValueError(msg)

        # Extract query text if it's a Data or Message object
        query_text = self.sql_query
        if hasattr(self.sql_query, "text"):
            query_text = self.sql_query.text
        elif hasattr(self.sql_query, "data") and isinstance(self.sql_query.data, dict):
            query_text = self.sql_query.data.get("text", str(self.sql_query.data))
        elif isinstance(self.sql_query, Data):
            query_text = str(self.sql_query.data)

        try:
            # Create connection string
            conn_str = (
                f"DATABASE={self.database};"
                f"HOSTNAME={self.hostname};"
                f"PORT={self.port};"
                f"PROTOCOL=TCPIP;"
                f"UID={self.username};"
                f"PWD={self.password};"
            )

            # Connect to Db2
            conn = ibm_db_dbi.connect(conn_str, "", "")
            self.log(f"Connected to Db2 database: {self.database}")

            # Execute query
            cursor = conn.cursor()
            cursor.execute(query_text)
            self.log(f"Executed query: {query_text[:100]}...")

            # Fetch results
            if cursor.description:
                # Query returns results (SELECT)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchmany(self.max_rows)

                self.log(f"Query returned {len(rows)} rows")

                # Convert to Data objects
                results = []
                for row in rows:
                    row_dict = dict(zip(columns, row, strict=False))
                    data = Data(data=row_dict)
                    results.append(data)

                cursor.close()
                conn.close()

                self.status = f"Retrieved {len(results)} rows"
                return results
            # Query doesn't return results (INSERT, UPDATE, DELETE)
            conn.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            conn.close()

            self.log(f"Query affected {affected_rows} rows")
            self.status = f"Query executed successfully. Affected {affected_rows} rows"

            # Return empty result with status
            return [Data(data={"status": "success", "affected_rows": affected_rows})]

        except Exception as e:
            error_msg = str(e)

            # Provide helpful error messages
            if "SQL30081N" in error_msg or "communication error" in error_msg.lower():
                msg = (
                    f"❌ Cannot connect to DB2 server at {self.hostname}:{self.port}\n\n"
                    f"Possible causes:\n"
                    f"1. DB2 server is not running\n"
                    f"2. Hostname/IP is incorrect (current: {self.hostname})\n"
                    f"3. Port is incorrect (current: {self.port})\n"
                    f"4. Firewall blocking connection\n\n"
                    f"Original error: {error_msg}"
                )
                raise ConnectionError(msg) from e
            if "SQL1336N" in error_msg or "not found" in error_msg.lower():
                msg = (
                    f"❌ Cannot resolve hostname: {self.hostname}\n\n"
                    f"Try using:\n"
                    f"  - localhost (if DB2 is on same machine)\n"
                    f"  - 127.0.0.1 (if DB2 is on same machine)\n"
                    f"  - Actual IP address of DB2 server\n\n"
                    f"Original error: {error_msg}"
                )
                raise ConnectionError(msg) from e
            if "SQL30082N" in error_msg or "security" in error_msg.lower():
                msg = (
                    f"❌ Authentication failed\n\nCheck username and password\n\nOriginal error: {error_msg}"
                )
                raise ConnectionError(msg) from e
            msg = f"❌ DB2 SQL Error: {error_msg}"
            raise RuntimeError(msg) from e


# Made with Bob
