# GitHub Actions Workflows

This directory contains CI/CD workflows for the SQL MCP Server project.

## Workflows

### CI Workflow (`ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

**Jobs:**
1. **Lint** - ESLint and Prettier checks
2. **Test** - Run unit tests with coverage
3. **Security** - npm audit, Snyk scan, TruffleHog secrets detection
4. **Build** - Build Docker image, scan with Trivy, push to ACR

### CD Workflow (`cd.yml`)

**Triggers:**
- Successful CI workflow on `main` branch
- Manual workflow dispatch

**Jobs:**
1. **Deploy Infrastructure** - Deploy Bicep templates
2. **Update Container App** - Update with new Docker image
3. **Health Check** - Verify deployment health and smoke tests
4. **Summary** - Generate deployment summary

## Setup Instructions

### 1. Azure OIDC Configuration

#### Create Azure AD App Registration

```bash
# Login to Azure
az login

# Set variables
APP_NAME="github-actions-sql-mcp"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

# Create app registration
APP_ID=$(az ad app create \
  --display-name $APP_NAME \
  --query appId -o tsv)

# Create service principal
az ad sp create --id $APP_ID

# Get service principal object ID
SP_OBJECT_ID=$(az ad sp show --id $APP_ID --query id -o tsv)
```

#### Configure Federated Credentials

For **GitHub Enterprise Cloud**:

```bash
# Main branch
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-main",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:YOUR-ORG/YOUR-REPO:ref:refs/heads/main",
    "description": "GitHub Actions - Main Branch",
    "audiences": ["api://AzureADTokenExchange"]
  }'

# Pull requests
az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-pr",
    "issuer": "https://token.actions.githubusercontent.com",
    "subject": "repo:YOUR-ORG/YOUR-REPO:pull_request",
    "description": "GitHub Actions - Pull Requests",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

For **GitHub Enterprise Server**:

```bash
# Replace with your GitHub Enterprise Server URL
GITHUB_SERVER_URL="https://github.yourdomain.com"

az ad app federated-credential create \
  --id $APP_ID \
  --parameters '{
    "name": "github-enterprise-main",
    "issuer": "'$GITHUB_SERVER_URL'",
    "subject": "repo:YOUR-ORG/YOUR-REPO:ref:refs/heads/main",
    "description": "GitHub Enterprise - Main Branch",
    "audiences": ["api://AzureADTokenExchange"]
  }'
```

#### Assign Azure Permissions

```bash
# Create resource group
RESOURCE_GROUP="rg-mcp-server-dev"
REGION="eastus"

az group create \
  --name $RESOURCE_GROUP \
  --location $REGION

# Assign Contributor role
az role assignment create \
  --assignee $APP_ID \
  --role Contributor \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP

# Additional roles if needed
az role assignment create \
  --assignee $APP_ID \
  --role "User Access Administrator" \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP
```

### 2. GitHub Secrets Configuration

#### Required Secrets

Add these secrets in GitHub Settings → Secrets and variables → Actions → Secrets:

```bash
# Azure OIDC credentials
AZURE_CLIENT_ID          # Application (client) ID
AZURE_TENANT_ID          # Directory (tenant) ID
AZURE_SUBSCRIPTION_ID    # Subscription ID

# SQL Server credentials
SQL_ADMIN_USERNAME       # SQL Server admin username
SQL_ADMIN_PASSWORD       # SQL Server admin password (strong password)

# Optional: Security scanning
SNYK_TOKEN              # Snyk API token (for vulnerability scanning)
```

#### Get Azure values:

```bash
echo "AZURE_CLIENT_ID: $APP_ID"
echo "AZURE_TENANT_ID: $TENANT_ID"
echo "AZURE_SUBSCRIPTION_ID: $SUBSCRIPTION_ID"
```

### 3. GitHub Variables Configuration

Add these variables in GitHub Settings → Secrets and variables → Actions → Variables:

```bash
# Azure configuration
AZURE_RESOURCE_GROUP     # rg-mcp-server-dev
AZURE_REGION             # eastus
BASE_NAME                # mcpsql (unique base name)

# Container Registry
ACR_NAME                 # Your ACR name (without .azurecr.io)
```

### 4. GitHub Environments (Optional)

Create environments for better control:

**Settings → Environments → New environment**

Create:
- `dev` - Development environment
- `staging` - Staging environment
- `prod` - Production environment (with protection rules)

For each environment, add:
- **Protection rules** (for prod):
  - Required reviewers
  - Wait timer
  - Branch restrictions
- **Environment secrets** (if different per environment)
- **Environment variables** (if different per environment)

## Workflow Permissions

### CI Workflow

```yaml
permissions:
  id-token: write      # OIDC authentication
  contents: read       # Checkout code
  pull-requests: write # Comment on PRs
  security-events: write # Upload security scans
```

### CD Workflow

```yaml
permissions:
  id-token: write   # OIDC authentication
  contents: read    # Checkout code
  deployments: write # Create deployments
```

## Manual Workflow Triggers

### Trigger CD Workflow Manually

1. Go to **Actions** tab
2. Select **CD - Deploy to Azure**
3. Click **Run workflow**
4. Select environment: `dev`, `staging`, or `prod`
5. Click **Run workflow**

### Using GitHub CLI

```bash
gh workflow run cd.yml \
  --ref main \
  -f environment=dev
```

## Troubleshooting

### OIDC Authentication Fails

**Error:** `Error: OIDC token exchange failed`

**Solutions:**
1. Verify federated credentials are correctly configured
2. Check subject format matches your repository
3. Ensure workflow has `id-token: write` permission
4. Verify Azure service principal has correct permissions

```bash
# List federated credentials
az ad app federated-credential list --id $APP_ID

# Verify service principal
az ad sp show --id $APP_ID
```

### ACR Push Fails

**Error:** `unauthorized: authentication required`

**Solutions:**
1. Verify managed identity has AcrPull/AcrPush role
2. Check ACR admin user is disabled
3. Ensure `az acr login` succeeded

```bash
# Verify ACR permissions
az role assignment list \
  --assignee $APP_ID \
  --scope /subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.ContainerRegistry/registries/$ACR_NAME
```

### Bicep Deployment Fails

**Error:** Various deployment errors

**Solutions:**
1. Validate Bicep template locally:
   ```bash
   az bicep build --file iac/main.bicep
   ```

2. Check parameter values are correct

3. Review deployment logs:
   ```bash
   az deployment group show \
     --resource-group $RESOURCE_GROUP \
     --name main \
     --query properties.error
   ```

### Container App Not Starting

**Solutions:**
1. Check logs:
   ```bash
   az containerapp logs show \
     --name <app-name> \
     --resource-group $RESOURCE_GROUP \
     --tail 100
   ```

2. Verify environment variables are set correctly

3. Check Key Vault secrets are accessible

4. Verify SQL connection string is correct

## Security Best Practices

1. **Never commit secrets** to the repository
2. **Use OIDC** instead of service principal credentials
3. **Enable branch protection** for main branch
4. **Require reviews** for production deployments
5. **Scan for vulnerabilities** in every build
6. **Rotate credentials** regularly
7. **Use environment secrets** for sensitive values
8. **Enable audit logging** in Azure

## Monitoring Workflows

### View Workflow Runs

```bash
# List recent workflow runs
gh run list --workflow=ci.yml

# View specific run
gh run view <run-id>

# Watch a run
gh run watch <run-id>
```

### Workflow Metrics

Monitor in GitHub:
- **Actions** tab → View all runs
- **Insights** → View success rates, duration trends

## Advanced Configuration

### Matrix Builds

For testing multiple Node.js versions:

```yaml
strategy:
  matrix:
    node-version: [18.x, 20.x]
```

### Conditional Deployments

Deploy only on version tags:

```yaml
on:
  push:
    tags:
      - 'v*'
```

### Deployment Notifications

Add Slack/Teams notifications:

```yaml
- name: Notify deployment
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
```

## Resources

- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Azure Login Action](https://github.com/Azure/login)
- [OIDC with Azure](https://docs.github.com/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-azure)
- [GitHub Enterprise Server OIDC](https://docs.github.com/enterprise-server/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
