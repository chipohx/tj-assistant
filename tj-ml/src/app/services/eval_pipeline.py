"""
Модуль пайплайна оценки качества RAG.

Реализует полный цикл оценки:
1. Загрузка эталонного набора данных (golden set).
2. Прогон каждого вопроса через RAG-пайплайн.
3. Вычисление метрик: exact match и F1-score по токенам.
4. Сохранение результатов в JSON-файлы.

Оценка запускается асинхронно (в фоновом режиме FastAPI)
и доступна через эндпоинты /eval/*.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.eval import EvalItemResult, GoldenItem
from app.services.rag_chain import query_rag


logger = get_logger(__name__)


def _now_iso() -> str:
    """
    Получить текущее время в формате ISO 8601 (UTC).

    Returns:
        str: Временная метка, например '2025-01-15T12:34:56.789012+00:00'.
    """
    return datetime.now(timezone.utc).isoformat()


def _normalize(text: str) -> str:
    """
    Нормализовать текст для сравнения: привести к нижнему регистру
    и удалить лишние пробелы.

    Args:
        text: Исходный текст.

    Returns:
        str: Нормализованный текст.
    """
    return " ".join(text.lower().split())


def _f1_score(prediction: str, ground_truth: str) -> float:
    """
    Вычислить F1-score по токенам (словам) между предсказанием и эталоном.

    F1 = 2 * precision * recall / (precision + recall),
    где precision = |пересечение| / |предсказание|,
    recall = |пересечение| / |эталон|.

    Args:
        prediction: Текст ответа модели.
        ground_truth: Эталонный ответ.

    Returns:
        float: F1-score от 0.0 до 1.0.
    """
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
    """
    Проверить точное совпадение нормализованных текстов.

    Args:
        prediction: Текст ответа модели.
        ground_truth: Эталонный ответ.

    Returns:
        float: 1.0 при совпадении, 0.0 иначе.
    """
    return 1.0 if _normalize(prediction) == _normalize(ground_truth) else 0.0


def _ensure_runs_dir() -> str:
    """
    Создать директорию для хранения результатов запусков (если не существует).

    Returns:
        str: Путь к директории eval_runs.
    """
    settings = get_settings()
    os.makedirs(settings.eval_runs_dir, exist_ok=True)
    return settings.eval_runs_dir


def _run_path(run_id: str) -> str:
    """
    Получить полный путь к файлу результатов запуска.

    Args:
        run_id: Уникальный идентификатор запуска (UUID).

    Returns:
        str: Полный путь к JSON-файлу запуска.
    """
    runs_dir = _ensure_runs_dir()
    return os.path.join(runs_dir, f"{run_id}.json")


def load_golden_set() -> List[GoldenItem]:
    """
    Загрузить эталонный набор данных из JSON-файла.

    Returns:
        List[GoldenItem]: Список эталонных пар (вопрос, ответ).

    Raises:
        FileNotFoundError: Если файл эталонного набора не найден.
    """
    settings = get_settings()
    if not os.path.exists(settings.eval_golden_path):
        raise FileNotFoundError(
            f"Файл эталонного набора не найден: {settings.eval_golden_path}"
        )
    with open(settings.eval_golden_path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return [GoldenItem(**item) for item in data]


def create_run(run_name: Optional[str] = None) -> str:
    """
    Создать новый запуск оценки.

    Генерирует UUID, создаёт начальный JSON-файл со статусом 'running'.

    Args:
        run_name: Необязательное имя запуска для удобства.

    Returns:
        str: UUID созданного запуска.
    """
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
    """
    Прочитать данные запуска из JSON-файла.

    Args:
        run_id: UUID запуска.

    Returns:
        Dict: Словарь с данными запуска.

    Raises:
        FileNotFoundError: Если файл запуска не найден.
    """
    run_path = _run_path(run_id)
    if not os.path.exists(run_path):
        raise FileNotFoundError(f"Запуск не найден: {run_id}")
    with open(run_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_run(run_id: str, payload: Dict) -> None:
    """
    Записать обновлённые данные запуска в JSON-файл.

    Args:
        run_id: UUID запуска.
        payload: Словарь с данными запуска.
    """
    run_path = _run_path(run_id)
    with open(run_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def run_evaluation(run_id: str) -> None:
    """
    Запустить полный цикл оценки для заданного run_id.

    Прогоняет каждый вопрос из golden set через RAG-пайплайн,
    вычисляет метрики и сохраняет результаты.

    Выполняется в фоновом режиме (BackgroundTasks FastAPI).

    Args:
        run_id: UUID запуска, созданного через create_run().
    """
    try:
        run_data = read_run(run_id)
        golden_set = load_golden_set()

        results: List[EvalItemResult] = []
        exact_matches: List[float] = []
        f1_scores: List[float] = []

        for i, item in enumerate(golden_set, 1):
            logger.info(
                "Оценка вопроса %d/%d: '%s'",
                i,
                len(golden_set),
                item.question[:60],
            )
            # Используем прямой RAG (без агента) для детерминированности оценки
            predicted, _context, _docs, _token_usage = query_rag(item.question)

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
            "exact_match_avg": (
                sum(exact_matches) / len(exact_matches) if exact_matches else 0.0
            ),
            "f1_avg": sum(f1_scores) / len(f1_scores) if f1_scores else 0.0,
        }

        settings = get_settings()
        run_data.update(
            {
                "status": "completed",
                "embedding_model": settings.embedding_model_name,
                "gigachat_model": settings.gigachat_model,
                "finished_at": _now_iso(),
                "metrics": metrics,
                "items": [result.model_dump() for result in results],
            }
        )
        write_run(run_id, run_data)
        logger.info(
            "Оценка завершена: run_id=%s, F1=%.3f, EM=%.3f",
            run_id,
            metrics["f1_avg"],
            metrics["exact_match_avg"],
        )

    except Exception as exc:
        logger.exception("Ошибка оценки: %s", exc)
        try:
            run_data = read_run(run_id)
        except FileNotFoundError:
            run_data = {"run_id": run_id}

        settings = get_settings()
        run_data.update(
            {
                "status": "failed",
                "embedding_model": settings.embedding_model_name,
                "gigachat_model": settings.gigachat_model,
                "finished_at": _now_iso(),
                "error": str(exc),
            }
        )
        write_run(run_id, run_data)
