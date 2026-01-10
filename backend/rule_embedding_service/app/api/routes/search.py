"""API routes for multi-mode similarity search (Story 3 stubs).

Provides endpoints for searching rules using different embedding types and strategies.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from backend.core.database import get_session
from backend.rule_embedding_service.app.services.schemas import (
    TextSearchRequest,
    EntitySearchRequest,
    OutcomeSearchRequest,
    LegalSourceSearchRequest,
    HybridSearchRequest,
    SearchResult,
)
from backend.rule_embedding_service.app.services.service import EmbeddingRuleService

router = APIRouter(prefix="/embedding/search", tags=["search"])


def get_service(session: Session = Depends(get_session)) -> EmbeddingRuleService:
    return EmbeddingRuleService(session)


@router.post("/by-text", response_model=list[SearchResult])
async def search_by_text(
    request: TextSearchRequest,
    service: EmbeddingRuleService = Depends(get_service),
) -> list[SearchResult]:
    """Search rules by natural language query.

    Uses semantic embeddings to find rules that match the meaning
    of the query text, even with different terminology.

    Args:
        request: Search parameters including query text and limits

    Returns:
        List of matching rules ranked by similarity

    Raises:
        NotImplementedError: Stub - not yet implemented
    """
    raise NotImplementedError("Stub: text search")


@router.post("/by-entities", response_model=list[SearchResult])
async def search_by_entities(
    request: EntitySearchRequest,
    service: EmbeddingRuleService = Depends(get_service),
) -> list[SearchResult]:
    """Search rules by entity list.

    Finds rules that reference similar data fields or entities,
    useful for impact analysis when fields change.

    Args:
        request: List of entities (field names, operators) to search for

    Returns:
        List of rules using similar entities

    Examples:
        Search for rules using income-related fields:
        {"entities": ["income", "salary", "annual_income"]}

    Raises:
        NotImplementedError: Stub - not yet implemented
    """
    raise NotImplementedError("Stub: entity search")


@router.post("/by-outcome", response_model=list[SearchResult])
async def search_by_outcome(
    request: OutcomeSearchRequest,
    service: EmbeddingRuleService = Depends(get_service),
) -> list[SearchResult]:
    """Search rules by decision outcome.

    Finds rules that produce similar decisions/outcomes,
    useful for finding related compliance requirements.

    Args:
        request: Decision outcome to search for (e.g., 'approved', 'eligible')

    Returns:
        List of rules with similar outcomes

    Raises:
        NotImplementedError: Stub - not yet implemented
    """
    raise NotImplementedError("Stub: outcome search")


@router.post("/by-legal-source", response_model=list[SearchResult])
async def search_by_legal_source(
    request: LegalSourceSearchRequest,
    service: EmbeddingRuleService = Depends(get_service),
) -> list[SearchResult]:
    """Search rules by legal citation.

    Finds all rules derived from the same legal source,
    useful for regulatory change impact analysis.

    Args:
        request: Legal citation or document ID to search for

    Returns:
        List of rules from the same legal source

    Examples:
        Find rules from MiCA Article 36:
        {"citation": "MiCA Article 36", "document_id": "mica_2023"}

    Raises:
        NotImplementedError: Stub - not yet implemented
    """
    raise NotImplementedError("Stub: legal source search")


@router.post("/hybrid", response_model=list[SearchResult])
async def search_hybrid(
    request: HybridSearchRequest,
    service: EmbeddingRuleService = Depends(get_service),
) -> list[SearchResult]:
    """Search with custom embedding type weights.

    Combines multiple embedding types with custom weights
    for fine-grained similarity search.

    Args:
        request: Query and weights for each embedding type

    Returns:
        List of rules ranked by weighted similarity

    Examples:
        Prioritize structural similarity over semantic:
        {
            "query": "income eligibility",
            "weights": {"semantic": 0.2, "structural": 0.5, "entity": 0.2, "legal": 0.1}
        }

    Raises:
        HTTPException: If weights don't sum to 1.0
        NotImplementedError: Stub - not yet implemented
    """
    # Validate weights sum to 1.0 (approximately)
    total = sum(request.weights.values())
    if abs(total - 1.0) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Weights must sum to 1.0, got {total}",
        )

    raise NotImplementedError("Stub: hybrid search")


@router.post("/similar/{rule_id}", response_model=list[SearchResult])
async def find_similar_rules(
    rule_id: str,
    embedding_type: str = "semantic",
    top_k: int = 10,
    service: EmbeddingRuleService = Depends(get_service),
) -> list[SearchResult]:
    """Find rules similar to a given rule.

    Uses the specified embedding type to find similar rules.

    Args:
        rule_id: Reference rule to find similar rules for
        embedding_type: Which embedding to use (semantic/structural/entity/legal)
        top_k: Number of results to return

    Returns:
        List of similar rules (excluding the reference rule)

    Raises:
        HTTPException: If the rule is not found
        NotImplementedError: Stub - not yet implemented
    """
    # Verify rule exists
    rule = service.get_rule_by_rule_id(rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule '{rule_id}' not found",
        )

    raise NotImplementedError("Stub: similar rules search")
