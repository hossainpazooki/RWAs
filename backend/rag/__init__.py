"""RAG module - Retrieval-Augmented Generation for factual Q&A."""

from .retriever import Retriever, RetrievalResult
from .bm25 import BM25Index
from .chunker import chunk_text, chunk_by_section, Chunk
from .rule_context import RuleContextRetriever, RuleContext, ProvisionContext

__all__ = [
    "Retriever",
    "RetrievalResult",
    "BM25Index",
    "chunk_text",
    "chunk_by_section",
    "Chunk",
    "RuleContextRetriever",
    "RuleContext",
    "ProvisionContext",
]
