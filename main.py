import os
from ollama import Client

from src.prepare_content import search_by_query, format_context
from src.run_prompt import run_prompt

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

  response = run_prompt(query, prepared_context, model='custom_qwen')
  print(f"\n{response}\n")

  try:
    new_query = input("\n Chat (or 'q' to quit): ")
  except EOFError:
    new_query = 'q'

  if new_query.lower() != 'q':
    query = new_query
  else:
     break