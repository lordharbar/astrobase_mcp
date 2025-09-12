"""
FastMCP Snowflake Server
Located in mcp_server_snowflake/server.py
"""

import os
import json
import logging
from typing import Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from fastmcp import FastMCP
import snowflake.connector
from snowflake.connector import DictCursor
from dotenv import load_dotenv

# Load environment variables from parent directory if needed
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    name="Snowflake MCP Server",
    instructions="""
    A FastMCP server for interacting with Snowflake data warehouse.
    
    Available tools:
    - execute_query: Run SQL queries against Snowflake
    - list_databases: List all databases in the account
    - list_schemas: List schemas in a database
    - list_tables: List tables in a schema
    - describe_table: Get table structure and metadata
    - create_table: Create a new table
    - drop_table: Drop an existing table
    
    The server uses environment variables for authentication:
    - SNOWFLAKE_ACCOUNT
    - SNOWFLAKE_USER
    - SNOWFLAKE_PASSWORD
    - SNOWFLAKE_WAREHOUSE (optional)
    - SNOWFLAKE_DATABASE (optional)
    - SNOWFLAKE_SCHEMA (optional)
    - SNOWFLAKE_ROLE (optional)
    """
)

# Type definitions for Snowflake objects
@dataclass
class TableColumn:
    """Represents a column in a Snowflake table."""
    name: str
    datatype: str
    nullable: bool = True
    comment: str | None = None


@dataclass
class TableInfo:
    """Represents information about a Snowflake table."""
    database_name: str
    schema_name: str
    table_name: str
    columns: list[TableColumn] = field(default_factory=list)
    comment: str | None = None
    kind: str = "PERMANENT"  # PERMANENT, TRANSIENT, TEMPORARY


class SnowflakeConnection:
    """Manages Snowflake database connections."""
    
    def __init__(self):
        self.connection_params = self._get_connection_params()
    
    def _get_connection_params(self) -> dict[str, Any]:
        """Get connection parameters from environment variables."""
        params = {
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "password": os.getenv("SNOWFLAKE_PASSWORD"),
        }
        
        # Add optional parameters if provided
        optional_params = {
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA"),
            "role": os.getenv("SNOWFLAKE_ROLE"),
        }
        
        for key, value in optional_params.items():
            if value:
                params[key] = value
        
        # Remove None values
        return {k: v for k, v in params.items() if v is not None}
    
    def get_connection(self, use_dict_cursor: bool = True):
        """Create a Snowflake connection."""
        try:
            conn = snowflake.connector.connect(**self.connection_params)
            if use_dict_cursor:
                return conn, conn.cursor(DictCursor)
            return conn, conn.cursor()
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            raise

    def execute_query(self, query: str) -> list[dict]:
        """Execute a query and return results."""
        conn, cursor = self.get_connection(use_dict_cursor=True)
        try:
            cursor.execute(query)
            results = cursor.fetchall()
            return results
        finally:
            cursor.close()
            conn.close()


# Create a global connection manager
sf_conn = SnowflakeConnection()


# ============================================================================
# MCP Tools
# ============================================================================

@mcp.tool()
def execute_query(query: str, limit: int | None = None) -> str:
    """
    Execute a SQL query on Snowflake and return the results.
    
    Args:
        query: The SQL query to execute
        limit: Optional limit on number of rows to return
    
    Returns:
        JSON string containing query results or error message
    """
    try:
        # Add limit if specified and not already in query
        if limit and "LIMIT" not in query.upper():
            query = f"{query.rstrip(';')} LIMIT {limit}"
        
        results = sf_conn.execute_query(query)
        
        # Convert any non-serializable types
        for row in results:
            for key, value in row.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    row[key] = value.isoformat()
        
        return json.dumps({
            "success": True,
            "row_count": len(results),
            "data": results
        }, indent=2)
    
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def list_databases(pattern: str | None = None) -> str:
    """
    List all databases in the Snowflake account.
    
    Args:
        pattern: Optional pattern to filter database names (SQL LIKE pattern)
    
    Returns:
        JSON string containing list of databases
    """
    try:
        query = "SHOW DATABASES"
        if pattern:
            query += f" LIKE '{pattern}'"
        
        results = sf_conn.execute_query(query)
        
        databases = [
            {
                "name": row.get("name"),
                "owner": row.get("owner"),
                "comment": row.get("comment"),
                "created_on": row.get("created_on").isoformat() if row.get("created_on") else None
            }
            for row in results
        ]
        
        return json.dumps({
            "success": True,
            "count": len(databases),
            "databases": databases
        }, indent=2)
    
    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def list_schemas(database_name: str, pattern: str | None = None) -> str:
    """
    List all schemas in a specific database.
    
    Args:
        database_name: Name of the database
        pattern: Optional pattern to filter schema names (SQL LIKE pattern)
    
    Returns:
        JSON string containing list of schemas
    """
    try:
        query = f"SHOW SCHEMAS IN DATABASE {database_name}"
        if pattern:
            query += f" LIKE '{pattern}'"
        
        results = sf_conn.execute_query(query)
        
        schemas = [
            {
                "name": row.get("name"),
                "database_name": row.get("database_name"),
                "owner": row.get("owner"),
                "comment": row.get("comment"),
                "created_on": row.get("created_on").isoformat() if row.get("created_on") else None
            }
            for row in results
        ]
        
        return json.dumps({
            "success": True,
            "database": database_name,
            "count": len(schemas),
            "schemas": schemas
        }, indent=2)
    
    except Exception as e:
        logger.error(f"Failed to list schemas: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def list_tables(
    database_name: str,
    schema_name: str,
    pattern: str | None = None,
    include_views: bool = False
) -> str:
    """
    List all tables in a specific schema.
    
    Args:
        database_name: Name of the database
        schema_name: Name of the schema
        pattern: Optional pattern to filter table names (SQL LIKE pattern)
        include_views: Whether to include views in the results
    
    Returns:
        JSON string containing list of tables
    """
    try:
        query = f"SHOW TABLES IN SCHEMA {database_name}.{schema_name}"
        if pattern:
            query += f" LIKE '{pattern}'"
        
        results = sf_conn.execute_query(query)
        
        tables = []
        for row in results:
            # Skip views if not requested
            if not include_views and row.get("kind") == "VIEW":
                continue
            
            tables.append({
                "name": row.get("name"),
                "database_name": row.get("database_name"),
                "schema_name": row.get("schema_name"),
                "kind": row.get("kind"),
                "comment": row.get("comment"),
                "rows": row.get("rows"),
                "bytes": row.get("bytes"),
                "created_on": row.get("created_on").isoformat() if row.get("created_on") else None
            })
        
        return json.dumps({
            "success": True,
            "database": database_name,
            "schema": schema_name,
            "count": len(tables),
            "tables": tables
        }, indent=2)
    
    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def describe_table(
    database_name: str,
    schema_name: str,
    table_name: str
) -> str:
    """
    Get detailed information about a table including columns and metadata.
    
    Args:
        database_name: Name of the database
        schema_name: Name of the schema
        table_name: Name of the table
    
    Returns:
        JSON string containing table structure and metadata
    """
    try:
        # Get column information
        query = f"DESCRIBE TABLE {database_name}.{schema_name}.{table_name}"
        columns_result = sf_conn.execute_query(query)
        
        columns = [
            {
                "name": row.get("name"),
                "type": row.get("type"),
                "nullable": row.get("null?") == "Y",
                "default": row.get("default"),
                "primary_key": row.get("primary key") == "Y",
                "unique_key": row.get("unique key") == "Y",
                "comment": row.get("comment")
            }
            for row in columns_result
        ]
        
        # Get table metadata
        info_query = f"SHOW TABLES LIKE '{table_name}' IN SCHEMA {database_name}.{schema_name}"
        info_result = sf_conn.execute_query(info_query)
        
        table_info = {}
        if info_result:
            row = info_result[0]
            table_info = {
                "kind": row.get("kind"),
                "comment": row.get("comment"),
                "rows": row.get("rows"),
                "bytes": row.get("bytes"),
                "created_on": row.get("created_on").isoformat() if row.get("created_on") else None,
                "owner": row.get("owner")
            }
        
        return json.dumps({
            "success": True,
            "database": database_name,
            "schema": schema_name,
            "table": table_name,
            "info": table_info,
            "columns": columns
        }, indent=2)
    
    except Exception as e:
        logger.error(f"Failed to describe table: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def create_table(
    database_name: str,
    schema_name: str,
    table_name: str,
    columns: list[dict],
    comment: str | None = None,
    replace_if_exists: bool = False
) -> str:
    """
    Create a new table in Snowflake.
    
    Args:
        database_name: Name of the database
        schema_name: Name of the schema
        table_name: Name of the table to create
        columns: List of column definitions, each with 'name', 'type', and optional 'nullable', 'default', 'comment'
        comment: Optional comment for the table
        replace_if_exists: Whether to replace the table if it already exists
    
    Returns:
        JSON string indicating success or failure
    """
    try:
        # Build CREATE TABLE statement
        create_or_replace = "CREATE OR REPLACE" if replace_if_exists else "CREATE"
        
        column_defs = []
        for col in columns:
            col_def = f"{col['name']} {col['type']}"
            
            if not col.get('nullable', True):
                col_def += " NOT NULL"
            
            if 'default' in col:
                col_def += f" DEFAULT {col['default']}"
            
            if 'comment' in col:
                col_def += f" COMMENT '{col['comment']}'"
            
            column_defs.append(col_def)
        
        query = f"{create_or_replace} TABLE {database_name}.{schema_name}.{table_name} (\n"
        query += ",\n".join(f"    {col_def}" for col_def in column_defs)
        query += "\n)"
        
        if comment:
            query += f" COMMENT = '{comment}'"
        
        sf_conn.execute_query(query)
        
        return json.dumps({
            "success": True,
            "message": f"Table {database_name}.{schema_name}.{table_name} created successfully",
            "query": query
        }, indent=2)
    
    except Exception as e:
        logger.error(f"Failed to create table: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


@mcp.tool()
def drop_table(
    database_name: str,
    schema_name: str,
    table_name: str,
    if_exists: bool = True
) -> str:
    """
    Drop a table from Snowflake.
    
    Args:
        database_name: Name of the database
        schema_name: Name of the schema
        table_name: Name of the table to drop
        if_exists: Whether to use IF EXISTS clause
    
    Returns:
        JSON string indicating success or failure
    """
    try:
        if_exists_clause = "IF EXISTS " if if_exists else ""
        query = f"DROP TABLE {if_exists_clause}{database_name}.{schema_name}.{table_name}"
        
        sf_conn.execute_query(query)
        
        return json.dumps({
            "success": True,
            "message": f"Table {database_name}.{schema_name}.{table_name} dropped successfully",
            "query": query
        }, indent=2)
    
    except Exception as e:
        logger.error(f"Failed to drop table: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2)


# ============================================================================
# Resources
# ============================================================================

@mcp.resource("snowflake://connection-info")
def get_connection_info() -> dict:
    """
    Get current Snowflake connection information.
    
    Returns connection parameters (excluding sensitive information).
    """
    params = sf_conn.connection_params.copy()
    # Remove sensitive information
    params.pop("password", None)
    
    return {
        "connection_params": params,
        "configured": bool(params.get("account") and params.get("user"))
    }


@mcp.resource("snowflake://query-examples")
def get_query_examples() -> dict:
    """
    Get example SQL queries for common Snowflake operations.
    """
    return {
        "examples": [
            {
                "description": "Show current warehouse",
                "query": "SHOW WAREHOUSES"
            },
            {
                "description": "Get current database and schema",
                "query": "SELECT CURRENT_DATABASE(), CURRENT_SCHEMA()"
            },
            {
                "description": "List all tables with row counts",
                "query": "SHOW TABLES"
            },
            {
                "description": "Query sample data",
                "query": "SELECT * FROM table_name LIMIT 10"
            },
            {
                "description": "Get table DDL",
                "query": "SELECT GET_DDL('TABLE', 'database.schema.table_name')"
            },
            {
                "description": "Show user privileges",
                "query": "SHOW GRANTS TO USER"
            }
        ]
    }


# ============================================================================
# Main entry point
# ============================================================================

if __name__ == "__main__":
    # Run the server
    # For FastMCP Cloud, this block will be ignored
    # For local testing, use: python mcp_server_snowflake/server.py
    mcp.run()