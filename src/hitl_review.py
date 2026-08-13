import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def is_hitl_enabled():
    return os.getenv("HITL_ENABLED", "false").lower() == "true"

def flag_for_feedback(ragas_scores, threshold=0.7):
    """
    Determines if the response should be flagged for human feedback based on RAGAS scores.

    Args:
        ragas_scores (dict): A dictionary containing RAGAS scores.
        threshold (float): The threshold below which feedback is needed.

    Returns:
        bool: True if feedback is needed, False otherwise.
    """
    for score in ragas_scores.values():
        if score < threshold:
            return True
    return False

def collect_human_feedback(question, response, reference_answer, ragas_scores):
    print("=== Human Feedback Needed ===")
    print(f"Question: {question}\nResponse: {response}\nReference Answer: {reference_answer}\nRAGAS Scores: {ragas_scores}")
    feedback = input("Feedback (Approve/Reject/Skip): ").strip().lower()

    if feedback == "skip" or feedback not in ["approve", "reject"]:
        print("Feedback skipped.")
        return None
    comment = input("Comment (optional): ").strip()
    feedback_data = {
        "question": question,
        "response": response,
        "reference_answer": reference_answer,
        "ragas_scores": ragas_scores,
        "human_reviewer": os.getenv("HITL_REVIEWER_NAME", "unknown"),
        "human_feedback": feedback,
        "human_comment": comment,
        "review_timestamp": datetime.datetime.now().isoformat()
    }
    return feedback_data
    
if __name__ == "__main__":
    # Example usage
    ragas_scores = {
        "faithfulness": 0.6,
        "answer_relevancy": 0.8,
        "context_precision": 0.9,
        "context_recall": 1
    }
    
    if is_hitl_enabled() and flag_for_feedback(ragas_scores):
        print(collect_human_feedback("What is the capital of France?", "The capital of France is Berlin.", "The capital of France is Paris.", ragas_scores))