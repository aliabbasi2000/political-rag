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
        Dict or bool: Returns a Dict of scores that are below the threshold if any, otherwise returns False.
    """
    flagged = {}
    for metric, score in ragas_scores.items():
        if score < threshold:
            flagged[metric] = score

    return False if not flagged else flagged

def collect_human_feedback(question, response, reference_answer, ragas_scores, hitl_flag_reasons):
    print(f"=== Human Feedback Needed: {hitl_flag_reasons} ===")
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
        "flag_reason": hitl_flag_reasons,
        "human_reviewer": os.getenv("HITL_REVIEWER_NAME", "unknown"),
        "human_feedback": feedback,
        "human_comment": comment,
        "review_timestamp": datetime.datetime.now().isoformat()
    }
    return feedback_data