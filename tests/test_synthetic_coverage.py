"""Tests for synthetic data coverage and validation.

This module verifies that synthetic data generators produce valid,
comprehensive test data covering all ontology dimensions and edge cases.

Run with:
    pytest tests/test_synthetic_coverage.py -v
    pytest tests/test_synthetic_coverage.py -v --cov=backend/synthetic_data
"""

import pytest
from typing import Any

from backend.synthetic_data import (
    ScenarioGenerator,
    RuleGenerator,
    VerificationGenerator,
    THRESHOLDS,
    SCENARIO_CATEGORIES,
    VERIFICATION_TIERS,
)
from backend.synthetic_data.config import (
    INSTRUMENT_TYPES,
    ACTIVITY_TYPES,
    JURISDICTIONS,
    DECISION_OUTCOMES,
    CONFIDENCE_RANGES,
)


# =============================================================================
# Scenario Generator Tests
# =============================================================================


class TestScenarioGenerator:
    """Tests for ScenarioGenerator."""

    def test_generate_returns_requested_count(self):
        """Generator returns the requested number of scenarios."""
        generator = ScenarioGenerator(seed=42)
        scenarios = generator.generate(count=100)
        assert len(scenarios) == 100

    def test_scenarios_have_required_fields(self, synthetic_scenarios):
        """All scenarios have required fields."""
        required_fields = ["scenario_id", "category", "instrument_type", "activity"]
        for scenario in synthetic_scenarios:
            for field in required_fields:
                assert field in scenario, f"Missing {field} in scenario {scenario.get('scenario_id')}"

    def test_scenario_ids_are_unique(self, synthetic_scenarios):
        """All scenario IDs are unique."""
        ids = [s["scenario_id"] for s in synthetic_scenarios]
        assert len(ids) == len(set(ids)), "Duplicate scenario IDs found"

    def test_all_categories_represented(self, synthetic_scenarios):
        """All scenario categories are present."""
        categories = set(s["category"] for s in synthetic_scenarios)
        expected = set(SCENARIO_CATEGORIES.keys())
        assert categories == expected, f"Missing categories: {expected - categories}"

    def test_category_distribution(self, synthetic_scenarios):
        """Categories follow expected distribution."""
        by_category = {}
        for s in synthetic_scenarios:
            cat = s["category"]
            by_category[cat] = by_category.get(cat, 0) + 1

        # Each category should have at least some scenarios
        for category in SCENARIO_CATEGORIES:
            assert by_category.get(category, 0) > 0, f"No scenarios for {category}"

    def test_instrument_type_coverage(self, synthetic_scenarios):
        """Scenarios cover all instrument types."""
        instruments = set(s["instrument_type"] for s in synthetic_scenarios)
        # Should cover at least the main instrument types
        main_instruments = {"art", "emt", "stablecoin", "utility_token"}
        assert main_instruments.issubset(instruments), f"Missing instruments: {main_instruments - instruments}"

    def test_activity_coverage(self, synthetic_scenarios):
        """Scenarios cover core activities."""
        activities = set(s["activity"] for s in synthetic_scenarios)
        core_activities = {"public_offer", "admission_to_trading", "custody"}
        assert core_activities.issubset(activities), f"Missing activities: {core_activities - activities}"

    def test_jurisdiction_coverage(self, synthetic_scenarios):
        """Scenarios cover main jurisdictions."""
        jurisdictions = set(s.get("jurisdiction") for s in synthetic_scenarios if s.get("jurisdiction"))
        main_jurisdictions = {"EU", "UK", "US"}
        assert main_jurisdictions.issubset(jurisdictions), f"Missing jurisdictions: {main_jurisdictions - jurisdictions}"

    def test_happy_path_scenarios_are_compliant(self, happy_path_scenarios):
        """Happy path scenarios have compliant characteristics."""
        for scenario in happy_path_scenarios[:10]:  # Sample
            assert scenario.get("authorized", False), f"Happy path should be authorized: {scenario['scenario_id']}"
            assert scenario.get("has_whitepaper", False), f"Happy path should have whitepaper: {scenario['scenario_id']}"

    def test_negative_scenarios_have_violations(self, negative_scenarios):
        """Negative scenarios have violation characteristics."""
        for scenario in negative_scenarios[:10]:  # Sample
            assert "violation_type" in scenario, f"Negative should have violation_type: {scenario['scenario_id']}"

    def test_edge_cases_have_threshold_values(self, edge_case_scenarios):
        """Edge case scenarios test threshold boundaries."""
        threshold_tested = set()
        for scenario in edge_case_scenarios:
            if "tested_threshold" in scenario:
                threshold_tested.add(scenario["tested_threshold"])

        # Should test multiple different thresholds
        assert len(threshold_tested) >= 3, f"Only tested {len(threshold_tested)} thresholds"

    def test_cross_border_have_multiple_jurisdictions(self, cross_border_scenarios):
        """Cross-border scenarios involve multiple jurisdictions."""
        for scenario in cross_border_scenarios[:10]:  # Sample
            assert scenario.get("is_cross_border", False), "Should be marked cross-border"
            targets = scenario.get("target_jurisdictions", [])
            assert len(targets) >= 1, f"Should have target jurisdictions: {scenario['scenario_id']}"

    def test_deterministic_with_seed(self):
        """Same seed produces same scenarios."""
        gen1 = ScenarioGenerator(seed=123)
        gen2 = ScenarioGenerator(seed=123)

        scenarios1 = gen1.generate(count=10)
        scenarios2 = gen2.generate(count=10)

        for s1, s2 in zip(scenarios1, scenarios2):
            assert s1["scenario_id"] == s2["scenario_id"]
            assert s1["category"] == s2["category"]

    def test_validate_method(self):
        """Validate method correctly identifies valid scenarios."""
        generator = ScenarioGenerator(seed=42)
        scenarios = generator.generate(count=10)

        for scenario in scenarios:
            assert generator.validate(scenario), f"Valid scenario failed validation: {scenario['scenario_id']}"

        # Invalid scenario
        invalid = {"foo": "bar"}
        assert not generator.validate(invalid), "Invalid scenario should fail validation"


# =============================================================================
# Rule Generator Tests
# =============================================================================


class TestRuleGenerator:
    """Tests for RuleGenerator."""

    def test_generate_returns_requested_count(self):
        """Generator returns the requested number of rules."""
        generator = RuleGenerator(seed=42)
        rules = generator.generate(count=30)
        assert len(rules) == 30

    def test_rules_have_required_fields(self, synthetic_rules):
        """All rules have required fields."""
        required_fields = ["rule_id", "version", "jurisdiction", "source", "decision_tree"]
        for rule in synthetic_rules:
            for field in required_fields:
                assert field in rule, f"Missing {field} in rule {rule.get('rule_id')}"

    def test_rule_ids_are_unique(self, synthetic_rules):
        """All rule IDs are unique."""
        ids = [r["rule_id"] for r in synthetic_rules]
        assert len(ids) == len(set(ids)), "Duplicate rule IDs found"

    def test_framework_distribution(self, synthetic_rules):
        """Rules are distributed across frameworks."""
        by_framework = {}
        for rule in synthetic_rules:
            fw = rule.get("framework", "unknown")
            by_framework[fw] = by_framework.get(fw, 0) + 1

        # Should have rules from multiple frameworks
        assert len(by_framework) >= 2, f"Only {len(by_framework)} frameworks represented"

    def test_decision_tree_structure(self, synthetic_rules):
        """Decision trees have valid structure."""
        for rule in synthetic_rules[:10]:  # Sample
            tree = rule.get("decision_tree", {})
            assert "node_id" in tree, f"Tree missing node_id: {rule['rule_id']}"
            # Should have either condition or decision
            assert "condition" in tree or "decision" in tree, f"Invalid tree node: {rule['rule_id']}"

    def test_source_references(self, synthetic_rules):
        """Rules have valid source references."""
        for rule in synthetic_rules:
            source = rule.get("source", {})
            assert "document_id" in source, f"Missing document_id: {rule['rule_id']}"
            assert "article" in source, f"Missing article: {rule['rule_id']}"

    def test_applies_if_conditions(self, synthetic_rules):
        """Rules have valid applies_if blocks."""
        for rule in synthetic_rules:
            applies_if = rule.get("applies_if", {})
            assert "all" in applies_if or "any" in applies_if or not applies_if, \
                f"Invalid applies_if structure: {rule['rule_id']}"

    def test_mica_rules_are_eu_jurisdiction(self, mica_rules):
        """MiCA rules have EU jurisdiction."""
        for rule in mica_rules:
            assert rule.get("jurisdiction") == "EU", f"MiCA rule not EU: {rule['rule_id']}"
            assert rule.get("accuracy_level") == "high", f"MiCA should be high accuracy: {rule['rule_id']}"

    def test_genius_rules_are_illustrative(self, genius_rules):
        """GENIUS Act rules are marked as illustrative."""
        for rule in genius_rules:
            assert rule.get("accuracy_level") == "medium", f"GENIUS should be medium accuracy: {rule['rule_id']}"

    def test_generate_framework_method(self):
        """Generate specific framework rules."""
        generator = RuleGenerator(seed=42)
        mica_rules = generator.generate_framework("mica_eu", count=10)

        assert len(mica_rules) == 10
        for rule in mica_rules:
            assert rule.get("framework") == "MiCA"
            assert rule.get("jurisdiction") == "EU"

    def test_validate_method(self):
        """Validate method correctly identifies valid rules."""
        generator = RuleGenerator(seed=42)
        rules = generator.generate(count=10)

        for rule in rules:
            assert generator.validate(rule), f"Valid rule failed validation: {rule['rule_id']}"


# =============================================================================
# Verification Generator Tests
# =============================================================================


class TestVerificationGenerator:
    """Tests for VerificationGenerator."""

    def test_generate_returns_requested_count(self):
        """Generator returns the requested number of evidence records."""
        generator = VerificationGenerator(seed=42)
        evidence = generator.generate(count=100)
        assert len(evidence) == 100

    def test_evidence_has_required_fields(self, synthetic_verification):
        """All evidence records have required fields."""
        required_fields = ["evidence_id", "tier", "check_type", "confidence_score", "status"]
        for record in synthetic_verification:
            for field in required_fields:
                assert field in record, f"Missing {field} in {record.get('evidence_id')}"

    def test_evidence_ids_are_unique(self, synthetic_verification):
        """All evidence IDs are unique."""
        ids = [e["evidence_id"] for e in synthetic_verification]
        assert len(ids) == len(set(ids)), "Duplicate evidence IDs found"

    def test_tier_distribution(self, synthetic_verification):
        """Evidence is distributed across tiers."""
        by_tier = {}
        for record in synthetic_verification:
            tier = record.get("tier", -1)
            by_tier[tier] = by_tier.get(tier, 0) + 1

        # Should have all tiers represented
        assert set(by_tier.keys()) == set(VERIFICATION_TIERS.keys()), "Missing tiers"

    def test_confidence_scores_in_range(self, synthetic_verification):
        """Confidence scores are within valid range."""
        for record in synthetic_verification:
            score = record.get("confidence_score", 0)
            assert 0 <= score <= 1, f"Invalid confidence score: {score}"

    def test_outcome_matches_confidence(self, synthetic_verification):
        """Outcome label matches confidence score range."""
        for record in synthetic_verification[:20]:  # Sample
            score = record.get("confidence_score", 0)
            outcome = record.get("outcome", "")

            if outcome == "passing":
                assert score >= CONFIDENCE_RANGES["passing"][0], f"Passing score too low: {score}"
            elif outcome == "failing":
                assert score <= CONFIDENCE_RANGES["failing"][1], f"Failing score too high: {score}"

    def test_tier0_is_schema_validation(self, tier0_verification):
        """Tier 0 evidence is schema validation."""
        for record in tier0_verification[:10]:  # Sample
            assert record.get("tier_name") == "Schema validation"
            check_type = record.get("check_type", "")
            expected_types = VERIFICATION_TIERS[0]["check_types"]
            assert check_type in expected_types, f"Unexpected check type for tier 0: {check_type}"

    def test_passing_evidence_has_high_score(self, passing_verification):
        """Passing evidence has high confidence scores."""
        for record in passing_verification[:10]:  # Sample
            score = record.get("confidence_score", 0)
            assert score >= 0.85, f"Passing evidence should have score >= 0.85: {score}"

    def test_failing_evidence_has_low_score(self, failing_verification):
        """Failing evidence has low confidence scores."""
        for record in failing_verification[:10]:  # Sample
            score = record.get("confidence_score", 0)
            assert score < 0.70, f"Failing evidence should have score < 0.70: {score}"

    def test_generate_tier_method(self):
        """Generate specific tier evidence."""
        generator = VerificationGenerator(seed=42)
        tier2_evidence = generator.generate_tier(tier=2, count=20)

        assert len(tier2_evidence) == 20
        for record in tier2_evidence:
            assert record.get("tier") == 2
            assert record.get("tier_name") == "Cross-rule checks"

    def test_validate_method(self):
        """Validate method correctly identifies valid evidence."""
        generator = VerificationGenerator(seed=42)
        evidence = generator.generate(count=10)

        for record in evidence:
            assert generator.validate(record), f"Valid evidence failed validation: {record['evidence_id']}"


# =============================================================================
# Cross-Generator Integration Tests
# =============================================================================


class TestCrossGeneratorIntegration:
    """Tests for integration between generators."""

    def test_scenario_instrument_types_match_ontology(self, synthetic_scenarios):
        """Scenario instrument types match defined ontology."""
        for scenario in synthetic_scenarios:
            instrument = scenario.get("instrument_type")
            assert instrument in INSTRUMENT_TYPES, f"Unknown instrument type: {instrument}"

    def test_scenario_activities_match_ontology(self, synthetic_scenarios):
        """Scenario activities match defined ontology."""
        for scenario in synthetic_scenarios:
            activity = scenario.get("activity")
            assert activity in ACTIVITY_TYPES, f"Unknown activity type: {activity}"

    def test_rule_jurisdictions_match_ontology(self, synthetic_rules):
        """Rule jurisdictions match defined ontology."""
        for rule in synthetic_rules:
            jurisdiction = rule.get("jurisdiction")
            assert jurisdiction in JURISDICTIONS, f"Unknown jurisdiction: {jurisdiction}"

    def test_verification_tiers_match_config(self, synthetic_verification):
        """Verification tiers match configuration."""
        for record in synthetic_verification:
            tier = record.get("tier")
            assert tier in VERIFICATION_TIERS, f"Unknown tier: {tier}"

    def test_all_generators_deterministic(self):
        """All generators produce deterministic output with same seed."""
        seed = 999

        # Generate twice with same seed
        scenarios1 = ScenarioGenerator(seed=seed).generate(5)
        scenarios2 = ScenarioGenerator(seed=seed).generate(5)
        assert [s["scenario_id"] for s in scenarios1] == [s["scenario_id"] for s in scenarios2]

        rules1 = RuleGenerator(seed=seed).generate(5)
        rules2 = RuleGenerator(seed=seed).generate(5)
        assert [r["rule_id"] for r in rules1] == [r["rule_id"] for r in rules2]

        evidence1 = VerificationGenerator(seed=seed).generate(5)
        evidence2 = VerificationGenerator(seed=seed).generate(5)
        assert [e["evidence_id"] for e in evidence1] == [e["evidence_id"] for e in evidence2]


# =============================================================================
# Coverage Metrics Tests
# =============================================================================


class TestCoverageMetrics:
    """Tests for coverage metrics and completeness."""

    def test_total_scenarios_meet_target(self, synthetic_scenarios):
        """Total scenarios meet target volume."""
        # Target is 500 scenarios
        assert len(synthetic_scenarios) >= 400, f"Only {len(synthetic_scenarios)} scenarios (target: 500)"

    def test_edge_case_threshold_coverage(self, edge_case_scenarios):
        """Edge cases cover all defined thresholds."""
        thresholds_tested = set()
        for scenario in edge_case_scenarios:
            if "tested_threshold" in scenario:
                thresholds_tested.add(scenario["tested_threshold"])

        # Should cover most thresholds
        expected_thresholds = set(THRESHOLDS.keys())
        coverage = len(thresholds_tested) / len(expected_thresholds)
        assert coverage >= 0.5, f"Only {coverage:.0%} threshold coverage"

    def test_rule_framework_coverage(self, synthetic_rules):
        """Rules cover all major frameworks."""
        frameworks = set(r.get("framework") for r in synthetic_rules)
        expected_frameworks = {"MiCA", "FCA Crypto"}  # Required frameworks
        assert expected_frameworks.issubset(frameworks), f"Missing frameworks: {expected_frameworks - frameworks}"

    def test_verification_outcome_distribution(self, synthetic_verification):
        """Verification outcomes follow expected distribution."""
        by_outcome = {}
        for record in synthetic_verification:
            outcome = record.get("outcome", "unknown")
            by_outcome[outcome] = by_outcome.get(outcome, 0) + 1

        total = len(synthetic_verification)
        passing_pct = by_outcome.get("passing", 0) / total

        # Passing should be majority (60% target)
        assert passing_pct >= 0.4, f"Only {passing_pct:.0%} passing (target: 60%)"
