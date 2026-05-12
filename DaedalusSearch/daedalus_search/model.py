import os

from dotenv import load_dotenv
from openai import OpenAI

class Model():
    def __init__(self):
        self.client = OpenAI(
            base_url = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1"),
            api_key = os.getenv("LLM_API_KEY", "not-needed"),
        )
        self.model = os.getenv("LLM_MODEL", "local-model")

    def prompt(self, msg):
        return self.client.chat.completions.create(
                model=self.model,
                messages=msg,
                temperature=0.2
        )
