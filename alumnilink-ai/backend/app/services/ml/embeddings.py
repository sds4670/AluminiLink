from typing import List
from numpy import dot
from numpy.linalg import norm
from sentence_transformers import SentenceTransformer

EMBEDDING_DIM = 384

# Loaded once per process at import time so requests never pay model-load cost.
model = SentenceTransformer("all-MiniLM-L6-v2")


def encode_text(text: str) -> List[float]:
    """Embed text into a 384-dim SBERT vector."""
    return model.encode(text).tolist()


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    return float(dot(v1, v2) / (norm(v1) * norm(v2)))
