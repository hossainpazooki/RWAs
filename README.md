# Droit — Regulatory Q&A System

A computational law platform for tokenized real-world assets (RWAs). Transforms regulatory documents into executable knowledge through ontology extraction, declarative rules, and traceable decision logic.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3: INTERFACE                                         │
│  • /ask  — Factual Q&A (RAG)                                │
│  • /decide — Decision queries (rule engine)                 │
│  • /rules — Inspect loaded rules                            │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2: REASONING                                         │
│  • Decision Engine evaluates rules against scenarios        │
│  • Produces traceable logic paths                           │
│  • Returns obligations with source pinpoints                │
└─────────────────────────────────────────────────────────────┘
                              ↑
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: KNOWLEDGE MODEL                                   │
│  • Typed ontology: Provision, Obligation, Actor, Instrument │
│  • Relations: IMPOSES_OBLIGATION_ON, PERMITS, PROHIBITS     │
│  • Declarative rules in YAML DSL                            │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Create virtual environment
python -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\activate

# Activate (Unix)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn backend.main:app --reload

# Run tests
pytest
```

## API Endpoints

### POST /ask
Factual Q&A using RAG retrieval.

```json
{
  "question": "What does Article 42 say about reserves?"
}
```

### POST /decide
Evaluate a scenario against regulatory rules.

```json
{
  "instrument_type": "stablecoin",
  "activity": "public_offer",
  "authorized": false,
  "jurisdiction": "EU"
}
```

Returns decision with full trace:

```json
{
  "decision": "not_authorized",
  "trace": [
    {"node": "check_instrument", "condition": "instrument_type in [art, stablecoin]", "result": true},
    {"node": "check_authorization", "condition": "authorized == true", "result": false}
  ],
  "obligations": [
    {"id": "obtain_auth_art21", "source": "MiCA Art. 36(1), p. 65"}
  ]
}
```

### GET /rules
List all loaded rules with metadata.

## Project Structure

```
backend/
├── ontology/    # Domain types (Provision, Obligation, Actor, etc.)
├── rules/       # YAML rule files + decision engine
├── rag/         # Retrieval (BM25 + optional vector search)
└── api/         # FastAPI routes
docs/
├── knowledge_model.md   # Ontology documentation
└── rule_dsl.md          # Rule DSL specification
tests/           # Test suite
```

## Optional ML Features

For enhanced retrieval with vector search:

```bash
pip install -r requirements-ml.txt
```

The system gracefully degrades to BM25-only retrieval if ML dependencies are unavailable.

## Documentation

- [Knowledge Model](docs/knowledge_model.md) — Ontology design and worked examples
- [Rule DSL](docs/rule_dsl.md) — YAML rule specification
