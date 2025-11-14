# Architecture Overview

This document provides a comprehensive overview of the SQL MCP Server system architecture, including components, data flows, and network topology.

## Table of Contents

- [System Architecture](#system-architecture)
- [Component Diagram](#component-diagram)
- [Network Architecture](#network-architecture)
- [Data Flow](#data-flow)
- [Security Architecture](#security-architecture)
- [Deployment Architecture](#deployment-architecture)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Azure Subscription                             │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                        Resource Group                               │ │
│  │                                                                      │ │
│  │  ┌────────────────────────────────────────────────────────────┐   │ │
│  │  │                   Virtual Network (10.0.0.0/16)             │   │ │
│  │  │                                                              │   │ │
│  │  │  ┌──────────────────────────┐  ┌──────────────────────┐   │   │ │
│  │  │  │  Container Apps Subnet   │  │  Private Endpoint    │   │   │ │
│  │  │  │  (10.0.0.0/23)           │  │  Subnet              │   │   │ │
│  │  │  │                           │  │  (10.0.2.0/24)      │   │   │ │
│  │  │  │  ┌───────────────────┐   │  │                      │   │   │ │
│  │  │  │  │ Container Apps    │   │  │  ┌────────────────┐ │   │   │ │
│  │  │  │  │ Environment       │   │  │  │  SQL Private   │ │   │   │ │
│  │  │  │  │                   │   │  │  │  Endpoint      │ │   │   │ │
│  │  │  │  │ ┌───────────────┐ │   │  │  └────────┬───────┘ │   │   │ │
│  │  │  │  │ │ MCP Server    │ │   │  │           │         │   │   │ │
│  │  │  │  │ │ Container App │◄┼───┼──┼───────────┘         │   │   │ │
│  │  │  │  │ │               │ │   │  │                      │   │   │ │
│  │  │  │  │ │ - Node.js     │ │   │  │                      │   │   │ │
│  │  │  │  │ │ - MCP SDK     │ │   │  │                      │   │   │ │
│  │  │  │  │ │ - Health:8080 │ │   │  │                      │   │   │ │
│  │  │  │  │ └───────┬───────┘ │   │  │                      │   │   │ │
│  │  │  │  │         │         │   │  │                      │   │   │ │
│  │  │  │  │         │ Pulls   │   │  │                      │   │   │ │
│  │  │  │  │         │ Image   │   │  │                      │   │   │ │
│  │  │  │  └─────────┼─────────┘   │  │                      │   │   │ │
│  │  │  └────────────┼─────────────┘  └──────────────────────┘   │   │ │
│  │  └───────────────┼──────────────────────────────────────────────┘   │ │
│  │                  │                                                   │ │
│  │  ┌───────────────▼──────────┐    ┌──────────────────────────────┐  │ │
│  │  │  Azure Container         │    │  Azure SQL Server            │  │ │
│  │  │  Registry (ACR)          │    │                              │  │ │
│  │  │                          │    │  ┌────────────────────────┐  │  │ │
│  │  │  - mcp-server:latest     │    │  │  DevOpsMetrics DB      │  │  │ │
│  │  │  - mcp-server:<sha>      │    │  │                        │  │  │ │
│  │  │                          │    │  │  - BuildRuns           │  │  │ │
│  │  └──────────────────────────┘    │  │  - TestRuns            │  │  │ │
│  │                                   │  │  - TestFailures        │  │  │ │
│  │  ┌──────────────────────────┐    │  │  - Analytics Views     │  │  │ │
│  │  │  Azure Key Vault         │    │  └────────────────────────┘  │  │ │
│  │  │                          │    │                              │  │ │
│  │  │  Secrets:                │    │  Security:                   │  │ │
│  │  │  - sql-connection-string │    │  - No public access         │  │ │
│  │  │  - app-settings          │    │  - Private Endpoint only    │  │ │
│  │  │                          │    │  - Read-only user (mcp_user)│  │ │
│  │  └──────────────────────────┘    └──────────────────────────────┘  │ │
│  │                                                                      │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │  Log Analytics Workspace                                     │  │ │
│  │  │                                                                │  │ │
│  │  │  - Container App logs                                         │  │ │
│  │  │  - SQL audit logs                                             │  │ │
│  │  │  - Key Vault audit logs                                       │  │ │
│  │  │  - Metrics and diagnostics                                    │  │ │
│  │  └──────────────────────────────────────────────────────────────┘  │ │
│  │                                                                      │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │  Managed Identity (mcp-server-identity)                      │  │ │
│  │  │                                                                │  │ │
│  │  │  Permissions:                                                  │  │ │
│  │  │  - AcrPull (Container Registry)                               │  │ │
│  │  │  - Key Vault Secrets User                                     │  │ │
│  │  └──────────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘

External Systems:
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│  GitHub          │       │  ChatGPT Desktop │       │  GitHub Copilot  │
│  Enterprise      │       │                  │       │                  │
│                  │       │  Uses MCP to     │       │  Uses MCP to     │
│  - CI/CD         │       │  query database  │       │  query database  │
│  - OIDC Auth     │       │  via natural     │       │  for code        │
│  - Bicep Deploy  │       │  language        │       │  assistance      │
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

## Component Diagram

### Core Components

#### 1. SQL MCP Server (Node.js)
- **Purpose**: Model Context Protocol server for read-only SQL access
- **Language**: Node.js 20 / TypeScript-ready
- **Framework**: MCP SDK (@modelcontextprotocol/sdk)
- **Tools Exposed**:
  - `listTables`: List all accessible tables and views
  - `describeTable`: Get table schema and metadata
  - `runQuery`: Execute read-only SELECT queries
- **Security**:
  - Query validation (read-only enforcement)
  - SQL injection prevention
  - 30-second timeout
  - Input sanitization
  - Comprehensive logging

#### 2. Azure SQL Database
- **Edition**: General Purpose
- **Compute**: Serverless (auto-pause)
- **Storage**: 32 GB
- **Schema**:
  - **BuildRuns**: CI/CD build execution data
  - **TestRuns**: Individual test execution records
  - **TestFailures**: Detailed failure information
  - **Views**: Analytics views for flakiness, trends, etc.
- **Access**: Read-only via `mcp_user` account

#### 3. Azure Container Apps
- **Runtime**: Managed container platform
- **Ingress**: Internal only (no public access)
- **Scaling**: 1-3 replicas (auto-scale on CPU/requests)
- **Health Probes**:
  - Liveness: `/health`
  - Readiness: `/ready` (includes DB check)
- **Environment**: VNet-integrated for private connectivity

#### 4. Azure Key Vault
- **Purpose**: Secrets management
- **Secrets Stored**:
  - SQL connection strings
  - Application settings
- **Access**: Managed Identity with RBAC
- **Audit**: All access logged to Log Analytics

#### 5. Azure Container Registry
- **Purpose**: Docker image storage
- **Images**: MCP server container images
- **Access**: Managed Identity with AcrPull role
- **Retention**: 30-day policy for old images

#### 6. Log Analytics Workspace
- **Purpose**: Centralized logging and monitoring
- **Data Sources**:
  - Container App logs (stdout/stderr)
  - SQL Database audit logs
  - Key Vault access logs
  - Azure Resource Manager activity logs
- **Retention**: 30 days (dev), 90 days (prod)
- **Queries**: Pre-configured KQL queries for common scenarios

## Network Architecture

### VNet Configuration

**Address Space**: `10.0.0.0/16`

#### Subnets

1. **Container Apps Subnet** (`10.0.0.0/23`)
   - Delegated to `Microsoft.App/environments`
   - Network Security Group applied
   - Service Endpoints: Key Vault, SQL
   - Hosts: Container Apps Environment

2. **Private Endpoint Subnet** (`10.0.2.0/24`)
   - Private Endpoint network policies disabled
   - Hosts: SQL Private Endpoint
   - DNS: Private DNS Zone for SQL

### Network Security Groups

#### Container Apps NSG
- **Inbound**:
  - Allow: VNet → VNet
  - Allow: Azure Load Balancer health probes
  - Deny: All other inbound traffic
- **Outbound**:
  - Allow: All (default)

#### Private Endpoint NSG
- **Inbound**:
  - Allow: VNet → VNet
  - Deny: All other inbound traffic

### Private Connectivity

- **SQL Server**: Private Endpoint only, no public access
- **Private DNS Zone**: `privatelink.database.windows.net`
- **DNS Resolution**: Automatic within VNet
- **Benefits**:
  - Traffic never leaves Azure backbone
  - No public IP exposure
  - Enhanced security

## Data Flow

### 1. MCP Query Request Flow

```
[ChatGPT/Copilot]
      │
      │ (1) MCP Request (stdio)
      │     Tool: runQuery
      │     Query: "SELECT * FROM BuildRuns"
      ▼
[MCP Server - Container App]
      │
      │ (2) Validate Query
      │     - Check for read-only
      │     - Validate syntax
      │     - Sanitize inputs
      ▼
[Security Module]
      │
      │ (3) Execute via Parameterized Query
      ▼
[Database Module]
      │
      │ (4) Connect via Private Endpoint
      │     - Use mcp_user credentials
      │     - Connection from Key Vault
      ▼
[Azure SQL Database]
      │
      │ (5) Return Results
      ▼
[MCP Server]
      │
      │ (6) Format Response
      │     - JSON output
      │     - Include metadata
      ▼
[ChatGPT/Copilot]
      │
      │ (7) Present to User
      ▼
[User]
```

### 2. CI/CD Deployment Flow

```
[Developer]
      │
      │ (1) Push Code
      ▼
[GitHub Enterprise]
      │
      │ (2) Trigger CI Workflow
      │     - Lint, test, security scan
      │     - Build Docker image
      ▼
[GitHub Actions]
      │
      │ (3) Authenticate via OIDC
      ▼
[Azure AD]
      │
      │ (4) Push Image
      ▼
[Azure Container Registry]
      │
      │ (5) Trigger CD Workflow
      ▼
[GitHub Actions]
      │
      │ (6) Deploy Bicep Templates
      ▼
[Azure Resource Manager]
      │
      │ (7) Update Container App
      ▼
[Container Apps Environment]
      │
      │ (8) Pull New Image
      │     - Zero-downtime deployment
      │     - Health checks
      ▼
[MCP Server - Running]
```

### 3. Secrets Access Flow

```
[MCP Server Startup]
      │
      │ (1) Request Connection String
      │     Using Managed Identity
      ▼
[Azure Key Vault]
      │
      │ (2) Verify Identity
      │     - Check RBAC permissions
      │     - Audit log access
      ▼
[Azure AD]
      │
      │ (3) Return Secret
      ▼
[MCP Server]
      │
      │ (4) Establish DB Connection
      ▼
[Azure SQL Database]
```

## Security Architecture

### Defense in Depth

#### Layer 1: Network Security
- Private VNet with NSGs
- No public IP addresses
- Private Endpoint for SQL
- Internal-only ingress

#### Layer 2: Identity & Access
- Managed Identity (no credentials in code)
- Azure AD OIDC for CI/CD
- RBAC everywhere
- Least privilege principle

#### Layer 3: Application Security
- Query validation (read-only)
- Input sanitization
- SQL injection prevention
- Parameterized queries
- Rate limiting

#### Layer 4: Data Security
- Encryption in transit (TLS 1.2+)
- Encryption at rest (Azure default)
- Read-only database user
- SQL audit logging

#### Layer 5: Monitoring & Response
- All access logged
- Security alerts configured
- Log Analytics queries for anomalies
- Container vulnerability scanning

### Compliance & Auditing

- **Audit Logs**: All database access logged
- **Key Vault Logs**: All secret access logged
- **Activity Logs**: All Azure operations logged
- **Container Logs**: All application logs captured
- **Retention**: 90 days (configurable)

## Deployment Architecture

### Environments

#### Development
- Single region
- Serverless SQL (auto-pause)
- 1-2 container replicas
- Standard ACR
- 30-day log retention

#### Production
- Multi-region (optional)
- Provisioned SQL compute
- 2-10 container replicas
- Premium ACR with geo-replication
- 90-day log retention
- Zone redundancy

### High Availability

- **Container Apps**: Auto-scaling with min replicas
- **SQL Database**: Built-in HA (99.99% SLA)
- **Key Vault**: Globally distributed
- **Health Probes**: Automatic failover
- **Zero Downtime Deploys**: Blue-green deployments

### Disaster Recovery

- **SQL Backups**: Automated (7-35 days)
- **Point-in-Time Restore**: Available
- **Geo-Replication**: Optional for SQL
- **Infrastructure as Code**: Complete recovery via Bicep
- **RTO**: < 1 hour
- **RPO**: < 5 minutes

## Performance Considerations

### Scalability

- **Container Apps**: Horizontal auto-scaling (1-30 replicas)
- **SQL Database**: Serverless auto-scale (0.5-4 vCores)
- **Connection Pooling**: Managed by mssql driver
- **Query Timeout**: 30 seconds
- **Result Limits**: Max 1000 rows per query

### Optimization

- **Indexes**: Pre-configured on BuildRuns, TestRuns
- **Views**: Pre-aggregated analytics
- **Caching**: Connection pool maintained
- **Logging**: Async, non-blocking

## Cost Optimization

### Development
- **Container Apps**: Consumption plan (~$10-20/month)
- **SQL Database**: Serverless with auto-pause (~$20-30/month)
- **Other Services**: ~$10-20/month
- **Total**: ~$40-70/month

### Production
- **Container Apps**: Consumption plan (~$50-100/month)
- **SQL Database**: Provisioned compute (~$200-400/month)
- **Other Services**: ~$50-100/month
- **Total**: ~$300-600/month

### Cost Reduction Tips
1. Use serverless SQL in non-prod
2. Enable auto-pause for SQL
3. Scale container apps to zero when idle
4. Use Basic/Standard ACR for non-prod
5. Reduce log retention in dev/test

## Summary

The SQL MCP Server architecture provides:

✅ **Security**: Defense-in-depth with multiple layers
✅ **Scalability**: Auto-scaling for both compute and database
✅ **Reliability**: High availability with built-in redundancy
✅ **Observability**: Comprehensive logging and monitoring
✅ **Maintainability**: Infrastructure as Code for repeatable deployments
✅ **Cost-Effective**: Serverless and consumption-based pricing
✅ **Enterprise-Ready**: Supports GitHub Enterprise, Azure AD, compliance requirements
