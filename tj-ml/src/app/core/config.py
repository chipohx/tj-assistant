import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    gigachat_auth_key: str
    qdrant_url: str
    collection_name: str
    embedding_model_name: str
    eval_golden_path: str
    eval_runs_dir: str


def get_settings() -> Settings:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    storage_dir = os.path.join(base_dir, "storage", "eval_runs")

    return Settings(
        gigachat_auth_key=os.getenv("GIGACHAT_AUTH_KEY", ""),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        collection_name=os.getenv("QDRANT_COLLECTION", "tj"),
        embedding_model_name=os.getenv(
            "EMBEDDING_MODEL_NAME",
            "sentence-transformers/all-MiniLM-L6-v2",
        ),
        eval_golden_path=os.getenv(
            "EVAL_GOLDEN_PATH",
            os.path.join(data_dir, "eval_golden.json"),
        ),
        eval_runs_dir=os.getenv(
            "EVAL_RUNS_DIR",
            storage_dir,
        ),
    )
