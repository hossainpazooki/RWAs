"""Rule generator for expanded regulatory coverage.

Generates YAML-compatible rule definitions following the existing structure:
- MiCA (EU): 15-20 new rules (High accuracy - enacted law)
- FCA (UK): 12-15 new rules (High accuracy - enacted rules)
- GENIUS Act (US): 10-15 new rules (Medium accuracy - proposed bill)
- RWA Tokenization: 10-15 new rules (Low accuracy - hypothetical)

Complexity levels:
- Simple (30%): Single condition -> single outcome
- Medium (50%): 2-3 nested conditions
- Complex (20%): Multi-branch decision trees
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from backend.synthetic_data.base import BaseGenerator
from backend.synthetic_data.config import (
    RULE_DISTRIBUTIONS,
    RULE_COMPLEXITY,
    INSTRUMENT_TYPES,
    ACTIVITY_TYPES,
    DECISION_OUTCOMES,
)


class RuleGenerator(BaseGenerator):
    """Generator for synthetic regulatory rules.

    Usage:
        generator = RuleGenerator(seed=42)
        rules = generator.generate(count=50)

        # Generate for specific framework
        mica_rules = generator.generate_framework("mica_eu", count=15)
    """

    def generate(self, count: int) -> list[dict[str, Any]]:
        """Generate synthetic rules distributed across frameworks.

        Args:
            count: Total number of rules to generate

        Returns:
            List of rule dictionaries (YAML-compatible)
        """
        rules = []

        # Calculate distribution based on framework ranges
        total_min = sum(cfg["count_range"][0] for cfg in RULE_DISTRIBUTIONS.values())
        scale = count / total_min

        for framework_key, config in RULE_DISTRIBUTIONS.items():
            min_count, max_count = config["count_range"]
            framework_count = max(1, int(min_count * scale))
            framework_rules = self.generate_framework(framework_key, framework_count)
            rules.extend(framework_rules)

        return self._shuffle(rules)[:count]

    def generate_framework(
        self, framework_key: str, count: int
    ) -> list[dict[str, Any]]:
        """Generate rules for a specific regulatory framework.

        Args:
            framework_key: One of mica_eu, fca_uk, genius_us, rwa_tokenization
            count: Number of rules to generate

        Returns:
            List of rule dictionaries
        """
        if framework_key not in RULE_DISTRIBUTIONS:
            raise ValueError(f"Unknown framework: {framework_key}")

        config = RULE_DISTRIBUTIONS[framework_key]
        rules = []

        for i in range(count):
            # Select article and complexity
            article = self._choice(config["articles"])
            complexity = self._select_complexity()

            rule = self._generate_rule(
                framework_key=framework_key,
                config=config,
                article=article,
                complexity=complexity,
                index=i,
            )
            rules.append(rule)

        return rules

    def validate(self, item: dict[str, Any]) -> bool:
        """Validate a rule has required fields.

        Args:
            item: Rule dictionary

        Returns:
            True if valid
        """
        required_fields = [
            "rule_id",
            "version",
            "jurisdiction",
            "source",
            "decision_tree",
        ]
        return all(field in item for field in required_fields)

    # =========================================================================
    # Rule Generation
    # =========================================================================

    def _generate_rule(
        self,
        framework_key: str,
        config: dict[str, Any],
        article: str,
        complexity: str,
        index: int,
    ) -> dict[str, Any]:
        """Generate a single rule."""
        # Parse article for naming
        article_id = self._parse_article_id(article)

        # Select activity for this rule
        activity = self._choice(ACTIVITY_TYPES[:6])

        # Generate rule_id
        framework_prefix = framework_key.split("_")[0]
        rule_id = f"{framework_prefix}_{article_id}_{activity}_{index:02d}"

        # Generate decision tree based on complexity
        decision_tree = self._generate_decision_tree(complexity, activity)

        # Select effective date based on framework
        effective_date = self._get_effective_date(framework_key)

        rule = {
            "rule_id": rule_id,
            "version": "1.0",
            "effective_from": effective_date,
            "jurisdiction": config["jurisdiction"],
            "framework": config["framework"],
            "accuracy_level": config["accuracy"],
            "description": f"{config['framework']} {article} - {activity.replace('_', ' ').title()}",
            # Applicability
            "applies_if": self._generate_applies_if(activity),
            # Decision logic
            "decision_tree": decision_tree,
            # Source reference
            "source": {
                "document_id": config["document_id"],
                "article": article,
                "text_excerpt": self._generate_excerpt(article, activity),
            },
            # Metadata
            "tags": self._generate_tags(framework_key, activity),
            "complexity": complexity,
        }

        # Add note for illustrative rules
        if config.get("note"):
            rule["note"] = config["note"]

        return rule

    def _select_complexity(self) -> str:
        """Select complexity level based on distribution."""
        levels = list(RULE_COMPLEXITY.keys())
        weights = [RULE_COMPLEXITY[level]["percentage"] for level in levels]
        return self._weighted_choice(levels, weights)

    def _parse_article_id(self, article: str) -> str:
        """Extract article identifier for rule naming."""
        # Handle formats like "Art. 36 (Authorization)" or "COBS 4.12A.1 (Scope)"
        article_lower = article.lower()

        if "art." in article_lower:
            # Extract number after "Art."
            parts = article.split()
            for i, part in enumerate(parts):
                if part.lower() == "art." and i + 1 < len(parts):
                    return f"art{parts[i + 1].rstrip('(').strip()}"

        if "cobs" in article_lower or "sec." in article_lower:
            # Use first two parts
            parts = article.split()
            if len(parts) >= 2:
                return f"{parts[0].lower()}_{parts[1].lower().replace('.', '_')}"

        # Default: use first 10 chars, cleaned
        return article[:10].lower().replace(" ", "_").replace(".", "_")

    def _get_effective_date(self, framework_key: str) -> str:
        """Get effective date based on framework."""
        dates = {
            "mica_eu": "2024-06-30",
            "fca_uk": "2024-01-08",
            "genius_us": "2025-07-01",  # Hypothetical
            "rwa_tokenization": "2025-12-01",  # Hypothetical
        }
        return dates.get(framework_key, "2024-01-01")

    # =========================================================================
    # Decision Tree Generation
    # =========================================================================

    def _generate_decision_tree(
        self, complexity: str, activity: str
    ) -> dict[str, Any]:
        """Generate decision tree based on complexity level."""
        config = RULE_COMPLEXITY[complexity]
        max_depth = config["max_depth"]

        return self._build_tree_node(
            node_id="root",
            depth=0,
            max_depth=max_depth,
            activity=activity,
        )

    def _build_tree_node(
        self,
        node_id: str,
        depth: int,
        max_depth: int,
        activity: str,
    ) -> dict[str, Any]:
        """Recursively build decision tree nodes."""
        # Base case: leaf node
        if depth >= max_depth or self._probability(0.3):
            return self._generate_leaf_node(node_id)

        # Generate condition node
        condition = self._generate_condition(activity, depth)

        node = {
            "node_id": node_id,
            "condition": condition["expression"],
            "condition_description": condition["description"],
            "true_branch": self._build_tree_node(
                f"{node_id}_t",
                depth + 1,
                max_depth,
                activity,
            ),
            "false_branch": self._build_tree_node(
                f"{node_id}_f",
                depth + 1,
                max_depth,
                activity,
            ),
        }

        return node

    def _generate_leaf_node(self, node_id: str) -> dict[str, Any]:
        """Generate a leaf (decision) node."""
        outcome = self._choice(DECISION_OUTCOMES)

        # Generate obligations for certain outcomes
        obligations = []
        if outcome in ["authorized", "compliant", "requires_authorization"]:
            num_obligations = self._randint(0, 2)
            for i in range(num_obligations):
                obligations.append({
                    "id": f"obl_{node_id}_{i}",
                    "description": self._generate_obligation_text(),
                    "deadline": self._choice(["30 days", "60 days", "90 days", "ongoing"]),
                })

        return {
            "node_id": node_id,
            "decision": outcome,
            "obligations": obligations,
        }

    def _generate_condition(self, activity: str, depth: int) -> dict[str, Any]:
        """Generate a condition based on activity and depth."""
        conditions = [
            {
                "expression": "instrument_type in ['art', 'emt']",
                "description": "Is asset-referenced or e-money token",
            },
            {
                "expression": "has_authorization == true",
                "description": "Entity has required authorization",
            },
            {
                "expression": "is_credit_institution == true",
                "description": "Entity is a credit institution",
            },
            {
                "expression": "reserve_ratio >= 1.0",
                "description": "Reserve assets meet 100% backing requirement",
            },
            {
                "expression": "has_whitepaper == true",
                "description": "Whitepaper has been submitted",
            },
            {
                "expression": "reserve_value_eur >= 5000000",
                "description": "Reserve value exceeds significance threshold",
            },
            {
                "expression": "investor_types contains 'retail'",
                "description": "Offering targets retail investors",
            },
            {
                "expression": "has_prescribed_risk_warning == true",
                "description": "Required risk warning is present",
            },
            {
                "expression": "is_significant_art == true",
                "description": "Token classified as significant ART",
            },
            {
                "expression": f"activity == '{activity}'",
                "description": f"Activity is {activity.replace('_', ' ')}",
            },
        ]

        return self._choice(conditions)

    def _generate_obligation_text(self) -> str:
        """Generate obligation description text."""
        obligations = [
            "Submit quarterly reserve attestation report",
            "Maintain segregated reserve assets",
            "Notify competent authority of material changes",
            "Update whitepaper within 20 days of material changes",
            "Implement redemption procedures for token holders",
            "Conduct regular stress testing of reserves",
            "Maintain adequate capital requirements",
            "Implement robust governance arrangements",
            "Ensure business continuity arrangements",
            "Report suspicious transactions",
        ]
        return self._choice(obligations)

    # =========================================================================
    # Applies-If Generation
    # =========================================================================

    def _generate_applies_if(self, activity: str) -> dict[str, Any]:
        """Generate applies_if condition block."""
        # Select 1-3 conditions
        num_conditions = self._randint(1, 3)

        conditions = []

        # Always include activity condition
        conditions.append({
            "field": "activity",
            "operator": "==",
            "value": activity,
        })

        # Add instrument type condition
        if self._probability(0.7):
            instruments = self._sample(INSTRUMENT_TYPES[:4], k=self._randint(1, 3))
            conditions.append({
                "field": "instrument_type",
                "operator": "in",
                "value": instruments,
            })

        # Add jurisdiction condition
        if self._probability(0.5):
            conditions.append({
                "field": "jurisdiction",
                "operator": "==",
                "value": self._choice(["EU", "UK", "US"]),
            })

        return {"all": conditions}

    # =========================================================================
    # Metadata Generation
    # =========================================================================

    def _generate_tags(self, framework_key: str, activity: str) -> list[str]:
        """Generate tags for rule categorization."""
        tags = [framework_key.replace("_", "-")]

        # Add activity tag
        tags.append(activity.replace("_", "-"))

        # Add framework-specific tags
        framework_tags = {
            "mica_eu": ["crypto", "regulation", "eu-law"],
            "fca_uk": ["crypto", "financial-promotion", "uk-regulation"],
            "genius_us": ["stablecoin", "proposed", "us-regulation"],
            "rwa_tokenization": ["rwa", "tokenization", "hypothetical"],
        }
        tags.extend(self._sample(framework_tags.get(framework_key, []), k=2))

        return list(set(tags))

    def _generate_excerpt(self, article: str, activity: str) -> str:
        """Generate a representative text excerpt."""
        excerpts = {
            "public_offer": f"No person shall make a public offer of the relevant crypto-asset unless authorized ({article}).",
            "admission_to_trading": f"Admission to trading requires prior approval from the competent authority ({article}).",
            "custody": f"Custody services shall only be provided by authorized entities ({article}).",
            "exchange": f"Exchange services require appropriate licensing under this regulation ({article}).",
            "transfer": f"Transfers must comply with applicable AML requirements ({article}).",
        }
        return excerpts.get(
            activity,
            f"Requirements under {article} apply to {activity.replace('_', ' ')}.",
        )


# =============================================================================
# CLI for Standalone Execution
# =============================================================================

if __name__ == "__main__":
    import argparse
    import json
    import yaml

    parser = argparse.ArgumentParser(description="Generate synthetic rules")
    parser.add_argument("--count", type=int, default=50, help="Number of rules")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--framework", type=str, help="Specific framework to generate")
    parser.add_argument("--validate", action="store_true", help="Validate generated rules")
    parser.add_argument("--output", type=str, help="Output file (JSON or YAML)")
    parser.add_argument("--format", choices=["json", "yaml"], default="yaml", help="Output format")

    args = parser.parse_args()

    generator = RuleGenerator(seed=args.seed)

    if args.framework:
        rules = generator.generate_framework(args.framework, args.count)
    else:
        rules = generator.generate(args.count)

    if args.validate:
        valid_count = sum(1 for r in rules if generator.validate(r))
        print(f"Generated {len(rules)} rules, {valid_count} valid")
    else:
        print(f"Generated {len(rules)} rules")

    # Print distribution
    by_framework = {}
    for rule in rules:
        fw = rule.get("framework", "unknown")
        by_framework[fw] = by_framework.get(fw, 0) + 1
    print(f"Distribution: {by_framework}")

    if args.output:
        with open(args.output, "w") as f:
            if args.format == "yaml":
                yaml.dump(rules, f, default_flow_style=False, sort_keys=False)
            else:
                json.dump(rules, f, indent=2, default=str)
        print(f"Saved to {args.output}")
    else:
        # Print sample
        sample_rule = rules[0] if rules else {}
        if args.format == "yaml":
            print(yaml.dump(sample_rule, default_flow_style=False))
        else:
            print(json.dumps(sample_rule, indent=2, default=str))
