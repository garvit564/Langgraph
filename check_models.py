
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY .env file mein nahi mili!")

client = genai.Client(api_key=api_key)

print("\nAvailable models:\n")

for model in client.models.list():
    supported_methods = model.supported_actions or []

    if "generateContent" in supported_methods:
        print(model.name)

