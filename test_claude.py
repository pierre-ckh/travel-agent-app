import anthropic
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
message = client.messages.create(
    model="claude-opus-4-1-20250805",
    
    # model="claude-opus-4-20250514", - works
    # model="claude-sonnet-4-20250514",  - works
    # model="claude-3-7-sonnet-20250219",  - works
    # model="claude-3-5-haiku-20241022",  - works
    # model="claude-3-haiku-20240307", - works
    
    max_tokens=1000,
    messages=[{"role": "user", "content": "Hello, Claude!"}]
)
print(message.content[0].text)