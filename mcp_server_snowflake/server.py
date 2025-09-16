# Copyright 2025 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
"""
FastMCP Snowflake Server
Main server module for Snowflake MCP integration
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, TypeAlias

import snowflake.connector
import yaml
from fastmcp import FastMCP
from snowflake.connector import DictCursor
from snowflake.core import Root

# Import the various tool modules
from mcp_server_snowflake.cortex_services.tools import (
    create_cortex_analyst_wrapper,
    create_search_wrapper,
)
from mcp_server_snowflake.object_manager.tools import initialize_object_manager_tools
from mcp_server_snowflake.query_manager.tools import initialize_query_manager_tool
from mcp_server_snowflake.semantic_manager.tools import initialize_semantic_manager_tools
from mcp_server_snowflake.server_utils import initialize_middleware
from mcp_server_snowflake.utils import (
    MissingArgumentsException,
    cleanup_snowflake_service,
    get_login_params,
    sanitize_tool_name,
    unpack_sql_statement_permissions,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type aliases
ConnectionParams: TypeAlias = dict[str, str | int | bool]
ServiceConfig: TypeAlias = dict[str, Any]

# Initialize FastMCP server
mcp = FastMCP(
    name="Snowflake MCP Server",
    description="A FastMCP server for interacting with Snowflake data warehouse, providing Cortex AI services, object management, and query capabilities."
)


@dataclass
class SnowflakeService:
    """Manages Snowflake database connections and configuration."""
    
    service_config_file: Path | None = None
    transport: str = "stdio"
    connection_params: ConnectionParams = field(default_factory=dict)
    
    # Service configurations
    search_services: list[ServiceConfig] = field(default_factory=list)
    analyst_services: list[ServiceConfig] = field(default_factory=list)
    object_manager_enabled: bool = True
    query_manager_enabled: bool = True
    semantic_manager_enabled: bool = True
    sql_statement_allowed: list[str] = field(default_factory=list)
    sql_statement_disallowed: list[str] = field(default_factory=list)
    
    # Runtime attributes
    connection: snowflake.connector.SnowflakeConnection | None = field(default=None, init=False)
    root: Root | None = field(default=None, init=False)
    
    def __post_init__(self) -> None:
        """Initialize the Snowflake service after dataclass initialization."""
        # Resolve config file path if provided
        if self.service_config_file:
            self.service_config_file = self._resolve_path(self.service_config_file)
        
        # Set connection parameters from environment if not provided
        if not self.connection_params:
            self.connection_params = self._get_connection_params_from_env()
        
        # Load service configuration if provided
        if self.service_config_file:
            self._load_service_config()
        
        # Initialize Snowflake connection and root
        self._initialize_connection()
    
    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve path to absolute, expanding ~ and relative paths."""
        path_obj = Path(path).expanduser().resolve()
        
        if not path_obj.exists():
            raise FileNotFoundError(f"Service config file not found: {path}")
        
        return path_obj
    
    def _get_connection_params_from_env(self) -> ConnectionParams:
        """Get connection parameters from environment variables."""
        params: ConnectionParams = {
            "account": os.getenv("SNOWFLAKE_ACCOUNT", ""),
            "user": os.getenv("SNOWFLAKE_USER", ""),
            "password": os.getenv("SNOWFLAKE_PASSWORD", ""),
        }
        
        # Add optional parameters if provided
        optional_params: dict[str, str | None] = {
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA"),
            "role": os.getenv("SNOWFLAKE_ROLE"),
        }
        
        for key, value in optional_params.items():
            if value:
                params[key] = value
        
        # Validate required parameters
        missing: list[str] = []
        if not params.get("account"):
            missing.append("SNOWFLAKE_ACCOUNT")
        if not params.get("user"):
            missing.append("SNOWFLAKE_USER")
        if not params.get("password"):
            missing.append("SNOWFLAKE_PASSWORD")
        
        if missing:
            raise MissingArgumentsException(missing)
        
        return {k: v for k, v in params.items() if v}
    
    def _load_service_config(self) -> None:
        """Load service configuration from YAML file."""
        if not self.service_config_file:
            return
        
        config_content = self.service_config_file.read_text()
        config = yaml.safe_load(config_content)
        
        # Load search services
        self.search_services = config.get("search_services", [])
        
        # Load analyst services
        self.analyst_services = config.get("analyst_services", [])
        
        # Load other services configuration
        other_services = config.get("other_services", {})
        self.object_manager_enabled = other_services.get("object_manager", True)
        self.query_manager_enabled = other_services.get("query_manager", True)
        self.semantic_manager_enabled = other_services.get("semantic_manager", True)
        
        # Load SQL statement permissions
        sql_permissions = config.get("sql_statement_permissions", [])
        self.sql_statement_allowed, self.sql_statement_disallowed = unpack_sql_statement_permissions(sql_permissions)
    
    def _initialize_connection(self) -> None:
        """Initialize Snowflake connection and root object."""
        try:
            self.connection = snowflake.connector.connect(**self.connection_params)
            self.root = Root(self.connection)
            logger.info("Successfully connected to Snowflake")
        except Exception as e:
            logger.error(f"Failed to connect to Snowflake: {e}")
            self.connection = None
            self.root = None
    
    def get_connection(
        self, 
        use_dict_cursor: bool = True, 
        session_parameters: dict[str, Any] | None = None
    ) -> tuple[snowflake.connector.SnowflakeConnection, Any]:
        """
        Create a Snowflake connection with optional cursor type.
        
        Args:
            use_dict_cursor: Whether to use dictionary cursor
            session_parameters: Optional session parameters
            
        Returns:
            Tuple of (connection, cursor)
        """
        conn_params = self.connection_params.copy()
        if session_parameters:
            conn_params["session_parameters"] = session_parameters
        
        conn = snowflake.connector.connect(**conn_params)
        cursor = conn.cursor(DictCursor) if use_dict_cursor else conn.cursor()
        return conn, cursor
    
    def get_query_tag_param(self) -> dict[str, str]:
        """Get query tag parameters for tracking."""
        return {"QUERY_TAG": "mcp-server-snowflake"}
    
    def get_api_host(self) -> str:
        """Get the API host for REST API calls."""
        account = self.connection_params.get("account", "")
        if not account.endswith(".snowflakecomputing.com"):
            account = f"{account}.snowflakecomputing.com"
        return f"https://{account}"
    
    def get_api_headers(self) -> dict[str, str]:
        """Get headers for REST API calls."""
        # This would need proper auth implementation for production
        return {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }


def initialize_cortex_search_tools(server: FastMCP, snowflake_service: SnowflakeService) -> None:
    """Initialize Cortex Search tools."""
    for service_details in snowflake_service.search_services:
        service_name = service_details.get("service_name", "")
        if not service_name:
            continue
        
        tool_name = f"search_{sanitize_tool_name(service_name)}"
        description = service_details.get("description", f"Search using {service_name}")
        
        # Create the search wrapper function
        search_func = create_search_wrapper(
            snowflake_service=snowflake_service,
            service_details=service_details
        )
        
        # Register the tool with FastMCP
        server.tool(name=tool_name, description=description)(search_func)
        logger.info(f"Registered Cortex Search tool: {tool_name}")


def initialize_cortex_analyst_tools(server: FastMCP, snowflake_service: SnowflakeService) -> None:
    """Initialize Cortex Analyst tools."""
    for service_details in snowflake_service.analyst_services:
        service_name = service_details.get("service_name", "")
        if not service_name:
            continue
        
        tool_name = f"analyst_{sanitize_tool_name(service_name)}"
        description = service_details.get("description", f"Analyze using {service_name}")
        
        # Create the analyst wrapper function
        analyst_func = create_cortex_analyst_wrapper(
            snowflake_service=snowflake_service,
            service_details=service_details
        )
        
        # Register the tool with FastMCP
        server.tool(name=tool_name, description=description)(analyst_func)
        logger.info(f"Registered Cortex Analyst tool: {tool_name}")


def initialize_all_tools(server: FastMCP, snowflake_service: SnowflakeService) -> None:
    """Initialize all enabled tools and services."""
    # Initialize Cortex services
    if snowflake_service.search_services:
        initialize_cortex_search_tools(server, snowflake_service)
    
    if snowflake_service.analyst_services:
        initialize_cortex_analyst_tools(server, snowflake_service)
    
    # Initialize other managers if enabled
    if snowflake_service.object_manager_enabled:
        initialize_object_manager_tools(server, snowflake_service)
        logger.info("Initialized Object Manager tools")
    
    if snowflake_service.query_manager_enabled:
        initialize_query_manager_tool(server, snowflake_service)
        logger.info("Initialized Query Manager tools")
    
    if snowflake_service.semantic_manager_enabled:
        initialize_semantic_manager_tools(server, snowflake_service)
        logger.info("Initialized Semantic Manager tools")
    
    # Initialize middleware for permission checking
    initialize_middleware(server, snowflake_service)
    logger.info("Initialized middleware")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Snowflake MCP Server")
    
    # Get login parameters configuration
    login_params = get_login_params()
    
    # Add arguments for each login parameter
    for param_name, param_config in login_params.items():
        flags = param_config[:2]  # First two items are the flag names
        default = param_config[2]  # Third item is default value
        help_text = param_config[3]  # Fourth item is help text
        
        parser.add_argument(
            *flags,
            dest=param_name,
            default=default,
            help=help_text
        )
    
    # Add service configuration file argument
    parser.add_argument(
        "--service-config-file",
        default=os.getenv("SERVICE_CONFIG_FILE"),
        help="Path to service configuration YAML file"
    )
    
    # Add transport argument
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "http"],
        help="Transport method for MCP server"
    )
    
    return parser.parse_args()


# Global Snowflake service instance
snowflake_service: SnowflakeService | None = None


def main() -> None:
    """Main entry point for the server."""
    global snowflake_service
    
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Build connection parameters from arguments
        connection_params: ConnectionParams = {}
        login_params = get_login_params()
        
        for param_name in login_params:
            value = getattr(args, param_name, None)
            if value:
                connection_params[param_name] = value
        
        # Initialize Snowflake service
        snowflake_service = SnowflakeService(
            service_config_file=args.service_config_file,
            transport=args.transport,
            connection_params=connection_params
        )
        
        # Initialize all tools
        initialize_all_tools(mcp, snowflake_service)
        
        # Run the FastMCP server
        logger.info("Starting Snowflake MCP Server...")
        mcp.run()
        
    except MissingArgumentsException as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
    finally:
        if snowflake_service:
            cleanup_snowflake_service(snowflake_service)


if __name__ == "__main__":
    main()