# Using the SQL MCP Server

Guide for connecting and using the SQL MCP Server with ChatGPT Desktop and GitHub Copilot.

## MCP Server Configuration

### ChatGPT Desktop

**Location**: `~/Library/Application Support/ChatGPT/mcp.json` (macOS)

```json
{
  "mcpServers": {
    "sql-devops-metrics": {
      "command": "node",
      "args": ["/absolute/path/to/sql-mcp-server/src/server.js"],
      "env": {
        "SQL_CONNECTION_STRING": "Server=localhost,1433;Database=DevOpsMetrics;User ID=mcp_user;Password=McpUser@Pass123;Encrypt=True;TrustServerCertificate=True;",
        "NODE_ENV": "production",
        "LOG_LEVEL": "info"
      }
    }
  }
}
```

**Restart ChatGPT Desktop** after configuration.

### GitHub Copilot

**Location**: `.copilot/mcp.json` in your project root

```json
{
  "mcpServers": {
    "sql-devops-metrics": {
      "command": "node",
      "args": ["/absolute/path/to/sql-mcp-server/src/server.js"],
      "env": {
        "SQL_CONNECTION_STRING": "Server=localhost,1433;Database=DevOpsMetrics;User ID=mcp_user;Password=McpUser@Pass123;Encrypt=True;TrustServerCertificate=True;"
      }
    }
  }
}
```

## Example Natural Language Queries

### Exploring the Database

**User**: "What tables are available in the database?"

**Expected**: MCP calls `listTables` tool, returns list of BuildRuns, TestRuns, TestFailures tables.

---

**User**: "Show me the structure of the BuildRuns table"

**Expected**: MCP calls `describeTable` with tableName="BuildRuns", returns column definitions, types, constraints.

### Querying Build Data

**User**: "Show me the last 10 builds"

**MCP generates**:
```sql
SELECT TOP 10 * FROM BuildRuns
ORDER BY StartTime DESC
```

---

**User**: "How many builds failed in the last 7 days?"

**MCP generates**:
```sql
SELECT COUNT(*) AS FailedBuilds
FROM BuildRuns
WHERE Status = 'Failed'
  AND StartTime >= DATEADD(DAY, -7, GETUTCDATE())
```

### Analyzing Test Flakiness

**User**: "Which tests are the most flaky?"

**MCP generates**:
```sql
SELECT TOP 10 *
FROM vw_TestFlakiness
WHERE FlakinessScore > 50
ORDER BY FlakinessScore DESC
```

---

**User**: "Show me test pass rates by suite"

**MCP generates**:
```sql
SELECT
    TestSuite,
    COUNT(*) AS TotalTests,
    SUM(CASE WHEN Status = 'Passed' THEN 1 ELSE 0 END) AS PassedTests,
    CAST(SUM(CASE WHEN Status = 'Passed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS PassRate
FROM TestRuns
GROUP BY TestSuite
ORDER BY PassRate ASC
```

### Build Trends

**User**: "Show daily build success rate for the main branch"

**MCP generates**:
```sql
SELECT *
FROM vw_BuildStatsDaily
WHERE Branch = 'main'
  AND BuildDate >= DATEADD(DAY, -30, GETUTCDATE())
ORDER BY BuildDate DESC
```

## Available Tools

### listTables

**Description**: List all accessible tables and views

**Parameters**:
- `schema` (optional): Filter by schema name

**Example**:
```json
{
  "tool": "listTables",
  "arguments": {
    "schema": "dbo"
  }
}
```

### describeTable

**Description**: Get detailed schema information

**Parameters**:
- `tableName` (required): Name of table
- `schema` (optional): Schema name (default: dbo)

**Example**:
```json
{
  "tool": "describeTable",
  "arguments": {
    "tableName": "BuildRuns",
    "schema": "dbo"
  }
}
```

### runQuery

**Description**: Execute read-only SQL query

**Parameters**:
- `query` (required): SELECT query
- `maxRows` (optional): Max rows to return (default: 100, max: 1000)

**Example**:
```json
{
  "tool": "runQuery",
  "arguments": {
    "query": "SELECT * FROM BuildRuns WHERE Status = 'Failed'",
    "maxRows": 50
  }
}
```

## Troubleshooting

### MCP Server Not Responding

```bash
# Check if server is running
ps aux | grep "node.*server.js"

# Check logs
tail -f /path/to/logs/mcp-server.log

# Test connection manually
curl http://localhost:8080/health
```

### Connection Refused Errors

```bash
# Verify SQL Server is accessible
sqlcmd -S localhost,1433 -U mcp_user -P "McpUser@Pass123" -Q "SELECT 1"

# Check connection string in config
cat ~/.config/ChatGPT/mcp.json | grep SQL_CONNECTION_STRING
```

### Query Validation Errors

Queries must be read-only:
- ✅ `SELECT * FROM BuildRuns`
- ❌ `UPDATE BuildRuns SET Status = 'Success'`
- ❌ `DELETE FROM TestRuns`
