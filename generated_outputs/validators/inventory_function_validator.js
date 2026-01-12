const { ClientSecretCredential } = require("@azure/identity");
const { WebSiteManagementClient } = require("@azure/arm-appservice");
require("dotenv").config();

const tenantId = process.env.tenantId;
const clientId = process.env.clientId;
const clientSecret = process.env.clientSecret;
const subscriptionId = process.env.subscriptionId;
const resourceGroupName = process.env.resourceGroupName;

const expectedFunctionAppName = `${resourceGroupName}-inventory`;
const expectedLocation = "East US";
const expectedRuntimeStack = "DOTNET|8";
const expectedHostingPlan = "Consumption";
const expectedFunctionName = "CheckStock";
const expectedSampleSku = "LAPTOP2024";
const expectedQuantity = 150;

const result = [
  { weightage: 1.0 / 5, name: "Check Function App Creation", status: false, error: "" },
  { weightage: 1.0 / 5, name: "Check Function App Location", status: false, error: "" },
  { weightage: 1.0 / 5, name: "Check Runtime Stack", status: false, error: "" },
  { weightage: 1.0 / 5, name: "Check Hosting Plan", status: false, error: "" },
  { weightage: 1.0 / 5, name: "Check Function Creation", status: false, error: "" }
];

const credential = new ClientSecretCredential(tenantId, clientId, clientSecret);
const client = new WebSiteManagementClient(credential, subscriptionId);

async function validate() {
  try {
    const functionApp = await client.webApps.get(resourceGroupName, expectedFunctionAppName);
    if (functionApp) {
      result[0].status = true;

      // Check location
      if (functionApp.location === expectedLocation) {
        result[1].status = true;
      } else {
        result[1].error = `Expected Location: ${expectedLocation}, Got: ${functionApp.location}`;
      }

      // Check runtime stack
      if (functionApp.kind && functionApp.kind.includes(expectedRuntimeStack)) {
        result[2].status = true;
      } else {
        result[2].error = `Expected Runtime Stack: ${expectedRuntimeStack}, Got: ${functionApp.kind}`;
      }

      // Check hosting plan
      // Note: Hosting plan check will require additional API calls to validate
      // Here we assume a function or property check exists for plan, replace this with actual call if needed
      const plan = await client.appServicePlans.get(resourceGroupName, functionApp.serverFarmId.split('/').pop());
      if (plan.sku.name.includes("Consumption")) {
        result[3].status = true;
      } else {
        result[3].error = `Expected Hosting Plan: Consumption, Got: ${plan.sku.name}`;
      }

      // Check function creation
      const functionsList = await client.webApps.listFunctions(resourceGroupName, expectedFunctionAppName);
      if (functionsList.some(fn => fn.name === expectedFunctionName)) {
        result[4].status = true;
      } else {
        result[4].error = `Function ${expectedFunctionName} not found`;
      }
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