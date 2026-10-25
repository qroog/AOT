from typing import List, Dict, Any, Set
from src.schemas import Question, LLMOutput

def compute_set_metrics(predicted: Set[str], gold: Set[str]) -> Dict[str, float]:
    if not gold and not predicted:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not gold:
        return {"precision": 0.0, "recall": 1.0, "f1": 0.0}
    if not predicted:
        return {"precision": 1.0, "recall": 0.0, "f1": 0.0}
    
    tp = len(predicted.intersection(gold))
    fp = len(predicted - gold)
    fn = len(gold - predicted)
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3)}

def evaluate_single(question: Question, output: LLMOutput) -> Dict[str, Any]:
    status_match = (output.status == question.gold_status)
    ev_metrics = compute_set_metrics(set(output.evidence_ids), set(question.gold_evidence_ids))
    cev_metrics = compute_set_metrics(set(output.counterevidence_ids), set(question.gold_counterevidence_ids))
    
    return {
        "question_id": question.question_id,
        "question_type": question.question_type,
        "gold_status": question.gold_status,
        "pred_status": output.status,
        "status_match": status_match,
        "confidence": output.confidence,
        "evidence_f1": ev_metrics["f1"],
        "evidence_precision": ev_metrics["precision"],
        "evidence_recall": ev_metrics["recall"],
        "counterevidence_recall": cev_metrics["recall"],
    }

def aggregate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not results:
        return {}
    n = len(results)
    acc = sum(1 for r in results if r["status_match"]) / n
    ev_f1 = sum(r["evidence_f1"] for r in results) / n
    ev_prec = sum(r["evidence_precision"] for r in results) / n
    ev_rec = sum(r["evidence_recall"] for r in results) / n
    
    # Specific metrics for 'both' and 'insufficient'
    both_cases = [r for r in results if r["gold_status"] == "both"]
    both_acc = (sum(1 for r in both_cases if r["pred_status"] == "both") / len(both_cases)) if both_cases else 1.0
    
    insufficient_cases = [r for r in results if r["gold_status"] == "insufficient"]
    insufficient_acc = (sum(1 for r in insufficient_cases if r["pred_status"] == "insufficient") / len(insufficient_cases)) if insufficient_cases else 1.0
    
    overconfident_insufficient = sum(1 for r in insufficient_cases if r["confidence"] > 0.7) / len(insufficient_cases) if insufficient_cases else 0.0
    
    return {
        "status_accuracy": round(acc, 3),
        "mean_evidence_f1": round(ev_f1, 3),
        "mean_evidence_precision": round(ev_prec, 3),
        "mean_evidence_recall": round(ev_rec, 3),
        "both_accuracy": round(both_acc, 3),
        "insufficient_accuracy": round(insufficient_acc, 3),
        "overconfident_insufficient_ratio": round(overconfident_insufficient, 3),
    }
