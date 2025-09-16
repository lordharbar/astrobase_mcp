# Copyright 2025 Snowflake Inc.
# SPDX-License-Identifier: Apache-2.0
"""
Snowflake MCP Server Package.

This package provides a Model Context Protocol (MCP) server implementation for
interacting with Snowflake's Cortex AI services. The server enables seamless
integration with Snowflake's machine learning and AI capabilities through a
standardized protocol interface.

The package supports:
- Cortex Search: Semantic search across Snowflake data
- Cortex Analyst: Natural language to SQL query generation
- Object Management: Create, drop, and manage Snowflake objects
- Query Management: Execute SQL queries with permission controls
- Semantic Views: Work with Snowflake semantic views

Environment Variables
---------------------
SNOWFLAKE_ACCOUNT : str
    Snowflake account identifier (alternative to --account)
SNOWFLAKE_USER : str
    Snowflake username (alternative to --username)
SNOWFLAKE_PASSWORD : str
    Password or Programmatic Access Token (alternative to --password)
SERVICE_CONFIG_FILE : str
    Path to service configuration file (alternative to --service-config-file)
"""

from mcp_server_snowflake.server import mcp, main

__all__ = ["mcp", "main"]
__version__ = "2.0.0"