from typing import List
from numpy import dot
from numpy.linalg import norm
import torch

# torch==2.1.0's CPU wheel has a broken oneDNN/mkldnn kernel path on aarch64
# (ARM64) that segfaults (SIGSEGV, exit 139) on a real transformer forward
# pass — model loading and tokenization work fine, only inference crashes,
# and since it's a native crash no Python try/except can catch it. Must be
# disabled before the first .encode() call in the process; also protects
# services/ml/moderation.py's toxic-bert pipeline, loaded later in the same
# process. Harmless on x86, where mkldnn works correctly.
torch.backends.mkldnn.enabled = False

from sentence_transformers import SentenceTransformer

EMBEDDING_DIM = 384

# Loaded once per process at import time so requests never pay model-load cost.
model = SentenceTransformer("all-MiniLM-L6-v2")


def encode_text(text: str) -> List[float]:
    """Embed text into a 384-dim SBERT vector."""
    return model.encode(text).tolist()


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    return float(dot(v1, v2) / (norm(v1) * norm(v2)))
