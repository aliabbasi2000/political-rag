import os
from ollama import Client

def run_prompt(query, context, model='custom_qwen'):
    """Run a prompt using the provided query and context.
    
    Args:
        query: The user query.
        context: The context.
        model: The model for generating the response.
    """

    prompt = (
        "You must answer using only the context below.\n"
        "If the context is sufficient, answer directly and do not add any disclaimer or refusal sentence.\n"
        "If the context is not sufficient, say exactly: I cannot answer from the provided context.\n"
        "When you use a fact from the context, cite it inline using the matching source label exactly as shown.\n\n"
        "<|content_start>\n"
        f"{context}\n"
        "<|content_end>\n\n"
        f"Question: {query}"
    )
    #print(f"\nPrompt:\n{prompt}\n")

    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    client = Client(host=host)

    response = client.chat(model=model, messages=[
        {
            'role': 'user',
            'content': prompt,
        },
    ])

    return response.message.content
