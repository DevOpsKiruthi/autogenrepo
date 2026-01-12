"""
Simple Azure Policy Creator - Template-based approach
"""

import asyncio
import json
from datetime import datetime
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from config import AzureConfig, FileManager


RESOURCE_EXTRACTOR_PROMPT = """List ALL Azure resource types for the services mentioned. Include base types, sub-resources (3-4 levels), and operations. Output ONLY a JSON array: ["type1", "type2", ...]"""


class SimplePolicyCreator:
    """Creates policies using a template-based approach"""
    
    def __init__(self):
        self.model_client = AzureConfig.create_model_client()
        FileManager.create_directories()
        
        self.policy_template = {
            "if": {
                "allOf": [
                    {"not": {"field": "type", "in": []}},
                    {"anyOf": []}
                ]
            },
            "then": {"effect": "deny"}
        }
    
    def _create_resource_extractor(self):
        return AssistantAgent(
            name="resource_extractor",
            model_client=self.model_client,
            system_message=RESOURCE_EXTRACTOR_PROMPT
        )
    
    async def extract_resource_types(self, requirements: str) -> list:
        print("📋 Extracting resource types...\n")
        
        extractor = self._create_resource_extractor()
        prompt = f"{requirements}\n\nList ALL Azure resource types as JSON array: [\"type1\", \"type2\", ...]"
        
        messages = [TextMessage(content=prompt, source="user")]
        response = await extractor.on_messages(messages, cancellation_token=None)
        
        content = response.chat_message.content.replace("```json", "").replace("```", "").strip()
        
        try:
            resource_types = json.loads(content)
            if isinstance(resource_types, list):
                print(f"✅ Extracted {len(resource_types)} resource types")
                return resource_types
        except:
            pass
        
        print("⚠️ Using fallback")
        return self._get_default_resources(requirements)
    
    def _get_default_resources(self, requirements: str) -> list:
        resources = ["Microsoft.Resources", "Microsoft.Resources/deployments"]
        req_lower = requirements.lower()
        
        if "event hub" in req_lower or "eventhub" in req_lower:
            resources.extend([
                "Microsoft.EventHub",
                "Microsoft.EventHub/namespaces",
                "Microsoft.EventHub/namespaces/authorizationRules/listkeys",
                "Microsoft.EventHub/namespaces/authorizationRules",
                "Microsoft.EventHub/namespaces/eventhubs",
                "Microsoft.EventHub/namespaces/write",
                "Microsoft.EventHub/register",
                "Microsoft.EventHub/namespaces/networkrulesets/write",
                "Microsoft.EventHub/namespaces/disasterRecoveryConfig",
                "Microsoft.EventHub/namespaces/disasterRecoveryConfigs/authorizationRules",
                "Microsoft.EventHub/unregister",
                "Microsoft.EventHub/sku/regions",
                "Microsoft.EventHub/operations",
                "Microsoft.EventHub/namespaces/eventhubs/authorizationRules",
                "Microsoft.EventHub/namespaces/eventhubs/authorizationRules/listkeys",
                "Microsoft.EventHub/namespaces/eventHubs/consumergroups",
                "Microsoft.EventHub/namespaces/SchemaGroups"
            ])
        
        if "storage" in req_lower:
            resources.extend([
                "Microsoft.Storage/storageAccounts",
                "Microsoft.Storage/storageAccounts/blobservices",
                "Microsoft.Storage/storageAccounts/blobServices/containers",
                "Microsoft.Storage/storageAccounts/blobServices/containers/blobs",
                "Microsoft.Storage/storageAccounts/fileservices"
            ])
        
        if "api management" in req_lower or "apim" in req_lower:
            resources.extend([
                "Microsoft.ApiManagement/service",
                "Microsoft.ApiManagement/service/apis",
                "Microsoft.ApiManagement/register",
                "Microsoft.ApiManagement/unregister"
            ])
        
        if "container" in req_lower:
            resources.append("Microsoft.ContainerInstance/containerGroups")
        
        if "app service" in req_lower or "web app" in req_lower:
            resources.extend([
                "Microsoft.AppService/apiApps/*",
                "Microsoft.Web/sites",
                "Microsoft.Web/serverFarms"
            ])
        
        return list(set(resources))
    
    def _create_storage_constraints(self) -> list:
        return [
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
    
    async def create_policy(self, requirements: str, output_filename: str = None):
        print("="*80)
        print("🚀 SIMPLE POLICY CREATOR")
        print("="*80)
        
        resource_types = await self.extract_resource_types(requirements)
        storage_constraints = self._create_storage_constraints()
        
        policy = json.loads(json.dumps(self.policy_template))
        policy["if"]["allOf"][0]["not"]["in"] = resource_types
        policy["if"]["allOf"][1]["anyOf"] = storage_constraints
        
        policy_json = json.dumps(policy, indent=2)
        
        print(f"✅ Policy created! ({len(resource_types)} resources)")
        
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"policy_{timestamp}.json"
        
        if not output_filename.endswith('.json'):
            output_filename += '.json'
        
        output_path = f"{AzureConfig.POLICY_OUTPUT}/{output_filename}"
        FileManager.save_file(policy_json, output_path)
        
        metadata = {
            "created_at": datetime.now().isoformat(),
            "requirements": requirements,
            "resource_types_count": len(resource_types),
            "output_file": output_filename
        }
        
        metadata_path = output_path.replace('.json', '_metadata.json')
        FileManager.save_file(json.dumps(metadata, indent=2), metadata_path)
        
        print(f"📄 {output_path}")
        print("="*80)
        
        return {
            "policy_json": policy_json,
            "policy_dict": policy,
            "output_path": output_path,
            "metadata": metadata
        }


async def main():
    creator = SimplePolicyCreator()
    
    requirements = "Allow: Event Hub, Storage, API Management, Container Instances"
    
    result = await creator.create_policy(
        requirements=requirements,
        output_filename="test_policy.json"
    )
    
    print(f"\n✅ Done! Check: {result['output_path']}")


if __name__ == "__main__":
    asyncio.run(main())
