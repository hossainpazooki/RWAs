"""Rule embedding service API routes."""

from .embedding import router as embedding_router
from .embeddings import router as embeddings_router
from .search import router as search_router
from .graph import router as graph_router

__all__ = [
    "embedding_router",
    "embeddings_router",
    "search_router",
    "graph_router",
]
