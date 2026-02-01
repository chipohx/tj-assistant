import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.eval import GoldenItem, EvalItemResult
from app.services.rag_chain import query_rag


logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _f1_score(prediction: str, ground_truth: str) -> float:
    pred_tokens = _normalize(prediction).split()
    gt_tokens = _normalize(ground_truth).split()
    if not pred_tokens or not gt_tokens:
        return 0.0
    common = set(pred_tokens) & set(gt_tokens)
    if not common:
        return 0.0
    precision = len(common) / len(pred_tokens)
    recall = len(common) / len(gt_tokens)
    return 2 * precision * recall / (precision + recall)


def _exact_match(prediction: str, ground_truth: str) -> float:
    return 1.0 if _normalize(prediction) == _normalize(ground_truth) else 0.0


def _ensure_runs_dir() -> str:
    settings = get_settings()
    os.makedirs(settings.eval_runs_dir, exist_ok=True)
    return settings.eval_runs_dir


def _run_path(run_id: str) -> str:
    runs_dir = _ensure_runs_dir()
    return os.path.join(runs_dir, f"{run_id}.json")


def _get_embedding_model_name() -> str:
    settings = get_settings()
    return settings.embedding_model_name


def load_golden_set() -> List[GoldenItem]:
    settings = get_settings()
    if not os.path.exists(settings.eval_golden_path):
        raise FileNotFoundError(f"Golden set not found: {settings.eval_golden_path}")
    with open(settings.eval_golden_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return [GoldenItem(**item) for item in data]


def create_run(run_name: Optional[str] = None) -> str:
    run_id = str(uuid.uuid4())
    run_path = _run_path(run_id)
    payload = {
        "run_id": run_id,
        "run_name": run_name,
        "status": "running",
        "started_at": _now_iso(),
        "finished_at": None,
        "metrics": {},
        "items": [],
        "error": None,
    }
    with open(run_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return run_id


def read_run(run_id: str) -> Dict:
    run_path = _run_path(run_id)
    if not os.path.exists(run_path):
        raise FileNotFoundError(f"Run not found: {run_id}")
    with open(run_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_run(run_id: str, payload: Dict) -> None:
    run_path = _run_path(run_id)
    with open(run_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def run_evaluation(run_id: str) -> None:
    try:
        run_data = read_run(run_id)
        golden_set = load_golden_set()

        results: List[EvalItemResult] = []
        exact_matches = []
        f1_scores = []

        for item in golden_set:
            predicted, _context, _docs = query_rag(item.question)
            exact = _exact_match(predicted, item.answer)
            f1 = _f1_score(predicted, item.answer)
            exact_matches.append(exact)
            f1_scores.append(f1)
            results.append(
                EvalItemResult(
                    question=item.question,
                    expected_answer=item.answer,
                    predicted_answer=predicted,
                    exact_match=exact,
                    f1=f1,
                )
            )

        metrics = {
            "count": len(results),
            "exact_match_avg": sum(exact_matches) / len(exact_matches)
            if exact_matches
            else 0.0,
            "f1_avg": sum(f1_scores) / len(f1_scores) if f1_scores else 0.0,
        }

        run_data.update(
            {
                "status": "completed",
                "embedding_model": _get_embedding_model_name(),
                "finished_at": _now_iso(),
                "metrics": metrics,
                "items": [result.model_dump() for result in results],
            }
        )
        write_run(run_id, run_data)
    except Exception as exc:
        logger.exception("Evaluation failed: %s", exc)
        run_data = read_run(run_id)
        run_data.update(
            {
                "status": "failed",
                "embedding_model": _get_embedding_model_name(),
                "finished_at": _now_iso(),
                "error": str(exc),
            }
        )
        write_run(run_id, run_data)
