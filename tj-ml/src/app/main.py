from app.core.config import get_settings
from fastapi import BackgroundTasks, FastAPI, HTTPException

from app.core.logging import configure_logging, get_logger
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, SourceDocument
from app.schemas.eval import (
    EvalRunRequest,
    EvalRunResponse,
    EvalStatusResponse,
    EvalReport
)
from app.services.embeddings import get_embeddings
from app.services.vector_store import get_vector_store
from app.services.llm import get_llm
from app.services.rag_chain import query_rag
from app.services.eval_pipeline import create_run, read_run, run_evaluation


logger = get_logger(__name__)

app = FastAPI(title="RAG Evaluation API", version="0.1.0")


@app.on_event("startup")
def _startup() -> None:
    configure_logging()
    logger.info("Initializing embeddings, vector store, and LLM...")
    get_embeddings()
    get_vector_store()
    get_llm()
    logger.info("Initialization complete.")
    logger.info(get_settings().embedding_model_name)


@app.post("/rag/query", response_model=RAGQueryResponse)
def rag_query(payload: RAGQueryRequest) -> RAGQueryResponse:
    answer, context, docs = query_rag(payload.question, top_k=payload.top_k)
    sources = [
        SourceDocument(content=doc.page_content, metadata=doc.metadata or {})
        for doc in docs
    ]
    return RAGQueryResponse(answer=answer, context=context, sources=sources)


@app.post("/eval/run", response_model=EvalRunResponse)
def eval_run(payload: EvalRunRequest, background_tasks: BackgroundTasks) -> EvalRunResponse:
    run_id = create_run(payload.run_name)
    background_tasks.add_task(run_evaluation, run_id)
    return EvalRunResponse(run_id=run_id, status="running")


@app.get("/eval/status", response_model=EvalStatusResponse)
def eval_status(run_id: str) -> EvalStatusResponse:
    try:
        run_data = read_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EvalStatusResponse(
        run_id=run_data["run_id"],
        status=run_data["status"],
        started_at=run_data.get("started_at"),
        finished_at=run_data.get("finished_at"),
        error=run_data.get("error"),
    )


@app.get("/eval/report", response_model=EvalReport)
def eval_report(run_id: str) -> EvalReport:
    try:
        run_data = read_run(run_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return EvalReport(
        run_id=run_data["run_id"],
        status=run_data["status"],
        metrics=run_data.get("metrics", {}),
        items=run_data.get("items", []),
    )


@app.get("/health")
def health_check():
    return {"status": "healthy"}
