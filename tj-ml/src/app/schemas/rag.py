from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=20)


class SourceDocument(BaseModel):
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGQueryResponse(BaseModel):
    answer: str
    context: str
    sources: List[SourceDocument]


class RAGErrorResponse(BaseModel):
    detail: str
