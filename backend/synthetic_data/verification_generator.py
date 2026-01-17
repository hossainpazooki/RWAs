"""Verification evidence generator for consistency engine testing.

Generates verification records across 5 tiers:
- Tier 0 (40%): Schema validation
- Tier 1 (25%): Semantic consistency
- Tier 2 (15%): Cross-rule checks
- Tier 3 (10%): Temporal consistency
- Tier 4 (10%): External alignment

Confidence score ranges:
- Passing: 0.85-0.99
- Marginal: 0.70-0.84
- Failing: 0.40-0.69
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from backend.synthetic_data.base import BaseGenerator
from backend.synthetic_data.config import (
    VERIFICATION_TIERS,
    CONFIDENCE_RANGES,
)


class VerificationGenerator(BaseGenerator):
    """Generator for verification evidence records.

    Usage:
        generator = VerificationGenerator(seed=42)
        evidence = generator.generate(count=200)

        # Generate for specific tier
        tier0_evidence = generator.generate_tier(tier=0, count=80)
    """

    def generate(self, count: int) -> list[dict[str, Any]]:
        """Generate verification evidence distributed across tiers.

        Args:
            count: Total number of evidence records to generate

        Returns:
            List of verification evidence dictionaries
        """
        evidence = []

        for tier, config in VERIFICATION_TIERS.items():
            tier_count = max(1, int(count * config["percentage"]))
            tier_evidence = self.generate_tier(tier, tier_count)
            evidence.extend(tier_evidence)

        return self._shuffle(evidence)[:count]

    def generate_tier(self, tier: int, count: int) -> list[dict[str, Any]]:
        """Generate verification evidence for a specific tier.

        Args:
            tier: Verification tier (0-4)
            count: Number of records to generate

        Returns:
            List of evidence dictionaries
        """
        if tier not in VERIFICATION_TIERS:
            raise ValueError(f"Unknown tier: {tier}")

        config = VERIFICATION_TIERS[tier]
        evidence = []

        for i in range(count):
            # Randomly assign outcome distribution
            # 60% passing, 25% marginal, 15% failing
            outcome_roll = self.rng.random()
            if outcome_roll < 0.60:
                outcome = "passing"
            elif outcome_roll < 0.85:
                outcome = "marginal"
            else:
                outcome = "failing"

            record = self._generate_evidence_record(
                tier=tier,
                config=config,
                outcome=outcome,
                index=i,
            )
            evidence.append(record)

        return evidence

    def validate(self, item: dict[str, Any]) -> bool:
        """Validate an evidence record has required fields.

        Args:
            item: Evidence dictionary

        Returns:
            True if valid
        """
        required_fields = [
            "evidence_id",
            "tier",
            "check_type",
            "confidence_score",
            "status",
        ]
        return all(field in item for field in required_fields)

    # =========================================================================
    # Evidence Generation
    # =========================================================================

    def _generate_evidence_record(
        self,
        tier: int,
        config: dict[str, Any],
        outcome: str,
        index: int,
    ) -> dict[str, Any]:
        """Generate a single verification evidence record."""
        check_type = self._choice(config["check_types"])

        # Generate confidence score based on outcome
        score_range = CONFIDENCE_RANGES[outcome]
        confidence_score = self._uniform(score_range[0], score_range[1])

        # Determine status from outcome
        status = "pass" if outcome == "passing" else ("warning" if outcome == "marginal" else "fail")

        # Generate rule reference
        rule_id = self._generate_rule_reference()

        record = {
            "evidence_id": self._generate_id(f"ev_t{tier}"),
            "tier": tier,
            "tier_name": config["name"],
            "check_type": check_type,
            "rule_id": rule_id,
            "confidence_score": round(confidence_score, 4),
            "status": status,
            "outcome": outcome,
            "timestamp": self._generate_timestamp(),
            "details": self._generate_check_details(tier, check_type, outcome),
            "evidence_data": self._generate_evidence_data(tier, check_type),
        }

        # Add tier-specific fields
        if tier >= 2:
            record["related_rules"] = self._generate_related_rules(rule_id)

        if tier == 3:
            record["temporal_info"] = self._generate_temporal_info()

        if tier == 4:
            record["source_reference"] = self._generate_source_reference()

        return record

    def _generate_rule_reference(self) -> str:
        """Generate a plausible rule ID reference."""
        prefixes = ["mica", "fca", "genius", "rwa"]
        articles = ["art36", "art38", "art43", "art59", "cobs_4_12a", "sec_101"]
        activities = ["authorization", "reserves", "disclosure", "custody", "offer"]

        prefix = self._choice(prefixes)
        article = self._choice(articles)
        activity = self._choice(activities)

        return f"{prefix}_{article}_{activity}"

    def _generate_timestamp(self) -> str:
        """Generate a recent timestamp."""
        days_ago = self._randint(0, 30)
        hours_ago = self._randint(0, 23)
        ts = datetime.now() - timedelta(days=days_ago, hours=hours_ago)
        return ts.isoformat()

    def _generate_check_details(
        self, tier: int, check_type: str, outcome: str
    ) -> dict[str, Any]:
        """Generate details specific to check type and outcome."""
        base_details = {
            "check_type": check_type,
            "execution_time_ms": self._randint(10, 500),
        }

        # Add outcome-specific details
        if outcome == "passing":
            base_details["message"] = f"{check_type} check passed successfully"
            base_details["issues_found"] = 0
        elif outcome == "marginal":
            base_details["message"] = f"{check_type} check passed with warnings"
            base_details["issues_found"] = self._randint(1, 3)
            base_details["warnings"] = self._generate_warnings(check_type)
        else:
            base_details["message"] = f"{check_type} check failed"
            base_details["issues_found"] = self._randint(2, 5)
            base_details["errors"] = self._generate_errors(check_type)

        return base_details

    def _generate_evidence_data(
        self, tier: int, check_type: str
    ) -> dict[str, Any]:
        """Generate evidence data based on tier and check type."""
        # Tier 0: Schema validation
        if tier == 0:
            return self._generate_schema_evidence(check_type)
        # Tier 1: Semantic consistency
        elif tier == 1:
            return self._generate_semantic_evidence(check_type)
        # Tier 2: Cross-rule checks
        elif tier == 2:
            return self._generate_cross_rule_evidence(check_type)
        # Tier 3: Temporal consistency
        elif tier == 3:
            return self._generate_temporal_evidence(check_type)
        # Tier 4: External alignment
        elif tier == 4:
            return self._generate_external_evidence(check_type)

        return {}

    def _generate_schema_evidence(self, check_type: str) -> dict[str, Any]:
        """Generate evidence for schema validation checks."""
        if check_type == "required_fields":
            return {
                "fields_checked": ["rule_id", "version", "jurisdiction", "decision_tree"],
                "fields_present": self._randint(3, 4),
                "fields_missing": self._sample(["tags", "effective_from"], k=self._randint(0, 1)),
            }
        elif check_type == "type_validation":
            return {
                "types_checked": {
                    "rule_id": "string",
                    "version": "string",
                    "effective_from": "date",
                },
                "type_errors": [],
            }
        elif check_type == "enum_values":
            return {
                "enums_checked": ["jurisdiction", "instrument_type", "activity"],
                "invalid_values": [],
            }
        return {"check": check_type}

    def _generate_semantic_evidence(self, check_type: str) -> dict[str, Any]:
        """Generate evidence for semantic consistency checks."""
        if check_type == "text_similarity":
            return {
                "rule_text_sample": "Requires authorization for public offers...",
                "source_text_sample": "No person shall make a public offer...",
                "similarity_score": self._uniform(0.70, 0.95),
                "similarity_method": "cosine",
            }
        elif check_type == "keyword_presence":
            return {
                "expected_keywords": ["authorization", "public offer", "crypto-asset"],
                "found_keywords": self._sample(["authorization", "public offer", "crypto-asset"], k=self._randint(2, 3)),
                "missing_keywords": [],
            }
        return {"check": check_type}

    def _generate_cross_rule_evidence(self, check_type: str) -> dict[str, Any]:
        """Generate evidence for cross-rule checks."""
        if check_type == "conflict_detection":
            return {
                "rules_compared": self._randint(5, 20),
                "potential_conflicts": self._randint(0, 3),
                "conflict_pairs": [],
            }
        elif check_type == "overlap_analysis":
            return {
                "overlap_percentage": self._uniform(0.1, 0.4),
                "overlapping_conditions": self._randint(1, 5),
            }
        return {"check": check_type}

    def _generate_temporal_evidence(self, check_type: str) -> dict[str, Any]:
        """Generate evidence for temporal consistency checks."""
        if check_type == "effective_date_ordering":
            return {
                "dates_checked": self._randint(5, 15),
                "ordering_violations": self._randint(0, 2),
            }
        elif check_type == "version_compatibility":
            return {
                "versions_checked": ["1.0", "1.1", "2.0"],
                "compatibility_issues": [],
            }
        return {"check": check_type}

    def _generate_external_evidence(self, check_type: str) -> dict[str, Any]:
        """Generate evidence for external alignment checks."""
        if check_type == "source_text_match":
            return {
                "source_document": "mica_2023",
                "article_reference": "Article 36",
                "match_confidence": self._uniform(0.80, 0.98),
            }
        elif check_type == "regulatory_update_check":
            return {
                "last_update_checked": self._generate_timestamp(),
                "updates_available": self._probability(0.2),
            }
        return {"check": check_type}

    def _generate_related_rules(self, rule_id: str) -> list[str]:
        """Generate list of related rule IDs."""
        prefixes = ["mica", "fca", "genius"]
        count = self._randint(1, 4)
        return [f"{self._choice(prefixes)}_related_{i}" for i in range(count)]

    def _generate_temporal_info(self) -> dict[str, Any]:
        """Generate temporal metadata."""
        return {
            "effective_from": "2024-06-30",
            "effective_to": None,
            "version": f"{self._randint(1, 3)}.{self._randint(0, 5)}",
            "supersedes": self._choice([None, "previous_version_id"]),
        }

    def _generate_source_reference(self) -> dict[str, Any]:
        """Generate source document reference."""
        documents = [
            ("mica_2023", "Regulation (EU) 2023/1114"),
            ("fca_crypto_2024", "FCA PS22/10"),
            ("genius_act_2025", "S.394 GENIUS Act"),
        ]
        doc_id, doc_name = self._choice(documents)
        return {
            "document_id": doc_id,
            "document_name": doc_name,
            "article": f"Article {self._randint(1, 90)}",
            "last_verified": self._generate_timestamp(),
        }

    def _generate_warnings(self, check_type: str) -> list[str]:
        """Generate warning messages."""
        warnings = [
            f"Minor discrepancy in {check_type} check",
            "Optional field missing but not required",
            "Date format inconsistency (still valid)",
            "Deprecated pattern detected",
        ]
        return self._sample(warnings, k=self._randint(1, 2))

    def _generate_errors(self, check_type: str) -> list[str]:
        """Generate error messages."""
        errors = [
            f"Failed {check_type} validation",
            "Required field missing",
            "Invalid value for enumerated field",
            "Type mismatch detected",
            "Reference to non-existent rule",
        ]
        return self._sample(errors, k=self._randint(1, 3))


# =============================================================================
# CLI for Standalone Execution
# =============================================================================

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate verification evidence")
    parser.add_argument("--count", type=int, default=100, help="Number of records")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--tier", type=int, help="Specific tier to generate (0-4)")
    parser.add_argument("--validate", action="store_true", help="Validate generated records")
    parser.add_argument("--output", type=str, help="Output JSON file")

    args = parser.parse_args()

    generator = VerificationGenerator(seed=args.seed)

    if args.tier is not None:
        evidence = generator.generate_tier(args.tier, args.count)
    else:
        evidence = generator.generate(args.count)

    if args.validate:
        valid_count = sum(1 for e in evidence if generator.validate(e))
        print(f"Generated {len(evidence)} evidence records, {valid_count} valid")
    else:
        print(f"Generated {len(evidence)} evidence records")

    # Print distribution
    by_tier = {}
    by_outcome = {}
    for e in evidence:
        tier = e.get("tier", -1)
        outcome = e.get("outcome", "unknown")
        by_tier[tier] = by_tier.get(tier, 0) + 1
        by_outcome[outcome] = by_outcome.get(outcome, 0) + 1

    print(f"By tier: {by_tier}")
    print(f"By outcome: {by_outcome}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(evidence, f, indent=2, default=str)
        print(f"Saved to {args.output}")
    else:
        # Print sample
        for record in evidence[:2]:
            print(json.dumps(record, indent=2, default=str))
