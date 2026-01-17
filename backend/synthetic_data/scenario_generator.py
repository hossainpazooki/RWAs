"""Scenario generator for comprehensive test coverage.

Generates test scenarios by combining ontology dimensions:
- instrument_type: art, emt, stablecoin, etc.
- activity: public_offer, custody, tokenization, etc.
- jurisdiction: EU, UK, US, CH, SG
- Authorization status, thresholds, and edge cases

Categories:
- Happy path (150): Valid compliant scenarios
- Edge cases (150): Threshold boundaries
- Negative cases (100): Rule violations
- Cross-border (75): Multi-jurisdiction
- Temporal (25): Version-dependent
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from backend.synthetic_data.base import BaseGenerator
from backend.synthetic_data.config import (
    THRESHOLDS,
    SCENARIO_CATEGORIES,
    INSTRUMENT_TYPES,
    ACTIVITY_TYPES,
    ACTOR_TYPES,
    JURISDICTIONS,
)


class ScenarioGenerator(BaseGenerator):
    """Generator for test scenarios covering regulatory edge cases.

    Usage:
        generator = ScenarioGenerator(seed=42)
        scenarios = generator.generate(count=500)

        # Generate by category
        happy_paths = generator.generate_category("happy_path", count=150)
        edge_cases = generator.generate_category("edge_case", count=150)
    """

    def generate(self, count: int) -> list[dict[str, Any]]:
        """Generate synthetic scenarios distributed across categories.

        Args:
            count: Total number of scenarios to generate

        Returns:
            List of scenario dictionaries
        """
        scenarios = []

        # Calculate distribution based on category percentages
        total_configured = sum(cat["count"] for cat in SCENARIO_CATEGORIES.values())
        scale = count / total_configured

        for category, config in SCENARIO_CATEGORIES.items():
            category_count = max(1, int(config["count"] * scale))
            category_scenarios = self.generate_category(category, category_count)
            scenarios.extend(category_scenarios)

        # Shuffle to mix categories
        return self._shuffle(scenarios)[:count]

    def generate_category(
        self, category: str, count: int
    ) -> list[dict[str, Any]]:
        """Generate scenarios for a specific category.

        Args:
            category: One of happy_path, edge_case, negative, cross_border, temporal
            count: Number of scenarios to generate

        Returns:
            List of scenario dictionaries
        """
        if category == "happy_path":
            return self._generate_happy_path(count)
        elif category == "edge_case":
            return self._generate_edge_cases(count)
        elif category == "negative":
            return self._generate_negative(count)
        elif category == "cross_border":
            return self._generate_cross_border(count)
        elif category == "temporal":
            return self._generate_temporal(count)
        else:
            raise ValueError(f"Unknown category: {category}")

    def validate(self, item: dict[str, Any]) -> bool:
        """Validate a scenario has required fields.

        Args:
            item: Scenario dictionary

        Returns:
            True if valid
        """
        required_fields = ["scenario_id", "category", "instrument_type", "activity"]
        return all(field in item for field in required_fields)

    # =========================================================================
    # Category Generators
    # =========================================================================

    def _generate_happy_path(self, count: int) -> list[dict[str, Any]]:
        """Generate compliant happy path scenarios."""
        scenarios = []

        for i in range(count):
            instrument = self._choice(INSTRUMENT_TYPES[:5])  # Exclude NFT for compliance
            activity = self._choice(ACTIVITY_TYPES[:5])  # Core activities
            jurisdiction = self._choice(JURISDICTIONS[:3])  # EU, UK, US

            scenario = {
                "scenario_id": self._generate_id("hp"),
                "category": "happy_path",
                "description": f"Compliant {instrument} {activity} in {jurisdiction}",
                # Core dimensions
                "instrument_type": instrument,
                "activity": activity,
                "jurisdiction": jurisdiction,
                # Authorization (compliant)
                "authorized": True,
                "has_authorization": True,
                "authorization_date": self._random_past_date(365),
                # Entity attributes (compliant)
                "is_credit_institution": self._probability(0.3),
                "is_electronic_money_institution": instrument == "emt" and self._probability(0.7),
                "is_regulated_entity": True,
                # Documentation (compliant)
                "has_whitepaper": True,
                "whitepaper_submitted": True,
                "whitepaper_approved": True,
                # Reserves (compliant for ARTs/EMTs)
                "reserve_ratio": self._uniform(1.0, 1.05),
                "reserve_value_eur": self._randint(1_000_000, 10_000_000),
                "reserve_custodian_authorized": True,
                # Risk warnings (compliant for UK)
                "has_prescribed_risk_warning": True,
                "risk_warning_prominent": True,
                # Investor targeting
                "investor_types": self._sample(["retail", "professional", "institutional"], k=self._randint(1, 3)),
                "is_first_time_investor": False,
                # Expected outcome
                "expected_decision": "authorized" if activity == "public_offer" else "compliant",
            }

            scenarios.append(scenario)

        return scenarios

    def _generate_edge_cases(self, count: int) -> list[dict[str, Any]]:
        """Generate threshold boundary scenarios."""
        scenarios = []

        # Distribute across different threshold types
        threshold_keys = list(THRESHOLDS.keys())

        for i in range(count):
            threshold_key = self._choice(threshold_keys)
            threshold_values = THRESHOLDS[threshold_key]
            threshold_value = self._choice(threshold_values)

            instrument = self._choice(INSTRUMENT_TYPES[:4])
            activity = self._choice(ACTIVITY_TYPES[:4])
            jurisdiction = self._choice(JURISDICTIONS[:3])

            scenario = {
                "scenario_id": self._generate_id("ec"),
                "category": "edge_case",
                "description": f"Edge case: {threshold_key}={threshold_value}",
                "tested_threshold": threshold_key,
                "threshold_value": threshold_value,
                # Core dimensions
                "instrument_type": instrument,
                "activity": activity,
                "jurisdiction": jurisdiction,
                # Authorization
                "authorized": True,
                "has_authorization": True,
                # Entity attributes
                "is_credit_institution": self._probability(0.3),
                "is_regulated_entity": True,
                # Documentation
                "has_whitepaper": True,
                "whitepaper_submitted": True,
                # Apply threshold to appropriate field
                **self._apply_threshold(threshold_key, threshold_value),
                # Investor targeting
                "investor_types": ["professional"],
            }

            # Determine expected outcome based on threshold
            scenario["expected_decision"] = self._threshold_outcome(threshold_key, threshold_value)

            scenarios.append(scenario)

        return scenarios

    def _generate_negative(self, count: int) -> list[dict[str, Any]]:
        """Generate rule violation scenarios."""
        scenarios = []

        violation_types = [
            "unauthorized",
            "no_whitepaper",
            "insufficient_reserves",
            "no_risk_warning",
            "unlicensed_custodian",
            "prohibited_activity",
        ]

        for i in range(count):
            violation = self._choice(violation_types)
            instrument = self._choice(INSTRUMENT_TYPES)
            activity = self._choice(ACTIVITY_TYPES)
            jurisdiction = self._choice(JURISDICTIONS[:3])

            scenario = {
                "scenario_id": self._generate_id("neg"),
                "category": "negative",
                "description": f"Violation: {violation} for {instrument} {activity}",
                "violation_type": violation,
                # Core dimensions
                "instrument_type": instrument,
                "activity": activity,
                "jurisdiction": jurisdiction,
                # Apply violation
                **self._apply_violation(violation),
                # Investor targeting
                "investor_types": ["retail"],
                "is_first_time_investor": self._probability(0.3),
                # Expected outcome
                "expected_decision": self._violation_outcome(violation),
            }

            scenarios.append(scenario)

        return scenarios

    def _generate_cross_border(self, count: int) -> list[dict[str, Any]]:
        """Generate multi-jurisdiction scenarios."""
        scenarios = []

        for i in range(count):
            issuer_jurisdiction = self._choice(JURISDICTIONS)
            # Select 1-3 target jurisdictions (different from issuer)
            other_jurisdictions = [j for j in JURISDICTIONS if j != issuer_jurisdiction]
            target_count = self._randint(1, min(3, len(other_jurisdictions)))
            target_jurisdictions = self._sample(other_jurisdictions, k=target_count)

            instrument = self._choice(INSTRUMENT_TYPES[:4])
            activity = self._choice(["public_offer", "admission_to_trading", "exchange"])

            scenario = {
                "scenario_id": self._generate_id("xb"),
                "category": "cross_border",
                "description": f"Cross-border: {issuer_jurisdiction} -> {', '.join(target_jurisdictions)}",
                # Core dimensions
                "instrument_type": instrument,
                "activity": activity,
                "jurisdiction": issuer_jurisdiction,
                # Cross-border specific
                "issuer_jurisdiction": issuer_jurisdiction,
                "target_jurisdictions": target_jurisdictions,
                "is_cross_border": True,
                # Authorization per jurisdiction
                "authorized": True,
                "has_authorization": True,
                f"authorized_in_{issuer_jurisdiction.lower()}": True,
                # Documentation
                "has_whitepaper": True,
                "whitepaper_submitted": True,
                # Reserves
                "reserve_ratio": self._uniform(1.0, 1.02),
                "reserve_value_eur": self._randint(5_000_000, 50_000_000),
                # Risk warnings
                "has_prescribed_risk_warning": True,
                "risk_warning_prominent": True,
                # Investor targeting
                "investor_types": self._sample(["retail", "professional", "institutional"], k=2),
                # Expected: may have conflicts
                "expected_conflicts": len(target_jurisdictions) > 1,
            }

            # Add target jurisdiction authorizations
            for target in target_jurisdictions:
                scenario[f"authorized_in_{target.lower()}"] = self._probability(0.8)

            scenarios.append(scenario)

        return scenarios

    def _generate_temporal(self, count: int) -> list[dict[str, Any]]:
        """Generate version-dependent scenarios."""
        scenarios = []

        temporal_cases = [
            ("pre_effective", -30),  # Before rule effective date
            ("effective_date", 0),   # On effective date
            ("post_effective", 30),  # After effective date
            ("sunset_approaching", -7),  # Near sunset date
            ("version_transition", 0),  # During version change
        ]

        for i in range(count):
            case_type, day_offset = self._choice(temporal_cases)
            instrument = self._choice(INSTRUMENT_TYPES[:4])
            activity = self._choice(ACTIVITY_TYPES[:4])
            jurisdiction = self._choice(JURISDICTIONS[:3])

            # Calculate evaluation date relative to a reference
            reference_date = date(2024, 6, 30)  # MiCA effective date
            evaluation_date = reference_date + timedelta(days=day_offset)

            scenario = {
                "scenario_id": self._generate_id("tmp"),
                "category": "temporal",
                "description": f"Temporal: {case_type} ({evaluation_date})",
                "temporal_case": case_type,
                "evaluation_date": evaluation_date.isoformat(),
                "day_offset": day_offset,
                # Core dimensions
                "instrument_type": instrument,
                "activity": activity,
                "jurisdiction": jurisdiction,
                # Authorization
                "authorized": True,
                "has_authorization": True,
                "authorization_date": (evaluation_date - timedelta(days=90)).isoformat(),
                # Entity attributes
                "is_credit_institution": self._probability(0.3),
                # Documentation
                "has_whitepaper": True,
                # Version info
                "rule_version": "1.0" if day_offset < 0 else "2.0",
                # Expected outcome depends on timing
                "expected_decision": self._temporal_outcome(case_type),
            }

            scenarios.append(scenario)

        return scenarios

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _random_past_date(self, max_days_ago: int) -> str:
        """Generate a random past date as ISO string."""
        days_ago = self._randint(1, max_days_ago)
        past_date = date.today() - timedelta(days=days_ago)
        return past_date.isoformat()

    def _apply_threshold(self, key: str, value: int | float) -> dict[str, Any]:
        """Apply threshold value to appropriate scenario fields."""
        if key == "reserve_value_eur":
            return {"reserve_value_eur": value, "is_significant_art": value >= 5_000_000}
        elif key == "total_token_value_eur":
            return {"total_token_value_eur": value}
        elif key == "reserve_ratio":
            return {"reserve_ratio": value, "reserves_sufficient": value >= 1.0}
        elif key == "customer_count":
            return {"customer_count": value}
        elif key == "daily_transaction_volume":
            return {"daily_transaction_volume": value}
        elif key == "whitepaper_pages":
            return {"whitepaper_pages": value}
        return {}

    def _threshold_outcome(self, key: str, value: int | float) -> str:
        """Determine expected outcome based on threshold."""
        if key == "reserve_ratio":
            return "compliant" if value >= 1.0 else "non_compliant"
        elif key == "reserve_value_eur":
            return "requires_authorization" if value >= 5_000_000 else "authorized"
        return "pending_review"

    def _apply_violation(self, violation: str) -> dict[str, Any]:
        """Apply violation characteristics to scenario."""
        violations = {
            "unauthorized": {
                "authorized": False,
                "has_authorization": False,
            },
            "no_whitepaper": {
                "authorized": True,
                "has_whitepaper": False,
                "whitepaper_submitted": False,
            },
            "insufficient_reserves": {
                "authorized": True,
                "has_whitepaper": True,
                "reserve_ratio": 0.85,
                "reserves_sufficient": False,
            },
            "no_risk_warning": {
                "authorized": True,
                "has_whitepaper": True,
                "has_prescribed_risk_warning": False,
                "risk_warning_prominent": False,
            },
            "unlicensed_custodian": {
                "authorized": True,
                "has_whitepaper": True,
                "reserve_custodian_authorized": False,
            },
            "prohibited_activity": {
                "authorized": True,
                "is_prohibited_jurisdiction": True,
            },
        }
        return violations.get(violation, {})

    def _violation_outcome(self, violation: str) -> str:
        """Determine expected outcome for violation type."""
        outcomes = {
            "unauthorized": "not_authorized",
            "no_whitepaper": "non_compliant",
            "insufficient_reserves": "non_compliant",
            "no_risk_warning": "non_compliant",
            "unlicensed_custodian": "non_compliant",
            "prohibited_activity": "prohibited",
        }
        return outcomes.get(violation, "non_compliant")

    def _temporal_outcome(self, case_type: str) -> str:
        """Determine expected outcome for temporal case."""
        outcomes = {
            "pre_effective": "exempt",  # Old rules apply
            "effective_date": "pending_review",  # Transition
            "post_effective": "requires_authorization",  # New rules apply
            "sunset_approaching": "compliant",  # Still valid
            "version_transition": "pending_review",  # Review needed
        }
        return outcomes.get(case_type, "pending_review")


# =============================================================================
# CLI for Standalone Execution
# =============================================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate synthetic scenarios")
    parser.add_argument("--count", type=int, default=100, help="Number of scenarios")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--category", type=str, help="Specific category to generate")
    parser.add_argument("--validate", action="store_true", help="Validate generated scenarios")
    parser.add_argument("--output", type=str, help="Output JSON file")

    args = parser.parse_args()

    generator = ScenarioGenerator(seed=args.seed)

    if args.category:
        scenarios = generator.generate_category(args.category, args.count)
    else:
        scenarios = generator.generate(args.count)

    if args.validate:
        valid_count = sum(1 for s in scenarios if generator.validate(s))
        print(f"Generated {len(scenarios)} scenarios, {valid_count} valid")
    else:
        print(f"Generated {len(scenarios)} scenarios")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(scenarios, f, indent=2, default=str)
        print(f"Saved to {args.output}")
    else:
        # Print sample
        for scenario in scenarios[:3]:
            print(json.dumps(scenario, indent=2, default=str))
