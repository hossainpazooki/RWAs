# Synthetic Data Strategy

## Overview

This document describes the synthetic data generation strategy for expanding test coverage from ~30 scenarios to 500, and from ~24 rules to 75-100 across MiCA, FCA, GENIUS Act, and RWA frameworks.

## Regulatory Accuracy Assessment

| Framework | Status | Accuracy | Notes |
|-----------|--------|----------|-------|
| **MiCA (EU)** | Enacted law | **High** | Based on Regulation (EU) 2023/1114, effective June 2024 |
| **FCA Crypto (UK)** | Enacted rules | **High** | Based on PS22/10, COBS 4.12A, real FCA handbook |
| **GENIUS Act (US)** | Proposed bill | **Medium** | Illustrative based on S.394 proposal |
| **RWA (EU)** | Hypothetical | **Low** | Explicitly marked "hypothetical rwa_eu_2025" |

**Implication:** Synthetic rule generation prioritizes MiCA/FCA (enacted law) and clearly labels GENIUS/RWA rules as illustrative.

## Database Storage Requirements

### Per-Record Sizes

| Record Type | Avg Size |
|-------------|----------|
| RuleRecord | ~3 KB |
| RuleVersionRecord | ~3 KB |
| RuleEventRecord | ~700 B |
| VerificationResultRecord | ~200 B |
| VerificationEvidenceRecord | ~450 B |
| EmbeddingRecord | ~1.7 KB |
| GraphNode | ~300 B |
| GraphEdge | ~200 B |
| Scenario (fixture) | ~300 B |

### Projected Storage (Target Volumes)

| Data Type | Count | Size |
|-----------|-------|------|
| Rules | 100 | 300 KB |
| Rule Versions (2/rule) | 200 | 600 KB |
| Rule Events (3/rule) | 300 | 210 KB |
| Verification Results | 200 | 40 KB |
| Verification Evidence | 400 | 180 KB |
| Embeddings (5 types x 100 rules) | 500 | 850 KB |
| Graph Nodes (5/rule) | 500 | 150 KB |
| Graph Edges (10/rule) | 1,000 | 200 KB |
| Scenarios | 500 | 150 KB |
| **Total** | - | **~2.7 MB** |

**Railway Compatibility:** Free tier (500 MB) = 0.5% utilization

## Package Structure

```
backend/synthetic_data/
├── __init__.py              # Package exports
├── base.py                  # BaseGenerator class
├── config.py                # Configuration and constants
├── scenario_generator.py    # ScenarioGenerator
├── rule_generator.py        # RuleGenerator
└── verification_generator.py # VerificationGenerator
```

## Generators

### ScenarioGenerator

Generates test scenarios by combining ontology dimensions:

```python
from backend.synthetic_data import ScenarioGenerator

generator = ScenarioGenerator(seed=42)
scenarios = generator.generate(count=500)

# Generate by category
happy_paths = generator.generate_category("happy_path", count=150)
edge_cases = generator.generate_category("edge_case", count=150)
```

**Scenario Categories:**

| Category | Count | Description |
|----------|-------|-------------|
| `happy_path` | 150 | Valid compliant scenarios |
| `edge_case` | 150 | Threshold boundaries |
| `negative` | 100 | Rule violations |
| `cross_border` | 75 | Multi-jurisdiction |
| `temporal` | 25 | Version-dependent |

**Dimensions Covered:**

- `instrument_type`: art, emt, stablecoin, utility_token, etc.
- `activity`: public_offer, admission_to_trading, custody, etc.
- `jurisdiction`: EU, UK, US, CH, SG
- `authorized`: True/False
- `is_significant`: True/False
- `is_credit_institution`: True/False

**Threshold Values Tested:**

```python
THRESHOLDS = {
    "reserve_value_eur": [4_999_999, 5_000_000, 5_000_001],      # Significant ART
    "total_token_value_eur": [999_999, 1_000_000, 100_000_000],  # Issuer tiers
    "reserve_ratio": [0.99, 1.0, 1.01],                          # Reserve requirements
}
```

### RuleGenerator

Generates YAML-compatible rule definitions:

```python
from backend.synthetic_data import RuleGenerator

generator = RuleGenerator(seed=42)
rules = generator.generate(count=50)

# Generate for specific framework
mica_rules = generator.generate_framework("mica_eu", count=15)
```

**Framework Distribution:**

| Framework | Count | Accuracy |
|-----------|-------|----------|
| MiCA (EU) | 15-20 | High |
| FCA (UK) | 12-15 | High |
| GENIUS Act (US) | 10-15 | Medium (illustrative) |
| RWA Tokenization | 10-15 | Low (hypothetical) |

**Complexity Levels:**

| Level | Percentage | Description |
|-------|------------|-------------|
| Simple | 30% | Single condition -> single outcome |
| Medium | 50% | 2-3 nested conditions |
| Complex | 20% | Multi-branch decision trees |

### VerificationGenerator

Generates verification evidence records:

```python
from backend.synthetic_data import VerificationGenerator

generator = VerificationGenerator(seed=42)
evidence = generator.generate(count=200)

# Generate for specific tier
tier0 = generator.generate_tier(tier=0, count=80)
```

**Verification Tiers:**

| Tier | Category | Distribution |
|------|----------|--------------|
| 0 | Schema validation | 40% |
| 1 | Semantic consistency | 25% |
| 2 | Cross-rule checks | 15% |
| 3 | Temporal consistency | 10% |
| 4 | External alignment | 10% |

**Confidence Score Ranges:**

| Outcome | Score Range |
|---------|-------------|
| Passing | 0.85-0.99 |
| Marginal | 0.70-0.84 |
| Failing | 0.40-0.69 |

## Pytest Integration

### Fixtures Available

Session-scoped fixtures (generated once):

```python
@pytest.fixture(scope="session")
def synthetic_scenarios() -> list[dict]:
    """500 scenarios across all categories."""

@pytest.fixture(scope="session")
def synthetic_rules() -> list[dict]:
    """50 rules across all frameworks."""

@pytest.fixture(scope="session")
def synthetic_verification() -> list[dict]:
    """200 evidence records across all tiers."""
```

Category-filtered fixtures:

```python
@pytest.fixture
def happy_path_scenarios(synthetic_scenarios) -> list[dict]:
    """Filter to only happy path scenarios."""

@pytest.fixture
def edge_case_scenarios(synthetic_scenarios) -> list[dict]:
    """Filter to only edge case scenarios."""

@pytest.fixture
def negative_scenarios(synthetic_scenarios) -> list[dict]:
    """Filter to only negative scenarios."""
```

Parametrized fixture for testing across categories:

```python
@pytest.fixture(params=["happy_path", "edge_case", "negative", "cross_border", "temporal"])
def scenario_category(request, synthetic_scenarios) -> list[dict]:
    """Parametrized fixture for all categories."""
```

### Example Test Using Fixtures

```python
def test_decision_engine_handles_edge_cases(decision_engine, edge_case_scenarios):
    """Test decision engine with threshold boundary scenarios."""
    for scenario in edge_case_scenarios[:10]:
        result = decision_engine.evaluate(scenario)
        assert result is not None
        # Verify boundary handling
        if scenario.get("reserve_ratio", 1.0) < 1.0:
            assert result.decision == "non_compliant"
```

## CLI Usage

### Generate Scenarios

```bash
# Generate 100 scenarios
python -m backend.synthetic_data.scenario_generator --count 100 --seed 42

# Generate specific category
python -m backend.synthetic_data.scenario_generator --category edge_case --count 50

# Output to file
python -m backend.synthetic_data.scenario_generator --count 500 --output scenarios.json
```

### Generate Rules

```bash
# Generate 50 rules
python -m backend.synthetic_data.rule_generator --count 50 --seed 42

# Generate for specific framework
python -m backend.synthetic_data.rule_generator --framework mica_eu --count 15

# Output as YAML
python -m backend.synthetic_data.rule_generator --count 50 --format yaml --output rules.yaml
```

### Generate Verification Evidence

```bash
# Generate 100 evidence records
python -m backend.synthetic_data.verification_generator --count 100 --seed 42

# Generate for specific tier
python -m backend.synthetic_data.verification_generator --tier 0 --count 50

# Output to file
python -m backend.synthetic_data.verification_generator --count 200 --output evidence.json
```

## Running Tests

```bash
# Run all synthetic data tests
pytest tests/test_synthetic_coverage.py -v

# Run with coverage
pytest tests/test_synthetic_coverage.py -v --cov=backend/synthetic_data

# Run specific test class
pytest tests/test_synthetic_coverage.py::TestScenarioGenerator -v

# Validate generated data
python -m backend.synthetic_data.scenario_generator --count 100 --validate
python -m backend.synthetic_data.rule_generator --count 50 --validate
```

## Data Volume Targets

| Data Type | Current | Target | Growth |
|-----------|---------|--------|--------|
| Rules | 24 | 75-100 | 3-4x |
| Scenarios | 30 | 500 | 16x |
| Verification Evidence | ~10 | 200 | 20x |
| Ontology Coverage | ~60% | 100% | - |

## Key Design Decisions

1. **Deterministic Generation**: All generators use seeded random for reproducibility
2. **Session-Scoped Fixtures**: Generated once per test session for performance
3. **Accuracy Labels**: Rules clearly labeled as high/medium/low accuracy
4. **Category Filtering**: Easy access to specific scenario types
5. **Ontology Alignment**: Generated data matches `backend/core/ontology/types.py`
6. **YAML Compatibility**: Generated rules match existing rule structure

## Future Enhancements

- [ ] Add embedding generation for synthetic rules
- [ ] Generate graph structures for rule relationships
- [ ] Add cross-jurisdiction conflict scenarios
- [ ] Generate temporal version chains
- [ ] Add natural language variation to rule descriptions
