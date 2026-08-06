"""Embeddings service using a local/open model (SentenceTransformers).

Responsibility:
chunks -> embedding model -> vectors

Usage:
from backend.app.services.embeddings import get_embedding_service
emb = get_embedding_service()
vectors = emb.embed(chunks)
"""
from __future__ import annotations

from typing import List, Optional

import numpy as np

try:
	from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
	SentenceTransformer = None  # type: ignore


class EmbeddingService:
	"""Wrap a local SentenceTransformers model to produce embeddings.

	Defaults to `all-MiniLM-L6-v2`, a compact and fast model suitable for local use.
	"""

	def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: Optional[str] = None):
		if SentenceTransformer is None:
			raise RuntimeError(
				"sentence-transformers is not installed. Install it or update requirements."
			)
		self.model_name = model_name
		self.device = device
		self._model: Optional[SentenceTransformer] = None

	def _load(self) -> None:
		if self._model is None:
			if self.device:
				self._model = SentenceTransformer(self.model_name, device=self.device)
			else:
				self._model = SentenceTransformer(self.model_name)

	def embed(self, texts: List[str], batch_size: int = 32, normalize: bool = True) -> List[List[float]]:
		"""Return a list of embedding vectors (one per input text).

		Args:
			texts: list of input text chunks to embed.
			batch_size: encode batch size used by the underlying model.
			normalize: whether to L2-normalize the vectors (useful for cosine similarity).

		Returns:
			List of vectors where each vector is a list[float].
		"""
		if not texts:
			return []
		self._load()
		assert self._model is not None

		embeddings = self._model.encode(
			texts,
			batch_size=batch_size,
			convert_to_numpy=True,
			show_progress_bar=False,
		)

		if normalize:
			norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
			norms[norms == 0] = 1.0
			embeddings = embeddings / norms

		return embeddings.tolist()


_default_service: Optional[EmbeddingService] = None


def get_embedding_service(model_name: str = "all-MiniLM-L6-v2", device: Optional[str] = None) -> EmbeddingService:
	global _default_service
	if _default_service is None:
		_default_service = EmbeddingService(model_name=model_name, device=device)
	return _default_service
