"""Analytics API routes for rule comparison, clustering, and similarity search.

These endpoints power the AI Engineering Workbench:
- Rule comparison across embedding types
- Clustering with K-means/DBSCAN
- Conflict detection
- Similarity search with explanations
- Coverage analysis
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from .schemas import (
    EmbeddingTypeEnum,
    ClusterAlgorithm,
    CompareRulesRequest,
    ComparisonResult,
    ClusterRequest,
    ClusterAnalysis,
    ConflictSearchRequest,
    ConflictReport,
    SimilarRulesRequest,
    SimilarRulesResponse,
    CoverageReport,
    UMAPProjectionRequest,
    UMAPProjectionResponse,
    GraphData,
    GraphNode,
    GraphLink,
)
from .service import RuleAnalyticsService
# Import from rules domain
from backend.rules import RuleLoader


router = APIRouter(prefix="/analytics", tags=["analytics"])


# =============================================================================
# Shared State (would be dependency-injected in production)
# =============================================================================

_rule_loader: RuleLoader | None = None
_analytics_service: RuleAnalyticsService | None = None


def get_rule_loader() -> RuleLoader:
    """Get or create the rule loader."""
    global _rule_loader
    if _rule_loader is None:
        from backend.core.config import get_settings
        settings = get_settings()
        _rule_loader = RuleLoader(settings.rules_dir)
        _rule_loader.load_directory()
    return _rule_loader


def get_analytics_service() -> RuleAnalyticsService:
    """Get or create the analytics service."""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = RuleAnalyticsService(rule_loader=get_rule_loader())
    return _analytics_service


# =============================================================================
# Rule Comparison Endpoints
# =============================================================================

@router.post("/rules/compare", response_model=ComparisonResult)
def compare_rules(request: CompareRulesRequest) -> ComparisonResult:
    """Compare two rules across all embedding types.

    Returns similarity scores for semantic, structural, entity, and legal
    dimensions, along with shared entities and conflict indicators.
    """
    service = get_analytics_service()
    loader = get_rule_loader()

    # Validate rules exist
    rule1 = loader.get_rule(request.rule1_id)
    rule2 = loader.get_rule(request.rule2_id)

    if rule1 is None:
        raise HTTPException(status_code=404, detail=f"Rule not found: {request.rule1_id}")
    if rule2 is None:
        raise HTTPException(status_code=404, detail=f"Rule not found: {request.rule2_id}")

    return service.compare_rules(
        rule1_id=request.rule1_id,
        rule2_id=request.rule2_id,
        weights=request.weights,
    )


# =============================================================================
# Clustering Endpoints
# =============================================================================

@router.get("/rule-clusters", response_model=ClusterAnalysis)
def get_rule_clusters(
    embedding_type: EmbeddingTypeEnum = Query(default=EmbeddingTypeEnum.SEMANTIC),
    n_clusters: int | None = Query(default=None, description="Auto-detect if None"),
    algorithm: ClusterAlgorithm = Query(default=ClusterAlgorithm.KMEANS),
) -> ClusterAnalysis:
    """Identify clusters of similar rules using K-means or DBSCAN.

    Returns cluster assignments with centroid rules and cohesion scores.
    """
    service = get_analytics_service()

    return service.cluster_rules(
        embedding_type=embedding_type.value,
        n_clusters=n_clusters,
        algorithm=algorithm.value,
    )


@router.post("/rule-clusters", response_model=ClusterAnalysis)
def cluster_rules_post(request: ClusterRequest) -> ClusterAnalysis:
    """Identify clusters of similar rules (POST variant with full options).

    Allows specifying rule subset and additional parameters.
    """
    service = get_analytics_service()

    return service.cluster_rules(
        embedding_type=request.embedding_type.value,
        n_clusters=request.n_clusters,
        algorithm=request.algorithm.value,
        rule_ids=request.rule_ids,
    )


# =============================================================================
# Conflict Detection Endpoints
# =============================================================================

@router.post("/find-conflicts", response_model=ConflictReport)
def find_conflicts(request: ConflictSearchRequest) -> ConflictReport:
    """Detect potentially conflicting rules.

    Analyzes rules for semantic, structural, temporal, and jurisdiction
    conflicts based on embedding similarity and outcome divergence.
    """
    service = get_analytics_service()

    return service.find_conflicts(
        rule_ids=request.rule_ids,
        conflict_types=[ct.value for ct in request.conflict_types],
        threshold=request.threshold,
    )


@router.get("/conflicts", response_model=ConflictReport)
def get_conflicts(
    threshold: float = Query(default=0.7, ge=0.0, le=1.0),
) -> ConflictReport:
    """Get all detected conflicts (GET variant for simple queries)."""
    service = get_analytics_service()

    return service.find_conflicts(
        rule_ids=None,
        conflict_types=["semantic", "structural", "jurisdiction"],
        threshold=threshold,
    )


# =============================================================================
# Similarity Search Endpoints
# =============================================================================

@router.get("/rules/{rule_id}/similar", response_model=SimilarRulesResponse)
def get_similar_rules(
    rule_id: str,
    embedding_type: str = Query(default="all", description="all | semantic | structural | entity | legal"),
    top_k: int = Query(default=10, ge=1, le=100),
    min_score: float = Query(default=0.5, ge=0.0, le=1.0),
    include_explanation: bool = Query(default=True),
) -> SimilarRulesResponse:
    """Get most similar rules with explanations.

    Returns rules ranked by similarity with breakdown by embedding type
    and natural language explanations of why they're similar.
    """
    service = get_analytics_service()
    loader = get_rule_loader()

    # Validate rule exists
    rule = loader.get_rule(rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")

    return service.find_similar(
        rule_id=rule_id,
        embedding_type=embedding_type,
        top_k=top_k,
        min_score=min_score,
        include_explanation=include_explanation,
    )


@router.post("/rules/similar", response_model=SimilarRulesResponse)
def find_similar_rules_post(request: SimilarRulesRequest) -> SimilarRulesResponse:
    """Find similar rules (POST variant with full options)."""
    service = get_analytics_service()
    loader = get_rule_loader()

    # Validate rule exists
    rule = loader.get_rule(request.rule_id)
    if rule is None:
        raise HTTPException(status_code=404, detail=f"Rule not found: {request.rule_id}")

    return service.find_similar(
        rule_id=request.rule_id,
        embedding_type=request.embedding_type.value if request.embedding_type else "all",
        top_k=request.top_k,
        min_score=request.min_score,
        include_explanation=request.include_explanation,
    )


# =============================================================================
# Coverage Analysis Endpoints
# =============================================================================

@router.get("/coverage", response_model=CoverageReport)
def get_coverage() -> CoverageReport:
    """Show which legal sources are well-covered by rules.

    Returns coverage percentages per framework and identifies gaps
    where legal requirements lack corresponding rules.
    """
    service = get_analytics_service()
    return service.analyze_coverage()


# =============================================================================
# UMAP Visualization Endpoints
# =============================================================================

@router.get("/umap-projection", response_model=UMAPProjectionResponse)
def get_umap_projection(
    embedding_type: EmbeddingTypeEnum = Query(default=EmbeddingTypeEnum.SEMANTIC),
    n_components: int = Query(default=2, ge=2, le=3),
    n_neighbors: int = Query(default=15, ge=2, le=100),
    min_dist: float = Query(default=0.1, ge=0.0, le=1.0),
) -> UMAPProjectionResponse:
    """Get 2D/3D UMAP projection of rule embeddings for visualization.

    Projects high-dimensional embeddings to 2D or 3D space using UMAP
    for interactive scatter plot visualization.
    """
    service = get_analytics_service()

    return service.get_umap_projection(
        embedding_type=embedding_type.value,
        n_components=n_components,
        n_neighbors=n_neighbors,
        min_dist=min_dist,
    )


@router.post("/umap-projection", response_model=UMAPProjectionResponse)
def get_umap_projection_post(request: UMAPProjectionRequest) -> UMAPProjectionResponse:
    """Get UMAP projection (POST variant with full options)."""
    service = get_analytics_service()

    return service.get_umap_projection(
        embedding_type=request.embedding_type.value,
        n_components=request.n_components,
        n_neighbors=request.n_neighbors,
        min_dist=request.min_dist,
        rule_ids=request.rule_ids,
    )


# =============================================================================
# Summary Statistics Endpoint
# =============================================================================

@router.get("/summary")
def get_analytics_summary() -> dict[str, Any]:
    """Get summary statistics for analytics.

    Returns counts for total rules, embeddings, clusters, and conflicts.
    """
    loader = get_rule_loader()

    rules = loader.get_all_rules()

    # Get basic stats
    summary = {
        "total_rules": len(rules),
        "jurisdictions": list(set(r.jurisdiction.value for r in rules if r.jurisdiction)),
        "frameworks": list(set(r.source.document_id for r in rules if r.source)),
        "embedding_types_available": [
            "semantic", "structural", "entity", "legal"
        ],
        "clustering_algorithms_available": [
            "kmeans", "dbscan", "hierarchical"
        ],
    }

    return summary


# =============================================================================
# Graph Visualization Endpoints
# =============================================================================

def _build_rule_graph(rule) -> tuple[list[GraphNode], list[GraphLink]]:
    """Build graph nodes and links from a single rule's decision tree."""
    nodes: list[GraphNode] = []
    links: list[GraphLink] = []

    # Add rule node
    rule_node = GraphNode(
        id=rule.rule_id,
        label=rule.rule_id,
        type="rule",
        rule_id=rule.rule_id,
        metadata={
            "jurisdiction": rule.jurisdiction.value if rule.jurisdiction else None,
            "version": rule.version,
        }
    )
    nodes.append(rule_node)

    # Add decision tree nodes if present
    if rule.decision_tree:
        node_counter = [0]

        def traverse_tree(tree_node, parent_id: str | None = None):
            node_counter[0] += 1
            node_id = f"{rule.rule_id}_node_{node_counter[0]}"

            # Determine node type and label
            if hasattr(tree_node, 'condition'):
                # Branch node
                condition = tree_node.condition
                label = f"{condition.field} {condition.operator} {condition.value}"
                node_type = "condition"
            else:
                # Leaf node
                label = str(tree_node.outcome) if hasattr(tree_node, 'outcome') else "outcome"
                node_type = "outcome"

            graph_node = GraphNode(
                id=node_id,
                label=label,
                type=node_type,
                rule_id=rule.rule_id,
            )
            nodes.append(graph_node)

            if parent_id:
                links.append(GraphLink(
                    source=parent_id,
                    target=node_id,
                    type="contains",
                    weight=1.0,
                ))

            # Traverse children
            if hasattr(tree_node, 'true_branch'):
                traverse_tree(tree_node.true_branch, node_id)
            if hasattr(tree_node, 'false_branch'):
                traverse_tree(tree_node.false_branch, node_id)

        traverse_tree(rule.decision_tree, rule.rule_id)

    return nodes, links


@router.get("/graph/{rule_id}", response_model=GraphData)
def get_rule_graph(rule_id: str) -> GraphData:
    """Get graph structure for a single rule's decision tree.

    Returns nodes and links representing the rule's decision tree
    for force-directed graph visualization.
    """
    loader = get_rule_loader()
    rule = loader.get_rule(rule_id)

    if rule is None:
        raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")

    nodes, links = _build_rule_graph(rule)

    return GraphData(
        nodes=nodes,
        links=links,
        metadata={"rule_id": rule_id, "view": "single_rule"}
    )


@router.get("/graph", response_model=GraphData)
def get_all_rules_graph() -> GraphData:
    """Get graph structure for all rules overview.

    Returns nodes for each rule with links based on jurisdiction grouping.
    """
    loader = get_rule_loader()
    rules = loader.get_all_rules()

    nodes: list[GraphNode] = []
    links: list[GraphLink] = []

    # Add jurisdiction nodes
    jurisdictions = set()
    for rule in rules:
        if rule.jurisdiction:
            jurisdictions.add(rule.jurisdiction.value)

    for j in jurisdictions:
        nodes.append(GraphNode(
            id=f"jurisdiction_{j}",
            label=j,
            type="jurisdiction",
        ))

    # Add rule nodes and links to jurisdictions
    for rule in rules:
        rule_node = GraphNode(
            id=rule.rule_id,
            label=rule.rule_id,
            type="rule",
            rule_id=rule.rule_id,
            metadata={
                "jurisdiction": rule.jurisdiction.value if rule.jurisdiction else None,
                "version": rule.version,
            }
        )
        nodes.append(rule_node)

        if rule.jurisdiction:
            links.append(GraphLink(
                source=f"jurisdiction_{rule.jurisdiction.value}",
                target=rule.rule_id,
                type="contains",
                weight=1.0,
            ))

    return GraphData(
        nodes=nodes,
        links=links,
        metadata={"view": "all_rules", "total_rules": len(rules)}
    )


@router.get("/network", response_model=GraphData)
def get_network_graph(
    min_similarity: float = Query(default=0.7, ge=0.0, le=1.0),
) -> GraphData:
    """Get network graph with rules as nodes and similarity edges.

    Returns a graph where nodes are rules and edges connect rules
    with similarity above the threshold.
    """
    loader = get_rule_loader()
    service = get_analytics_service()
    rules = loader.get_all_rules()

    nodes: list[GraphNode] = []
    links: list[GraphLink] = []

    # Add rule nodes
    for rule in rules:
        rule_node = GraphNode(
            id=rule.rule_id,
            label=rule.rule_id,
            type="rule",
            rule_id=rule.rule_id,
            metadata={
                "jurisdiction": rule.jurisdiction.value if rule.jurisdiction else None,
                "version": rule.version,
            }
        )
        nodes.append(rule_node)

    # Find similar pairs and add edges
    for i, rule in enumerate(rules):
        try:
            similar = service.find_similar(
                rule_id=rule.rule_id,
                embedding_type="all",
                top_k=10,
                min_score=min_similarity,
                include_explanation=False,
            )
            for sim_rule in similar.similar_rules:
                # Avoid duplicate edges (only add if source < target alphabetically)
                if rule.rule_id < sim_rule.rule_id:
                    links.append(GraphLink(
                        source=rule.rule_id,
                        target=sim_rule.rule_id,
                        type="similar",
                        weight=sim_rule.overall_score,
                    ))
        except Exception:
            # Skip rules that fail similarity search
            continue

    return GraphData(
        nodes=nodes,
        links=links,
        metadata={
            "view": "network",
            "min_similarity": min_similarity,
            "total_rules": len(rules),
            "total_edges": len(links),
        }
    )
