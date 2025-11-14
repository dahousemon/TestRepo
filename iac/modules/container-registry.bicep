// =============================================================================
// Azure Container Registry Module
// =============================================================================
// Creates:
//   - Azure Container Registry
//   - Role assignment for Managed Identity (AcrPull)
//   - Admin user disabled (using managed identity)
//   - Diagnostics settings
// =============================================================================

@description('Container Registry name')
@minLength(5)
@maxLength(50)
param name string

@description('Location for resources')
param location string

@description('Resource tags')
param tags object

@description('SKU')
@allowed([
  'Basic'
  'Standard'
  'Premium'
])
param sku string = 'Standard'

@description('Managed Identity Principal ID for AcrPull access')
param managedIdentityPrincipalId string

@description('Enable anonymous pull access')
param anonymousPullEnabled bool = false

@description('Enable public network access')
param publicNetworkAccess bool = true

// =============================================================================
// Container Registry
// =============================================================================

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: false
    anonymousPullEnabled: anonymousPullEnabled
    publicNetworkAccess: publicNetworkAccess ? 'Enabled' : 'Disabled'
    networkRuleBypassOptions: 'AzureServices'
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      trustPolicy: {
        type: 'Notary'
        status: 'disabled'
      }
      retentionPolicy: {
        days: 30
        status: 'enabled'
      }
      exportPolicy: {
        status: 'enabled'
      }
    }
    encryption: {
      status: 'disabled'
    }
    dataEndpointEnabled: false
    publicNetworkAccess: publicNetworkAccess ? 'Enabled' : 'Disabled'
    networkRuleSet: {
      defaultAction: 'Allow'
    }
    zoneRedundancy: sku == 'Premium' ? 'Enabled' : 'Disabled'
  }
}

// =============================================================================
// Role Assignments
// =============================================================================

// AcrPull role for managed identity (read access)
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, managedIdentityPrincipalId, 'AcrPull')
  scope: acr
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: managedIdentityPrincipalId
    principalType: 'ServicePrincipal'
  }
}

// =============================================================================
// Outputs
// =============================================================================

output acrName string = acr.name
output acrId string = acr.id
output loginServer string = acr.properties.loginServer
