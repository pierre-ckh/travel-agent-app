import anthropic
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_code(prompt, output_file):
    message = client.messages.create(
        model="claude-opus-4-1-20250805",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    code = message.content[0].text
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"Generated {output_file}")

# Example usage below
