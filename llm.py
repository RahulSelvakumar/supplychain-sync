import os
import requests
import vertexai
from vertexai.generative_models import GenerativeModel

from config import GCP_PROJECT, GCP_LOCATION, GEMINI_MODEL, NVIDIA_NIM_URL, NVIDIA_NIM_MODEL

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
vertexai.init(project=GCP_PROJECT, location=GCP_LOCATION)

gemini_llm = GenerativeModel(GEMINI_MODEL)


def nvidia_nim_invoke(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}",
        "Accept": "application/json",
    }
    payload = {
        "model": NVIDIA_NIM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "temperature": 0.7,
    }
    response = requests.post(NVIDIA_NIM_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()
