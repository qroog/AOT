from typing import List, Dict, Any, Set
from src.schemas import Question, LLMOutput

def compute_set_metrics(pred: Set[str], gold: Set[str]) -> Dict[str, float]:
    if not gold and not pred: return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not gold or not pred: return {"precision": 0.0 if not gold else 1.0, "recall": 0.0, "f1": 0.0}
    tp = len(pred & gold)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gold) if gold else 0.0
    f1 = 2 * p * r / (p + r) if (p + r) else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3), "f1": round(f1, 3)}

def evaluate_single(q: Question, out: LLMOutput) -> Dict[str, Any]:
    ev_m = compute_set_metrics(set(out.evidence_ids), set(q.gold_evidence_ids))
    cev_m = compute_set_metrics(set(out.counterevidence_ids), set(q.gold_counterevidence_ids))
    return {
        "question_id": q.question_id, "question_type": q.question_type, "gold_status": q.gold_status,
        "pred_status": out.status, "status_match": out.status == q.gold_status, "confidence": out.confidence,
        "evidence_f1": ev_m["f1"], "evidence_precision": ev_m["precision"], "evidence_recall": ev_m["recall"],
        "counterevidence_recall": cev_m["recall"]
    }

def aggregate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not results: return {}
    n = len(results)
    both = [r for r in results if r["gold_status"] == "both"]
    insuf = [r for r in results if r["gold_status"] == "insufficient"]
    return {
        "status_accuracy": round(sum(r["status_match"] for r in results) / n, 3),
        "mean_evidence_f1": round(sum(r["evidence_f1"] for r in results) / n, 3),
        "both_accuracy": round(sum(r["pred_status"] == "both" for r in both) / len(both), 3) if both else 1.0,
        "insufficient_accuracy": round(sum(r["pred_status"] == "insufficient" for r in insuf) / len(insuf), 3) if insuf else 1.0,
        "overconfident_insufficient_ratio": round(sum(r["confidence"] > 0.7 for r in insuf) / len(insuf), 3) if insuf else 0.0
    }
