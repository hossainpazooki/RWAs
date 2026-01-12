"""Template Registry - manages explanation templates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .schemas import (
    ExplanationTier,
    ExplanationTemplate,
    TemplateSection,
    TemplateVariable,
    CitationSlot,
)

if TYPE_CHECKING:
    pass


# ============================================================================
# Default Templates
# ============================================================================

DEFAULT_TEMPLATES: list[ExplanationTemplate] = [
    # MiCA Compliant Templates
    ExplanationTemplate(
        id="mica_compliant_general",
        name="MiCA Compliant - General",
        version="1.0",
        activity_types=["public_offer", "trading", "custody", "swap", "general"],
        frameworks=["MiCA"],
        outcome="compliant",
        tiers={
            ExplanationTier.RETAIL: [
                TemplateSection(
                    type="headline",
                    template="This activity is allowed under EU rules.",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="Your {{activity_type}} activity complies with MiCA regulations. No additional actions required.",
                    llm_enhance=True,
                ),
            ],
            ExplanationTier.PROTOCOL: [
                TemplateSection(
                    type="headline",
                    template="Compliance Status: APPROVED",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="Activity: {{activity_type}} | Framework: MiCA | Status: Compliant | Rule: {{rule_id}}",
                    llm_enhance=False,
                ),
            ],
            ExplanationTier.INSTITUTIONAL: [
                TemplateSection(
                    type="headline",
                    template="Compliance Status: APPROVED",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="**Regulatory Basis:** MiCA (EU) 2023/1114\n**Activity:** {{activity_type}}\n**Compliance:** Verified\n**Risk Rating:** LOW",
                    llm_enhance=False,
                ),
            ],
            ExplanationTier.REGULATOR: [
                TemplateSection(
                    type="headline",
                    template="Regulatory Decision: APPROVED",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="## Compliance Assessment\n\nActivity {{activity_type}} evaluated under MiCA framework.\nRule {{rule_id}} applied.\nOutcome: Compliant.\n\n## Legal Basis\n{{primary_citation}}",
                    llm_enhance=False,
                ),
            ],
        },
        variables=[
            TemplateVariable(name="activity_type", source="decision", required=True),
            TemplateVariable(name="rule_id", source="decision", required=True),
            TemplateVariable(name="primary_citation", source="rag", required=False),
        ],
        citation_slots=[
            CitationSlot(slot_id="primary_citation", framework="MiCA", article_pattern="Art. {{article}}"),
        ],
    ),
    # MiCA Conditional Templates
    ExplanationTemplate(
        id="mica_conditional_general",
        name="MiCA Conditional - General",
        version="1.0",
        activity_types=["public_offer", "trading", "custody", "swap", "general"],
        frameworks=["MiCA"],
        outcome="conditional",
        tiers={
            ExplanationTier.RETAIL: [
                TemplateSection(
                    type="headline",
                    template="This activity may be allowed with conditions.",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="Your {{activity_type}} activity requires meeting certain conditions under MiCA rules. Review the requirements below.",
                    llm_enhance=True,
                ),
            ],
            ExplanationTier.PROTOCOL: [
                TemplateSection(
                    type="headline",
                    template="Compliance Status: CONDITIONAL",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="Activity: {{activity_type}} | Framework: MiCA | Status: Conditional | Conditions: See below",
                    llm_enhance=False,
                ),
            ],
            ExplanationTier.INSTITUTIONAL: [
                TemplateSection(
                    type="headline",
                    template="Compliance Status: CONDITIONAL",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="**Regulatory Basis:** MiCA (EU) 2023/1114\n**Activity:** {{activity_type}}\n**Compliance:** Conditional\n**Risk Rating:** MEDIUM\n\n**Action Required:** Review and satisfy conditions listed below.",
                    llm_enhance=False,
                ),
            ],
            ExplanationTier.REGULATOR: [
                TemplateSection(
                    type="headline",
                    template="Regulatory Decision: CONDITIONAL APPROVAL",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="## Conditional Assessment\n\nActivity {{activity_type}} evaluated under MiCA framework.\nConditional approval granted pending satisfaction of requirements.\n\n## Outstanding Conditions\n{{conditions}}",
                    llm_enhance=False,
                ),
            ],
        },
        variables=[
            TemplateVariable(name="activity_type", source="decision", required=True),
            TemplateVariable(name="conditions", source="decision", required=False),
        ],
        citation_slots=[],
    ),
    # MiCA Non-Compliant Templates
    ExplanationTemplate(
        id="mica_non_compliant_general",
        name="MiCA Non-Compliant - General",
        version="1.0",
        activity_types=["public_offer", "trading", "custody", "swap", "general"],
        frameworks=["MiCA"],
        outcome="non_compliant",
        tiers={
            ExplanationTier.RETAIL: [
                TemplateSection(
                    type="headline",
                    template="This activity is not allowed.",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="Your {{activity_type}} activity does not comply with MiCA regulations. Consider restructuring or consulting a compliance advisor.",
                    llm_enhance=True,
                ),
            ],
            ExplanationTier.PROTOCOL: [
                TemplateSection(
                    type="headline",
                    template="Compliance Status: DENIED",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="Activity: {{activity_type}} | Framework: MiCA | Status: Non-Compliant | Action: Restructure required",
                    llm_enhance=False,
                ),
            ],
            ExplanationTier.INSTITUTIONAL: [
                TemplateSection(
                    type="headline",
                    template="Compliance Status: DENIED",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="**Regulatory Basis:** MiCA (EU) 2023/1114\n**Activity:** {{activity_type}}\n**Compliance:** Non-Compliant\n**Risk Rating:** HIGH\n\n**Recommendation:** Do not proceed. Consult compliance team.",
                    llm_enhance=False,
                ),
            ],
            ExplanationTier.REGULATOR: [
                TemplateSection(
                    type="headline",
                    template="Regulatory Decision: DENIED",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="## Non-Compliance Assessment\n\nActivity {{activity_type}} evaluated under MiCA framework.\nDecision: Non-compliant.\n\n## Violations\n{{violations}}\n\n## Required Actions\nCease activity or restructure to achieve compliance.",
                    llm_enhance=False,
                ),
            ],
        },
        variables=[
            TemplateVariable(name="activity_type", source="decision", required=True),
            TemplateVariable(name="violations", source="decision", required=False),
        ],
        citation_slots=[],
    ),
    # FCA Templates
    ExplanationTemplate(
        id="fca_compliant_general",
        name="FCA Compliant - General",
        version="1.0",
        activity_types=["public_offer", "trading", "custody", "promotion", "general"],
        frameworks=["FCA"],
        outcome="compliant",
        tiers={
            ExplanationTier.RETAIL: [
                TemplateSection(
                    type="headline",
                    template="This activity is allowed under UK rules.",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="Your {{activity_type}} activity complies with FCA regulations.",
                    llm_enhance=True,
                ),
            ],
            ExplanationTier.INSTITUTIONAL: [
                TemplateSection(
                    type="headline",
                    template="Compliance Status: APPROVED",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="**Regulatory Basis:** FCA Handbook\n**Activity:** {{activity_type}}\n**Compliance:** Verified",
                    llm_enhance=False,
                ),
            ],
        },
        variables=[
            TemplateVariable(name="activity_type", source="decision", required=True),
        ],
        citation_slots=[],
    ),
    # Generic Fallback Template
    ExplanationTemplate(
        id="generic_fallback",
        name="Generic Fallback",
        version="1.0",
        activity_types=["general"],
        frameworks=["Unknown"],
        outcome="compliant",
        tiers={
            ExplanationTier.RETAIL: [
                TemplateSection(
                    type="headline",
                    template="Compliance assessment complete.",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="Please review the detailed assessment below.",
                    llm_enhance=False,
                ),
            ],
            ExplanationTier.INSTITUTIONAL: [
                TemplateSection(
                    type="headline",
                    template="Compliance Assessment",
                    llm_enhance=False,
                ),
                TemplateSection(
                    type="body",
                    template="Assessment completed. Review details and citations for full analysis.",
                    llm_enhance=False,
                ),
            ],
        },
        variables=[],
        citation_slots=[],
    ),
]


class TemplateRegistry:
    """Registry for explanation templates."""

    def __init__(self):
        """Initialize with default templates."""
        self._templates: dict[str, ExplanationTemplate] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Load default templates."""
        for template in DEFAULT_TEMPLATES:
            self.register(template)

    def register(self, template: ExplanationTemplate) -> None:
        """Register a template.

        Args:
            template: Template to register
        """
        self._templates[template.id] = template

    def get(self, template_id: str) -> ExplanationTemplate | None:
        """Get template by ID.

        Args:
            template_id: Template identifier

        Returns:
            Template if found, None otherwise
        """
        return self._templates.get(template_id)

    def list_templates(self) -> list[ExplanationTemplate]:
        """List all registered templates."""
        return list(self._templates.values())

    def select(
        self,
        activity_type: str,
        framework: str,
        outcome: str,
    ) -> ExplanationTemplate | None:
        """Select best matching template.

        Args:
            activity_type: Type of activity (e.g., "swap", "custody")
            framework: Regulatory framework (e.g., "MiCA")
            outcome: Decision outcome (e.g., "compliant")

        Returns:
            Best matching template or None
        """
        candidates: list[tuple[int, ExplanationTemplate]] = []

        for template in self._templates.values():
            score = self._calculate_match_score(
                template, activity_type, framework, outcome
            )
            if score > 0:
                candidates.append((score, template))

        if not candidates:
            # Return generic fallback
            return self._templates.get("generic_fallback")

        # Sort by score descending
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def _calculate_match_score(
        self,
        template: ExplanationTemplate,
        activity_type: str,
        framework: str,
        outcome: str,
    ) -> int:
        """Calculate how well a template matches criteria.

        Returns:
            Score (higher is better match)
        """
        score = 0

        # Check outcome match (required)
        if template.outcome != outcome:
            return 0

        # Framework match
        if framework in template.frameworks:
            score += 10
        elif "Unknown" in template.frameworks:
            score += 1

        # Activity type match
        if activity_type in template.activity_types:
            score += 5
        elif "general" in template.activity_types:
            score += 1

        return score

    def render_template(
        self,
        template: ExplanationTemplate,
        tier: ExplanationTier,
        variables: dict[str, str],
    ) -> dict[str, str]:
        """Render a template with variables.

        Args:
            template: Template to render
            tier: Target tier
            variables: Variable values

        Returns:
            Dict with rendered sections
        """
        sections = template.tiers.get(tier, [])
        result = {}

        for section in sections:
            rendered = section.template
            for var_name, var_value in variables.items():
                placeholder = "{{" + var_name + "}}"
                rendered = rendered.replace(placeholder, str(var_value))
            result[section.type] = rendered

        return result
