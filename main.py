import os
from ollama import Client
import sys

from src.prepare_content import search_by_query

query = "Tell me about children's rights in Iran."
if len(sys.argv) > 1:
    query = sys.argv[1]
context = search_by_query(query)

prompt = f"<|content> {context}<|content_end> {query}"
print(f"\nPrompt:\n{prompt}\n")


host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
client = Client(host=host)

response = client.chat(model='qwen3:0.6b', messages=[
  {
    'role': 'user',
    'content': prompt,
  },
])

print(response.message.content)