# Security Model

Comprehensive security documentation for the SQL MCP Server system.

## Table of Contents

- [Security Principles](#security-principles)
- [SQL Read-Only Model](#sql-read-only-model)
- [Azure Key Vault Usage](#azure-key-vault-usage)
- [Network Security](#network-security)
- [Identity and Access Management](#identity-and-access-management)
- [Application Security](#application-security)
- [Monitoring and Auditing](#monitoring-and-auditing)
- [Compliance](#compliance)

## Security Principles

The SQL MCP Server is built on these core security principles:

1. **Least Privilege**: Every component has minimum required permissions
2. **Defense in Depth**: Multiple layers of security controls
3. **Zero Trust**: Verify explicitly, never trust implicitly
4. **Secure by Default**: Security enabled out-of-the-box
5. **Audit Everything**: Complete audit trail for all access

## SQL Read-Only Model

### Database User Configuration

The MCP server connects to Azure SQL using a dedicated read-only user:

**User**: `mcp_user`
**Permissions**:
- ✅ SELECT on all tables
- ✅ VIEW DEFINITION (for metadata)
- ✅ db_datareader role
- ❌ INSERT - Explicitly denied
- ❌ UPDATE - Explicitly denied
- ❌ DELETE - Explicitly denied
- ❌ DROP - Explicitly denied
- ❌ ALTER - Explicitly denied
- ❌ CREATE - Explicitly denied

### Query Validation

All queries are validated before execution:

```javascript
// Validation checks:
1. Query must start with SELECT or WITH (CTE)
2. No destructive keywords (INSERT, UPDATE, DELETE, DROP, etc.)
3. No dangerous patterns (xp_cmdshell, sp_executesql, etc.)
4. No multiple statements (semicolon-separated)
5. No SQL comments that could hide malicious code
```

Example validation:

```javascript
// Valid queries
"SELECT * FROM BuildRuns WHERE Status = 'Failed'"
"SELECT TOP 10 * FROM TestRuns ORDER BY StartTime DESC"
"WITH FlakTests AS (...) SELECT * FROM FlakyTests"

// Blocked queries
"SELECT * FROM Users; DROP TABLE Users;" // Multiple statements
"UPDATE BuildRuns SET Status = 'Success'" // Destructive operation
"EXEC xp_cmdshell 'dir'" // Dangerous stored procedure
```

### SQL Injection Prevention

Multiple layers protect against SQL injection:

1. **Parameterized Queries**: All user inputs use SQL parameters
2. **Input Sanitization**: Remove dangerous characters
3. **Query Validation**: Reject suspicious patterns
4. **Connection String Security**: No credentials in code

Example parameterized query:

```javascript
// Secure approach (used)
const params = [
  { name: 'schema', type: 'NVarChar', value: schemaName },
  { name: 'table', type: 'NVarChar', value: tableName }
];
await query("SELECT * FROM @schema.@table", params);

// Insecure approach (NOT used)
await query(`SELECT * FROM ${schemaName}.${tableName}`);
```

### Query Timeout Enforcement

All queries have a 30-second timeout to prevent:
- Resource exhaustion
- Runaway queries
- Denial of service

```javascript
// Configured in db.js
const QUERY_TIMEOUT = 30000; // 30 seconds
request.timeout = QUERY_TIMEOUT;
```

## Azure Key Vault Usage

### Secrets Stored

Key Vault stores all sensitive configuration:

| Secret Name | Purpose | Accessed By |
|-------------|---------|-------------|
| `sql-connection-string` | SQL Server connection | MCP Server |
| `sql-admin-password` | SQL admin password | CI/CD only |

### Access Control

**Managed Identity**: `mcp-server-identity`

**Permissions**:
- Key Vault Secrets User (read-only)
- No keys or certificates access
- No management operations

### Secret Rotation

Secrets should be rotated periodically:

```bash
# Update SQL password
az sql server update \
  --resource-group $RG \
  --name $SQL_SERVER \
  --admin-password "NewStrongPassword123!"

# Update Key Vault secret
az keyvault secret set \
  --vault-name $KEY_VAULT \
  --name sql-connection-string \
  --value "Server=...;Password=NewStrongPassword123!;..."

# Restart Container App to pick up new secret
az containerapp revision restart \
  --name $CONTAINER_APP \
  --resource-group $RG
```

### Audit Logging

All Key Vault access is logged:

```kql
// Query in Log Analytics
AzureDiagnostics
| where ResourceType == "VAULTS"
| where OperationName == "SecretGet"
| where identity_claim_appid_g == "<managed-identity-id>"
| project TimeGenerated, CallerIPAddress, OperationName, Resource
```

## Network Security

### Virtual Network Isolation

```
Internet
    │
    X (No Public Access)
    │
┌───▼────────────────────────────┐
│  Azure VNet (10.0.0.0/16)      │
│                                 │
│  ┌──────────────────────────┐  │
│  │ Container Apps Subnet    │  │
│  │ (10.0.0.0/23)            │  │
│  │ - Internal ingress only  │  │
│  │ - No public IP           │  │
│  └──────────────────────────┘  │
│                                 │
│  ┌──────────────────────────┐  │
│  │ Private Endpoint Subnet  │  │
│  │ (10.0.2.0/24)            │  │
│  │ - SQL Private Endpoint   │  │
│  └──────────────────────────┘  │
└─────────────────────────────────┘
```

### Network Security Groups

**Container Apps NSG Rules**:

| Priority | Direction | Source | Destination | Port | Action |
|----------|-----------|--------|-------------|------|--------|
| 100 | Inbound | VNet | VNet | Any | Allow |
| 110 | Inbound | AzureLoadBalancer | Any | Any | Allow |
| 4096 | Inbound | Any | Any | Any | Deny |

**Private Endpoint NSG Rules**:

| Priority | Direction | Source | Destination | Port | Action |
|----------|-----------|--------|-------------|------|--------|
| 100 | Inbound | VNet | VNet | Any | Allow |
| 4096 | Inbound | Any | Any | Any | Deny |

### SQL Private Endpoint

SQL Server has:
- ❌ Public network access disabled
- ✅ Private Endpoint in VNet
- ✅ Private DNS resolution
- ✅ Traffic never leaves Azure backbone

Connection flow:

```
MCP Server Container
    │
    │ (Private IP: 10.0.0.x)
    ▼
Private Endpoint
    │
    │ (Private IP: 10.0.2.x)
    ▼
SQL Server (privatelink.database.windows.net)
    │
    │ (No public IP)
    ▼
DevOpsMetrics Database
```

### TLS Encryption

All connections use TLS 1.2+:
- Container Apps → SQL Server: TLS 1.2
- Container Apps → Key Vault: TLS 1.2
- GitHub Actions → Azure: TLS 1.2

## Identity and Access Management

### Managed Identity

The MCP server uses **User-Assigned Managed Identity**:

**Benefits**:
- No passwords in code or config
- Automatic credential rotation
- Azure AD authentication
- RBAC enforcement

**Permissions**:

| Resource | Role | Scope |
|----------|------|-------|
| Azure Container Registry | AcrPull | ACR resource |
| Azure Key Vault | Key Vault Secrets User | Key Vault resource |

### Azure AD OIDC for CI/CD

GitHub Actions authenticate using OpenID Connect:

**Traditional (not used)**:
```yaml
# Service principal credentials stored as secrets
- uses: azure/login@v1
  with:
    creds: ${{ secrets.AZURE_CREDENTIALS }}
```

**OIDC (used)**:
```yaml
# No long-lived credentials
permissions:
  id-token: write
- uses: azure/login@v1
  with:
    client-id: ${{ secrets.AZURE_CLIENT_ID }}
    tenant-id: ${{ secrets.AZURE_TENANT_ID }}
    subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

Benefits:
- No stored credentials
- Short-lived tokens (hours)
- Automatic expiration
- Federated trust

### RBAC Hierarchy

```
Azure Subscription
    │
    ├─ Resource Group: rg-mcp-server-dev
    │  ├─ Role: Contributor
    │  │  └─ GitHub Actions Service Principal
    │  │
    │  └─ Resources:
    │     ├─ Container App
    │     │  └─ Identity: mcp-server-identity
    │     │
    │     ├─ Key Vault
    │     │  └─ RBAC: Key Vault Secrets User
    │     │     └─ mcp-server-identity
    │     │
    │     └─ ACR
    │        └─ RBAC: AcrPull
    │           └─ mcp-server-identity
```

## Application Security

### Input Validation

All user inputs are validated:

```javascript
// Table/schema names
function isValidObjectName(name) {
  // Only alphanumeric and underscore
  const pattern = /^[a-zA-Z_][a-zA-Z0-9_]{0,127}$/;
  return pattern.test(name);
}

// Sanitize input
function sanitizeInput(input) {
  // Remove dangerous characters
  return input.replace(/[^\w\s.-]/g, '').substring(0, 128);
}
```

### Rate Limiting

Simple in-memory rate limiting prevents abuse:

```javascript
// 100 requests per minute per client
checkRateLimit(clientId, 100, 60000);
```

For production, use Azure API Management or Azure Front Door.

### Security Headers

(If HTTP ingress is enabled):

```javascript
// Recommended security headers
res.headers({
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',
  'X-XSS-Protection': '1; mode=block',
  'Strict-Transport-Security': 'max-age=31536000'
});
```

### Container Security

**Base Image**: `node:20-alpine`
- Minimal attack surface
- Regular security updates
- Non-root user

**Dockerfile Security**:
```dockerfile
# Multi-stage build (minimal final image)
FROM node:20-alpine

# Non-root user
RUN adduser -S nodejs -u 1001
USER nodejs

# Health check
HEALTHCHECK CMD curl -f http://localhost:8080/health
```

**Image Scanning**:
- Trivy scan in CI/CD
- Azure Defender for Container Registry
- Vulnerability alerts

## Monitoring and Auditing

### SQL Audit Logging

Azure SQL Database auditing enabled:

```sql
-- Audited events
- SUCCESSFUL_DATABASE_AUTHENTICATION_GROUP
- FAILED_DATABASE_AUTHENTICATION_GROUP
- BATCH_COMPLETED_GROUP
```

View audit logs:

```kql
AzureDiagnostics
| where ResourceType == "SERVERS/DATABASES"
| where Category == "SQLSecurityAuditEvents"
| project TimeGenerated, action_name_s, database_name_s, statement_s
```

### Application Logging

All MCP tool calls are logged:

```json
{
  "timestamp": "2025-01-14T10:30:00Z",
  "level": "info",
  "message": "Tool called",
  "tool": "runQuery",
  "queryLength": 45,
  "maxRows": 100
}
```

### Security Alerts

Configured alerts:
- Failed authentication attempts (5+ in 5 minutes)
- Suspicious queries (UNION, --, etc.)
- High query volume (1000+ in 1 hour)
- Container restarts (3+ in 10 minutes)

Query for suspicious activity:

```kql
ContainerAppConsoleLogs_CL
| where Log_s contains "validation failed"
| summarize Count=count() by bin(TimeGenerated, 5m)
| where Count > 10
```

### Monitoring Dashboard

Key metrics to monitor:
- Query execution time (p50, p95, p99)
- Failed authentication attempts
- Error rate
- Query validation failures
- Container health status

## Compliance

### Data Protection

- **Encryption at Rest**: Azure default encryption
- **Encryption in Transit**: TLS 1.2+
- **Data Classification**: Mark sensitive columns
- **Data Retention**: Configurable (30-90 days)

### Audit Requirements

- **Log Retention**: 90 days minimum for production
- **Access Logging**: All database access logged
- **Change Tracking**: Git history + Azure activity logs
- **Incident Response**: Alert on anomalies

### GDPR Considerations

If storing personal data:
1. Document data flows
2. Implement data subject requests (export, delete)
3. Maintain audit logs
4. Implement data retention policies

### SOC 2 Controls

Relevant controls:
- **CC6.1**: Logical access controls (RBAC, Managed Identity)
- **CC6.6**: Encryption (TLS, at-rest encryption)
- **CC7.2**: System monitoring (Log Analytics, alerts)
- **CC7.3**: Security event detection (audit logs)

## Security Best Practices

### Do's ✅

- Use Managed Identity for all Azure service authentication
- Store all secrets in Key Vault
- Enable audit logging on all services
- Use Private Endpoints for SQL
- Implement read-only database access
- Validate all user inputs
- Use parameterized queries
- Monitor for anomalies
- Rotate credentials regularly
- Use least privilege everywhere

### Don'ts ❌

- Never hardcode passwords
- Never disable TLS/encryption
- Never allow public SQL access
- Never grant write permissions to MCP user
- Never skip query validation
- Never log sensitive data (passwords, tokens)
- Never use SA account for applications
- Never disable audit logging
- Never trust user input
- Never use dynamic SQL with unsanitized inputs

## Incident Response

### Suspected SQL Injection

1. Check audit logs for suspicious queries
2. Review application logs for validation failures
3. Verify read-only permissions still in place
4. Check for unauthorized schema changes
5. Review firewall rules and access logs

### Credential Compromise

1. Immediately rotate affected credentials
2. Review Key Vault access logs
3. Check for unauthorized resource access
4. Update secrets in Key Vault
5. Restart affected services
6. Review Azure AD sign-in logs

### Container Compromise

1. Stop affected container
2. Review container logs
3. Scan image for vulnerabilities
4. Deploy clean image
5. Review network logs for lateral movement
6. Check for data exfiltration

## Security Checklist

Before deploying to production:

- [ ] SQL public access disabled
- [ ] Private Endpoint configured
- [ ] Managed Identity configured
- [ ] Key Vault RBAC enabled
- [ ] Read-only SQL user created
- [ ] Query validation enabled
- [ ] Audit logging enabled
- [ ] Log Analytics workspace configured
- [ ] Security alerts configured
- [ ] Container image scanned
- [ ] Network Security Groups applied
- [ ] TLS 1.2+ enforced
- [ ] Secrets in Key Vault (not code)
- [ ] OIDC configured for CI/CD
- [ ] Monitoring dashboard created
- [ ] Incident response plan documented

## Resources

- [Azure Security Best Practices](https://docs.microsoft.com/azure/security/fundamentals/best-practices-and-patterns)
- [SQL Database Security](https://docs.microsoft.com/azure/azure-sql/database/security-overview)
- [Key Vault Security](https://docs.microsoft.com/azure/key-vault/general/security-features)
- [Container Apps Security](https://docs.microsoft.com/azure/container-apps/security)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
