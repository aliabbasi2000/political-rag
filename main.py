import os
from ollama import Client

from src.prepare_content import search_by_query

query = input("Ask me about Politics (or press enter to tell you about the Politics in Italy): ")
if not query or query.strip() == "":
    query = "Tell me about Politics in Italy."

while True:
  context = search_by_query(query)

  prompt = f"<|content_start> {context}<|content_end> {query}"
  #print(f"\nPrompt:\n{prompt}\n")


  host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
  client = Client(host=host)

  response = client.chat(model='custom_qwen', messages=[
    {
      'role': 'user',
      'content': prompt,
    },
  ])

  print(f"\n{response.message.content}\n")

  new_query = input("\n Chat (or 'q' to quit): ")
  if new_query.lower() != 'q':
    query = new_query
  else:
     break