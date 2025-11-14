// =============================================================================
// Main Bicep Template - SQL MCP Server Infrastructure
// =============================================================================
// Deploys complete Azure infrastructure for SQL MCP Server:
//   - Virtual Network with subnets
//   - Log Analytics Workspace
//   - Azure Container Registry
//   - Azure SQL Server + Database with Private Endpoint
//   - Azure Key Vault
//   - Container Apps Environment
//   - Container App for MCP Server
//
// Usage:
//   az deployment group create \
//     --resource-group <rg-name> \
//     --template-file main.bicep \
//     --parameters parameters.json
// =============================================================================

targetScope = 'resourceGroup'

// =============================================================================
// Parameters
// =============================================================================

@description('Environment name (dev, staging, prod)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string = 'dev'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Base name for all resources')
@minLength(3)
@maxLength(15)
param baseName string

@description('SQL Server administrator login')
param sqlAdminUsername string

@description('SQL Server administrator password')
@secure()
param sqlAdminPassword string

@description('SQL Database name')
param sqlDatabaseName string = 'DevOpsMetrics'

@description('MCP Server container image (will be updated by CI/CD)')
param mcpServerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Tags to apply to all resources')
param tags object = {
  Environment: environment
  Project: 'SQL-MCP-Server'
  ManagedBy: 'Bicep'
}

// =============================================================================
// Variables
// =============================================================================

var uniqueSuffix = uniqueString(resourceGroup().id)
var vnetName = 'vnet-${baseName}-${environment}'
var logAnalyticsName = 'log-${baseName}-${environment}'
var acrName = 'acr${baseName}${environment}${take(uniqueSuffix, 4)}'
var sqlServerName = 'sql-${baseName}-${environment}-${take(uniqueSuffix, 6)}'
var keyVaultName = 'kv-${baseName}-${take(uniqueSuffix, 8)}'
var containerAppEnvName = 'cae-${baseName}-${environment}'
var containerAppName = 'ca-mcp-server-${environment}'
var managedIdentityName = 'id-${baseName}-mcp-${environment}'

// =============================================================================
// Managed Identity for MCP Server
// =============================================================================

resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: managedIdentityName
  location: location
  tags: tags
}

// =============================================================================
// Log Analytics Workspace
// =============================================================================

module logAnalytics 'modules/log-analytics.bicep' = {
  name: 'deploy-log-analytics'
  params: {
    name: logAnalyticsName
    location: location
    tags: tags
    retentionInDays: environment == 'prod' ? 90 : 30
  }
}

// =============================================================================
// Virtual Network
// =============================================================================

module network 'modules/network.bicep' = {
  name: 'deploy-network'
  params: {
    vnetName: vnetName
    location: location
    tags: tags
    addressPrefix: '10.0.0.0/16'
  }
}

// =============================================================================
// Azure Container Registry
// =============================================================================

module acr 'modules/container-registry.bicep' = {
  name: 'deploy-acr'
  params: {
    name: acrName
    location: location
    tags: tags
    sku: environment == 'prod' ? 'Premium' : 'Standard'
    managedIdentityPrincipalId: managedIdentity.properties.principalId
  }
}

// =============================================================================
// Azure SQL Server and Database
// =============================================================================

module sql 'modules/sql.bicep' = {
  name: 'deploy-sql'
  params: {
    serverName: sqlServerName
    location: location
    tags: tags
    administratorLogin: sqlAdminUsername
    administratorLoginPassword: sqlAdminPassword
    databaseName: sqlDatabaseName
    vnetName: network.outputs.vnetName
    privateEndpointSubnetId: network.outputs.privateEndpointSubnetId
    enablePrivateEndpoint: true
  }
}

// =============================================================================
// Azure Key Vault
// =============================================================================

module keyVault 'modules/key-vault.bicep' = {
  name: 'deploy-key-vault'
  params: {
    name: keyVaultName
    location: location
    tags: tags
    managedIdentityPrincipalId: managedIdentity.properties.principalId
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
  }
}

// =============================================================================
// Store SQL Connection String in Key Vault
// =============================================================================

resource sqlConnectionStringSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  name: '${keyVault.outputs.keyVaultName}/sql-connection-string'
  properties: {
    value: 'Server=tcp:${sql.outputs.sqlServerFqdn},1433;Database=${sqlDatabaseName};User ID=${sqlAdminUsername};Password=${sqlAdminPassword};Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;'
  }
}

// =============================================================================
// Container Apps Environment
// =============================================================================

module containerAppEnv 'modules/container-app-environment.bicep' = {
  name: 'deploy-container-app-env'
  params: {
    name: containerAppEnvName
    location: location
    tags: tags
    vnetName: network.outputs.vnetName
    infrastructureSubnetId: network.outputs.containerAppSubnetId
    logAnalyticsWorkspaceId: logAnalytics.outputs.workspaceId
    internal: true
  }
}

// =============================================================================
// MCP Server Container App
// =============================================================================

module mcpServer 'modules/container-app.bicep' = {
  name: 'deploy-mcp-server'
  params: {
    name: containerAppName
    location: location
    tags: tags
    containerAppEnvironmentId: containerAppEnv.outputs.environmentId
    containerImage: mcpServerImage
    managedIdentityId: managedIdentity.id
    keyVaultName: keyVault.outputs.keyVaultName
    sqlConnectionStringSecretName: 'sql-connection-string'
  }
}

// =============================================================================
// Outputs
// =============================================================================

output resourceGroupName string = resourceGroup().name
output location string = location
output environment string = environment

output vnetName string = network.outputs.vnetName
output vnetId string = network.outputs.vnetId

output logAnalyticsWorkspaceId string = logAnalytics.outputs.workspaceId
output logAnalyticsWorkspaceName string = logAnalytics.outputs.workspaceName

output acrName string = acr.outputs.acrName
output acrLoginServer string = acr.outputs.loginServer

output sqlServerName string = sql.outputs.sqlServerName
output sqlServerFqdn string = sql.outputs.sqlServerFqdn
output sqlDatabaseName string = sql.outputs.sqlDatabaseName

output keyVaultName string = keyVault.outputs.keyVaultName
output keyVaultUri string = keyVault.outputs.keyVaultUri

output containerAppEnvironmentName string = containerAppEnv.outputs.environmentName
output containerAppName string = mcpServer.outputs.containerAppName
output containerAppFqdn string = mcpServer.outputs.fqdn

output managedIdentityName string = managedIdentity.name
output managedIdentityClientId string = managedIdentity.properties.clientId
output managedIdentityPrincipalId string = managedIdentity.properties.principalId
