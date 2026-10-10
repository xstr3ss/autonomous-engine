import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

headers = {"Authorization": f"Bearer {api_key}"}
response = requests.get("https://api.groq.com/openai/v1/models", headers=headers)

if response.status_code == 200:
    models = response.json().get("data", [])
    print("\n✅ ACTIVE GROQ MODELS:")
    for m in models:
        print(f" - {m['id']}")
else:
    print(f"❌ Failed to fetch models: {response.text}")
