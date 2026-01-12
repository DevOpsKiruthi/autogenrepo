require('dotenv').config();
const { DefaultAzureCredential } = require('@azure/identity');
const { EventHubManagementClient } = require('@azure/arm-eventhub');
const { NetworkManagementClient } = require('@azure/arm-network');

const credential = new DefaultAzureCredential();

const subscriptionId = process.env.AZURE_SUBSCRIPTION_ID;
const resourceGroupName = process.env.AZURE_RESOURCE_GROUP;
const eventHubNamespaceName = process.env.AZURE_EVENTHUB_NAMESPACE;
const eventHubName = process.env.AZURE_EVENTHUB_NAME;
const vnetName = process.env.AZURE_VNET_NAME;
const expectedAddressSpace = process.env.AZURE_VNET_ADDRESS_SPACE;

async function validateRequirements() {
    const results = [];

    // Event Hub Management Client
    const eventHubClient = new EventHubManagementClient(credential, subscriptionId);
    const networkClient = new NetworkManagementClient(credential, subscriptionId);

    try {
        // Validation for Event Hub Namespace Existence
        const namespace = await eventHubClient.namespaces.get(resourceGroupName, eventHubNamespaceName);
        results.push({
            weightage: 1,
            name: "Event Hub Namespace Exist",
            status: "Success",
            error: null
        });

        // Validation for Namespace Tier
        if (namespace.sku.name !== 'Standard') {
            results.push({
                weightage: 2,
                name: "Namespace Tier is Standard",
                status: "Failed",
                error: "Namespace is not Standard tier."
            });
        } else {
            results.push({
                weightage: 2,
                name: "Namespace Tier is Standard",
                status: "Success",
                error: null
            });
        }

        // Validation for Event Hub Partition Count
        const eventHub = await eventHubClient.eventHubs.get(resourceGroupName, eventHubNamespaceName, eventHubName);
        if (eventHub.partitionCount < 4) {
            results.push({
                weightage: 3,
                name: "Event Hub has 4+ Partitions",
                status: "Failed",
                error: "Event Hub has fewer than 4 partitions."
            });
        } else {
            results.push({
                weightage: 3,
                name: "Event Hub has 4+ Partitions",
                status: "Success",
                error: null
            });
        }
    } catch (err) {
        console.error(err);
        results.push({
            weightage: 1,
            name: "Error fetching Event Hub data",
            status: "Failed",
            error: `Error fetching Event Hub Namespace: ${err.message}`
        });
    }

    // Validation for VNet Existence
    try {
        const vnet = await networkClient.virtualNetworks.get(resourceGroupName, vnetName);
        results.push({
            weightage: 4,
            name: "VNet Exists",
            status: "Success",
            error: null
        });

        // Validation for correct Address Space
        if (vnet.addressSpace.addressPrefixes[0] !== expectedAddressSpace) {
            results.push({
                weightage: 5,
                name: "VNet Address Space is Correct",
                status: "Failed",
                error: `VNet does not have the expected address space: ${expectedAddressSpace}.`
            });
        } else {
            results.push({
                weightage: 5,
                name: "VNet Address Space is Correct",
                status: "Success",
                error: null
            });
        }
    } catch (err) {
        results.push({
            weightage: 4,
            name: "Error fetching VNet data",
            status: "Failed",
            error: `Error fetching VNet: ${err.message}`
        });
    }

    return results;
}

// Execute the validation
validateRequirements().then(results => {
    console.log(JSON.stringify(results, null, 2));
}).catch(error => {
    console.error("Failed to validate requirements: ", error);
});