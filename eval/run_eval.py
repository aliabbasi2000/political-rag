import asyncio
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness

import os
from dotenv import load_dotenv

load_dotenv()

async def faithfulness_test():
    client = AsyncOpenAI(
        base_url=os.getenv("OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1"), 
        api_key=os.getenv("OLLAMA_API_KEY", "ollama")
    )
    
    llm = llm_factory(
        "qwen3:0.6b", 
        client=client, 
        max_tokens=2048, 
        temperature=0.0
    )
    
    scorer = Faithfulness(llm=llm)

    result = await scorer.ascore(
        user_input="Who is the prime minister of the Italy?",
        response="The Prime Minister of Italy is Giorgia Meloni.",
        retrieved_contexts=["The current president of Italy is Sergio Mattarella, and the current prime minister is Giorgia Meloni."]
    )
    print("Faithfulness score:", result.value)

asyncio.run(faithfulness_test())