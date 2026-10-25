import random
from typing import List, Dict, Tuple
from src.schemas import Document, Claim
from src.padic import format_padic_context

def build_mode_a_context(docs: List[Document]) -> str:
    return "\n".join(f"=== {d.document_id}: {d.title} ({d.source_type}, {d.author}, {d.created_at}) ===\n{d.text}\n" for d in docs)

def build_mode_b_context(claims: List[Claim]) -> str:
    return "=== BM25 TOP-15 УТВЕРЖДЕНИЙ ===\n" + "\n".join(f"[{c.claim_id}] {c.text} (Источник: {c.document_id}, {c.status})" for c in claims)

def build_mode_c_context(claims: List[Claim], paths: Dict[str, Tuple[int, int, int]]) -> str:
    return "=== p-АДИЧЕСКАЯ ИЕРАРХИЯ ДОКАЗАТЕЛЬСТВ (p=3) ===\n" + format_padic_context(claims, paths)

def permute_documents(docs: List[Document], seed: int = 42) -> List[Document]:
    d = list(docs)
    random.Random(seed).shuffle(d)
    return d

def remove_premise(claims: List[Claim], target_id: str) -> List[Claim]:
    return [c for c in claims if c.claim_id != target_id]

def add_contradiction(claims: List[Claim], item: Claim) -> List[Claim]:
    return list(claims) + [item]
