import os
import json
from fastmcp import FastMCP
import snowflake.connector
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Snowflake Connection Details ---
# It's recommended to use environment variables for security
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PAT = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")

# --- FastMCP Server Definition ---
mcp = FastMCP(
    name="Snowflake MCP Server",
    instructions="A FastMCP server to interact with a Snowflake database. Use the 'execute_snowflake_query' tool to run SQL queries.",
)

def get_snowflake_connection():
    """Establishes a connection to Snowflake."""
    try:
        conn = snowflake.connector.connect(
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PAT,
            account=SNOWFLAKE_ACCOUNT,
            warehouse=SNOWFLAKE_WAREHOUSE,
            database=SNOWFLAKE_DATABASE,
            schema=SNOWFLAKE_SCHEMA,
            authenticator='oauth'
        )
        return conn
    except Exception as e:
        print(f"Error connecting to Snowflake: {e}")
        return None

@mcp.tool
def execute_snowflake_query(query: str) -> str:
    """
    Executes a SQL query on Snowflake and returns the results as a JSON string.

    :param query: The SQL query to execute.
    :return: A JSON string representing a list of dictionaries, where each dictionary is a row.
    """
    conn = get_snowflake_connection()
    if not conn:
        return json.dumps({"error": "Failed to connect to Snowflake."})

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            # Fetch all rows and column names
            rows = cur.fetchall()
            col_names = [desc[0] for desc in cur.description]

            # Create a list of dictionaries
            results = [dict(zip(col_names, row)) for row in rows]
            return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": f"An error occurred: {e}"})
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    # To run this server locally with HTTP transport on port 8000:
    # `uv run fastmcp run snowflake_mcp_server.py:mcp --transport http --port 8000`
    # Or, to run with stdio:
    mcp.run()