"""
Validator Creator - Generates JavaScript validation scripts
"""

import asyncio
import json
from datetime import datetime
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from config import AzureConfig, FileManager


VALIDATOR_PROMPT = """You are an Azure validation script generator.

Create a JavaScript validation script that:
1. Uses Azure SDK (@azure/identity, @azure/arm-eventhub, @azure/arm-network, etc.)
2. Validates all requirements mentioned
3. Returns a result array with weightage, name, status, error
4. Uses environment variables for credentials

Output ONLY complete, runnable JavaScript code."""


class ValidatorCreator:
    """Creates JavaScript validation scripts"""
    
    def __init__(self):
        self.model_client = AzureConfig.create_model_client()
        FileManager.create_directories()
    
    def _create_validator_agent(self):
        return AssistantAgent(
            name="validator_generator",
            model_client=self.model_client,
            system_message=VALIDATOR_PROMPT
        )
    
    async def create_validator(self, requirements: str, output_filename: str = None):
        print("="*80)
        print("🚀 VALIDATOR CREATOR")
        print("="*80)
        
        generator = self._create_validator_agent()
        
        prompt = f"""
Create validation script for:

{requirements}

Output complete JavaScript using Azure SDKs.
"""
        
        messages = [TextMessage(content=prompt, source="user")]
        response = await generator.on_messages(messages, cancellation_token=None)
        
        content = response.chat_message.content
        validator_js = FileManager.extract_code_block(content, "javascript")
        if not validator_js or validator_js == content:
            validator_js = FileManager.extract_code_block(content, "js")
        if not validator_js or validator_js == content:
            validator_js = content
        
        print("✅ Validator created!")
        
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"validator_{timestamp}.js"
        
        if not output_filename.endswith('.js'):
            output_filename += '.js'
        
        output_path = f"{AzureConfig.VALIDATOR_OUTPUT}/{output_filename}"
        FileManager.save_file(validator_js, output_path)
        
        # Create package.json
        package_json = {
            "name": output_filename.replace('.js', ''),
            "version": "1.0.0",
            "dependencies": {
                "@azure/identity": "^3.3.0",
                "@azure/arm-eventhub": "^5.1.0",
                "@azure/arm-network": "^32.0.0",
                "dotenv": "^16.3.1"
            }
        }
        
        package_path = f"{AzureConfig.VALIDATOR_OUTPUT}/package.json"
        FileManager.save_file(json.dumps(package_json, indent=2), package_path)
        
        # Create .env.example
        env_example = """tenantId=your-tenant-id
clientId=your-client-id
clientSecret=your-client-secret
subscriptionId=your-subscription-id
resourceGroupName=your-resource-group
"""
        env_path = f"{AzureConfig.VALIDATOR_OUTPUT}/.env.example"
        FileManager.save_file(env_example, env_path)
        
        print(f"📄 {output_path}")
        print(f"📄 {package_path}")
        print("="*80)
        
        return {
            "validator_js": validator_js,
            "output_path": output_path
        }


async def main():
    creator = ValidatorCreator()
    
    requirements = """
Validate:
- Event Hub namespace exists
- Namespace is Standard tier
- Event Hub has 4+ partitions
- VNet exists with correct address space
"""
    
    result = await creator.create_validator(
        requirements=requirements,
        output_filename="test_validator.js"
    )
    
    print(f"\n✅ Done! Check: {result['output_path']}")


if __name__ == "__main__":
    asyncio.run(main())
