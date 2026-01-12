"""Decoder Service - transforms decisions into tiered explanations."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from .schemas import (
    ExplanationTier,
    DecoderRequest,
    DecoderResponse,
    Explanation,
    ExplanationSummary,
    AuditInfo,
    Citation,
)

if TYPE_CHECKING:
    from backend.rule_service.app.services.engine import DecisionResult
    from .citations import CitationInjector
    from .templates import TemplateRegistry


class DecoderService:
    """Transforms decision results into tiered explanations."""

    def __init__(
        self,
        citation_injector: CitationInjector | None = None,
        template_registry: TemplateRegistry | None = None,
    ):
        """Initialize decoder with optional dependencies.

        Args:
            citation_injector: Service to retrieve legal citations
            template_registry: Registry of explanation templates
        """
        self._citations = citation_injector
        self._templates = template_registry

    @property
    def citations(self) -> CitationInjector:
        """Lazy-load citation injector."""
        if self._citations is None:
            from .citations import CitationInjector

            self._citations = CitationInjector()
        return self._citations

    @property
    def templates(self) -> TemplateRegistry:
        """Lazy-load template registry."""
        if self._templates is None:
            from .templates import TemplateRegistry

            self._templates = TemplateRegistry()
        return self._templates

    def explain(
        self,
        decision: DecisionResult,
        tier: ExplanationTier = ExplanationTier.INSTITUTIONAL,
        include_citations: bool = True,
    ) -> DecoderResponse:
        """Generate tiered explanation for a decision.

        Args:
            decision: The decision result to explain
            tier: Target audience tier
            include_citations: Whether to include legal citations

        Returns:
            DecoderResponse with explanation and citations
        """
        start_time = time.time()

        # Extract metadata from decision
        framework = self._extract_framework(decision)
        status = self._determine_status(decision)
        risk_level = self._assess_risk(decision)

        # Select and render template
        template = self.templates.select(
            activity_type=self._extract_activity(decision),
            framework=framework,
            outcome=self._map_outcome(status),
        )

        # Generate explanation based on tier
        explanation = self._render_explanation(decision, template, tier)

        # Retrieve citations if requested
        citations: list[Citation] = []
        if include_citations:
            citations = self.citations.get_citations(
                rule_id=decision.rule_id,
                framework=framework,
                max_citations=self._citation_limit_for_tier(tier),
            )

        processing_time = int((time.time() - start_time) * 1000)

        return DecoderResponse(
            decision_id=decision.rule_id,
            tier=tier,
            summary=ExplanationSummary(
                status=status,
                confidence=self._calculate_confidence(decision),
                primary_framework=framework,
                risk_level=risk_level,
            ),
            explanation=explanation,
            citations=citations,
            audit=AuditInfo(
                trace_id=decision.rule_id,
                rules_evaluated=1,
                processing_time_ms=processing_time,
                template_id=template.id if template else None,
            ),
        )

    def explain_by_id(
        self,
        decision_id: str,
        tier: ExplanationTier = ExplanationTier.INSTITUTIONAL,
        include_citations: bool = True,
    ) -> DecoderResponse:
        """Generate explanation by decision ID.

        This requires looking up the decision from storage.
        For now, returns a placeholder - integrate with decision storage as needed.
        """
        # TODO: Integrate with decision storage/cache
        return DecoderResponse(
            decision_id=decision_id,
            tier=tier,
            summary=ExplanationSummary(
                status="UNKNOWN",
                confidence=0.0,
                primary_framework="Unknown",
                risk_level="MEDIUM",
            ),
            explanation=Explanation(
                headline="Decision not found",
                body=f"Could not find decision with ID: {decision_id}",
                conditions=[],
                warnings=["Decision lookup not yet implemented"],
            ),
            citations=[],
            audit=AuditInfo(rules_evaluated=0),
        )

    def _extract_framework(self, decision: DecisionResult) -> str:
        """Extract regulatory framework from decision."""
        if decision.rule_metadata and decision.rule_metadata.source:
            doc_id = decision.rule_metadata.source.document_id
            if doc_id:
                # Map document IDs to framework names
                framework_map = {
                    "mica": "MiCA",
                    "fca": "FCA",
                    "sec": "SEC",
                    "mas": "MAS",
                    "finma": "FINMA",
                }
                for key, name in framework_map.items():
                    if key in doc_id.lower():
                        return name
        return "Unknown"

    def _extract_activity(self, decision: DecisionResult) -> str:
        """Extract activity type from decision."""
        # Try to infer from rule_id
        rule_id = decision.rule_id.lower()
        if "swap" in rule_id:
            return "swap"
        if "offer" in rule_id or "public_offer" in rule_id:
            return "public_offer"
        if "custody" in rule_id:
            return "custody"
        if "trading" in rule_id:
            return "trading"
        if "transfer" in rule_id:
            return "transfer"
        return "general"

    def _determine_status(self, decision: DecisionResult) -> str:
        """Determine compliance status from decision."""
        if not decision.applicable:
            return "NOT_APPLICABLE"

        outcome = (decision.decision or "").lower()
        if outcome in ("authorized", "compliant", "approved", "exempt"):
            return "APPROVED"
        if outcome in ("conditional", "requires_review", "pending"):
            return "CONDITIONAL"
        if outcome in ("not_authorized", "non_compliant", "denied", "prohibited"):
            return "DENIED"

        return "UNKNOWN"

    def _map_outcome(self, status: str) -> str:
        """Map status to template outcome category."""
        if status in ("APPROVED", "NOT_APPLICABLE"):
            return "compliant"
        if status == "CONDITIONAL":
            return "conditional"
        return "non_compliant"

    def _assess_risk(self, decision: DecisionResult) -> str:
        """Assess risk level from decision."""
        status = self._determine_status(decision)

        if status == "DENIED":
            return "HIGH"
        if status == "CONDITIONAL":
            return "MEDIUM"
        if status in ("APPROVED", "NOT_APPLICABLE"):
            return "LOW"

        # Check for warnings in trace
        if decision.trace:
            warning_count = sum(
                1 for step in decision.trace if not step.result
            )
            if warning_count > 2:
                return "MEDIUM"

        return "LOW"

    def _calculate_confidence(self, decision: DecisionResult) -> float:
        """Calculate confidence score for explanation."""
        base_confidence = 0.8

        # Adjust based on consistency metadata
        if decision.rule_metadata and decision.rule_metadata.consistency:
            summary = decision.rule_metadata.consistency.summary
            if summary and summary.confidence:
                base_confidence = min(base_confidence, summary.confidence)

        # Reduce confidence for conditional/unknown outcomes
        status = self._determine_status(decision)
        if status == "CONDITIONAL":
            base_confidence *= 0.9
        elif status == "UNKNOWN":
            base_confidence *= 0.5

        return round(base_confidence, 2)

    def _citation_limit_for_tier(self, tier: ExplanationTier) -> int:
        """Get citation limit based on tier."""
        limits = {
            ExplanationTier.RETAIL: 0,
            ExplanationTier.PROTOCOL: 3,
            ExplanationTier.INSTITUTIONAL: 5,
            ExplanationTier.REGULATOR: 10,
        }
        return limits.get(tier, 3)

    def _render_explanation(
        self,
        decision: DecisionResult,
        template,
        tier: ExplanationTier,
    ) -> Explanation:
        """Render explanation using template and tier."""
        status = self._determine_status(decision)
        framework = self._extract_framework(decision)

        # Generate tier-appropriate content
        if tier == ExplanationTier.RETAIL:
            return self._render_retail(decision, status, framework)
        elif tier == ExplanationTier.PROTOCOL:
            return self._render_protocol(decision, status, framework)
        elif tier == ExplanationTier.INSTITUTIONAL:
            return self._render_institutional(decision, status, framework)
        else:  # REGULATOR
            return self._render_regulator(decision, status, framework)

    def _render_retail(
        self, decision: DecisionResult, status: str, framework: str
    ) -> Explanation:
        """Render retail-tier explanation (plain language)."""
        if status == "APPROVED":
            headline = "This activity is allowed."
            body = (
                f"Based on {framework} regulations, this activity is compliant. "
                "No special requirements apply."
            )
        elif status == "CONDITIONAL":
            headline = "This activity may be allowed with conditions."
            body = (
                f"Under {framework} rules, this activity requires meeting "
                "certain conditions. Please review the requirements below."
            )
        elif status == "DENIED":
            headline = "This activity is not allowed."
            body = (
                f"{framework} regulations prohibit this activity in its current form. "
                "Consider restructuring or consulting a compliance advisor."
            )
        else:
            headline = "Status could not be determined."
            body = "We couldn't determine the compliance status. Please consult an expert."

        return Explanation(
            headline=headline,
            body=body,
            conditions=[o.description or o.id for o in decision.obligations if o.description],
            warnings=[decision.notes] if decision.notes else [],
        )

    def _render_protocol(
        self, decision: DecisionResult, status: str, framework: str
    ) -> Explanation:
        """Render protocol-tier explanation (technical)."""
        headline = f"Compliance Status: {status}"

        # Build technical body
        parts = [
            f"Framework: {framework}",
            f"Rule: {decision.rule_id}",
            f"Applicable: {decision.applicable}",
            f"Decision: {decision.decision or 'N/A'}",
        ]

        if decision.source:
            parts.append(f"Source: {decision.source}")

        body = " | ".join(parts)

        # Extract conditions from obligations
        conditions = []
        for ob in decision.obligations:
            cond = f"{ob.id}: {ob.description}" if ob.description else ob.id
            conditions.append(cond)

        return Explanation(
            headline=headline,
            body=body,
            conditions=conditions,
            warnings=[decision.notes] if decision.notes else [],
        )

    def _render_institutional(
        self, decision: DecisionResult, status: str, framework: str
    ) -> Explanation:
        """Render institutional-tier explanation (full report)."""
        headline = f"Compliance Status: {status}"

        # Build comprehensive body
        lines = [
            f"**Regulatory Basis:** {framework}",
            f"**Rule ID:** {decision.rule_id}",
            f"**Applicability:** {'Yes' if decision.applicable else 'No'}",
            f"**Decision:** {decision.decision or 'Pending'}",
        ]

        if decision.source:
            lines.append(f"**Source Reference:** {decision.source}")

        if decision.rule_metadata:
            meta = decision.rule_metadata
            if meta.version:
                lines.append(f"**Rule Version:** {meta.version}")
            if meta.tags:
                lines.append(f"**Tags:** {', '.join(meta.tags)}")

        body = "\n".join(lines)

        # Structured conditions
        conditions = []
        for ob in decision.obligations:
            cond_parts = [ob.id]
            if ob.description:
                cond_parts.append(ob.description)
            if ob.deadline:
                cond_parts.append(f"(Deadline: {ob.deadline})")
            conditions.append(" - ".join(cond_parts))

        # Warnings from trace failures
        warnings = []
        if decision.notes:
            warnings.append(decision.notes)
        for step in decision.trace:
            if not step.result and "warning" in step.condition.lower():
                warnings.append(f"Check failed: {step.condition}")

        return Explanation(
            headline=headline,
            body=body,
            conditions=conditions,
            warnings=warnings,
        )

    def _render_regulator(
        self, decision: DecisionResult, status: str, framework: str
    ) -> Explanation:
        """Render regulator-tier explanation (complete legal analysis)."""
        headline = f"Regulatory Decision: {status}"

        # Full legal analysis
        lines = [
            f"## Regulatory Framework",
            f"Primary Framework: {framework}",
            f"Rule Identifier: {decision.rule_id}",
            "",
            f"## Decision Details",
            f"Applicability Determination: {'Applicable' if decision.applicable else 'Not Applicable'}",
            f"Compliance Outcome: {decision.decision or 'Under Review'}",
        ]

        if decision.source:
            lines.extend([
                "",
                f"## Legal Basis",
                f"Source: {decision.source}",
            ])

        if decision.rule_metadata:
            meta = decision.rule_metadata
            lines.extend([
                "",
                f"## Rule Metadata",
                f"Version: {meta.version}",
            ])
            if meta.source:
                if meta.source.article:
                    lines.append(f"Article: {meta.source.article}")
                if meta.source.section:
                    lines.append(f"Section: {meta.source.section}")

            if meta.consistency:
                lines.extend([
                    "",
                    f"## Consistency Verification",
                    f"Status: {meta.consistency.summary.status if meta.consistency.summary else 'Unknown'}",
                ])

        # Decision trace
        if decision.trace:
            lines.extend([
                "",
                f"## Evaluation Trace",
            ])
            for i, step in enumerate(decision.trace, 1):
                result = "✓" if step.result else "✗"
                lines.append(f"{i}. [{result}] {step.node}: {step.condition}")

        body = "\n".join(lines)

        # All obligations as conditions
        conditions = []
        for ob in decision.obligations:
            parts = [f"**{ob.id}**"]
            if ob.description:
                parts.append(ob.description)
            if ob.source:
                parts.append(f"(Ref: {ob.source})")
            if ob.deadline:
                parts.append(f"[Deadline: {ob.deadline}]")
            conditions.append(" ".join(parts))

        # Collect all warnings
        warnings = []
        if decision.notes:
            warnings.append(decision.notes)

        return Explanation(
            headline=headline,
            body=body,
            conditions=conditions,
            warnings=warnings,
        )
