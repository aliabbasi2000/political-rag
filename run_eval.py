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
GENERATED_ANSWERS_PATH = "data/eval/generated_answers.json"
EVAL_RESULTS_PATH = "data/eval/eval_results.csv"


def load_dataset(path=DATASET_PATH):
    with open(path) as f:
        return json.load(f)


def save_generated_answers(eval_data, path=GENERATED_ANSWERS_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, ensure_ascii=False, indent=2)


def load_generated_answers(path=GENERATED_ANSWERS_PATH):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


async def run():
    # PASS 1: Generate All Answers using CHAT_MODEL 
    dataset = load_dataset()
    eval_data = load_generated_answers()
    if eval_data is not None:
        print(f"=== PASS 1: Reusing saved answers from {GENERATED_ANSWERS_PATH} ===")
    else:
        eval_data = []
        print("=== PASS 1: Generating Answers ===")
        for i, item in enumerate(dataset, 1):
            question = item["question"]
            print(f"[{i}/{len(dataset)}] Question: {question}")

            raw_context = search_by_query(question)
            retrieved_contexts = format_context(raw_context)
            context_text = "\n\n".join(retrieved_contexts)

            response = run_prompt(question, context_text, model=CHAT_MODEL)
            print(f"Generated Response: {response}\n")

            eval_data.append({
                "question": question,
                "response": response,
                "retrieved_contexts": retrieved_contexts
            })
            save_generated_answers(eval_data)

        print(f"Saved generated answers to {GENERATED_ANSWERS_PATH}")

    # PASS 2: Evaluate All Answers using JUDGE_MODEL
    eval_data = load_generated_answers()
    if eval_data is None:
        raise RuntimeError(f"PASS 1 output file not found: {GENERATED_ANSWERS_PATH}")

    print("\n=== PASS 2: Evaluating Generated Answers ===")
    ollama_client = AsyncOpenAI(base_url=f"{OLLAMA_HOST}/v1", api_key="ollama")
    
    judge_llm = llm_factory(
        JUDGE_MODEL,
        client=ollama_client,
        max_tokens=4096,
        temperature=0.0
    )
    faithfulness = Faithfulness(llm=judge_llm)

    rows = []
    for i, item in enumerate(eval_data, 1):
        question = item["question"]
        response = item["response"]
        retrieved_contexts = item["retrieved_contexts"]

        print(f"[{i}/{len(eval_data)}] Question: {question}")
        
        faith_score_value = None
        try:
            faith_score = await faithfulness.ascore(
                user_input=question,
                response=response,
                retrieved_contexts=retrieved_contexts
            )
            faith_score_value = faith_score.value
            print(f"Faithfulness score: {faith_score_value}\n")
        except Exception as e:
            print(f"Error calculating score sample[{i}]: {e}\n")

        rows.append({
            "question": question,
            "response": response,
            "faithfulness": faith_score_value
        })

        df = pd.DataFrame(rows)
        df.to_csv(EVAL_RESULTS_PATH, index=False)

    print(f"\nSaved Eval results to {EVAL_RESULTS_PATH}")
    print("\n=== Mean scores ===")
    print(df[["faithfulness"]].mean())


if __name__ == "__main__":
    asyncio.run(run())