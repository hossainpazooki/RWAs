"""API routes for embedding generation (Story 2 stubs).

Provides endpoints for generating and retrieving embeddings for rules.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlmodel import Session

from backend.core.database import get_session
from backend.rule_embedding_service.app.services.schemas import EmbeddingRead
from backend.rule_embedding_service.app.services.service import EmbeddingRuleService

router = APIRouter(prefix="/embedding", tags=["embeddings"])


def get_service(session: Session = Depends(get_session)) -> EmbeddingRuleService:
    return EmbeddingRuleService(session)


@router.post("/rules/{rule_id}/embeddings/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_embeddings(
    rule_id: str,
    background_tasks: BackgroundTasks,
    service: EmbeddingRuleService = Depends(get_service),
) -> dict:
    """Regenerate embeddings for a rule asynchronously.

    This endpoint queues embedding generation as a background task.

    Args:
        rule_id: The rule identifier to generate embeddings for
        background_tasks: FastAPI background tasks handler

    Returns:
        Status message with task information

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

    # Stub: Queue embedding generation
    raise NotImplementedError("Stub: async embedding generation")


@router.get("/rules/{rule_id}/embeddings", response_model=list[EmbeddingRead])
async def get_embeddings(
    rule_id: str,
    service: EmbeddingRuleService = Depends(get_service),
) -> list[EmbeddingRead]:
    """Retrieve all embeddings for a rule.

    Returns embeddings for all 4 types (semantic, structural, entity, legal).

    Args:
        rule_id: The rule identifier

    Returns:
        List of embedding records for the rule

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

    # Stub: Retrieve embeddings
    raise NotImplementedError("Stub: get embeddings")


@router.delete("/rules/{rule_id}/embeddings", status_code=status.HTTP_204_NO_CONTENT)
async def delete_embeddings(
    rule_id: str,
    service: EmbeddingRuleService = Depends(get_service),
) -> None:
    """Delete all embeddings for a rule.

    Useful for forcing regeneration of embeddings.

    Args:
        rule_id: The rule identifier

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

    # Stub: Delete embeddings
    raise NotImplementedError("Stub: delete embeddings")


@router.get("/stats", response_model=dict)
async def get_embedding_stats(
    service: EmbeddingRuleService = Depends(get_service),
) -> dict:
    """Get statistics about embeddings in the system.

    Returns counts of rules and embeddings by type.

    Returns:
        Dictionary with embedding statistics

    Raises:
        NotImplementedError: Stub - not yet implemented
    """
    raise NotImplementedError("Stub: embedding statistics")
