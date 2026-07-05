"""
Utility: list all available Vertex AI models for the configured project.

Run:
    python3 scripts/list_models.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from google import genai
from config import GCP_PROJECT, GCP_LOCATION

client = genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)

print("--- AVAILABLE VERTEX AI MODELS ---")
for model_info in client.models.list():
    print(f"- {model_info.name.replace('models/', '')}")
