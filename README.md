# Regulatory Knowledge Engineering Workbench

A computational law platform for MiCA, RWA tokenization, and stablecoin frameworks. Transforms regulatory documents into executable rules with traceable decision logic.

**Live Demo:** [pazooki.streamlit.app](https://pazooki.streamlit.app)

## Architecture

```mermaid
%%{init: {
  "flowchart": {
    "nodeSpacing": 16,
    "rankSpacing": 22,
    "curve": "basis"
  }
}}%%

flowchart LR

subgraph Input[" "]
  direction TB
  DSL[YAML Rules]
  Corpus[Legal Corpus]
  DSL ~~~ Corpus
end

subgraph MLWorkflows["ML workflows"]
  direction LR

  subgraph EmbeddingService["rule_embedding_service/"]
    direction TB
    GEN[Generator] --> EMB4[4-Type Embeddings]
    EMB4 --> VS[Vector Search]
    EMB4 -.- SEM[semantic]
    EMB4 -.- STR[structural]
    EMB4 -.- ENT[entity]
    EMB4 -.- LEG[legal]
    GEN --> GEMB[Graph Embedding]
    GEMB --> N2V[Node2Vec]
    VS ~~~ N2V
  end

  subgraph VerifyService["verification_service/"]
    direction TB
    CE[Consistency Engine]
    CE --> T0[Tier 0: Schema]
    CE --> T1[Tier 1: Semantic]
    CE --> T2[Tier 2: Cross-rule]
    CE --> T3[Tier 3: Temporal]
    CE --> T4[Tier 4: External]
  end

  subgraph RAGService["rag_service/"]
    direction TB
    BM25[BM25 Index]
    BM25 --> CTX[Context Helpers]
  end

  subgraph DecoderService["decoder_service/"]
    direction TB
    DEC[Decoder] --> TMPL[Templates]
    DEC --> CIT[Citations]
    DEC --> CF[Counterfactual]
    CF --> DELTA[Delta]
    TMPL ~~~ CIT
    CIT ~~~ CF
  end
end

subgraph CoreEngine["Core rule execution"]
  direction LR

  subgraph CoreServices["core/"]
    direction TB
    ONT[Ontology]
    TYPES[Types & Enums]
    RDSL[Rule DSL]
    TRC[Trace & Consistency]
    ONT --> TYPES --> RDSL
    RDSL ~~~ TRC
  end

  subgraph RuleService["rule_service/"]
    direction TB
    VER[Version Service]
    DE[Decision Engine]
    VER ~~~ DE

    subgraph Jurisdiction["jurisdiction/"]
      JR[Resolver] --> JE[Evaluator]
      JE --> CD[Conflicts] --> PS[Pathway]
    end
  end

  subgraph DatabaseService["database_service/"]
    direction LR

    subgraph TemporalEngine["temporal_engine/"]
      direction TB
      VREPO[Version Repo]
      EREPO[Event Repo]
      VREPO ~~~ EREPO
    end

    subgraph RetrievalEngine["retrieval_engine/"]
      direction TB
      COMP[Compiler] --> IDX[Premise Index]
      COMP --> CACHE[IR Cache]
      IDX ~~~ CACHE
    end

    subgraph Stores["stores/"]
      direction TB
      JCFG[Jurisdiction Config]
      ESTORE[Embedding Store]
      GSTORE[Graph Store]
      JCFG ~~~ ESTORE
      ESTORE ~~~ GSTORE
    end
  end
end

subgraph Output[" "]
  direction TB
  subgraph API["FastAPI"]
    direction TB
    R1["/decide"]
    R2["/rules"]
    R3["/verify"]
    R4["/search/*"]
    R5["/navigate"]
    R6["/embeddings"]
    R7["/graph"]
    R8["/decoder"]
    R9["/counterfactual"]
  end
  ST[Streamlit UI]
  R1 -.-> ST
  R2 -.-> ST
  R3 -.-> ST
  R4 -.-> ST
  R5 -.-> ST
  R8 -.-> ST
  R9 -.-> ST
end

%% YAML rules derived from DSL layer
RDSL -.-> DSL

%% Main flows
DSL --> VER --> VREPO
VER --> EREPO
DSL --> COMP
DSL --> GEN

VREPO --> DE --> JE
JR <--> JCFG
PS <--> JCFG

Corpus --> CE
Corpus --> BM25

VS --> R4
VS <--> ESTORE
N2V <--> GSTORE
ESTORE --> R6
GSTORE --> R7

DE --> R1
PS --> R5
CE --> R3
CTX --> R2

%% Decoder Service connections
DE --> DEC
BM25 --> CIT
VS --> TMPL
DEC --> R8
CF --> R9

%% Cross-subgraph packing
GEN ~~~ CE
CE ~~~ BM25
VER ~~~ COMP
DE ~~~ GEN
VREPO ~~~ COMP
ONT ~~~ GEN
RDSL ~~~ CE
BM25 ~~~ DEC
```

## Project Structure

```
backend/
├── core/                    # Shared infrastructure
│   ├── config.py            # Settings & feature flags
│   ├── database.py          # SQLModel ORM utilities
│   ├── ontology/            # Domain types (Actor, Instrument, Provision)
│   ├── visualization/       # Tree rendering (Graphviz, Mermaid)
│   └── api/                 # FastAPI routers
│
├── rule_service/            # Rule management & evaluation
│   ├── data/                # YAML rule packs (MiCA, FCA, GENIUS)
│   └── app/services/
│       ├── loader.py        # YAML parsing
│       ├── engine.py        # Decision engine
│       └── jurisdiction/    # Multi-jurisdiction (resolver, evaluator, conflicts)
│
├── database_service/        # Persistence & compilation
│   └── app/services/
│       ├── compiler/        # YAML → IR compilation
│       └── runtime/         # IR cache & execution
│
├── verification_service/    # Semantic consistency
│   └── app/services/        # Tier 0-4 consistency checks
│
├── analytics_service/       # Error patterns & drift
│   └── app/services/        # Pattern analysis, drift detection
│
├── rag_service/             # Retrieval-augmented context
│   └── app/services/        # BM25 index, context helpers
│
└── rule_embedding_service/  # Vector embeddings & similarity search
    └── app/services/
        ├── models.py        # RuleEmbedding, EmbeddingType
        ├── generator.py     # 4-type embedding generation
        └── service.py       # CRUD + vector search

frontend/
├── Home.py                  # Landing page
└── pages/
    ├── 1_KE_Workbench.py    # Rule verification & review
    ├── 2_Production_Demo.py # IR compilation & benchmarks
    └── 3_Navigator.py       # Cross-border compliance

data/legal/                  # Legal corpus (MiCA, FCA, GENIUS Act)
docs/                        # Design documentation
```

## Regulatory Frameworks

| Framework | Jurisdiction | Status |
|-----------|--------------|--------|
| MiCA | EU | Modeled (9 rules) |
| FCA Crypto | UK | Modeled (5 rules) |
| GENIUS Act | US | Illustrative (6 rules) |
| RWA Tokenization | EU | Illustrative (2 rules) |

## Rule Embeddings

The system generates 4 types of vector embeddings per rule for multi-faceted similarity search:

| Type | Source | Use Case |
|------|--------|----------|
| **Semantic** | Name, description, decision explanation | Natural language search |
| **Structural** | Conditions, operators, decision logic | Find structurally similar rules |
| **Entity** | Field names, operators | Find rules using same data fields |
| **Legal** | Citations, document IDs | Find rules from same legal sources |

- Uses `sentence-transformers` (all-MiniLM-L6-v2) for dense embeddings
- Falls back to hash-based vectors when ML unavailable
- SQLite: JSON arrays; PostgreSQL: pgvector ready

## Documentation

- [Knowledge Model](docs/knowledge_model.md) — Ontology design
- [Rule DSL](docs/rule_dsl.md) — YAML rule specification
- [Engine Design](docs/engine_design.md) — Architecture details
- [Embedding Service](docs/embedding_service.md) — Vector search design

## Disclaimer

Research/demo project, not legal advice. Rules are interpretive models—consult qualified legal counsel for compliance decisions.

## License

MIT License. See [LICENSE](LICENSE).

---

Built with [Claude Code](https://claude.ai/code)
