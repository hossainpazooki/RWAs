"""Database service - centralized data access middleware.

Structure:
- temporal_engine/: Version and event repositories for rule lifecycle
- retrieval_engine/: Compiler and runtime for rule execution
- stores/: Embedding, graph, and configuration stores
- repositories/: Core rule and verification repos
"""

from .database import (
    get_db,
    get_db_path,
    set_db_path,
    init_db,
    reset_db,
    get_table_stats,
    seed_jurisdictions,
    init_db_with_seed,
)

from .migration import (
    migrate_yaml_rules,
    sync_rule_to_db,
    load_rules_from_db,
    extract_premise_keys,
    get_migration_status,
)

# Repositories (core CRUD)
from .repositories import RuleRepository, VerificationRepository

# Temporal Engine (versioning & event sourcing)
from .temporal_engine import (
    RuleVersionRepository,
    RuleEventRepository,
    RuleVersionRecord,
    RuleEventRecord,
    RuleEventType,
)

# Retrieval Engine (compiler + runtime)
from .retrieval_engine import (
    # Compiler - IR Types
    RuleCompiler,
    compile_rule,
    compile_rules,
    PremiseIndexBuilder,
    get_premise_index,
    RuleIR,
    CompiledCheck,
    DecisionEntry,
    ObligationSpec,
    # Runtime
    RuleRuntime,
    execute_rule,
    IRCache,
    get_ir_cache,
    reset_ir_cache,
    ExecutionTrace,
    TraceStep,
    DecisionResult,
)

# Stores (embeddings, graphs, configuration)
from .stores import (
    EmbeddingStore,
    GraphStore,
    JurisdictionConfigRepository,
    EmbeddingRecord,
    EmbeddingType,
    GraphNode,
    GraphEdge,
    GraphQuery,
    GraphQueryResult,
)

__all__ = [
    # Database
    "get_db",
    "get_db_path",
    "set_db_path",
    "init_db",
    "reset_db",
    "get_table_stats",
    "seed_jurisdictions",
    "init_db_with_seed",
    # Migration
    "migrate_yaml_rules",
    "sync_rule_to_db",
    "load_rules_from_db",
    "extract_premise_keys",
    "get_migration_status",
    # Repositories
    "RuleRepository",
    "VerificationRepository",
    # Temporal Engine
    "RuleVersionRepository",
    "RuleEventRepository",
    "RuleVersionRecord",
    "RuleEventRecord",
    "RuleEventType",
    # Retrieval Engine - Compiler
    "RuleCompiler",
    "compile_rule",
    "compile_rules",
    "PremiseIndexBuilder",
    "get_premise_index",
    "RuleIR",
    "CompiledCheck",
    "DecisionEntry",
    "ObligationSpec",
    # Retrieval Engine - Runtime
    "RuleRuntime",
    "execute_rule",
    "IRCache",
    "get_ir_cache",
    "reset_ir_cache",
    "ExecutionTrace",
    "TraceStep",
    "DecisionResult",
    # Stores
    "EmbeddingStore",
    "GraphStore",
    "JurisdictionConfigRepository",
    "EmbeddingRecord",
    "EmbeddingType",
    "GraphNode",
    "GraphEdge",
    "GraphQuery",
    "GraphQueryResult",
]
