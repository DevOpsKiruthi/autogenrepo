"""
Configuration file for Azure AutoGen System
"""

import os
from dotenv import load_dotenv

load_dotenv()


class AzureConfig:
    """Azure OpenAI Configuration"""
    
    DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    
    OUTPUT_DIR = "generated_outputs"
    POLICY_OUTPUT = f"{OUTPUT_DIR}/policies"
    VALIDATOR_OUTPUT = f"{OUTPUT_DIR}/validators"
    EVALUATION_OUTPUT = f"{OUTPUT_DIR}/evaluations"
    QUESTIONS_OUTPUT = f"{OUTPUT_DIR}/questions"
    SUMMARIES_OUTPUT = f"{OUTPUT_DIR}/summaries"
    
    @classmethod
    def validate(cls):
        missing = []
        if not cls.ENDPOINT:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not cls.API_KEY:
            missing.append("AZURE_OPENAI_API_KEY")
        
        if missing:
            raise ValueError(f"Missing: {', '.join(missing)}")
    
    @classmethod
    def create_model_client(cls):
        cls.validate()
        from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
        
        return AzureOpenAIChatCompletionClient(
            model=cls.DEPLOYMENT_NAME,
            api_version=cls.API_VERSION,
            azure_endpoint=cls.ENDPOINT,
            api_key=cls.API_KEY,
            model_info={
                "vision": True,
                "function_calling": True,
                "json_output": True,
                "structured_output": True,
                "family": "gpt-4o",
            }
        )


class FileManager:
    """File operations utility"""
    
    @staticmethod
    def create_directories():
        os.makedirs(AzureConfig.POLICY_OUTPUT, exist_ok=True)
        os.makedirs(AzureConfig.VALIDATOR_OUTPUT, exist_ok=True)
        os.makedirs(AzureConfig.EVALUATION_OUTPUT, exist_ok=True)
        os.makedirs(AzureConfig.QUESTIONS_OUTPUT, exist_ok=True)
        os.makedirs(AzureConfig.SUMMARIES_OUTPUT, exist_ok=True)
    
    @staticmethod
    def save_file(content: str, filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"✅ Saved: {filepath}")
    
    @staticmethod
    def load_file(filepath: str) -> str:
        with open(filepath, 'r') as f:
            return f.read()
    
    @staticmethod
    def extract_code_block(content: str, language: str) -> str:
        marker = f"```{language}"
        if marker in content:
            start = content.find(marker) + len(marker)
            end = content.find("```", start)
            if end != -1:
                return content[start:end].strip()
        return content


if __name__ == "__main__":
    print("Testing configuration...")
    try:
        AzureConfig.validate()
        print("✅ Configuration valid!")
    except ValueError as e:
        print(f"❌ Error: {e}")
