# Setup Guide

Complete guide for deploying the SQL MCP Server in both local and Azure environments.

## Table of Contents

- [Local Development Setup](#local-development-setup)
- [Azure Deployment](#azure-deployment)
- [GitHub Enterprise CI/CD Setup](#github-enterprise-cicd-setup)
- [Post-Deployment Configuration](#post-deployment-configuration)
- [Verification](#verification)

## Local Development Setup

### Prerequisites

- Docker Desktop 20.10+
- Docker Compose 2.0+
- Node.js 20+
- Git

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/sql-mcp-server.git
cd sql-mcp-server

# Setup environment
cd local-dev
cp .env.example .env

# Edit .env (optional - update passwords)
nano .env

# Start services
docker-compose up -d

# Verify
curl http://localhost:8080/health
```

### Detailed Steps

#### 1. Configure Environment

Edit `local-dev/.env`:

```bash
# Required: Set strong passwords
SQL_ADMIN_PASSWORD=YourStrong@Passw0rd123
SQL_PASSWORD=McpUser@Pass123

# Optional: Adjust ports if conflicts exist
MCP_SERVER_PORT=8080
ADMINER_PORT=8090
```

#### 2. Start Services

```bash
cd local-dev

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

#### 3. Initialize Database

The database is automatically initialized with:
- DevOpsMetrics database
- Read-only user (`mcp_user`)
- Schema (tables and views)
- Sample data

To verify:

```bash
# Connect to database
docker exec -it sql-mcp-server-db /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U mcp_user -P "McpUser@Pass123" -d DevOpsMetrics \
  -Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"
```

#### 4. Test MCP Server

```bash
# Health check
curl http://localhost:8080/health

# Readiness (includes DB connectivity)
curl http://localhost:8080/ready
```

### Using VS Code Dev Containers

1. Install **Remote - Containers** extension
2. Open project in VS Code
3. Command Palette (F1) → **Remote-Containers: Reopen in Container**
4. VS Code rebuilds and connects to dev container

Benefits:
- Pre-configured environment
- Extensions auto-installed
- Debugging configured
- SQL Server connection ready

### Troubleshooting Local Setup

**SQL Server won't start:**
```bash
# Check logs
docker-compose logs sqlserver

# Ensure strong password
# Ensure Docker has 2GB+ memory
```

**Port conflicts:**
```bash
# Find process using port
lsof -i :1433  # or :8080

# Update ports in .env
```

**Database not initialized:**
```bash
# Manually run init script
docker-compose run --rm sql-init
```

## Azure Deployment

### Prerequisites

- Azure subscription with Contributor access
- Azure CLI 2.50+
- Bicep CLI (included with Azure CLI)

### Step 1: Azure Login

```bash
# Login
az login

# Select subscription
az account set --subscription <subscription-id>

# Verify
az account show
```

### Step 2: Create Resource Group

```bash
# Set variables
RESOURCE_GROUP="rg-mcp-server-dev"
LOCATION="eastus"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

### Step 3: Prepare Parameters

Create `iac/parameters.local.json`:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "environment": {
      "value": "dev"
    },
    "baseName": {
      "value": "mcpsql"
    },
    "sqlAdminUsername": {
      "value": "sqladmin"
    },
    "sqlAdminPassword": {
      "value": "STRONG_PASSWORD_HERE"
    }
  }
}
```

**Security Note:** For production, use Key Vault reference instead of plain text password.

### Step 4: Deploy Infrastructure

```bash
# Navigate to project root
cd /path/to/sql-mcp-server

# Deploy Bicep
az deployment group create \
  --resource-group $RESOURCE_GROUP \
  --template-file iac/main.bicep \
  --parameters iac/parameters.local.json \
  --name main-deployment

# Monitor deployment
az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main-deployment \
  --query properties.provisioningState
```

Deployment takes approximately 10-15 minutes.

### Step 5: Configure SQL Database

```bash
# Get SQL Server FQDN
SQL_SERVER=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main-deployment \
  --query properties.outputs.sqlServerFqdn.value -o tsv)

echo "SQL Server: $SQL_SERVER"

# Temporarily enable public access for setup
az sql server update \
  --resource-group $RESOURCE_GROUP \
  --name $(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name main-deployment \
    --query properties.outputs.sqlServerName.value -o tsv) \
  --set publicNetworkAccess=Enabled

# Add your IP to firewall
MY_IP=$(curl -s https://api.ipify.org)
az sql server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --server $(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name main-deployment \
    --query properties.outputs.sqlServerName.value -o tsv) \
  --name AllowMyIP \
  --start-ip-address $MY_IP \
  --end-ip-address $MY_IP

# Run SQL scripts
sqlcmd -S $SQL_SERVER -U sqladmin -P "STRONG_PASSWORD_HERE" \
  -i sql/01-security-setup.sql

sqlcmd -S $SQL_SERVER -U sqladmin -P "STRONG_PASSWORD_HERE" \
  -i sql/02-create-schema.sql

sqlcmd -S $SQL_SERVER -U sqladmin -P "STRONG_PASSWORD_HERE" \
  -i sql/03-create-views.sql

# Optional: Sample data
sqlcmd -S $SQL_SERVER -U sqladmin -P "STRONG_PASSWORD_HERE" \
  -i sql/04-sample-data.sql

# Remove firewall rule and disable public access
az sql server firewall-rule delete \
  --resource-group $RESOURCE_GROUP \
  --server $(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name main-deployment \
    --query properties.outputs.sqlServerName.value -o tsv) \
  --name AllowMyIP

az sql server update \
  --resource-group $RESOURCE_GROUP \
  --name $(az deployment group show \
    --resource-group $RESOURCE_GROUP \
    --name main-deployment \
    --query properties.outputs.sqlServerName.value -o tsv) \
  --set publicNetworkAccess=Disabled
```

### Step 6: Build and Push Container Image

```bash
# Get ACR name
ACR_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main-deployment \
  --query properties.outputs.acrName.value -o tsv)

echo "ACR Name: $ACR_NAME"

# Build and push image
az acr build \
  --registry $ACR_NAME \
  --image mcp-server:latest \
  --file Dockerfile \
  .
```

### Step 7: Update Container App

```bash
# Get Container App name
CONTAINER_APP_NAME=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main-deployment \
  --query properties.outputs.containerAppName.value -o tsv)

# Update with new image
az containerapp update \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --image $ACR_NAME.azurecr.io/mcp-server:latest

# Wait for deployment
az containerapp revision list \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table
```

## GitHub Enterprise CI/CD Setup

### Step 1: Create Azure AD App Registration

```bash
# Set variables
APP_NAME="github-actions-sql-mcp"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

# Create app registration
APP_ID=$(az ad app create \
  --display-name $APP_NAME \
  --query appId -o tsv)

echo "Application (Client) ID: $APP_ID"

# Create service principal
az ad sp create --id $APP_ID

# Get service principal object ID
SP_OBJECT_ID=$(az ad sp show --id $APP_ID --query id -o tsv)
```

### Step 2: Configure Federated Credentials

**For GitHub Enterprise Cloud:**

```bash
# Replace with your organization and repository
GH_ORG="your-org"
GH_REPO="sql-mcp-server"

# Main branch credential
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'$GH_ORG'/'$GH_REPO':ref:refs/heads/main",
    "description": "GitHub Actions - Main Branch",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Pull request credential
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-pr",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:'$GH_ORG'/'$GH_REPO':pull_request",
    "description": "GitHub Actions - Pull Requests",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

**For GitHub Enterprise Server:**

```bash
# Replace with your GitHub Enterprise Server URL
GITHUB_SERVER_URL="https://github.yourdomain.com"

az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-enterprise-main",
    "issuer": "'$GITHUB_SERVER_URL'",
    "subject": "repo:'$GH_ORG'/'$GH_REPO':ref:refs/heads/main",
    "description": "GitHub Enterprise - Main Branch",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

### Step 3: Assign Azure Permissions

```bash
# Assign Contributor role to resource group
az role assignment create \
  --assignee $APP_ID \
  --role Contributor \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP
```

### Step 4: Configure GitHub Secrets

In GitHub repository → Settings → Secrets and variables → Actions:

**Secrets:**
```
AZURE_CLIENT_ID: <APP_ID from above>
AZURE_TENANT_ID: <TENANT_ID from above>
AZURE_SUBSCRIPTION_ID: <SUBSCRIPTION_ID from above>
SQL_ADMIN_USERNAME: sqladmin
SQL_ADMIN_PASSWORD: <strong password>
```

**Variables:**
```
AZURE_RESOURCE_GROUP: rg-mcp-server-dev
AZURE_REGION: eastus
BASE_NAME: mcpsql
ACR_NAME: <ACR_NAME from deployment>
```

### Step 5: Test CI/CD

```bash
# Push code to trigger CI
git add .
git commit -m "Initial deployment"
git push origin main

# Monitor workflows in GitHub Actions tab
```

## How GitHub OIDC Works

### Traditional Approach (Not Used)
```
GitHub Actions → Uses stored credentials (secret) → Azure
```

Problems:
- Credentials can expire
- Must rotate secrets manually
- Security risk if exposed

### OIDC Approach (Used)
```
GitHub Actions → Request token from GitHub → GitHub issues short-lived token
→ Exchange token with Azure AD → Azure AD verifies and grants access
```

Benefits:
- No long-lived credentials
- Automatic token expiration
- More secure
- No manual rotation

### OIDC Flow Diagram

```
┌─────────────────┐
│ GitHub Actions  │
│   Workflow      │
└────────┬────────┘
         │
         │ (1) Request OIDC token
         ▼
┌─────────────────┐
│ GitHub OIDC     │
│   Provider      │
└────────┬────────┘
         │
         │ (2) Return JWT token
         ▼
┌─────────────────┐
│ GitHub Actions  │
│   Workflow      │
└────────┬────────┘
         │
         │ (3) Exchange token
         ▼
┌─────────────────┐
│ Azure AD        │
│ (Token Exchange)│
└────────┬────────┘
         │
         │ (4) Verify token
         │ (5) Check federated credential
         │ (6) Issue Azure access token
         ▼
┌─────────────────┐
│ GitHub Actions  │
│   Workflow      │
└────────┬────────┘
         │
         │ (7) Call Azure APIs
         ▼
┌─────────────────┐
│ Azure Resources │
└─────────────────┘
```

## Post-Deployment Configuration

### 1. Verify All Resources

```bash
# List all resources
az resource list \
  --resource-group $RESOURCE_GROUP \
  --output table
```

### 2. Check Container App Health

```bash
# View logs
az containerapp logs show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --tail 50

# Check revision status
az containerapp revision list \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --output table
```

### 3. Verify Managed Identity Permissions

```bash
# Get managed identity
IDENTITY_ID=$(az deployment group show \
  --resource-group $RESOURCE_GROUP \
  --name main-deployment \
  --query properties.outputs.managedIdentityPrincipalId.value -o tsv)

# Check role assignments
az role assignment list \
  --assignee $IDENTITY_ID \
  --output table
```

## Verification

### Local Deployment

```bash
# Health check
curl http://localhost:8080/health
#Expected: {"status":"healthy","timestamp":"...","uptime":123}

# Readiness check
curl http://localhost:8080/ready
# Expected: {"status":"ready","database":"connected","timestamp":"..."}

# SQL connection
docker exec -it sql-mcp-server-db /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U mcp_user -P "McpUser@Pass123" -d DevOpsMetrics \
  -Q "SELECT COUNT(*) FROM BuildRuns"
```

### Azure Deployment

```bash
# Check Container App status
az containerapp show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query "properties.runningStatus"

# View logs for errors
az containerapp logs show \
  --name $CONTAINER_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --tail 100 \
  | grep -i error

# Test from within VNet (requires bastion/VPN)
# Health check URL (internal)
# https://<container-app-fqdn>/health
```

## Next Steps

1. **Configure MCP Client**: See [03-using-mcp.md](03-using-mcp.md)
2. **Review Security**: See [02-security-model.md](02-security-model.md)
3. **Explore Queries**: See [04-sql-examples.md](04-sql-examples.md)
4. **Set Up Monitoring**: Configure alerts in Azure Monitor
5. **Enable Optional Features**: See [/optional/README.md](../optional/README.md)

## Troubleshooting

See [GitHub Workflows README](../github/workflows/README.md) for CI/CD troubleshooting.

For local dev issues, see [Local Dev README](../local-dev/README.md).

## Cleanup

### Local

```bash
# Stop and remove all containers
cd local-dev
docker-compose down -v
```

### Azure

```bash
# Delete resource group (removes ALL resources)
az group delete \
  --name $RESOURCE_GROUP \
  --yes --no-wait
```
