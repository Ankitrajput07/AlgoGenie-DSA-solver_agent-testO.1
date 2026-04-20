import os
from dotenv import load_dotenv

from autogen_ext.models.openai import OpenAIChatCompletionClient
from config.constant import MODEL

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')

def get_model_client():
    #Initializee the OpenAI model client
    openai_client = OpenAIChatCompletionClient(
        model="gemini-2.5-flash",
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": False,
            "family": "unknown",
            "structured_output": True,
        }
    )

    return openai_client