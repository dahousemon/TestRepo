# Local Development Environment

This directory contains everything you need to run the SQL MCP Server locally.

## Quick Start

### Prerequisites

- **Docker Desktop** (v20.10+)
- **Docker Compose** (v2.0+)
- **Node.js** (v20+) - if running outside Docker
- **Git**

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and update passwords (optional)
nano .env
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check service health
docker-compose ps
```

### 3. Verify Setup

```bash
# Check SQL Server is ready
docker exec -it sql-mcp-server-db /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P "YourStrong@Passw0rd123" \
  -Q "SELECT name FROM sys.databases"

# Check MCP Server health
curl http://localhost:8080/health
curl http://localhost:8080/ready
```

### 4. Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **MCP Server Health** | http://localhost:8080/health | N/A |
| **SQL Server** | localhost:1433 | User: `mcp_user`<br>Pass: `McpUser@Pass123` |
| **SQL Admin** | localhost:1433 | User: `sa`<br>Pass: `YourStrong@Passw0rd123` |
| **Adminer (SQL UI)** | http://localhost:8090 | System: `MS SQL`<br>Server: `sqlserver`<br>User: `mcp_user` |

## Development Workflows

### Using Docker Compose (Recommended)

```bash
# Start services in background
docker-compose up -d

# View logs
docker-compose logs -f mcp-server

# Restart MCP Server after code changes
docker-compose restart mcp-server

# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

### Using VS Code Dev Containers

1. Install **Remote - Containers** extension
2. Open project in VS Code
3. Press `F1` → **Remote-Containers: Reopen in Container**
4. VS Code will build and connect to the dev container

Features:
- ✅ Full IDE support inside container
- ✅ Extensions pre-installed
- ✅ SQL Server connection configured
- ✅ Debugging configured

### Running Locally (Without Docker)

```bash
# Install dependencies
npm install

# Start SQL Server in Docker
docker-compose up -d sqlserver sql-init

# Set environment variables
export SQL_CONNECTION_STRING="Server=localhost,1433;Database=DevOpsMetrics;User ID=mcp_user;Password=McpUser@Pass123;Encrypt=True;TrustServerCertificate=True;Connection Timeout=30;"
export NODE_ENV=development
export LOG_LEVEL=debug

# Start MCP Server
npm start

# Or with nodemon for auto-reload
npm run dev
```

## Database Management

### Connect with sqlcmd

```bash
# As admin (sa)
docker exec -it sql-mcp-server-db /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P "YourStrong@Passw0rd123"

# As MCP user (read-only)
docker exec -it sql-mcp-server-db /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U mcp_user -P "McpUser@Pass123" -d DevOpsMetrics
```

### Query from Host

```bash
# Install sqlcmd on host (optional)
# macOS
brew install sqlcmd

# Linux
curl https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list | sudo tee /etc/apt/sources.list.d/msprod.list
sudo apt-get update
sudo apt-get install mssql-tools unixodbc-dev

# Connect
sqlcmd -S localhost,1433 -U mcp_user -P "McpUser@Pass123" -d DevOpsMetrics
```

### Example Queries

```sql
-- List all tables
SELECT * FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;

-- View recent builds
SELECT TOP 10 * FROM BuildRuns
ORDER BY StartTime DESC;

-- Check test flakiness
SELECT * FROM vw_TestFlakiness
WHERE FlakinessScore > 50
ORDER BY FlakinessScore DESC;

-- Daily build stats
SELECT * FROM vw_BuildStatsDaily
WHERE BuildDate >= DATEADD(DAY, -7, GETUTCDATE())
ORDER BY BuildDate DESC;
```

### Reset Database

```bash
# Stop services
docker-compose down

# Remove volumes
docker volume rm sql-mcp-server-data

# Start fresh
docker-compose up -d
```

## Testing the MCP Server

### Manual Testing

Use the health check endpoints:

```bash
# Health check (liveness)
curl http://localhost:8080/health

# Readiness check (includes DB connectivity)
curl http://localhost:8080/ready
```

### Integration with ChatGPT Desktop

1. Copy `chatgpt-mcp-config.json` to ChatGPT config directory:
   - **macOS**: `~/Library/Application Support/ChatGPT/mcp.json`
   - **Windows**: `%APPDATA%\ChatGPT\mcp.json`
   - **Linux**: `~/.config/ChatGPT/mcp.json`

2. Update the absolute path to `server.js`

3. Restart ChatGPT Desktop

4. Test with prompts:
   - "List all tables in the database"
   - "Show me the schema for BuildRuns table"
   - "What are the most flaky tests?"

### Integration with GitHub Copilot

1. Copy `.copilot/mcp.json` to your project root as `.copilot/mcp.json`

2. Update the absolute path to `server.js`

3. Restart VS Code

4. Use Copilot Chat:
   - "What tables are in the database?"
   - "Show me recent build failures"
   - "Analyze test flakiness trends"

## Debugging

### VS Code Debugging

Launch configurations are pre-configured in `.vscode/launch.json`:

1. **Launch MCP Server** - Start server with debugger attached
2. **Attach to MCP Server** - Attach to running server
3. **Run Tests** - Run all tests with coverage
4. **Debug Single Test** - Debug currently open test file

**Usage:**
1. Press `F5` or go to **Run and Debug**
2. Select configuration
3. Set breakpoints
4. Start debugging

### View Logs

```bash
# All services
docker-compose logs -f

# MCP Server only
docker-compose logs -f mcp-server

# SQL Server only
docker-compose logs -f sqlserver

# Last 100 lines
docker-compose logs --tail=100 mcp-server
```

### Common Issues

#### Port Already in Use

```bash
# Find process using port
lsof -i :1433  # or 8080

# Kill process
kill -9 <PID>
```

#### SQL Server Won't Start

```bash
# Check logs
docker-compose logs sqlserver

# Common issues:
# - Weak SA password (must be strong)
# - Insufficient Docker memory (need 2GB+)
# - Port 1433 already in use
```

#### MCP Server Can't Connect to Database

```bash
# Check SQL Server is healthy
docker-compose ps

# Test connection manually
docker exec -it sql-mcp-server-db /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U mcp_user -P "McpUser@Pass123" -d DevOpsMetrics \
  -Q "SELECT 1"

# Check connection string in .env
cat .env | grep SQL_CONNECTION_STRING
```

## Development Tools

### Adminer (Web SQL Client)

Access at http://localhost:8090

**Login:**
- System: `MS SQL`
- Server: `sqlserver`
- Username: `mcp_user` (or `sa` for admin)
- Password: `McpUser@Pass123` (or SA password)
- Database: `DevOpsMetrics`

### Azure Data Studio (Optional)

Download: https://docs.microsoft.com/en-us/sql/azure-data-studio/download

**Connection:**
- Server: `localhost,1433`
- Authentication: SQL Login
- Username: `mcp_user`
- Password: `McpUser@Pass123`
- Database: `DevOpsMetrics`

## Environment Variables

See `.env.example` for all available variables.

**Key variables:**

| Variable | Description | Default |
|----------|-------------|---------|
| `SQL_ADMIN_PASSWORD` | SA password | `YourStrong@Passw0rd123` |
| `SQL_USER` | MCP user | `mcp_user` |
| `SQL_PASSWORD` | MCP password | `McpUser@Pass123` |
| `NODE_ENV` | Node environment | `development` |
| `LOG_LEVEL` | Logging level | `debug` |

## Running Tests

```bash
# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- src/security.test.js

# Watch mode
npm run test:watch
```

## Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes (data will be lost)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Complete cleanup
docker-compose down -v --rmi all --remove-orphans
```

## Tips

1. **Use dev containers** for consistent environment
2. **Keep SA password strong** (Azure SQL requirements)
3. **Use Adminer** for quick SQL queries
4. **Check logs** when troubleshooting
5. **Reset database** if schema changes
6. **Use VS Code debugging** for efficient debugging

## Next Steps

- Read [/docs/03-using-mcp.md](../docs/03-using-mcp.md) for usage examples
- Check [/docs/04-sql-examples.md](../docs/04-sql-examples.md) for query examples
- Review [/docs/01-setup-guide.md](../docs/01-setup-guide.md) for deployment to Azure
