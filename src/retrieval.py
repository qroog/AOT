import re
from typing import List
from rank_bm25 import BM25Okapi
from src.schemas import Claim

def simple_tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())

class BM25ClaimRetriever:
    def __init__(self, claims: List[Claim]):
        self.claims = claims
        self.corpus = [simple_tokenize(f"{c.text} {c.evidence}") for c in claims]
        self.bm25 = BM25Okapi(self.corpus) if self.corpus else None

    def retrieve(self, query: str, top_k: int = 15) -> List[Claim]:
        if not self.claims or not self.bm25:
            return []
        tokenized_query = simple_tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)
        
        # Индексы, отсортированные по убыванию score
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        top_indices = ranked_indices[:top_k]
        return [self.claims[i] for i in top_indices]
