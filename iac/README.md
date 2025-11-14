# Infrastructure as Code (Bicep)

This directory contains Bicep templates for deploying the SQL MCP Server infrastructure on Azure.

## Architecture

The infrastructure includes:

- **Virtual Network** with two subnets:
  - Container Apps subnet (delegated)
  - Private Endpoint subnet
- **Log Analytics Workspace** for centralized logging
- **Azure Container Registry** for Docker images
- **Azure SQL Server + Database** with Private Endpoint (no public access)
- **Azure Key Vault** for secrets management
- **Container Apps Environment** with VNet integration
- **Container App** running the MCP server
- **Managed Identity** for secure authentication

## File Structure

```
iac/
├── main.bicep                              # Main orchestration template
├── parameters.json                         # Example parameters file
├── modules/
│   ├── network.bicep                       # VNet, subnets, NSGs
│   ├── log-analytics.bicep                 # Log Analytics workspace
│   ├── container-registry.bicep            # Azure Container Registry
│   ├── sql.bicep                           # SQL Server + Database + Private Endpoint
│   ├── key-vault.bicep                     # Key Vault + RBAC
│   ├── container-app-environment.bicep     # Container Apps Environment
│   └── container-app.bicep                 # MCP Server container app
└── README.md                               # This file
```

## Prerequisites

1. **Azure CLI** (v2.50.0 or later)
   ```bash
   az --version
   ```

2. **Azure Subscription** with appropriate permissions

3. **Bicep CLI** (installed with Azure CLI)
   ```bash
   az bicep version
   ```

## Deployment

### 1. Login to Azure

```bash
az login
az account set --subscription <subscription-id>
```

### 2. Create Resource Group

```bash
az group create \
  --name rg-mcp-server-dev \
  --location eastus
```

### 3. Update Parameters

Edit `parameters.json` to customize:
- `baseName`: Unique base name for resources
- `environment`: dev, staging, or prod
- `location`: Azure region
- `sqlAdminPassword`: Use Key Vault reference (see below)

### 4. Deploy Infrastructure

```bash
az deployment group create \
  --resource-group rg-mcp-server-dev \
  --template-file main.bicep \
  --parameters parameters.json
```

### 5. Validate Deployment

```bash
# Check deployment status
az deployment group show \
  --resource-group rg-mcp-server-dev \
  --name main

# List deployed resources
az resource list \
  --resource-group rg-mcp-server-dev \
  --output table
```

## Parameter Configuration

### SQL Admin Password

For production, store the SQL admin password in Key Vault:

```bash
# Create a Key Vault for deployment secrets
az keyvault create \
  --name kv-deployment-secrets \
  --resource-group rg-deployment \
  --location eastus

# Store SQL password
az keyvault secret set \
  --vault-name kv-deployment-secrets \
  --name sql-admin-password \
  --value '<strong-password>'
```

Update `parameters.json`:

```json
"sqlAdminPassword": {
  "reference": {
    "keyVault": {
      "id": "/subscriptions/{sub-id}/resourceGroups/rg-deployment/providers/Microsoft.KeyVault/vaults/kv-deployment-secrets"
    },
    "secretName": "sql-admin-password"
  }
}
```

### Container Image

Initially, use a placeholder image. CI/CD will update it:

```json
"mcpServerImage": {
  "value": "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
}
```

After CI/CD builds your image:

```json
"mcpServerImage": {
  "value": "{acr-name}.azurecr.io/mcp-server:latest"
}
```

## Post-Deployment Steps

### 1. Configure SQL Database

```bash
# Get SQL Server FQDN
SQL_SERVER=$(az deployment group show \
  --resource-group rg-mcp-server-dev \
  --name main \
  --query properties.outputs.sqlServerFqdn.value -o tsv)

# Connect and run SQL scripts
sqlcmd -S $SQL_SERVER -U sqladmin -P '<password>' -i ../sql/01-security-setup.sql
sqlcmd -S $SQL_SERVER -U sqladmin -P '<password>' -i ../sql/02-create-schema.sql
sqlcmd -S $SQL_SERVER -U sqladmin -P '<password>' -i ../sql/03-create-views.sql
```

### 2. Update Container Image

```bash
# Get ACR name
ACR_NAME=$(az deployment group show \
  --resource-group rg-mcp-server-dev \
  --name main \
  --query properties.outputs.acrName.value -o tsv)

# Build and push image
az acr build \
  --registry $ACR_NAME \
  --image mcp-server:latest \
  --file ../Dockerfile \
  ..

# Update Container App
az containerapp update \
  --name ca-mcp-server-dev \
  --resource-group rg-mcp-server-dev \
  --image $ACR_NAME.azurecr.io/mcp-server:latest
```

### 3. Verify Health

```bash
# Get Container App FQDN
FQDN=$(az deployment group show \
  --resource-group rg-mcp-server-dev \
  --name main \
  --query properties.outputs.containerAppFqdn.value -o tsv)

# Check health (from within VNet or via bastion)
curl http://$FQDN/health
curl http://$FQDN/ready
```

## Environment-Specific Configurations

### Development

```json
{
  "environment": "dev",
  "minReplicas": 1,
  "maxReplicas": 2,
  "databaseSku": "GP_S_Gen5_2",
  "acrSku": "Standard"
}
```

### Production

```json
{
  "environment": "prod",
  "minReplicas": 2,
  "maxReplicas": 10,
  "databaseSku": "GP_Gen5_4",
  "acrSku": "Premium",
  "zoneRedundant": true
}
```

## Monitoring

### View Logs

```bash
# Container App logs
az containerapp logs show \
  --name ca-mcp-server-dev \
  --resource-group rg-mcp-server-dev \
  --follow

# Log Analytics queries
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "ContainerAppConsoleLogs_CL | where ContainerAppName_s contains 'mcp-server' | top 100 by TimeGenerated desc"
```

### Metrics

```bash
# Container App metrics
az monitor metrics list \
  --resource <container-app-id> \
  --metric "Requests"
```

## Security Considerations

1. **No Public SQL Access**: SQL Server uses Private Endpoint only
2. **Managed Identity**: No passwords for Azure service authentication
3. **Key Vault**: All secrets stored in Key Vault with RBAC
4. **Internal Ingress**: Container App not exposed to internet
5. **NSGs**: Network Security Groups restrict traffic
6. **Diagnostics**: All logs sent to Log Analytics

## Troubleshooting

### Deployment Fails

```bash
# Check deployment errors
az deployment group show \
  --resource-group rg-mcp-server-dev \
  --name main \
  --query properties.error
```

### Container App Not Starting

```bash
# Check revision provisioning state
az containerapp revision list \
  --name ca-mcp-server-dev \
  --resource-group rg-mcp-server-dev \
  --output table

# View logs
az containerapp logs show \
  --name ca-mcp-server-dev \
  --resource-group rg-mcp-server-dev \
  --tail 100
```

### SQL Connection Issues

1. Verify Private Endpoint DNS resolution
2. Check NSG rules allow traffic
3. Verify Managed Identity has SQL permissions
4. Check Key Vault secret is accessible

## Cost Optimization

1. **Use Serverless SQL**: Auto-pause when inactive
2. **Container Apps**: Scale to zero when not in use
3. **Log Analytics**: Set data retention limits
4. **ACR**: Use geo-replication only in production

## Cleanup

```bash
# Delete resource group (removes all resources)
az group delete \
  --name rg-mcp-server-dev \
  --yes --no-wait
```

## Additional Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure SQL Database Documentation](https://learn.microsoft.com/azure/azure-sql/)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
