"""IBM Db2 SQL Component for Langflow."""

import ibm_db_dbi

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import IntInput, MessageTextInput, SecretStrInput, StrInput
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
        MessageTextInput(
            name="sql_query",
            display_name="SQL Query",
            info="SQL query to execute",
            required=True,
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
            cursor.execute(self.sql_query)

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
            error_msg = f"Error executing query: {e!s}"
            self.log(error_msg)
            raise RuntimeError(error_msg) from e


# Made with Bob
