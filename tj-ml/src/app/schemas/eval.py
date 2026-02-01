from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GoldenItem(BaseModel):
    question: str
    answer: str
    reference_context: Optional[str] = None


class EvalRunRequest(BaseModel):
    run_name: Optional[str] = None


class EvalRunResponse(BaseModel):
    run_id: str
    status: str


class EvalStatusResponse(BaseModel):
    run_id: str
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error: Optional[str] = None


class EvalItemResult(BaseModel):
    question: str
    expected_answer: str
    predicted_answer: str
    exact_match: float
    f1: float


class EvalReport(BaseModel):
    run_id: str
    status: str
    metrics: Dict[str, Any]
    items: List[EvalItemResult]
