from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class Document(BaseModel):
    document_id: str
    title: str
    source_type: str
    created_at: str
    author: str
    text: str

class Claim(BaseModel):
    claim_id: str
    text: str
    document_id: str
    evidence: str
    status: Literal["direct", "reported", "inferred", "disputed"]

class Question(BaseModel):
    question_id: str
    question: str
    question_type: Optional[str] = None
    gold_status: Literal["entailed", "contradicted", "both", "insufficient"]
    gold_answer: str
    gold_evidence_ids: List[str] = Field(default_factory=list)
    gold_counterevidence_ids: List[str] = Field(default_factory=list)

class LLMOutput(BaseModel):
    question_id: str
    status: Literal["entailed", "contradicted", "both", "insufficient"]
    answer: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)
    counterevidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
