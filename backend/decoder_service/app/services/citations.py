"""Citation Injector - retrieves regulatory citations using RAG."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .schemas import Citation

if TYPE_CHECKING:
    from backend.rag_service.app.services.retriever import Retriever


# Framework metadata for citation enrichment
FRAMEWORK_METADATA = {
    "MiCA": {
        "full_name": "Markets in Crypto-Assets Regulation",
        "regulation_id": "Regulation (EU) 2023/1114",
        "url_base": "https://eur-lex.europa.eu/eli/reg/2023/1114",
        "effective_date": "2024-06-30",
    },
    "FCA": {
        "full_name": "Financial Conduct Authority Cryptoasset Rules",
        "regulation_id": "FCA Handbook",
        "url_base": "https://www.handbook.fca.org.uk",
        "effective_date": "2024-01-01",
    },
    "SEC": {
        "full_name": "Securities and Exchange Commission",
        "regulation_id": "Securities Act of 1933 / Exchange Act of 1934",
        "url_base": "https://www.sec.gov/rules",
        "effective_date": None,
    },
    "MAS": {
        "full_name": "Monetary Authority of Singapore",
        "regulation_id": "Payment Services Act 2019",
        "url_base": "https://www.mas.gov.sg",
        "effective_date": "2020-01-28",
    },
    "FINMA": {
        "full_name": "Swiss Financial Market Supervisory Authority",
        "regulation_id": "DLT Act",
        "url_base": "https://www.finma.ch",
        "effective_date": "2021-08-01",
    },
}

# Common article patterns for citation extraction
ARTICLE_PATTERNS = {
    "MiCA": {
        "authorization": ["Art. 16", "Art. 36", "Art. 59"],
        "stablecoin": ["Art. 48", "Art. 49", "Art. 50"],
        "exemptions": ["Art. 76", "Art. 77"],
        "definitions": ["Art. 3"],
        "casp": ["Art. 59", "Art. 60", "Art. 61"],
    },
    "FCA": {
        "crypto_promotion": ["COBS 4", "PS 23/6"],
        "custody": ["CASS"],
        "aml": ["MLR 2017"],
    },
}


class CitationInjector:
    """Retrieves and enriches regulatory citations."""

    def __init__(self, retriever: Retriever | None = None):
        """Initialize with optional RAG retriever.

        Args:
            retriever: RAG service for semantic citation retrieval
        """
        self._retriever = retriever

    @property
    def retriever(self) -> Retriever | None:
        """Lazy-load RAG retriever."""
        if self._retriever is None:
            try:
                from backend.rag_service.app.services.retriever import Retriever

                self._retriever = Retriever()
            except ImportError:
                pass
        return self._retriever

    def get_citations(
        self,
        rule_id: str,
        framework: str,
        activity_type: str | None = None,
        max_citations: int = 5,
    ) -> list[Citation]:
        """Retrieve relevant citations for a rule.

        Args:
            rule_id: The rule identifier
            framework: Regulatory framework (e.g., "MiCA")
            activity_type: Optional activity type for filtering
            max_citations: Maximum number of citations to return

        Returns:
            List of Citation objects
        """
        citations: list[Citation] = []

        # Try RAG-based retrieval first
        if self.retriever:
            rag_citations = self._retrieve_from_rag(
                rule_id, framework, activity_type, max_citations
            )
            citations.extend(rag_citations)

        # Fall back to pattern-based citations
        if len(citations) < max_citations:
            pattern_citations = self._get_pattern_citations(
                rule_id, framework, activity_type, max_citations - len(citations)
            )
            citations.extend(pattern_citations)

        # Enrich with metadata
        citations = [self._enrich_citation(c) for c in citations]

        return citations[:max_citations]

    def get_citation_by_reference(
        self,
        framework: str,
        reference: str,
    ) -> Citation | None:
        """Get a specific citation by reference.

        Args:
            framework: Regulatory framework
            reference: Article/section reference (e.g., "Art. 3(1)(5)")

        Returns:
            Citation if found, None otherwise
        """
        meta = FRAMEWORK_METADATA.get(framework, {})

        citation = Citation(
            framework=framework,
            reference=reference,
            full_reference=f"{meta.get('regulation_id', framework)}, {reference}",
            text=f"Reference to {reference}",
            url=meta.get("url_base"),
            effective_date=meta.get("effective_date"),
            relevance="supporting",
        )

        return self._enrich_citation(citation)

    def _retrieve_from_rag(
        self,
        rule_id: str,
        framework: str,
        activity_type: str | None,
        max_results: int,
    ) -> list[Citation]:
        """Retrieve citations using RAG service."""
        if not self.retriever:
            return []

        citations = []

        try:
            # Build search query
            query_parts = [framework, rule_id]
            if activity_type:
                query_parts.append(activity_type)
            query = " ".join(query_parts)

            # Search using BM25
            results = self.retriever.search(query, top_k=max_results)

            for result in results:
                # Extract citation from RAG result
                citation = Citation(
                    framework=framework,
                    reference=result.get("reference", ""),
                    full_reference=result.get("full_reference", ""),
                    text=result.get("text", result.get("content", "")),
                    url=result.get("url"),
                    relevance_score=result.get("score", 0.0),
                    relevance=self._score_to_relevance(result.get("score", 0.0)),
                )
                citations.append(citation)

        except Exception:
            # RAG retrieval failed, will fall back to patterns
            pass

        return citations

    def _get_pattern_citations(
        self,
        rule_id: str,
        framework: str,
        activity_type: str | None,
        max_results: int,
    ) -> list[Citation]:
        """Get citations based on known patterns."""
        citations = []
        patterns = ARTICLE_PATTERNS.get(framework, {})

        # Determine relevant categories from rule_id
        categories = self._extract_categories(rule_id, activity_type)

        for category in categories:
            if category in patterns:
                for ref in patterns[category]:
                    if len(citations) >= max_results:
                        break

                    meta = FRAMEWORK_METADATA.get(framework, {})
                    citation = Citation(
                        framework=framework,
                        reference=ref,
                        full_reference=f"{meta.get('regulation_id', framework)}, {ref}",
                        text=f"{category.replace('_', ' ').title()} provision",
                        url=meta.get("url_base"),
                        effective_date=meta.get("effective_date"),
                        relevance="supporting",
                    )
                    citations.append(citation)

        return citations

    def _extract_categories(
        self,
        rule_id: str,
        activity_type: str | None,
    ) -> list[str]:
        """Extract citation categories from rule ID and activity."""
        categories = []
        rule_lower = rule_id.lower()

        # Map rule patterns to categories
        category_patterns = {
            "authorization": ["auth", "license", "register"],
            "stablecoin": ["stablecoin", "emt", "art_"],
            "exemptions": ["exempt", "waiver"],
            "definitions": ["definition", "scope"],
            "casp": ["casp", "service_provider"],
            "custody": ["custody", "safekeep"],
        }

        for category, patterns in category_patterns.items():
            if any(p in rule_lower for p in patterns):
                categories.append(category)

        # Add activity-based category
        if activity_type:
            activity_map = {
                "public_offer": "authorization",
                "custody": "custody",
                "trading": "casp",
                "swap": "casp",
            }
            if activity_type in activity_map:
                cat = activity_map[activity_type]
                if cat not in categories:
                    categories.append(cat)

        # Default to definitions if nothing matched
        if not categories:
            categories.append("definitions")

        return categories

    def _enrich_citation(self, citation: Citation) -> Citation:
        """Enrich citation with framework metadata."""
        meta = FRAMEWORK_METADATA.get(citation.framework, {})

        # Update full reference if incomplete
        if not citation.full_reference or citation.full_reference == citation.reference:
            reg_id = meta.get("regulation_id", citation.framework)
            citation.full_reference = f"{reg_id}, {citation.reference}"

        # Add URL if missing
        if not citation.url:
            citation.url = meta.get("url_base")

        # Add effective date if missing
        if not citation.effective_date:
            citation.effective_date = meta.get("effective_date")

        return citation

    def _score_to_relevance(self, score: float) -> str:
        """Convert relevance score to category."""
        if score >= 0.8:
            return "primary"
        elif score >= 0.5:
            return "supporting"
        return "contextual"
