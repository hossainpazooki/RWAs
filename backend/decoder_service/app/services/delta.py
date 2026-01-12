"""Delta Analyzer - computes differences between outcomes."""

from __future__ import annotations

from .schemas import (
    DeltaAnalysis,
    OutcomeSummary,
)


# Risk level ordering for comparison
RISK_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


class DeltaAnalyzer:
    """Analyzes differences between baseline and counterfactual outcomes."""

    def compare(
        self,
        baseline: OutcomeSummary,
        counterfactual: OutcomeSummary,
    ) -> DeltaAnalysis:
        """Compare baseline and counterfactual outcomes.

        Args:
            baseline: Original outcome
            counterfactual: What-if outcome

        Returns:
            DeltaAnalysis with all differences
        """
        delta = DeltaAnalysis()

        # Status comparison
        delta.status_from = baseline.status
        delta.status_to = counterfactual.status
        delta.status_changed = baseline.status != counterfactual.status

        # Framework comparison
        delta.framework_changed = baseline.framework != counterfactual.framework
        if delta.framework_changed:
            delta.frameworks_removed = [baseline.framework]
            delta.frameworks_added = [counterfactual.framework]

        # Risk comparison
        delta.risk_delta = self._calculate_risk_delta(
            baseline.risk_level, counterfactual.risk_level
        )
        if delta.risk_delta > 0:
            delta.risk_factors_added = self._infer_risk_factors(
                baseline, counterfactual, increasing=True
            )
        elif delta.risk_delta < 0:
            delta.risk_factors_removed = self._infer_risk_factors(
                baseline, counterfactual, increasing=False
            )

        # Condition/requirement comparison
        baseline_conditions = set(baseline.conditions)
        counterfactual_conditions = set(counterfactual.conditions)

        delta.new_requirements = list(counterfactual_conditions - baseline_conditions)
        delta.removed_requirements = list(baseline_conditions - counterfactual_conditions)

        # Track modified requirements (same topic, different wording)
        delta.modified_requirements = self._find_modified_requirements(
            baseline.conditions, counterfactual.conditions
        )

        return delta

    def _calculate_risk_delta(self, from_risk: str, to_risk: str) -> int:
        """Calculate risk level change.

        Returns:
            Integer from -3 to +3 representing risk change
        """
        try:
            from_idx = RISK_LEVELS.index(from_risk)
            to_idx = RISK_LEVELS.index(to_risk)
            return to_idx - from_idx
        except ValueError:
            return 0

    def _infer_risk_factors(
        self,
        baseline: OutcomeSummary,
        counterfactual: OutcomeSummary,
        increasing: bool,
    ) -> list[str]:
        """Infer what risk factors changed.

        Args:
            baseline: Original outcome
            counterfactual: What-if outcome
            increasing: Whether risk is increasing

        Returns:
            List of inferred risk factor changes
        """
        factors = []

        if baseline.status != counterfactual.status:
            if increasing:
                factors.append(f"Status changed from {baseline.status} to {counterfactual.status}")
            else:
                factors.append(f"Status improved from {baseline.status} to {counterfactual.status}")

        if baseline.framework != counterfactual.framework:
            if increasing:
                factors.append(f"Now subject to {counterfactual.framework} requirements")
            else:
                factors.append(f"No longer subject to {baseline.framework} requirements")

        new_conditions = set(counterfactual.conditions) - set(baseline.conditions)
        if new_conditions and increasing:
            factors.append(f"{len(new_conditions)} new condition(s) required")

        removed_conditions = set(baseline.conditions) - set(counterfactual.conditions)
        if removed_conditions and not increasing:
            factors.append(f"{len(removed_conditions)} condition(s) no longer required")

        return factors

    def _find_modified_requirements(
        self,
        baseline_conditions: list[str],
        counterfactual_conditions: list[str],
    ) -> list[dict[str, str]]:
        """Find requirements that were modified (not added/removed).

        Uses simple keyword matching to identify related conditions.
        """
        modified = []

        # Extract keywords from conditions
        def extract_keywords(condition: str) -> set[str]:
            # Simple tokenization
            words = condition.lower().replace(",", " ").replace(".", " ").split()
            # Filter common words
            stopwords = {"the", "a", "an", "is", "are", "to", "of", "for", "and", "or", "in", "on"}
            return {w for w in words if len(w) > 2 and w not in stopwords}

        baseline_keywords = [(c, extract_keywords(c)) for c in baseline_conditions]
        cf_keywords = [(c, extract_keywords(c)) for c in counterfactual_conditions]

        for b_cond, b_keys in baseline_keywords:
            for cf_cond, cf_keys in cf_keywords:
                # Skip if conditions are identical
                if b_cond == cf_cond:
                    continue

                # Check for significant keyword overlap
                overlap = b_keys & cf_keys
                if len(overlap) >= 2 and len(overlap) >= len(b_keys) * 0.5:
                    modified.append({
                        "requirement": " ".join(overlap)[:50],
                        "baseline": b_cond,
                        "counterfactual": cf_cond,
                        "change": "modified",
                    })

        return modified

    def summarize_impact(self, delta: DeltaAnalysis) -> str:
        """Generate human-readable impact summary.

        Args:
            delta: The delta analysis

        Returns:
            Summary string
        """
        parts = []

        # Status impact
        if delta.status_changed:
            parts.append(f"Status changes from {delta.status_from} to {delta.status_to}.")

        # Risk impact
        if delta.risk_delta > 0:
            parts.append(f"Risk increases by {delta.risk_delta} level(s).")
        elif delta.risk_delta < 0:
            parts.append(f"Risk decreases by {abs(delta.risk_delta)} level(s).")

        # Framework impact
        if delta.framework_changed:
            if delta.frameworks_added:
                parts.append(f"New framework applies: {', '.join(delta.frameworks_added)}.")
            if delta.frameworks_removed:
                parts.append(f"Previous framework no longer applies: {', '.join(delta.frameworks_removed)}.")

        # Requirements impact
        if delta.new_requirements:
            parts.append(f"{len(delta.new_requirements)} new requirement(s) apply.")
        if delta.removed_requirements:
            parts.append(f"{len(delta.removed_requirements)} requirement(s) no longer apply.")

        if not parts:
            return "No significant changes detected."

        return " ".join(parts)

    def calculate_severity(self, delta: DeltaAnalysis) -> str:
        """Calculate overall severity of changes.

        Returns:
            "low", "medium", "high", or "critical"
        """
        score = 0

        # Status change scoring
        if delta.status_changed:
            status_severity = {
                ("APPROVED", "CONDITIONAL"): 1,
                ("APPROVED", "DENIED"): 3,
                ("CONDITIONAL", "DENIED"): 2,
                ("CONDITIONAL", "APPROVED"): -1,
                ("DENIED", "CONDITIONAL"): -1,
                ("DENIED", "APPROVED"): -2,
            }
            key = (delta.status_from, delta.status_to)
            score += status_severity.get(key, 0)

        # Risk delta scoring
        score += delta.risk_delta

        # Requirement change scoring
        score += len(delta.new_requirements) * 0.5
        score -= len(delta.removed_requirements) * 0.3

        # Map to severity
        if score >= 3:
            return "critical"
        elif score >= 1.5:
            return "high"
        elif score >= 0.5:
            return "medium"
        else:
            return "low"
