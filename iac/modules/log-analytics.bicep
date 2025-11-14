// =============================================================================
// Log Analytics Workspace Module
// =============================================================================
// Creates Log Analytics workspace for:
//   - Container Apps logs
//   - SQL Database diagnostics
//   - Key Vault audit logs
//   - Application insights
// =============================================================================

@description('Log Analytics Workspace name')
param name string

@description('Location for resources')
param location string

@description('Resource tags')
param tags object

@description('Data retention in days')
@minValue(30)
@maxValue(730)
param retentionInDays int = 30

@description('SKU name')
@allowed([
  'PerGB2018'
  'CapacityReservation'
])
param sku string = 'PerGB2018'

@description('Daily ingestion limit in GB (0 = no limit)')
param dailyQuotaGb int = 0

// =============================================================================
// Log Analytics Workspace
// =============================================================================

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    sku: {
      name: sku
    }
    retentionInDays: retentionInDays
    workspaceCapping: dailyQuotaGb > 0 ? {
      dailyQuotaGb: dailyQuotaGb
    } : null
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

// =============================================================================
// Diagnostic Solutions
// =============================================================================

// Container Insights
resource containerInsightsSolution 'Microsoft.OperationsManagement/solutions@2015-11-01-preview' = {
  name: 'ContainerInsights(${workspace.name})'
  location: location
  tags: tags
  plan: {
    name: 'ContainerInsights(${workspace.name})'
    product: 'OMSGallery/ContainerInsights'
    promotionCode: ''
    publisher: 'Microsoft'
  }
  properties: {
    workspaceResourceId: workspace.id
  }
}

// Security Insights (optional)
resource securityInsightsSolution 'Microsoft.OperationsManagement/solutions@2015-11-01-preview' = {
  name: 'SecurityInsights(${workspace.name})'
  location: location
  tags: tags
  plan: {
    name: 'SecurityInsights(${workspace.name})'
    product: 'OMSGallery/SecurityInsights'
    promotionCode: ''
    publisher: 'Microsoft'
  }
  properties: {
    workspaceResourceId: workspace.id
  }
}

// =============================================================================
// Saved Queries (Custom KQL Queries)
// =============================================================================

resource savedQueryMcpErrors 'Microsoft.OperationalInsights/workspaces/savedSearches@2020-08-01' = {
  parent: workspace
  name: 'mcp-server-errors'
  properties: {
    displayName: 'MCP Server Errors'
    category: 'Application'
    query: '''
      ContainerAppConsoleLogs_CL
      | where ContainerAppName_s contains "mcp-server"
      | where Log_s contains "error" or Log_s contains "ERROR"
      | project TimeGenerated, ContainerAppName_s, Log_s
      | order by TimeGenerated desc
    '''
    version: 2
  }
}

resource savedQuerySlowQueries 'Microsoft.OperationalInsights/workspaces/savedSearches@2020-08-01' = {
  parent: workspace
  name: 'slow-sql-queries'
  properties: {
    displayName: 'Slow SQL Queries (>5s)'
    category: 'Application'
    query: '''
      ContainerAppConsoleLogs_CL
      | where ContainerAppName_s contains "mcp-server"
      | where Log_s contains "executionTime"
      | extend ExecutionTime = extract("executionTime\":(\\d+)", 1, Log_s)
      | where toint(ExecutionTime) > 5000
      | project TimeGenerated, ContainerAppName_s, ExecutionTime, Log_s
      | order by toint(ExecutionTime) desc
    '''
    version: 2
  }
}

// =============================================================================
// Outputs
// =============================================================================

output workspaceId string = workspace.id
output workspaceName string = workspace.name
output customerId string = workspace.properties.customerId
