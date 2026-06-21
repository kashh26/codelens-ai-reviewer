import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load the API key from .env
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.5-flash")

response = model.generate_content(
    "Say hello and confirm you're ready to review code!"
)

print(response.text)

# Optional: see token usage
print(f"\n--- Tokens used: {response.usage_metadata.prompt_token_count} in / "
      f"{response.usage_metadata.candidates_token_count} out ---")