"""
Master Generator - Creates all 3 files from question description
"""

import asyncio
import json
import os
from datetime import datetime
from simple_policy_creator import SimplePolicyCreator
from validator_creator import ValidatorCreator
from config import AzureConfig, FileManager


class MasterGenerator:
    """Orchestrates generation of all files"""
    
    def __init__(self):
        self.policy_creator = SimplePolicyCreator()
        self.validator_creator = ValidatorCreator()
        FileManager.create_directories()
    
    async def generate_all(self, question_description: str, project_name: str = "iot_telemetry"):
        print("="*80)
        print("🚀 MASTER GENERATOR - Creating All 3 Files")
        print("="*80)
        print(f"📁 Project: {project_name}\n")
        
        # Step 1: Save Question
        print("📋 Step 1: Saving question...\n")
        question_path = f"{AzureConfig.QUESTIONS_OUTPUT}/{project_name}_question.txt"
        FileManager.save_file(question_description, question_path)
        
        # Step 2: Generate Policy
        print("\n📋 Step 2: Generating policy...\n")
        policy_requirements = "Allow: Event Hub, Storage, API Management, Container Instances"
        
        policy_result = await self.policy_creator.create_policy(
            requirements=policy_requirements,
            output_filename=f"{project_name}_policy.json"
        )
        
        # Step 3: Generate Validator
        print("\n📋 Step 3: Generating validator...\n")
        validator_requirements = question_description[:500]
        
        validator_result = await self.validator_creator.create_validator(
            requirements=validator_requirements,
            output_filename=f"{project_name}_validator.js"
        )
        
        # Step 4: Create Summary
        print("\n📋 Step 4: Creating summary...\n")
        
        summary = {
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "question_file": question_path,
            "policy_file": policy_result["output_path"],
            "validator_file": validator_result["output_path"]
        }
        
        summary_path = f"{AzureConfig.SUMMARIES_OUTPUT}/{project_name}_summary.json"
        FileManager.save_file(json.dumps(summary, indent=2), summary_path)
        
        print("\n" + "="*80)
        print("✅ ALL FILES GENERATED!")
        print("="*80)
        print(f"\n📄 1. Question: {question_path}")
        print(f"📄 2. Policy: {policy_result['output_path']}")
        print(f"📄 3. Validator: {validator_result['output_path']}")
        print(f"📄 4. Summary: {summary_path}")
        print("="*80)
        
        return summary


async def main():
    generator = MasterGenerator()
    
    iot_question = """
IoT Telemetry Data Processing System

Create an Event Hub namespace, VNet, Event Hub with 4+ partitions,
3+ days retention, consumer group, and service endpoints.

Specifications:
- Event Hub Namespace: <ResourceGroupName>IoTTelemetryHub
- Tier: Standard
- Event Hub: SensorDataStream
- Partitions: >= 4
- Retention: >= 3 days
- Consumer Group: analytics_processor
- VNet: IoTVNet (10.5.0.0/16)
- Subnet: IoTSubnet
- Service Endpoint: Microsoft.EventHub
"""
    
    result = await generator.generate_all(
        question_description=iot_question,
        project_name="iot_telemetry"
    )
    
    print("\n✅ Complete! All files ready.")


if __name__ == "__main__":
    asyncio.run(main())
