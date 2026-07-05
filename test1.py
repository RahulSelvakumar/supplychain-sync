# First, you might need to run: pip install google-genai
from google import genai

# Initialize the modern client, explicitly pointing it to Vertex AI
client = genai.Client(
    vertexai=True, 
    project="supplychain-sync-hackathon", 
    location="us-central1"
)

print("--- AVAILABLE VERTEX AI MODELS ---")

# Iterate through Google's foundational catalog and print the exact ID strings
for model_info in client.models.list():
    # We print the model name, avoiding the 'models/' prefix for cleaner reading
    model_name = model_info.name.replace("models/", "")
    print(f"- {model_name}")