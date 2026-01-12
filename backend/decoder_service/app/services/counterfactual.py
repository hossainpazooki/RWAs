"""Counterfactual Engine - what-if analysis for compliance decisions."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from .schemas import (
    Scenario,
    ScenarioType,
    OutcomeSummary,
    DeltaAnalysis,
    CounterfactualRequest,
    CounterfactualResponse,
    CounterfactualExplanation,
    ComparisonRequest,
    ComparisonMatrix,
    MatrixInsight,
    ExplanationTier,
    Citation,
)
from .delta import DeltaAnalyzer

if TYPE_CHECKING:
    from backend.rule_service.app.services.engine import DecisionEngine, DecisionResult
    from .decoder import DecoderService


class CounterfactualEngine:
    """What-if analysis engine - child of Decoder.

    Evaluates how changes to facts, jurisdiction, or entity type
    would affect compliance outcomes.
    """

    def __init__(
        self,
        decision_engine: DecisionEngine | None = None,
        decoder_service: DecoderService | None = None,
    ):
        """Initialize with optional dependencies.

        Args:
            decision_engine: Engine to re-evaluate decisions
            decoder_service: Parent decoder for explanations
        """
        self._decision_engine = decision_engine
        self._decoder = decoder_service
        self._delta_analyzer = DeltaAnalyzer()

    @property
    def decision_engine(self) -> DecisionEngine:
        """Lazy-load decision engine."""
        if self._decision_engine is None:
            from backend.rule_service.app.services.engine import DecisionEngine

            self._decision_engine = DecisionEngine()
        return self._decision_engine

    @property
    def decoder(self) -> DecoderService:
        """Lazy-load decoder service."""
        if self._decoder is None:
            from .decoder import DecoderService

            self._decoder = DecoderService()
        return self._decoder

    def analyze(
        self,
        baseline_decision: DecisionResult,
        scenario: Scenario,
        include_explanation: bool = True,
        explanation_tier: ExplanationTier = ExplanationTier.INSTITUTIONAL,
    ) -> CounterfactualResponse:
        """Analyze a single what-if scenario.

        Args:
            baseline_decision: The original decision result
            scenario: The counterfactual scenario to apply
            include_explanation: Whether to include narrative explanation
            explanation_tier: Tier for explanation (if included)

        Returns:
            CounterfactualResponse with baseline, counterfactual, and delta
        """
        # Create baseline outcome summary
        baseline_outcome = self._decision_to_outcome(baseline_decision)

        # Apply scenario and get counterfactual outcome
        counterfactual_outcome = self._evaluate_scenario(
            baseline_decision, scenario
        )

        # Compute delta
        delta = self._delta_analyzer.compare(baseline_outcome, counterfactual_outcome)

        # Generate explanation if requested
        explanation = None
        if include_explanation:
            explanation = self._generate_explanation(
                baseline_outcome, counterfactual_outcome, delta, scenario
            )

        # Get relevant citations for the counterfactual framework
        citations: list[Citation] = []
        if counterfactual_outcome.framework != baseline_outcome.framework:
            citations = self.decoder.citations.get_citations(
                rule_id=baseline_decision.rule_id,
                framework=counterfactual_outcome.framework,
                max_citations=3,
            )

        return CounterfactualResponse(
            baseline_decision_id=baseline_decision.rule_id,
            scenario_applied=scenario,
            baseline_outcome=baseline_outcome,
            counterfactual_outcome=counterfactual_outcome,
            delta=delta,
            explanation=explanation,
            citations=citations,
        )

    def analyze_by_id(
        self,
        request: CounterfactualRequest,
    ) -> CounterfactualResponse:
        """Analyze counterfactual by decision ID.

        This requires looking up the baseline decision from storage.
        """
        # TODO: Integrate with decision storage/cache
        # For now, return a placeholder response
        return CounterfactualResponse(
            baseline_decision_id=request.baseline_decision_id,
            scenario_applied=request.scenario,
            baseline_outcome=OutcomeSummary(
                status="UNKNOWN",
                framework="Unknown",
                risk_level="MEDIUM",
            ),
            counterfactual_outcome=OutcomeSummary(
                status="UNKNOWN",
                framework="Unknown",
                risk_level="MEDIUM",
            ),
            delta=DeltaAnalysis(),
            explanation=CounterfactualExplanation(
                summary="Could not find baseline decision",
                key_differences=[],
            ),
        )

    def compare(
        self,
        baseline_decision: DecisionResult,
        scenarios: list[Scenario],
    ) -> ComparisonMatrix:
        """Compare multiple scenarios against baseline.

        Args:
            baseline_decision: Original decision
            scenarios: List of scenarios to evaluate

        Returns:
            ComparisonMatrix with all results and insights
        """
        baseline_outcome = self._decision_to_outcome(baseline_decision)
        results: list[CounterfactualResponse] = []

        # Evaluate each scenario
        for scenario in scenarios:
            result = self.analyze(
                baseline_decision,
                scenario,
                include_explanation=False,  # Save processing for matrix
            )
            results.append(result)

        # Build comparison matrix
        matrix = self._build_matrix(baseline_outcome, results)

        # Generate insights
        insights = self._generate_insights(baseline_outcome, results)

        return ComparisonMatrix(
            baseline=baseline_outcome,
            scenarios=scenarios,
            results=results,
            matrix=matrix,
            insights=insights,
        )

    def compare_by_id(
        self,
        request: ComparisonRequest,
    ) -> ComparisonMatrix:
        """Compare scenarios by baseline decision ID."""
        # TODO: Integrate with decision storage/cache
        return ComparisonMatrix(
            baseline=OutcomeSummary(
                status="UNKNOWN",
                framework="Unknown",
            ),
            scenarios=request.scenarios,
            results=[],
            matrix={},
            insights=[
                MatrixInsight(
                    type="warning",
                    text="Could not find baseline decision",
                )
            ],
        )

    def _decision_to_outcome(self, decision: DecisionResult) -> OutcomeSummary:
        """Convert DecisionResult to OutcomeSummary."""
        # Determine status
        outcome = (decision.decision or "").lower()
        if outcome in ("authorized", "compliant", "approved", "exempt"):
            status = "APPROVED"
        elif outcome in ("conditional", "requires_review", "pending"):
            status = "CONDITIONAL"
        elif outcome in ("not_authorized", "non_compliant", "denied", "prohibited"):
            status = "DENIED"
        else:
            status = "UNKNOWN"

        # Extract framework
        framework = "Unknown"
        if decision.rule_metadata and decision.rule_metadata.source:
            doc_id = decision.rule_metadata.source.document_id
            if doc_id:
                framework_map = {
                    "mica": "MiCA",
                    "fca": "FCA",
                    "sec": "SEC",
                    "mas": "MAS",
                    "finma": "FINMA",
                }
                for key, name in framework_map.items():
                    if key in doc_id.lower():
                        framework = name
                        break

        # Determine risk level
        if status == "DENIED":
            risk_level = "HIGH"
        elif status == "CONDITIONAL":
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Extract conditions from obligations
        conditions = [
            o.description or o.id
            for o in decision.obligations
            if o.description or o.id
        ]

        return OutcomeSummary(
            status=status,
            framework=framework,
            risk_level=risk_level,
            conditions=conditions,
        )

    def _evaluate_scenario(
        self,
        baseline_decision: DecisionResult,
        scenario: Scenario,
    ) -> OutcomeSummary:
        """Evaluate a counterfactual scenario.

        Args:
            baseline_decision: Original decision
            scenario: Scenario to apply

        Returns:
            OutcomeSummary for the counterfactual
        """
        # Apply scenario modifications based on type
        if scenario.type == ScenarioType.JURISDICTION_CHANGE:
            return self._apply_jurisdiction_change(baseline_decision, scenario)
        elif scenario.type == ScenarioType.ENTITY_CHANGE:
            return self._apply_entity_change(baseline_decision, scenario)
        elif scenario.type == ScenarioType.THRESHOLD:
            return self._apply_threshold_change(baseline_decision, scenario)
        elif scenario.type == ScenarioType.TEMPORAL:
            return self._apply_temporal_change(baseline_decision, scenario)
        elif scenario.type == ScenarioType.ACTIVITY_RESTRUCTURE:
            return self._apply_activity_restructure(baseline_decision, scenario)
        elif scenario.type == ScenarioType.PROTOCOL_CHANGE:
            return self._apply_protocol_change(baseline_decision, scenario)
        elif scenario.type == ScenarioType.REGULATORY_CHANGE:
            return self._apply_regulatory_change(baseline_decision, scenario)
        else:
            # Unknown scenario type, return baseline
            return self._decision_to_outcome(baseline_decision)

    def _apply_jurisdiction_change(
        self,
        baseline_decision: DecisionResult,
        scenario: Scenario,
    ) -> OutcomeSummary:
        """Apply jurisdiction change scenario."""
        params = scenario.parameters
        new_jurisdiction = params.get("to_jurisdiction", "EU")

        # Map jurisdiction to framework
        jurisdiction_frameworks = {
            "EU": "MiCA",
            "UK": "FCA",
            "US": "SEC",
            "SG": "MAS",
            "CH": "FINMA",
        }
        new_framework = jurisdiction_frameworks.get(new_jurisdiction, "Unknown")

        baseline_outcome = self._decision_to_outcome(baseline_decision)

        # Simulate jurisdiction change effects
        # Different frameworks have different requirements
        if new_framework == baseline_outcome.framework:
            return baseline_outcome

        # Framework-specific logic
        if new_framework == "MiCA":
            # MiCA generally more permissive for licensed entities
            return OutcomeSummary(
                status="CONDITIONAL",
                framework="MiCA",
                risk_level="MEDIUM",
                conditions=["MiCA authorization required", "Whitepaper publication"],
            )
        elif new_framework == "FCA":
            # FCA stricter on promotions
            return OutcomeSummary(
                status="CONDITIONAL",
                framework="FCA",
                risk_level="MEDIUM",
                conditions=["FCA registration required", "Promotion restrictions apply"],
            )
        elif new_framework == "SEC":
            # SEC strictest - securities law applies
            return OutcomeSummary(
                status="CONDITIONAL",
                framework="SEC",
                risk_level="HIGH",
                conditions=["Securities registration required", "Accredited investor only"],
            )
        else:
            return OutcomeSummary(
                status="CONDITIONAL",
                framework=new_framework,
                risk_level="MEDIUM",
                conditions=[f"{new_framework} compliance review required"],
            )

    def _apply_entity_change(
        self,
        baseline_decision: DecisionResult,
        scenario: Scenario,
    ) -> OutcomeSummary:
        """Apply entity type change scenario."""
        params = scenario.parameters
        new_entity_type = params.get("to_entity_type", "corporate")

        baseline_outcome = self._decision_to_outcome(baseline_decision)

        # Entity type affects compliance requirements
        if new_entity_type == "retail":
            # Retail investors face more restrictions
            return OutcomeSummary(
                status="CONDITIONAL" if baseline_outcome.status == "APPROVED" else baseline_outcome.status,
                framework=baseline_outcome.framework,
                risk_level="MEDIUM" if baseline_outcome.risk_level == "LOW" else baseline_outcome.risk_level,
                conditions=baseline_outcome.conditions + ["Retail investor protections apply"],
            )
        elif new_entity_type == "institutional":
            # Institutional often have exemptions
            return OutcomeSummary(
                status="APPROVED" if baseline_outcome.status == "CONDITIONAL" else baseline_outcome.status,
                framework=baseline_outcome.framework,
                risk_level="LOW" if baseline_outcome.risk_level == "MEDIUM" else baseline_outcome.risk_level,
                conditions=[c for c in baseline_outcome.conditions if "retail" not in c.lower()],
            )
        else:
            return baseline_outcome

    def _apply_threshold_change(
        self,
        baseline_decision: DecisionResult,
        scenario: Scenario,
    ) -> OutcomeSummary:
        """Apply threshold change scenario."""
        params = scenario.parameters
        threshold_type = params.get("threshold_type", "amount")
        new_value = params.get("new_value", 0)

        baseline_outcome = self._decision_to_outcome(baseline_decision)

        # Threshold changes can trigger different regulatory regimes
        if threshold_type == "amount" and new_value > 5_000_000:
            # Large amounts trigger additional scrutiny
            return OutcomeSummary(
                status="CONDITIONAL",
                framework=baseline_outcome.framework,
                risk_level="HIGH",
                conditions=baseline_outcome.conditions + ["Large value transaction - enhanced due diligence"],
            )
        elif threshold_type == "holders" and new_value > 150:
            # Many holders triggers public offer rules
            return OutcomeSummary(
                status="CONDITIONAL",
                framework=baseline_outcome.framework,
                risk_level="MEDIUM",
                conditions=baseline_outcome.conditions + ["Public offer threshold exceeded"],
            )
        else:
            return baseline_outcome

    def _apply_temporal_change(
        self,
        baseline_decision: DecisionResult,
        scenario: Scenario,
    ) -> OutcomeSummary:
        """Apply temporal change scenario."""
        params = scenario.parameters
        new_date = params.get("effective_date", "2024-07-01")

        baseline_outcome = self._decision_to_outcome(baseline_decision)

        # Simulate temporal effects (e.g., MiCA phases)
        # MiCA full application: June 30, 2024
        if new_date >= "2024-06-30" and baseline_outcome.framework == "MiCA":
            return OutcomeSummary(
                status=baseline_outcome.status,
                framework="MiCA",
                risk_level=baseline_outcome.risk_level,
                conditions=baseline_outcome.conditions + ["Full MiCA regime now applies"],
            )

        return baseline_outcome

    def _apply_activity_restructure(
        self,
        baseline_decision: DecisionResult,
        scenario: Scenario,
    ) -> OutcomeSummary:
        """Apply activity restructure scenario."""
        params = scenario.parameters
        new_activity = params.get("new_activity", "custody")

        baseline_outcome = self._decision_to_outcome(baseline_decision)

        # Different activities have different requirements
        activity_requirements = {
            "custody": ["Safekeeping requirements", "Segregation of assets"],
            "trading": ["Trading venue authorization", "Best execution"],
            "public_offer": ["Whitepaper publication", "Investor disclosures"],
            "swap": ["Derivative regulations", "Margin requirements"],
        }

        new_conditions = activity_requirements.get(new_activity, [])

        return OutcomeSummary(
            status="CONDITIONAL",
            framework=baseline_outcome.framework,
            risk_level="MEDIUM",
            conditions=new_conditions,
        )

    def _apply_protocol_change(
        self,
        baseline_decision: DecisionResult,
        scenario: Scenario,
    ) -> OutcomeSummary:
        """Apply protocol/technology change scenario."""
        params = scenario.parameters
        new_protocol = params.get("protocol", "ethereum")

        baseline_outcome = self._decision_to_outcome(baseline_decision)

        # Protocol changes might affect regulatory classification
        if new_protocol in ("bitcoin", "ethereum"):
            # Well-established protocols
            return baseline_outcome
        else:
            # Novel protocols may face additional scrutiny
            return OutcomeSummary(
                status="CONDITIONAL",
                framework=baseline_outcome.framework,
                risk_level="MEDIUM",
                conditions=baseline_outcome.conditions + ["Novel protocol - additional review required"],
            )

    def _apply_regulatory_change(
        self,
        baseline_decision: DecisionResult,
        scenario: Scenario,
    ) -> OutcomeSummary:
        """Apply regulatory change scenario."""
        params = scenario.parameters
        regulation_change = params.get("change_type", "amendment")

        baseline_outcome = self._decision_to_outcome(baseline_decision)

        if regulation_change == "stricter":
            # Regulations becoming stricter
            return OutcomeSummary(
                status="CONDITIONAL" if baseline_outcome.status == "APPROVED" else "DENIED",
                framework=baseline_outcome.framework,
                risk_level="HIGH",
                conditions=baseline_outcome.conditions + ["New regulatory requirements"],
            )
        elif regulation_change == "relaxed":
            # Regulations becoming more permissive
            return OutcomeSummary(
                status="APPROVED" if baseline_outcome.status == "CONDITIONAL" else baseline_outcome.status,
                framework=baseline_outcome.framework,
                risk_level="LOW",
                conditions=[c for c in baseline_outcome.conditions if "required" not in c.lower()],
            )
        else:
            return baseline_outcome

    def _generate_explanation(
        self,
        baseline: OutcomeSummary,
        counterfactual: OutcomeSummary,
        delta: DeltaAnalysis,
        scenario: Scenario,
    ) -> CounterfactualExplanation:
        """Generate explanation for counterfactual analysis."""
        # Build summary
        summary_parts = []

        if delta.status_changed:
            summary_parts.append(
                f"Status would change from {delta.status_from} to {delta.status_to}."
            )

        if delta.framework_changed:
            summary_parts.append(
                f"Regulatory framework would change from {baseline.framework} to {counterfactual.framework}."
            )

        if delta.risk_delta != 0:
            direction = "increase" if delta.risk_delta > 0 else "decrease"
            summary_parts.append(
                f"Risk level would {direction} by {abs(delta.risk_delta)} level(s)."
            )

        if not summary_parts:
            summary_parts.append("No significant changes would result from this scenario.")

        summary = " ".join(summary_parts)

        # Build key differences
        key_differences: list[dict[str, str]] = []

        if delta.new_requirements:
            for req in delta.new_requirements[:3]:  # Limit to 3
                key_differences.append({
                    "type": "new_requirement",
                    "description": req,
                })

        if delta.removed_requirements:
            for req in delta.removed_requirements[:3]:
                key_differences.append({
                    "type": "removed_requirement",
                    "description": req,
                })

        if delta.risk_factors_added:
            for factor in delta.risk_factors_added:
                key_differences.append({
                    "type": "risk_increase",
                    "description": factor,
                })

        if delta.risk_factors_removed:
            for factor in delta.risk_factors_removed:
                key_differences.append({
                    "type": "risk_decrease",
                    "description": factor,
                })

        return CounterfactualExplanation(
            summary=summary,
            key_differences=key_differences,
        )

    def _build_matrix(
        self,
        baseline: OutcomeSummary,
        results: list[CounterfactualResponse],
    ) -> dict[str, list[str]]:
        """Build comparison matrix data structure."""
        matrix: dict[str, list[str]] = {
            "scenario": ["Baseline"],
            "status": [baseline.status],
            "framework": [baseline.framework],
            "risk_level": [baseline.risk_level],
            "conditions_count": [str(len(baseline.conditions))],
        }

        for i, result in enumerate(results):
            scenario_name = result.scenario_applied.name or f"Scenario {i + 1}"
            matrix["scenario"].append(scenario_name)
            matrix["status"].append(result.counterfactual_outcome.status)
            matrix["framework"].append(result.counterfactual_outcome.framework)
            matrix["risk_level"].append(result.counterfactual_outcome.risk_level)
            matrix["conditions_count"].append(
                str(len(result.counterfactual_outcome.conditions))
            )

        return matrix

    def _generate_insights(
        self,
        baseline: OutcomeSummary,
        results: list[CounterfactualResponse],
    ) -> list[MatrixInsight]:
        """Generate insights from comparison analysis."""
        insights: list[MatrixInsight] = []

        # Find best outcome
        best_result = None
        best_score = self._outcome_score(baseline)

        for result in results:
            score = self._outcome_score(result.counterfactual_outcome)
            if score > best_score:
                best_score = score
                best_result = result

        if best_result:
            scenario_name = best_result.scenario_applied.name or "Alternative scenario"
            insights.append(
                MatrixInsight(
                    type="recommendation",
                    text=f"{scenario_name} would improve compliance outcome to {best_result.counterfactual_outcome.status}.",
                )
            )

        # Find worst outcome
        worst_result = None
        worst_score = self._outcome_score(baseline)

        for result in results:
            score = self._outcome_score(result.counterfactual_outcome)
            if score < worst_score:
                worst_score = score
                worst_result = result

        if worst_result:
            scenario_name = worst_result.scenario_applied.name or "Alternative scenario"
            insights.append(
                MatrixInsight(
                    type="warning",
                    text=f"Avoid {scenario_name} - would result in {worst_result.counterfactual_outcome.status} status.",
                )
            )

        # Check for jurisdiction arbitrage opportunities
        approved_jurisdictions = []
        for result in results:
            if (
                result.scenario_applied.type == ScenarioType.JURISDICTION_CHANGE
                and result.counterfactual_outcome.status == "APPROVED"
            ):
                jurisdiction = result.scenario_applied.parameters.get("to_jurisdiction")
                if jurisdiction:
                    approved_jurisdictions.append(jurisdiction)

        if approved_jurisdictions and baseline.status != "APPROVED":
            insights.append(
                MatrixInsight(
                    type="opportunity",
                    text=f"Consider operating in {', '.join(approved_jurisdictions)} for smoother compliance path.",
                )
            )

        return insights

    def _outcome_score(self, outcome: OutcomeSummary) -> int:
        """Score an outcome for comparison (higher is better)."""
        status_scores = {
            "APPROVED": 3,
            "CONDITIONAL": 2,
            "DENIED": 0,
            "UNKNOWN": 1,
        }
        risk_scores = {
            "LOW": 3,
            "MEDIUM": 2,
            "HIGH": 1,
            "CRITICAL": 0,
        }

        status_score = status_scores.get(outcome.status, 1)
        risk_score = risk_scores.get(outcome.risk_level, 2)

        # Penalty for many conditions
        condition_penalty = min(len(outcome.conditions), 5) * 0.2

        return status_score + risk_score - condition_penalty
