import os
import json
import asyncio
import pandas as pd
import csv
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall
from ragas.embeddings.base import embedding_factory
from src.prepare_content import search_by_query, format_context
from src.run_prompt import run_prompt
from src.hitl_review import is_hitl_enabled, flag_for_feedback, collect_human_feedback


OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
JUDGE_MODEL = os.environ.get("RAGAS_JUDGE_MODEL", "judge_qwen")
EMBED_MODEL = os.environ.get("RAGAS_EMBED_MODEL", "nomic-embed-text")
CHAT_MODEL = os.environ.get("OLLAMA_MODEL", "custom_qwen")
HITL_FLAG_THRESHOLD = float(os.environ.get("HITL_FLAG_THRESHOLD", 0.7))

DATASET_PATH = "eval/golden_dataset.json"
GENERATED_ANSWERS_PATH = "eval/gen_qwen1.7b_judge_qwen4b/generated_answers.json"
EVAL_RESULTS_PATH = "eval/gen_qwen1.7b_judge_qwen4b/eval_results.csv"
HITL_FEEDBACK_PATH = "eval/gen_qwen1.7b_judge_qwen4b/hitl_feedback.json"


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

def load_hitl_feedbacks(path=HITL_FEEDBACK_PATH):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def load_eval_result(path=EVAL_RESULTS_PATH):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))

def save_hitl_feedback(feedback_data, path=HITL_FEEDBACK_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing_feedbacks = load_hitl_feedbacks(path)

    # Handle the duplicates
    is_duplicate = False
    for i in range(len(existing_feedbacks)):
        if (existing_feedbacks[i]["question"] == feedback_data["question"] and
            existing_feedbacks[i]["response"] == feedback_data["response"]):
            # Overwrite the existing feedback entry
            existing_feedbacks[i] = feedback_data
            is_duplicate = True
            break

    if not is_duplicate:
        existing_feedbacks.append(feedback_data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing_feedbacks, f, ensure_ascii=False, indent=2)

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
            reference_answer = item["reference_answer"]
            print(f"[{i}/{len(dataset)}] Question: {question}")

            raw_context = search_by_query(question)
            retrieved_contexts = format_context(raw_context)
            context_text = "\n\n".join(retrieved_contexts)

            response = run_prompt(question, context_text, model=CHAT_MODEL)
            print(f"Generated Response: {response}\n")

            eval_data.append({
                "question": question,
                "reference_answer": reference_answer,
                "response": response,
                "retrieved_contexts": retrieved_contexts
            })
            save_generated_answers(eval_data)

        print(f"Saved generated answers to {GENERATED_ANSWERS_PATH}")

    # PASS 2: Evaluate All Answers using JUDGE_MODEL
    eval_result = load_eval_result()
    if eval_result is None:
        eval_data = load_generated_answers()
        if eval_data is None:
            raise RuntimeError(f"PASS 1 output file not found: {GENERATED_ANSWERS_PATH}")

        print("\n=== PASS 2: Evaluating Generated Answers ===")
        ollama_client = AsyncOpenAI(base_url=f"{OLLAMA_HOST}/v1", api_key="ollama")
        
        judge_llm = llm_factory(
            JUDGE_MODEL,
            client=ollama_client,
            max_tokens=8192,
            temperature=0.0
        )

        judge_embeddings = embedding_factory(
            "openai",
            model=EMBED_MODEL,
            client=ollama_client
        )

        faithfulness = Faithfulness(llm=judge_llm)
        answer_relevancy = AnswerRelevancy(llm=judge_llm, embeddings=judge_embeddings)
        context_precision = ContextPrecision(llm=judge_llm)
        context_recall = ContextRecall(llm=judge_llm)

        eval_result = []
        for i, item in enumerate(eval_data, 1):
            question = item["question"]
            reference_answer = item["reference_answer"]
            response = item["response"]
            retrieved_contexts = item["retrieved_contexts"]

            print(f"\n[{i}/{len(eval_data)}] Question: {question}")
            
            metrics = {
                "faithfulness": None,
                "answer_relevancy": None,
                "context_precision": None,
                "context_recall": None
            }

            for metric_name in metrics.keys():
                try:
                    if metric_name == "faithfulness":
                        score = await faithfulness.ascore(
                            user_input=question,
                            response=response,
                            retrieved_contexts=retrieved_contexts
                        )
                    elif metric_name == "answer_relevancy":
                        score = await answer_relevancy.ascore(
                            user_input=question,
                            response=response
                        )
                    elif metric_name == "context_precision":
                        score = await context_precision.ascore(
                            user_input=question,
                            reference=reference_answer,
                            retrieved_contexts=retrieved_contexts
                        )
                    elif metric_name == "context_recall":
                        score = await context_recall.ascore(
                            user_input=question,
                            reference=reference_answer,
                            retrieved_contexts=retrieved_contexts
                        )
                    metrics[metric_name] = score.value
                    print(f"{metric_name} score: {score.value}")
                except Exception as e:
                    print(f"Error calculating {metric_name} score sample[{i}]: {e}")

            eval_result.append({
                "question": question,
                "reference_answer": reference_answer,
                "response": response,
                "faithfulness": metrics["faithfulness"],
                "answer_relevancy": metrics["answer_relevancy"],
                "context_precision": metrics["context_precision"],
                "context_recall": metrics["context_recall"],
            })

            df = pd.DataFrame(eval_result)
            df.to_csv(EVAL_RESULTS_PATH, index=False)

        print(f"\nSaved Eval results to {EVAL_RESULTS_PATH}")
        print("\n=== Mean scores ===")
        print(df[["faithfulness", "answer_relevancy", "context_precision", "context_recall"]].mean())

    # PASS 3: Huamn In The Loop
    print("\n=== PASS 2: Human In The Loop ===")
    if is_hitl_enabled():
        existing_feedback = load_hitl_feedbacks()
        existing_questions = {item["question"] for item in existing_feedback}
        for row in eval_result:
            if row["question"] in existing_questions:
                continue
            metrics = {}
            for k in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
                metrics[k] = float(row[k])
                
            hitl_flag_reasons = flag_for_feedback(metrics, threshold=HITL_FLAG_THRESHOLD)
            # if HITL is needed due to low scores, collect human feedback
            if hitl_flag_reasons:
                review = collect_human_feedback(row["question"], row["response"], row["reference_answer"], metrics, "; ".join(map(str, hitl_flag_reasons)))
                if review:
                    save_hitl_feedback(review)
        
    else:
        print("\n(HITL skipped — set HITL_ENABLED=true when an SME is available)")



if __name__ == "__main__":
    asyncio.run(run())