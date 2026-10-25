import random
from typing import List, Dict, Tuple, Optional
from src.schemas import Document, Claim
from src.padic import format_padic_context

def build_mode_a_context(documents: List[Document]) -> str:
    parts = []
    for doc in documents:
        header = f"=== ДОКУМЕНТ {doc.document_id}: {doc.title} ==="
        meta = f"Тип: {doc.source_type} | Автор: {doc.author} | Дата: {doc.created_at}"
        parts.append(f"{header}\n{meta}\n\n{doc.text}\n")
    return "\n".join(parts)

def build_mode_b_context(claims: List[Claim]) -> str:
    lines = ["=== ИЗВЛЕЧЕННЫЕ АТОМАРНЫЕ УТВЕРЖДЕНИЯ (BM25 TOP-15) ==="]
    for c in claims:
        lines.append(f"[{c.claim_id}] {c.text} (Источник: {c.document_id}, Статус: {c.status})")
    return "\n".join(lines)

def build_mode_c_context(
    claims: List[Claim],
    claim_paths: Dict[str, Tuple[int, int, int]]
) -> str:
    header = "=== p-АДИЧЕСКАЯ ИЕРАРХИЯ ДОКАЗАТЕЛЬСТВ (ВЕТВИ p=3) ===\n"
    return header + format_padic_context(claims, claim_paths)

def permute_documents(documents: List[Document], seed: int = 42) -> List[Document]:
    docs_copy = list(documents)
    rng = random.Random(seed)
    rng.shuffle(docs_copy)
    return docs_copy

def remove_premise(claims: List[Claim], target_claim_id: str) -> List[Claim]:
    return [c for c in claims if c.claim_id != target_claim_id]

def add_contradiction(claims: List[Claim], contradiction_claim: Claim) -> List[Claim]:
    return list(claims) + [contradiction_claim]
