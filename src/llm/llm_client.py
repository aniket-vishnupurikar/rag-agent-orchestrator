import httpx
import os
from typing import List, Dict
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


class LocalLLMClient:
    """
    Local LLM client for grounded answer generation.
    (Later replaceable with HF API / internal LLM service.)
    """

    def __init__(self, model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
            device_map="auto"
        )

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        output = self.model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False
        )

        decoded = self.tokenizer.decode(output[0], skip_special_tokens=True)
        return decoded[len(prompt):].strip()


class HFInferenceClient:
    def __init__(self, model_name: str):
        self.api_token = os.getenv("HF_API_TOKEN")
        if not self.api_token:
            raise RuntimeError("HF_API_TOKEN environment variable not set")

        self.model_name = model_name
        self.endpoint = (
            f"https://api-inference.huggingface.co/models/{model_name}"
        )

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def generate(self, prompt: str) -> str:
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 256,
                "temperature": 0.2
            }
        }

        response = httpx.post(
            self.endpoint,
            headers=self.headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()
        output = response.json()

        return output[0]["generated_text"]
    

class OpenAICompatibleClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.api_base = os.getenv(
            "OPENAI_API_BASE",
            "https://api.openai.com/v1"
        )
        self.model = os.getenv(
            "OPENAI_MODEL",
            "mistralai/mistral-7b-instruct"
        )

        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not set")

        self.client = httpx.Client(
            base_url=self.api_base,
            timeout=30.0
        )

    def generate(self, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # OpenRouter-specific (recommended)
            "HTTP-Referer": os.getenv("OPENROUTER_APP_URL", ""),
            "X-Title": os.getenv("OPENROUTER_APP_NAME", "RAG-Agent"),
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1000
        }

        response = self.client.post(
            "/chat/completions",
            headers=headers,
            json=payload
        )

        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]



