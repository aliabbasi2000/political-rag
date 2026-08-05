import asyncio
import pandas as pd
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness
import json
import os
from ragas.embeddings.base import embedding_factory
from src.prepare_content import search_by_query, format_context
from src.run_prompt import run_prompt


OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
JUDGE_MODEL = os.environ.get("RAGAS_JUDGE_MODEL", "judge_qwen")
EMBED_MODEL = os.environ.get("RAGAS_EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.environ.get("OLLAMA_MODEL", "custom_qwen")

DATASET_PATH = "data/eval/golden_dataset.json"
RESULTS_PATH = "data/eval/results.csv"


def load_dataset(path=DATASET_PATH):
    with open(path) as f:
        return json.load(f)

async def run():
    ollama_client = AsyncOpenAI(base_url=f"{OLLAMA_HOST}/v1", api_key="ollama")

    judge_llm = llm_factory(
        JUDGE_MODEL,
        client=ollama_client,
        max_tokens=2048,
        temperature=0.0
    )
    faithfulness = Faithfulness(llm=judge_llm)

    dataset = load_dataset()
    rows = []

    for i, item in enumerate(dataset, 1):
        question = item["question"]
        print(f"[Test {i}/{len(dataset)}] {question}")

        raw_context = search_by_query(question)
        retrieved_contexts = format_context(raw_context)
        context_text = "\n\n".join(retrieved_contexts)
        response = run_prompt(question, context_text, model=CHAT_MODEL)

        faith_score = await faithfulness.ascore(
            user_input=question, response=response, retrieved_contexts=retrieved_contexts
        )

        rows.append({
            "question": question,
            "response": response,
            "faithfulness": faith_score.value  
        })
        print(f"Response: {response}")
        print(f"Faithfulness score: {faith_score.value}\n")

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS_PATH, index=False)

    print(f"\nResults saved to {RESULTS_PATH}")
    print("\n=== Mean scores ===")
    print(df[["faithfulness"]].mean())


if __name__ == "__main__":
    asyncio.run(run())