"""
Student Submission Evaluator
"""

import asyncio
import json
from datetime import datetime
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from config import AzureConfig, FileManager


EVALUATION_PROMPT = """You are an Azure deployment evaluator.

Analyze the student's deployment and provide:
1. Overall status (PASS/FAIL)
2. Score for each validation criterion
3. Detailed feedback
4. Recommendations for improvement

Be specific and educational."""


class DeploymentEvaluator:
    """Evaluates student Azure deployments"""
    
    def __init__(self):
        self.model_client = AzureConfig.create_model_client()
        FileManager.create_directories()
    
    def _create_evaluator(self):
        return AssistantAgent(
            name="evaluator",
            model_client=self.model_client,
            system_message=EVALUATION_PROMPT
        )
    
    async def evaluate_submission(self, student_submission: str, requirements: str = None, output_filename: str = None):
        print("="*80)
        print("🚀 DEPLOYMENT EVALUATOR")
        print("="*80)
        
        evaluator = self._create_evaluator()
        
        prompt = f"""
Evaluate this deployment:

{student_submission}

Requirements:
{requirements or "Check all Azure best practices"}

Provide detailed evaluation with scores.
"""
        
        messages = [TextMessage(content=prompt, source="user")]
        response = await evaluator.on_messages(messages, cancellation_token=None)
        
        evaluation = response.chat_message.content
        
        print("✅ Evaluation complete!")
        
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"evaluation_{timestamp}.txt"
        
        if not output_filename.endswith('.txt'):
            output_filename += '.txt'
        
        output_path = f"{AzureConfig.EVALUATION_OUTPUT}/{output_filename}"
        FileManager.save_file(evaluation, output_path)
        
        print(f"📄 {output_path}")
        print("="*80)
        
        return {
            "evaluation": evaluation,
            "output_path": output_path
        }


async def main():
    evaluator = DeploymentEvaluator()
    
    submission = """
I created:
- Event Hub namespace: myRGIoTTelemetryHub (Standard tier)
- Event Hub: SensorDataStream (4 partitions, 7 days retention)
- VNet: IoTVNet (10.5.0.0/16)
- Subnet: IoTSubnet with EventHub service endpoint
"""
    
    result = await evaluator.evaluate_submission(
        student_submission=submission,
        output_filename="test_evaluation.txt"
    )
    
    print(f"\n✅ Done! Check: {result['output_path']}")


if __name__ == "__main__":
    asyncio.run(main())
