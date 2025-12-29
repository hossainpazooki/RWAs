# Claude Code Project: Regulatory KE Workbench

## Overview

This repo is a **computational law system** for tokenized real-world assets (RWAs).
It has layered architecture:

- Layer 1–2 (ontology + rule DSL) in **OCaml** under `ocaml/core/`
- Layer 3+ (decision engine, API, RAG) in **Python** under `backend/`

The goal: executable legal logic, traceable decisions, strong typing, and clear documentation.

## Project structure (desired)

- `ocaml/core/`              – OCaml ontology + rule DSL + tests
- `backend/ontology/`        – (optional) Python mirrors of OCaml types if needed
- `backend/rules/`           – YAML rule packs (MiCA etc.) + decision engine
- `backend/rag/`             – retrieval utilities for factual Q&A + rule context
- `backend/verify/`          – semantic consistency engine (Tier 0-4 checks)
- `backend/analytics/`       – error pattern analysis + drift detection
- `backend/visualization/`   – tree adapter for decision tree rendering
- `backend/api/`             – FastAPI endpoints (`/decide`, `/ke/*` internal endpoints)
- `frontend/`                – Streamlit KE dashboard
- `docs/`                    – design docs (`ontology_design.md`, `rule_dsl_design.md`, `engine_design.md`, `knowledge_model.md`)
- `tests/`                   – Python tests for engine/API; OCaml tests live in `ocaml/core/test/`

## Build & development commands

### OCaml (Layers 1–2)

From repo root:

- `cd ocaml`
- `dune build`
- `dune runtest`

The active opam switch is `rwaproject`.

### Python (Layers 3–5)

From repo root:

- Activate venv: `.\.venv\Scripts\activate`
- Install deps: `pip install -r requirements.txt`
- Run tests: `pytest`
- Run API dev server: `uvicorn backend.api.main:app --reload`
- Run KE dashboard: `streamlit run frontend/ke_dashboard.py`

## How Claude Code should behave

- Treat OCaml `ocaml/core/ontology.ml` and `ocaml/core/rule_dsl.ml` as the **source of truth** for the legal ontology and rule schema.
- Keep legal logic in **YAML rule files** under `backend/rules/`, not hard-coded in Python.
- Each layer should be built and tested in isolation:
  - Layer 1: ontology types + docs + OCaml tests
  - Layer 2: rule DSL types + YAML examples + OCaml tests
  - Layer 3: Python decision engine + tests
  - Layer 4: FastAPI API + tests
  - Layer 5: RAG + extra tests
- Update `docs/*.md` whenever we change the ontology, rule DSL, or engine behaviour.
- Prefer small, incremental changes over huge refactors in one go.
