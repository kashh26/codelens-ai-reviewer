import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-2.0-flash-lite")

SYSTEM_PROMPT = """You are a senior software engineer doing a thorough code review.

For the code provided, analyze it across these categories:
1. BUGS - logic errors, edge cases, potential crashes
2. SECURITY - injection risks, hardcoded secrets, unsafe operations
3. STYLE - readability, naming, formatting issues
4. PERFORMANCE - inefficiencies, unnecessary complexity

Output your review in this exact format:

## Summary
(1-2 sentence overall verdict)

## Issues Found
For each issue, use this format:
- [SEVERITY: HIGH/MEDIUM/LOW] [CATEGORY] Description of the issue
  Suggestion: how to fix it

## What's Good
(briefly note anything done well)

If there are no issues in a category, skip it. Be specific and reference line numbers or exact code where possible. Be concise — no fluff."""

# Example code to review - replace this with your own code later
CODE_TO_REVIEW = """
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    result = db.execute(query)
    return result

def calculate_discount(price, discount_percent):
    return price - (price * discount_percent)
"""

response = model.generate_content(
    f"{SYSTEM_PROMPT}\n\nHere is the code to review:\n\n```python\n{CODE_TO_REVIEW}\n```"
)

print(response.text)
print(f"\n--- Tokens used: {response.usage_metadata.prompt_token_count} in / "
      f"{response.usage_metadata.candidates_token_count} out ---")