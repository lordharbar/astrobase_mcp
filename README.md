# Snowflake MCP Server

## 🚀 Overview

The Snowflake MCP (Model Context Protocol) Server is a FastMCP-based server that provides a standardized interface for AI models and agents to interact with Snowflake's data warehouse and AI services. This server enables seamless integration between Large Language Models (LLMs) and Snowflake's powerful data platform, including Cortex AI services, database management, and SQL query execution.

## 📋 Table of Contents

- [What is MCP?](#what-is-mcp)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Available Services](#available-services)
- [Usage Examples](#usage-examples)
- [Deployment](#deployment)
- [Security Considerations](#security-considerations)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🤔 What is MCP?

Model Context Protocol (MCP) is an open standard that enables seamless communication between AI models and external data sources or tools. Think of it as a universal translator that allows AI assistants to:

- **Access real-time data** from databases, APIs, and other sources
- **Execute actions** like running queries or managing database objects
- **Maintain context** across conversations while respecting security boundaries
- **Provide consistent interfaces** regardless of the underlying system

This server implements MCP for Snowflake, meaning any MCP-compatible AI client (like Claude, ChatGPT with plugins, or custom applications) can interact with your Snowflake data warehouse through a standardized interface.

## ✨ Key Features

### 1. **Snowflake Cortex AI Integration**
- **Cortex Search**: Semantic search across your Snowflake data using natural language
- **Cortex Analyst**: Convert natural language questions into SQL queries automatically
- **Custom AI Services**: Define and expose your own Cortex-powered services

### 2. **Database Management Tools**
- Create, modify, and drop databases, schemas, and tables
- Manage warehouses and compute resources
- Handle roles, users, and permissions
- Work with stages and image repositories

### 3. **Advanced Query Capabilities**
- Execute arbitrary SQL queries with configurable permission controls
- Work with Semantic Views for business-friendly data access
- Query semantic dimensions, metrics, and facts
- Support for complex analytical queries

### 4. **Security & Governance**
- Granular permission controls for SQL statement types
- Configurable allow/deny lists for operations
- Query tagging for audit trails
- Session parameter management

## 🏗️ Architecture

```
┌─────────────────────┐
│   AI Application    │
│  (Claude, ChatGPT,  │
│   Custom Client)    │
└──────────┬──────────┘
           │
      MCP Protocol
           │
┌──────────▼──────────┐
│   FastMCP Server    │
│  (This Application) │
├─────────────────────┤
│   Service Layer     │
│  ┌───────────────┐  │
│  │ Cortex Tools  │  │
│  ├───────────────┤  │
│  │ Object Mgmt   │  │
│  ├───────────────┤  │
│  │ Query Engine  │  │
│  ├───────────────┤  │
│  │ Semantic Mgr  │  │
│  └───────────────┘  │
├─────────────────────┤
│  Connection Manager │
└──────────┬──────────┘
           │
    Snowflake Python
       Connector
           │
┌──────────▼──────────┐
│  Snowflake Account  │
│  ┌───────────────┐  │
│  │   Databases    │  │
│  ├───────────────┤  │
│  │  Cortex AI    │  │
│  ├───────────────┤  │
│  │   Warehouses  │  │
│  └───────────────┘  │
└─────────────────────┘
```

### Component Descriptions

- **FastMCP Server**: The core server that handles MCP protocol communication
- **Service Layer**: Modular components that provide specific functionality
  - **Cortex Tools**: Integration with Snowflake's AI services
  - **Object Management**: CRUD operations for Snowflake objects
  - **Query Engine**: SQL execution with permission controls
  - **Semantic Manager**: Business-friendly data access layer
- **Connection Manager**: Handles Snowflake authentication and session management

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- Snowflake account with appropriate permissions
- Access to Snowflake Cortex services (if using AI features)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/snowflake-mcp-server.git
cd snowflake-mcp-server
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables

Create a `.env` file in the project root:

```env
# Required Snowflake Credentials
SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password

# Optional Settings
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=MY_DATABASE
SNOWFLAKE_SCHEMA=PUBLIC
SNOWFLAKE_ROLE=SYSADMIN

# Service Configuration
SERVICE_CONFIG_FILE=services/configuration.yaml
```

## ⚙️ Configuration

### Service Configuration File

The server uses a YAML configuration file to define available services and permissions. Here's a comprehensive example:

```yaml
# services/configuration.yaml

# Cortex Search Services
search_services:
  - service_name: "product_search"
    description: "Search service that finds product information and reviews"
    database_name: "RETAIL_DB"
    schema_name: "PRODUCTS"
    columns: ["product_name", "description", "price", "rating"]
    limit: 20
    
  - service_name: "customer_insights"
    description: "Search service that analyzes customer feedback and support tickets"
    database_name: "SUPPORT_DB"
    schema_name: "TICKETS"
    columns: ["ticket_id", "customer_name", "issue", "resolution", "satisfaction_score"]
    limit: 10

# Cortex Analyst Services
analyst_services:
  - service_name: "sales_analyst"
    semantic_model: "@ANALYTICS.SEMANTIC.SALES_MODEL.yaml"
    description: "Analyst service that answers questions about sales performance and trends"
    
  - service_name: "inventory_analyst"
    semantic_model: "ANALYTICS.SEMANTIC.INVENTORY_VIEW"
    description: "Analyst service that analyzes inventory levels and supply chain metrics"

# Other Services Configuration
other_services:
  object_manager: true     # Enable database object management
  query_manager: true      # Enable SQL query execution
  semantic_manager: true   # Enable semantic view management

# SQL Statement Permissions
sql_statement_permissions:
  # Data Query Operations
  - Select: true
  - Describe: true
  
  # Data Modification Operations
  - Insert: true
  - Update: true
  - Delete: true
  - Merge: true
  - TruncateTable: false  # Disabled for safety
  
  # Schema Modification Operations
  - Create: true
  - Alter: true
  - Drop: false  # Disabled for safety
  
  # Transaction Control
  - Transaction: true
  - Commit: true
  - Rollback: true
  
  # Administrative Operations
  - Use: true
  - Command: true
  - Comment: true
  
  # Unknown statement types
  - Unknown: false  # Reject unrecognized statement types
```

### Understanding Configuration Options

#### Search Services
Each search service configuration includes:
- **service_name**: Unique identifier for the service
- **description**: Human-readable description (should start with "Search service that...")
- **database_name**: Snowflake database containing the search service
- **schema_name**: Schema within the database
- **columns** (optional): Specific columns to return in results
- **limit** (optional): Maximum number of results (default: 10)

#### Analyst Services
Each analyst service configuration includes:
- **service_name**: Unique identifier for the service
- **semantic_model**: Path to YAML file or name of Semantic View
- **description**: Human-readable description (should start with "Analyst service that...")

#### SQL Permissions
Control which SQL operations are allowed:
- Set to `true` to allow the operation
- Set to `false` to deny the operation
- Unspecified operations default to deny

## 🛠️ Available Services

### 1. Cortex Search Tools

Dynamic tools created based on your configuration:

```python
# Example: If you configured "product_search" service
search_product_search(
    query="wireless headphones under $200",
    columns=["product_name", "price", "rating"],
    filter_query={"@gte": {"price": 50}, "@lte": {"price": 200}}
)
```

### 2. Cortex Analyst Tools

Natural language to SQL conversion:

```python
# Example: If you configured "sales_analyst" service
analyst_sales_analyst(
    query="What were our top 5 products by revenue last quarter?"
)
```

### 3. Object Management Tools

#### create_object
Create Snowflake objects (databases, schemas, tables, etc.):

```python
create_object(
    object_type="table",
    target_object={
        "name": "CUSTOMER_ORDERS",
        "database_name": "RETAIL_DB",
        "schema_name": "SALES",
        "columns": [
            {"name": "order_id", "datatype": "NUMBER", "nullable": False},
            {"name": "customer_id", "datatype": "VARCHAR(100)"},
            {"name": "order_date", "datatype": "DATE"},
            {"name": "total_amount", "datatype": "DECIMAL(10,2)"}
        ]
    },
    mode="error_if_exists"
)
```

#### list_objects
List existing objects:

```python
list_objects(
    object_type="table",
    database_name="RETAIL_DB",
    schema_name="SALES",
    like="CUSTOMER%"
)
```

#### describe_object
Get detailed information about an object:

```python
describe_object(
    object_type="table",
    target_object={
        "name": "CUSTOMER_ORDERS",
        "database_name": "RETAIL_DB",
        "schema_name": "SALES"
    }
)
```

### 4. Query Management

#### run_snowflake_query
Execute SQL queries with permission controls:

```python
run_snowflake_query(
    statement="""
        SELECT 
            c.customer_name,
            COUNT(o.order_id) as order_count,
            SUM(o.total_amount) as total_spent
        FROM customers c
        JOIN orders o ON c.customer_id = o.customer_id
        WHERE o.order_date >= '2024-01-01'
        GROUP BY c.customer_name
        ORDER BY total_spent DESC
        LIMIT 10
    """
)
```

### 5. Semantic View Management

#### list_semantic_views
List available semantic views:

```python
list_semantic_views(
    database_name="ANALYTICS",
    schema_name="SEMANTIC"
)
```

#### query_semantic_view
Query semantic views using business-friendly terms:

```python
query_semantic_view(
    database_name="ANALYTICS",
    schema_name="SEMANTIC",
    view_name="SALES_METRICS",
    dimensions=[
        {"table": "sales", "name": "product_category"},
        {"table": "sales", "name": "region"}
    ],
    metrics=[
        {"table": "sales", "name": "total_revenue"},
        {"table": "sales", "name": "units_sold"}
    ],
    where_clause="region = 'North America'",
    order_by="total_revenue DESC",
    limit=100
)
```

## 💡 Usage Examples

### Example 1: Building a Sales Dashboard

```python
# 1. First, check available data
tables = list_objects(
    object_type="table",
    database_name="SALES_DB",
    schema_name="PUBLIC"
)

# 2. Run analysis query
sales_data = run_snowflake_query(
    statement="""
        WITH monthly_sales AS (
            SELECT 
                DATE_TRUNC('month', order_date) as month,
                product_category,
                SUM(revenue) as total_revenue,
                COUNT(DISTINCT customer_id) as unique_customers
            FROM sales_facts
            WHERE order_date >= DATEADD('month', -12, CURRENT_DATE())
            GROUP BY 1, 2
        )
        SELECT * FROM monthly_sales
        ORDER BY month DESC, total_revenue DESC
    """
)

# 3. Use Cortex Analyst for insights
insights = analyst_sales_analyst(
    query="What are the key trends in our sales data over the last 12 months?"
)
```

### Example 2: Customer Support Analysis

```python
# 1. Search for customer issues
issues = search_customer_insights(
    query="payment processing errors",
    filter_query={
        "@gte": {"created_date": "2024-01-01"},
        "@eq": {"priority": "high"}
    }
)

# 2. Analyze patterns
analysis = analyst_support_analyst(
    query="What are the common causes of payment processing errors?"
)

# 3. Create summary table
create_object(
    object_type="table",
    target_object={
        "name": "PAYMENT_ISSUES_SUMMARY",
        "database_name": "SUPPORT_DB",
        "schema_name": "ANALYTICS",
        "columns": [
            {"name": "issue_category", "datatype": "VARCHAR(100)"},
            {"name": "frequency", "datatype": "NUMBER"},
            {"name": "avg_resolution_time", "datatype": "NUMBER"},
            {"name": "last_updated", "datatype": "TIMESTAMP"}
        ]
    }
)
```

## 🚢 Deployment

### FastMCP Cloud Deployment (Recommended)

This server is specifically designed and optimized for deployment on FastMCP Cloud, which provides a managed environment for MCP servers with built-in scaling, monitoring, and security features.

#### Step 1: Prepare Your Repository

Ensure your repository structure follows FastMCP requirements:

```
snowflake-mcp-server/
├── mcp_server_snowflake/
│   ├── __init__.py
│   ├── server.py              # Main server with mcp instance
│   ├── cortex_services/       # Cortex AI integrations
│   ├── object_manager/        # Database object management
│   ├── query_manager/         # SQL query execution
│   ├── semantic_manager/      # Semantic view management
│   └── utils.py               # Utility functions
├── services/
│   └── configuration.yaml     # Service configuration
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Package configuration
└── README.md
```

#### Step 2: Configure in FastMCP Dashboard

1. **Login to FastMCP Cloud**: Navigate to [cloud.fastmcp.com](https://cloud.fastmcp.com)

2. **Create New Server**:
   - Click "New Server"
   - Name: `snowflake-mcp-server`
   - Repository: Link your GitHub repository

3. **Set Environment Variables**:
   ```
   SNOWFLAKE_ACCOUNT=your_account_identifier
   SNOWFLAKE_USER=service_account_user
   SNOWFLAKE_PASSWORD=secure_password
   SNOWFLAKE_WAREHOUSE=MCP_WAREHOUSE
   SNOWFLAKE_DATABASE=DEFAULT_DB
   SNOWFLAKE_SCHEMA=PUBLIC
   SNOWFLAKE_ROLE=MCP_ROLE
   SERVICE_CONFIG_FILE=services/configuration.yaml
   ```

4. **Configure Secrets** (for sensitive data):
   - Use FastMCP's secret management for passwords
   - Enable encryption at rest
   - Set up secret rotation schedules

#### Step 3: Deploy

Using FastMCP CLI:

```bash
# Install FastMCP CLI if not already installed
pip install fastmcp-cli

# Login to your FastMCP account
fastmcp login

# Deploy the server
fastmcp deploy \
  --name snowflake-mcp-server \
  --path . \
  --env production

# Check deployment status
fastmcp status snowflake-mcp-server
```

#### Step 4: Configure Auto-Scaling

FastMCP Cloud automatically handles scaling, but you can configure:

```yaml
# fastmcp.yaml (in your repository root)
scaling:
  min_instances: 1
  max_instances: 10
  target_cpu: 70
  target_memory: 80
  scale_down_delay: 300  # seconds
```

#### Step 5: Set Up Monitoring

FastMCP provides built-in monitoring, accessible from the dashboard:

- **Metrics**: Request rates, response times, error rates
- **Logs**: Real-time log streaming and historical logs
- **Alerts**: Configure alerts for errors or performance issues
- **Usage**: Track API calls and resource consumption

### Local Development

For local testing before deploying to FastMCP Cloud:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export SNOWFLAKE_ACCOUNT=your_account
export SNOWFLAKE_USER=your_user
export SNOWFLAKE_PASSWORD=your_password
export SERVICE_CONFIG_FILE=services/configuration.yaml

# Run the server locally
python -m mcp_server_snowflake.server

# Or use the FastMCP development server
fastmcp dev --reload
```

### Production Considerations for FastMCP Cloud

#### Service Account Setup

Create a dedicated Snowflake service account for FastMCP:

```sql
-- Create role for MCP server
CREATE ROLE MCP_ROLE;

-- Create service account user
CREATE USER mcp_service_account
    PASSWORD = 'strong_password_here'
    DEFAULT_ROLE = MCP_ROLE
    DEFAULT_WAREHOUSE = MCP_WAREHOUSE
    MUST_CHANGE_PASSWORD = FALSE;

-- Grant necessary permissions
GRANT USAGE ON WAREHOUSE MCP_WAREHOUSE TO ROLE MCP_ROLE;
GRANT USAGE ON DATABASE YOUR_DB TO ROLE MCP_ROLE;
GRANT USAGE ON SCHEMA YOUR_DB.PUBLIC TO ROLE MCP_ROLE;
GRANT SELECT ON ALL TABLES IN SCHEMA YOUR_DB.PUBLIC TO ROLE MCP_ROLE;
GRANT ROLE MCP_ROLE TO USER mcp_service_account;

-- For Cortex services
GRANT USAGE ON DATABASE CORTEX_DB TO ROLE MCP_ROLE;
GRANT USAGE ON SCHEMA CORTEX_DB.SEARCH TO ROLE MCP_ROLE;
```

#### FastMCP Cloud Features

1. **Automatic SSL/TLS**: All connections are encrypted by default
2. **Built-in Rate Limiting**: Configurable per-client rate limits
3. **API Key Management**: FastMCP handles API key generation and validation
4. **Audit Logging**: All requests are logged with client information
5. **Secret Rotation**: Automatic credential rotation support
6. **High Availability**: Multi-region deployment options
7. **Zero-Downtime Updates**: Blue-green deployments for updates

#### Performance Optimization

Configure these settings in your FastMCP dashboard:

```yaml
# fastmcp.performance.yaml
performance:
  connection_pool:
    min_size: 2
    max_size: 20
    idle_timeout: 300
  
  cache:
    enabled: true
    ttl: 300  # seconds
    max_size: 1000  # entries
  
  timeout:
    request: 30  # seconds
    query: 120   # seconds for long-running queries
  
  rate_limiting:
    requests_per_minute: 100
    burst_size: 20
```

#### Monitoring and Alerts

FastMCP Cloud provides comprehensive monitoring:

1. **Dashboard Metrics**:
   - Request volume and latency
   - Error rates by error type
   - Snowflake query performance
   - Resource utilization

2. **Alert Configuration**:
   ```yaml
   alerts:
     - name: high_error_rate
       condition: error_rate > 0.05
       action: email
       recipients: ["ops-team@company.com"]
     
     - name: slow_queries
       condition: p95_latency > 5000  # ms
       action: slack
       webhook: "https://hooks.slack.com/..."
   ```

3. **Log Aggregation**:
   - Structured JSON logs
   - Full query history
   - Error stack traces
   - Performance metrics

#### Cost Optimization

FastMCP Cloud pricing is based on usage. Optimize costs by:

1. **Caching Frequently Used Data**: Configure cache TTLs appropriately
2. **Query Optimization**: Use Snowflake query optimization techniques
3. **Connection Pooling**: Reuse connections efficiently
4. **Auto-Scaling Configuration**: Set appropriate min/max instances
5. **Scheduled Scaling**: Reduce instances during off-hours

## 🔒 Security Considerations

### Authentication Best Practices

1. **Never commit credentials** to version control
2. **Use environment variables** or secure secret management systems
3. **Implement key pair authentication** for production:

```python
# Using key pair authentication
SNOWFLAKE_PRIVATE_KEY_FILE=/path/to/private_key.p8
SNOWFLAKE_PRIVATE_KEY_PWD=passphrase
```

### Permission Management

1. **Principle of Least Privilege**: Grant only necessary permissions
2. **Role-Based Access Control**: Use Snowflake roles appropriately
3. **Audit SQL Permissions**: Regularly review sql_statement_permissions

### Network Security

1. **IP Whitelisting**: Configure Snowflake network policies
2. **Encrypted Connections**: Always use encrypted connections
3. **VPC/Private Link**: Use private connectivity when available

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Connection Issues

**Problem**: Cannot connect to Snowflake
```
Error: Failed to connect to Snowflake: Incorrect username or password was specified
```

**Solution**:
1. Verify credentials in environment variables
2. Check account identifier format (exclude .snowflakecomputing.com)
3. Ensure network connectivity to Snowflake
4. Verify user has appropriate permissions

#### Permission Denied

**Problem**: SQL statement execution denied
```
Error: Statement type of DROP is not allowed
```

**Solution**:
1. Review sql_statement_permissions in configuration
2. Add the operation to the allow list if appropriate
3. Check Snowflake role permissions

#### Service Not Found

**Problem**: Cortex service not accessible
```
Error: Cortex Search Error: The resource cannot be found
```

**Solution**:
1. Verify service exists in Snowflake
2. Check database and schema names in configuration
3. Ensure user has access to the service
4. Verify Cortex is enabled for your account

### Debug Mode

Enable detailed logging for troubleshooting:

```python
# In your environment or code
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

Verify server health:

```python
# Check connection
connection_info = get_connection_info()
print(f"Connected: {connection_info['configured']}")

# List available databases
databases = list_databases()
print(f"Accessible databases: {databases['count']}")

# Test query execution
test_result = run_snowflake_query("SELECT CURRENT_VERSION()")
print(f"Snowflake version: {test_result}")
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. Fork the repository
2. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

3. Make your changes following the coding standards:
   - Use type hints everywhere
   - Use `@dataclass` for classes
   - Follow Python 3.11+ patterns
   - Write comprehensive docstrings

4. Run tests:
```bash
pytest tests/
```

5. Submit a pull request

### Coding Standards

- **Type Hints**: Use `X | None` instead of `Optional[X]`
- **Classes**: Always use `@dataclass` decorator
- **Defaults**: Use `field(default_factory=list)` for mutable defaults
- **Paths**: Use `pathlib.Path` exclusively
- **Strings**: Use f-strings for formatting
- **Async**: Use modern async/await patterns

### Testing

Write tests for new features:

```python
# tests/test_new_feature.py
import pytest
from mcp_server_snowflake.your_module import your_function

@pytest.mark.asyncio
async def test_your_function():
    result = await your_function(param="value")
    assert result.success is True
    assert result.data is not None
```

## 📚 Additional Resources

- [Snowflake Documentation](https://docs.snowflake.com)
- [MCP Protocol Specification](https://github.com/anthropics/mcp)
- [FastMCP Documentation](https://fastmcp.com/docs)
- [Snowflake Cortex Documentation](https://docs.snowflake.com/en/guides-overview-ai-features)

## 📄 License

Copyright 2025 Snowflake Inc.
Licensed under the Apache License, Version 2.0

## 🙏 Acknowledgments

- Snowflake team for the comprehensive Python SDK
- Anthropic for the MCP protocol specification
- FastMCP community for the server framework
- Contributors and users of this project

---

For questions, issues, or suggestions, please open an issue on GitHub or contact the maintainers.
