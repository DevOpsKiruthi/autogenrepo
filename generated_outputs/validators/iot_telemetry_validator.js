const { ClientSecretCredential } = require("@azure/identity");
const { EventHubManagementClient } = require("@azure/arm-eventhub");
const { NetworkManagementClient } = require("@azure/arm-network");
require("dotenv").config();

const tenantId = process.env.tenantId;
const clientId = process.env.clientId;
const clientSecret = process.env.clientSecret;
const subscriptionId = process.env.subscriptionId;
const resourceGroupName = process.env.resourceGroupName;

const expectedNamespaceName = `${resourceGroupName}IoTTelemetryHub`;
const expectedEventHubName = "SensorDataStream";
const expectedPartitionCount = 4;
const expectedRetentionDays = 3;
const expectedVNetName = "IoTVNet";
const expectedVNetAddressSpace = "10.5.0.0/16";
const expectedSubnetName = "IoTSubnet";
const expectedServiceEndpoint = "Microsoft.EventHub";

const result = [
  { weightage: 1.0 / 4, name: "Check Event Hub Namespace", status: false, error: "" },
  { weightage: 1.0 / 4, name: "Check Virtual Network", status: false, error: "" },
  { weightage: 1.0 / 4, name: "Check Event Hub Configuration", status: false, error: "" },
  { weightage: 1.0 / 4, name: "Check Service Endpoint", status: false, error: "" },
];

const credential = new ClientSecretCredential(tenantId, clientId, clientSecret);
const eventHubClient = new EventHubManagementClient(credential, subscriptionId);
const networkClient = new NetworkManagementClient(credential, subscriptionId);

async function validate() {
  try {
    // Check Event Hub Namespace
    const namespaces = await eventHubClient.namespaces.listByResourceGroup(resourceGroupName);
    const namespace = namespaces.find(ns => ns.name === expectedNamespaceName);
    if (namespace && namespace.sku.name === "Standard") {
      result[0].status = true;
    } else {
      result[0].error = `Event Hub Namespace ${expectedNamespaceName} not found or tier is not Standard.`;
    }

    // Check Virtual Network
    const vnet = await networkClient.virtualNetworks.get(resourceGroupName, expectedVNetName);
    if (vnet && vnet.addressSpace.addressPrefixes.includes(expectedVNetAddressSpace)) {
      result[1].status = true;
    } else {
      result[1].error = `Virtual Network ${expectedVNetName} not found or address space is incorrect.`;
    }

    // Check Event Hub Configuration
    const eventHubs = await eventHubClient.eventHubs.listByNamespace(resourceGroupName, expectedNamespaceName);
    const eventHub = eventHubs.find(eh => eh.name === expectedEventHubName);
    if (eventHub && eventHub.partitionCount >= expectedPartitionCount && eventHub.retentionTimeInDays >= expectedRetentionDays) {
      result[2].status = true;
    } else {
      result[2].error = `Event Hub ${expectedEventHubName} not found or configuration is incorrect.`;
    }

    // Check Service Endpoint
    const subnets = await networkClient.subnets.list(resourceGroupName, expectedVNetName);
    const subnet = subnets.find(s => s.name === expectedSubnetName);
    if (subnet && subnet.serviceEndpoints.some(se => se.service === expectedServiceEndpoint)) {
      result[3].status = true;
    } else {
      result[3].error = `Service endpoint for ${expectedServiceEndpoint} not found on subnet ${expectedSubnetName}.`;
    }
  } catch (error) {
    result.forEach(r => { if (!r.error) r.error = error.message; });
  }
  return result;
}

(async () => {
  const output = await validate();
  console.log(output);
  return output;
})();