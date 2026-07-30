import os
from ollama import Client

from src.prepare_content import search_by_query, format_context

DEFAULT_QUERY = "Tell me about Politics in Italy."
try:
    query = input("Ask me about Politics (or press enter to tell you about the Politics in Italy): ")
except EOFError:
    query = DEFAULT_QUERY

if not query or query.strip() == "":
    query = DEFAULT_QUERY

while True:
  context = search_by_query(query)
  #print(f"\nRetrieved context:\n{context}\n")
  prepared_context = format_context(context)
  #print(f"\nPrepared context:\n{prepared_context}\n")

  prompt = f"""
  You must answer using only the context below.
  If the context is sufficient, answer directly and do not add any disclaimer or refusal sentence.
  If the context is not sufficient, say exactly: I cannot answer from the provided context.
  When you use a fact from the context, cite it inline using the matching source label exactly as shown.

  <|content_start>
  {prepared_context}
  <|content_end>

  Question: {query}"""
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

  try:
    new_query = input("\n Chat (or 'q' to quit): ")
  except EOFError:
    new_query = 'q'

  if new_query.lower() != 'q':
    query = new_query
  else:
     break