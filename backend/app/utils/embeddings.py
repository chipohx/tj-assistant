"""
Docstring
"""

from __future__ import annotations
from typing import List, Optional, Iterable
import itertools
import numpy as np
from sentence_transformers import SentenceTransformer


def _chunked(iterable: Iterable, size: int):
    """
    Docstring
    """
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk


def _l2_normalize(vec: List[float]) -> List[float]:
    """
    Docstring
    """
    a = np.array(vec, dtype=float)
    norm = np.linalg.norm(a)
    if norm == 0:
        return vec
    return (a / norm).tolist()

class SentenceTransformerEmbedder():
    """
    Docstring
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        batch_size: int = 64,
        normalize: bool = True,
    ):
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.normalize = normalize
        # lazy load model
        self._model: Optional[SentenceTransformer] = None

    @property
    def model(self) -> SentenceTransformer:
        """
        Docstring
        """
        if self._model is None:
            if self.device:
                self._model = SentenceTransformer(self.model_name, device=self.device)
            else:
                self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Docstring
        """
        if not texts:
            return []
        # sentence-transformers поддерживает батчи внутри encode
        arr = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=False,  # мы нормализуем сами(пока хз, как лучше)
        )
        if self.normalize:
            # arr shape (n, d)
            norms = np.linalg.norm(arr, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            arr = arr / norms
        # возвращаем в виде list[list[float]]
        return arr.astype(float).tolist()
