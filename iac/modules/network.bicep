// =============================================================================
// Network Module - Virtual Network and Subnets
// =============================================================================
// Creates:
//   - Virtual Network
//   - Subnet for Container Apps
//   - Subnet for Private Endpoints
//   - Network Security Groups
// =============================================================================

@description('Virtual Network name')
param vnetName string

@description('Location for resources')
param location string

@description('Resource tags')
param tags object

@description('VNet address prefix')
param addressPrefix string = '10.0.0.0/16'

@description('Container Apps subnet address prefix')
param containerAppSubnetPrefix string = '10.0.0.0/23'

@description('Private Endpoint subnet address prefix')
param privateEndpointSubnetPrefix string = '10.0.2.0/24'

// =============================================================================
// Network Security Groups
// =============================================================================

// NSG for Container Apps subnet
resource nsgContainerApp 'Microsoft.Network/networkSecurityGroups@2023-06-01' = {
  name: '${vnetName}-containerapp-nsg'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowInternalInbound'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'VirtualNetwork'
          access: 'Allow'
          priority: 100
          direction: 'Inbound'
        }
      }
      {
        name: 'AllowHealthProbes'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'AzureLoadBalancer'
          destinationAddressPrefix: '*'
          access: 'Allow'
          priority: 110
          direction: 'Inbound'
        }
      }
      {
        name: 'DenyAllInbound'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
          access: 'Deny'
          priority: 4096
          direction: 'Inbound'
        }
      }
    ]
  }
}

// NSG for Private Endpoints subnet
resource nsgPrivateEndpoint 'Microsoft.Network/networkSecurityGroups@2023-06-01' = {
  name: '${vnetName}-pe-nsg'
  location: location
  tags: tags
  properties: {
    securityRules: [
      {
        name: 'AllowVNetInbound'
        properties: {
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: 'VirtualNetwork'
          destinationAddressPrefix: 'VirtualNetwork'
          access: 'Allow'
          priority: 100
          direction: 'Inbound'
        }
      }
    ]
  }
}

// =============================================================================
// Virtual Network
// =============================================================================

resource vnet 'Microsoft.Network/virtualNetworks@2023-06-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        addressPrefix
      ]
    }
    subnets: [
      {
        name: 'snet-containerapp'
        properties: {
          addressPrefix: containerAppSubnetPrefix
          networkSecurityGroup: {
            id: nsgContainerApp.id
          }
          delegations: [
            {
              name: 'Microsoft.App.environments'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
          serviceEndpoints: [
            {
              service: 'Microsoft.KeyVault'
            }
            {
              service: 'Microsoft.Sql'
            }
          ]
        }
      }
      {
        name: 'snet-privateendpoint'
        properties: {
          addressPrefix: privateEndpointSubnetPrefix
          networkSecurityGroup: {
            id: nsgPrivateEndpoint.id
          }
          privateEndpointNetworkPolicies: 'Disabled'
          privateLinkServiceNetworkPolicies: 'Enabled'
        }
      }
    ]
  }
}

// =============================================================================
// Outputs
// =============================================================================

output vnetName string = vnet.name
output vnetId string = vnet.id
output containerAppSubnetId string = vnet.properties.subnets[0].id
output privateEndpointSubnetId string = vnet.properties.subnets[1].id
