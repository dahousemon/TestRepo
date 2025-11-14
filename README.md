# SQL MCP Server - Enterprise Edition

Production-ready SQL Model Context Protocol (MCP) server for secure read-only access to Azure SQL Database in GitHub Enterprise environments.

## 🎯 Overview

This system provides AI assistants (ChatGPT, GitHub Copilot) with secure, read-only access to your DevOps metrics stored in Azure SQL Database through the Model Context Protocol (MCP).

**Use Cases**:
- Query build and test data using natural language
- Analyze test flakiness trends
- Generate reports on CI/CD performance
- Investigate build failures
- Track quality metrics over time

## ✨ Features

### Security
- ✅ Read-only database access
- ✅ SQL injection prevention
- ✅ Azure Private Endpoint (no public SQL access)
- ✅ Azure Key Vault for secrets
- ✅ Managed Identity authentication
- ✅ Query validation and sanitization
- ✅ Comprehensive audit logging

### Infrastructure
- ✅ Complete Bicep Infrastructure as Code
- ✅ Azure Container Apps with auto-scaling
- ✅ GitHub Enterprise CI/CD with OIDC
- ✅ VNet isolation with NSGs
- ✅ Log Analytics integration
- ✅ Zero-downtime deployments

### Developer Experience
- ✅ Local development with Docker Compose
- ✅ VS Code Dev Containers
- ✅ ChatGPT Desktop integration
- ✅ GitHub Copilot integration
- ✅ Comprehensive documentation
- ✅ Sample data and queries

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Enterprise                         │
│                   CI/CD (OIDC Auth)                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Azure Subscription                        │
│                                                              │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Container App  │  │  Azure SQL   │  │  Key Vault     │  │
│  │ (MCP Server)   │──│  Database    │  │  (Secrets)     │  │
│  │                │  │  (Private    │  │                │  │
│  │ - Node.js      │  │   Endpoint)  │  │                │  │
│  │ - Read-only    │  │              │  │                │  │
│  └────────────────┘  └──────────────┘  └────────────────┘  │
│          │                                                   │
│  ┌───────▼────────────────────────────────────────────┐    │
│  │       Log Analytics Workspace                       │    │
│  │       (Centralized Logging & Monitoring)            │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│           AI Assistants (via MCP Protocol)                   │
│                                                              │
│    ChatGPT Desktop          GitHub Copilot                   │
│         │                        │                           │
│         └────────────────────────┘                           │
│                    │                                         │
│          Natural Language Queries                            │
└──────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
sql-mcp-server/
├── src/                    # MCP Server implementation
│   ├── server.js          # Main MCP server
│   ├── db.js              # Database connection
│   ├── security.js        # Query validation
│   ├── logger.js          # Structured logging
│   └── health.js          # Health check endpoints
├── sql/                    # Database scripts
│   ├── 01-security-setup.sql
│   ├── 02-create-schema.sql
│   ├── 03-create-views.sql
│   └── 04-sample-data.sql
├── iac/                    # Bicep infrastructure
│   ├── main.bicep
│   └── modules/
├── github/workflows/       # CI/CD pipelines
│   ├── ci.yml
│   └── cd.yml
├── local-dev/              # Local development
│   ├── docker-compose.yaml
│   ├── .env.example
│   └── .devcontainer/
├── docs/                   # Documentation
│   ├── 00-architecture.md
│   ├── 01-setup-guide.md
│   ├── 02-security-model.md
│   ├── 03-using-mcp.md
│   └── 04-sql-examples.md
├── optional/               # Optional components
│   └── function-app/      # Event-driven ingestion
├── Dockerfile
├── package.json
└── README.md
```

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd sql-mcp-server

# Start local environment
cd local-dev
cp .env.example .env
docker-compose up -d

# Verify
curl http://localhost:8080/health
```

**Access**:
- MCP Server: http://localhost:8080
- SQL Server: localhost:1433
- Adminer (SQL UI): http://localhost:8090

### Azure Deployment

```bash
# Login to Azure
az login
az account set --subscription <subscription-id>

# Deploy infrastructure
az group create --name rg-mcp-server-dev --location eastus
az deployment group create \
  --resource-group rg-mcp-server-dev \
  --template-file iac/main.bicep \
  --parameters iac/parameters.json

# Setup database
sqlcmd -S <sql-server>.database.windows.net -U sqladmin \
  -i sql/01-security-setup.sql \
  -i sql/02-create-schema.sql \
  -i sql/03-create-views.sql

# Build and push image
az acr build --registry <acr-name> --image mcp-server:latest .

# Update container app
az containerapp update \
  --name <app-name> \
  --resource-group rg-mcp-server-dev \
  --image <acr-name>.azurecr.io/mcp-server:latest
```

## 🔧 Configuration

### ChatGPT Desktop

Add to `~/Library/Application Support/ChatGPT/mcp.json`:

```json
{
  "mcpServers": {
    "sql-devops-metrics": {
      "command": "node",
      "args": ["/path/to/sql-mcp-server/src/server.js"],
      "env": {
        "SQL_CONNECTION_STRING": "Server=localhost,1433;Database=DevOpsMetrics;..."
      }
    }
  }
}
```

### GitHub Copilot

Add `.copilot/mcp.json` to your project root with similar configuration.

## 📊 Example Queries

**Natural Language** → **SQL** (automated by MCP)

- "Show me the last 10 builds" → `SELECT TOP 10 * FROM BuildRuns ORDER BY StartTime DESC`
- "Which tests are flaky?" → `SELECT * FROM vw_TestFlakiness WHERE FlakinessScore > 50`
- "Build success rate by branch" → Aggregation query with GROUP BY

## 🛡️ Security

- **Read-Only**: MCP user can only SELECT
- **Private Network**: SQL Server has no public access
- **Secrets Management**: All credentials in Azure Key Vault
- **Query Validation**: Destructive operations blocked
- **Audit Logging**: All access logged to Log Analytics
- **OIDC Authentication**: No long-lived credentials in CI/CD

See [docs/02-security-model.md](docs/02-security-model.md) for details.

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/00-architecture.md) | System architecture and diagrams |
| [Setup Guide](docs/01-setup-guide.md) | Local and Azure deployment |
| [Security Model](docs/02-security-model.md) | Security controls and best practices |
| [Using MCP](docs/03-using-mcp.md) | ChatGPT/Copilot integration |
| [SQL Examples](docs/04-sql-examples.md) | Useful queries |

## 🧪 Database Schema

### BuildRuns
Tracks CI/CD build executions.

**Columns**: BuildRunId, Branch, StartTime, EndTime, Status, TriggeredBy, CommitSha, BuildNumber

### TestRuns
Individual test execution records.

**Columns**: TestRunId, BuildRunId, TestName, TestSuite, StartTime, EndTime, Status

### TestFailures
Detailed failure information.

**Columns**: TestFailureId, TestRunId, FailureReason, ErrorMessage, StackTrace, FailureCategory

### Analytics Views
- `vw_TestFlakiness` - Flaky test detection with scoring
- `vw_BuildStatsDaily` - Daily build metrics
- `vw_RecentBuildSummary` - Recent builds with test metrics
- `vw_TopFailingTests` - Most frequently failing tests

## 🔄 CI/CD

### CI Pipeline
- Lint (ESLint, Prettier)
- Test (Jest with coverage)
- Security scan (Snyk, Trivy)
- Build Docker image
- Push to ACR

### CD Pipeline
- Authenticate via OIDC (no stored credentials)
- Deploy Bicep infrastructure
- Update Container App
- Health checks and smoke tests

## 💡 Optional Components

### Event-Driven Data Ingestion

Azure Function for automatic build/test data insertion:

```bash
cd optional/function-app
npm install
func start
```

See [optional/README.md](optional/README.md) for details.

## 🐛 Troubleshooting

### Local Development

```bash
# Check service health
docker-compose ps

# View logs
docker-compose logs -f mcp-server

# Test SQL connection
docker exec -it sql-mcp-server-db /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U mcp_user -P "McpUser@Pass123" -d DevOpsMetrics
```

### Azure Deployment

```bash
# Check container logs
az containerapp logs show --name <app-name> --resource-group <rg> --tail 100

# Verify revision status
az containerapp revision list --name <app-name> --resource-group <rg>

# Test health endpoint (requires VPN/bastion access)
curl https://<internal-fqdn>/health
```

## 📈 Monitoring

**Key Metrics**:
- Query execution time (p50, p95, p99)
- Error rate
- Container health status
- SQL connection pool usage

**Alerts Configured**:
- Container restarts (3+ in 10 minutes)
- Failed authentication attempts (5+ in 5 minutes)
- High error rate (>5% in 5 minutes)

## 🤝 Contributing

1. Create feature branch
2. Make changes
3. Run tests: `npm test`
4. Lint: `npm run lint`
5. Create pull request

## 📝 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- Model Context Protocol by Anthropic
- Azure SQL Database team
- GitHub Actions team
- Open source community

## 📞 Support

- **Issues**: GitHub Issues
- **Docs**: `/docs` directory
- **Examples**: `/sql` and `local-dev/`

## 🗺️ Roadmap

- [ ] Multi-region deployment support
- [ ] Advanced caching layer
- [ ] Query result pagination
- [ ] GraphQL endpoint (optional)
- [ ] Prometheus metrics export
- [ ] Terraform version (alternative to Bicep)

---

**Built with ❤️ for GitHub Enterprise environments**

For detailed setup instructions, see [docs/01-setup-guide.md](docs/01-setup-guide.md).
