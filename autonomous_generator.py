"""
Autonomous Generator - AI reads specifications and creates everything automatically
NO templates, NO examples - Pure AI generation from requirements
"""

import asyncio
import json
from datetime import datetime
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from config import AzureConfig, FileManager


class AutonomousGenerator:
    """
    Reads question description → Automatically creates:
    1. Azure Policy JSON
    2. Validation JavaScript
    3. Question file
    All generated purely from the specifications
    """
    
    def __init__(self):
        self.model_client = AzureConfig.create_model_client()
        FileManager.create_directories()
    
    def _create_policy_generator(self):
        """AI that generates Azure Policy from specifications"""
        return AssistantAgent(
            name="policy_generator",
            model_client=self.model_client,
            system_message="""You are an Azure Policy expert.

Read the specifications and create an Azure Policy JSON that:
1. Allows ONLY the resources needed for the task
2. Denies everything else
3. Follows this exact structure:

{
  "if": {
    "allOf": [
      {
        "not": {
          "field": "type",
          "in": ["LIST_ALL_REQUIRED_RESOURCE_TYPES"]
        }
      },
      {
        "anyOf": [
          {
            "allOf": [
              {"field": "type", "equals": "Microsoft.Storage/storageAccounts"},
              {"not": {"allOf": [
                {"field": "Microsoft.Storage/storageAccounts/sku.tier", "equals": "Standard"},
                {"field": "Microsoft.Storage/storageAccounts/accessTier", "equals": "Hot"}
              ]}}
            ]
          },
          {
            "allOf": [
              {"field": "type", "equals": "Microsoft.Storage/storageAccounts"},
              {"not": {"field": "Microsoft.Storage/storageAccounts/sku.name", "in": [
                "Standard_LRS", "Standard_GRS", "Standard_RAGRS", "Standard_ZRS"
              ]}}
            ]
          }
        ]
      }
    ]
  },
  "then": {"effect": "deny"}
}

CRITICAL RULES:
- Output ONLY JSON
- NO markdown, NO explanations
- Include ALL resource types for the service (base + sub-resources + operations)
- For Functions: Microsoft.Web/sites, Microsoft.Web/serverfarms, Microsoft.Web/sites/functions, etc.
- For EventHub: Microsoft.EventHub/*, all sub-types
- Always include: Microsoft.Resources, Microsoft.Resources/deployments
- Storage constraints are ALWAYS the same (tier+access, sku.name)"""
        )
    
    def _create_validator_generator(self):
        """AI that generates validation JavaScript from specifications"""
        return AssistantAgent(
            name="validator_generator",
            model_client=self.model_client,
            system_message="""You are an Azure validation script expert.

Read the specifications and create a complete JavaScript validation script.

STRUCTURE:
```javascript
const { ClientSecretCredential } = require("@azure/identity");
const { APPROPRIATE_CLIENT } = require("@azure/arm-SERVICE");
require("dotenv").config();

const tenantId = process.env.tenantId;
const clientId = process.env.clientId;
const clientSecret = process.env.clientSecret;
const subscriptionId = process.env.subscriptionId;
const resourceGroupName = process.env.resourceGroupName;

// Extract expected values from specifications
const expectedName = "VALUE_FROM_SPECS";

const result = [
  { weightage: EQUAL_WEIGHT, name: "Check 1", status: false, error: "" },
  // ... one check per specification requirement
];

const credential = new ClientSecretCredential(tenantId, clientId, clientSecret);
const client = new APPROPRIATE_CLIENT(credential, subscriptionId);

async function validate() {
  try {
    // Implement each validation check
    // Use appropriate Azure SDK methods
    // Set result[i].status = true on success
    // Set result[i].error on failure
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
```

CRITICAL RULES:
- Output ONLY JavaScript code
- NO markdown, NO explanations
- Use correct Azure SDK for the service type
- Equal weightage for all checks (1.0 / number_of_checks)
- Extract ALL expected values from specifications
- Implement complete validation logic
- Handle all errors properly

AZURE SDK MAPPING:
- Functions: @azure/arm-appservice (WebSiteManagementClient)
- EventHub: @azure/arm-eventhub (EventHubManagementClient)
- Storage: @azure/arm-storage (StorageManagementClient)
- Network: @azure/arm-network (NetworkManagementClient)
- SQL: @azure/arm-sql (SqlManagementClient)"""
        )
    
    async def generate_policy(self, question: str) -> dict:
        """Generate Azure Policy from question specifications"""
        print("🔧 Generating Azure Policy from specifications...\n")
        
        generator = self._create_policy_generator()
        
        prompt = f"""
Read these specifications carefully and generate the Azure Policy:

{question}

Analyze what Azure resources are needed and create the policy JSON.
Output ONLY the JSON, nothing else.
"""
        
        messages = [TextMessage(content=prompt, source="user")]
        response = await generator.on_messages(messages, cancellation_token=None)
        
        content = response.chat_message.content
        
        # Clean response
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Try to parse
        try:
            policy = json.loads(content)
            
            # Validate structure
            if "if" in policy and "then" in policy:
                print("✅ Valid policy generated!")
                return {"policy": policy, "raw": content}
            else:
                print("⚠️ Invalid structure, attempting fix...")
                # Try to extract if/then
                if "policyRule" in policy:
                    policy = policy["policyRule"]
                    return {"policy": policy, "raw": json.dumps(policy, indent=2)}
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse: {e}")
            # Return raw content, will be saved anyway
            return {"policy": None, "raw": content}
        
        return {"policy": None, "raw": content}
    
    async def generate_validator(self, question: str) -> dict:
        """Generate validation script from question specifications"""
        print("🔧 Generating validation script from specifications...\n")
        
        generator = self._create_validator_generator()
        
        prompt = f"""
Read these specifications carefully and generate the complete validation JavaScript:

{question}

Analyze:
1. What Azure service is this? (Function App, Event Hub, etc.)
2. What needs to be validated? (Extract from specifications)
3. What are the expected values? (Names, counts, settings)
4. How many validation checks are needed?

Create complete, runnable JavaScript validation script.
Output ONLY JavaScript code, nothing else.
"""
        
        messages = [TextMessage(content=prompt, source="user")]
        response = await generator.on_messages(messages, cancellation_token=None)
        
        content = response.chat_message.content
        
        # Clean response
        content = content.replace("```javascript", "").replace("```js", "").replace("```", "").strip()
        
        print("✅ Validator script generated!")
        
        return {"script": content}
    
    async def generate_all(self, question_description: str, project_name: str = None):
        """
        Main method: Read question → Generate everything automatically
        
        Args:
            question_description: The complete question text with specifications
            project_name: Optional name for output files
            
        Returns:
            Dictionary with all generated file paths
        """
        
        if not project_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = f"auto_{timestamp}"
        
        print("="*80)
        print("🤖 AUTONOMOUS GENERATOR - AI Creates Everything")
        print("="*80)
        print(f"📁 Project: {project_name}")
        print("="*80)
        print("\n📖 Reading specifications from question...\n")
        
        # Step 1: Save question
        question_path = f"{AzureConfig.QUESTIONS_OUTPUT}/{project_name}_question.txt"
        FileManager.save_file(question_description, question_path)
        print(f"✅ Question saved: {question_path}\n")
        
        # Step 2: Generate Policy (AI reads specs and creates it)
        print("="*80)
        print("🧠 AI TASK 1: Generate Azure Policy")
        print("="*80)
        policy_result = await self.generate_policy(question_description)
        
        policy_path = f"{AzureConfig.POLICY_OUTPUT}/{project_name}_policy.json"
        FileManager.save_file(policy_result["raw"], policy_path)
        print(f"✅ Policy saved: {policy_path}\n")
        
        # Step 3: Generate Validator (AI reads specs and creates it)
        print("="*80)
        print("🧠 AI TASK 2: Generate Validation Script")
        print("="*80)
        validator_result = await self.generate_validator(question_description)
        
        validator_path = f"{AzureConfig.VALIDATOR_OUTPUT}/{project_name}_validator.js"
        FileManager.save_file(validator_result["script"], validator_path)
        print(f"✅ Validator saved: {validator_path}\n")
        
        # Step 4: Create package.json for validator
        package_json = {
            "name": f"{project_name}-validator",
            "version": "1.0.0",
            "description": f"Auto-generated validator for {project_name}",
            "main": f"{project_name}_validator.js",
            "scripts": {
                "start": f"node {project_name}_validator.js"
            },
            "dependencies": {
                "@azure/identity": "^3.3.0",
                "@azure/arm-appservice": "^13.0.0",
                "@azure/arm-eventhub": "^5.1.0",
                "@azure/arm-network": "^32.0.0",
                "@azure/arm-storage": "^18.1.0",
                "axios": "^1.6.0",
                "dotenv": "^16.3.1"
            }
        }
        
        package_path = f"{AzureConfig.VALIDATOR_OUTPUT}/package.json"
        FileManager.save_file(json.dumps(package_json, indent=2), package_path)
        
        # Step 5: Create .env.example
        env_example = """# Azure Service Principal Credentials
tenantId=your-tenant-id
clientId=your-client-id
clientSecret=your-client-secret
subscriptionId=your-subscription-id
resourceGroupName=your-resource-group
"""
        env_path = f"{AzureConfig.VALIDATOR_OUTPUT}/.env.example"
        FileManager.save_file(env_example, env_path)
        
        # Step 6: Create summary
        summary = {
            "project_name": project_name,
            "generated_at": datetime.now().isoformat(),
            "question_file": question_path,
            "policy_file": policy_path,
            "validator_file": validator_path,
            "generation_method": "autonomous_ai",
            "ai_generated": True
        }
        
        summary_path = f"{AzureConfig.SUMMARIES_OUTPUT}/{project_name}_summary.json"
        FileManager.save_file(json.dumps(summary, indent=2), summary_path)
        
        # Final summary
        print("\n" + "="*80)
        print("✅ AUTONOMOUS GENERATION COMPLETE!")
        print("="*80)
        print("\n📦 Generated Files:")
        print(f"  1. Question:  {question_path}")
        print(f"  2. Policy:    {policy_path}")
        print(f"  3. Validator: {validator_path}")
        print(f"  4. Package:   {package_path}")
        print(f"  5. Env:       {env_path}")
        print(f"  6. Summary:   {summary_path}")
        print("\n🚀 Next Steps:")
        print(f"  1. Review generated policy: cat {policy_path}")
        print(f"  2. Review generated validator: cat {validator_path}")
        print(f"  3. Test validator:")
        print(f"     cd {AzureConfig.VALIDATOR_OUTPUT}")
        print(f"     npm install")
        print(f"     cp .env.example .env")
        print(f"     # Edit .env with credentials")
        print(f"     node {project_name}_validator.js")
        print("="*80)
        
        return summary


async def main():
    """Example: Generate from Azure Functions question"""
    
    generator = AutonomousGenerator()
    
    # Example 1: Azure Functions Question
    functions_question = """
Product Inventory Checker for Warehouse Management

You're an Azure developer in an e-commerce company and have been tasked with creating 
an Azure Function App that provides real-time inventory status for warehouse products. 
The Function App should be triggered via HTTP requests and respond with stock availability 
information based on the product SKU provided in the request.

Task Details:
* Create an Azure Function App in the existing resource group with the required details
* Create a new function with an HTTP Trigger with the default Storage Account
* Choose the Authorization level as "Function"
* Implement the logic in .NET 8 in-process Model to check and return inventory status
* If a valid SKU is provided, respond with "Product {sku} is in stock. Available quantity: {quantity} units."
* If no SKU is provided, return error: "Please provide a product SKU in the query string."
* If SKU doesn't exist, return: "Product {sku} not found in inventory."

Specifications:
* Resource Group: Existing resource group
* Function App Name: <Resource Group Name>-inventory
* Location: East US 
* Runtime Stack: .NET 8 in-process Model
* Hosting Plan: Consumption Plan
* Function Name: CheckStock
* Query Parameter Name: sku
* Sample Test Value: LAPTOP2024
* Expected Response: "Product LAPTOP2024 is in stock. Available quantity: 150 units."
"""
    
    print("🎯 EXAMPLE 1: Azure Functions Question\n")
    result1 = await generator.generate_all(
        question_description=functions_question,
        project_name="inventory_checker"
    )
    
    # Example 2: Event Hub Question
    eventhub_question = """
IoT Telemetry Data Processing System

Configure an Azure Event Hub integrated with a Virtual Network to stream and analyze 
sensor telemetry for predictive analytics.

Task Details:
1. Create an Event Hub Namespace with Standard tier for VNet integration
2. Create a Virtual Network with address space 10.5.0.0/16
3. Create Event Hub with 4+ partitions and 3+ days retention
4. Enable service endpoint for Event Hub on subnet

Specifications:
* Event Hub Namespace: <ResourceGroupName>IoTTelemetryHub
* Namespace Tier: Standard 
* Region: West US3
* Event Hub Name: SensorDataStream
* Partition Count: Minimum 4
* Message Retention: Minimum 3 days
* Consumer Group: analytics_processor
* VNet Name: IoTVNet
* VNet Address Space: 10.5.0.0/16
* Subnet Name: IoTSubnet
* Service Endpoint: Microsoft.EventHub
"""
    
    print("\n\n🎯 EXAMPLE 2: Event Hub Question\n")
    result2 = await generator.generate_all(
        question_description=eventhub_question,
        project_name="iot_telemetry"
    )
    
    print("\n\n✅ ALL EXAMPLES COMPLETE!")
    print("Check generated_outputs/ for all files")


if __name__ == "__main__":
    asyncio.run(main())
