"""Ontology module - Domain types for regulatory knowledge modeling."""

from .types import (
    Provision,
    ProvisionType,
    Obligation,
    Permission,
    Prohibition,
    Actor,
    ActorType,
    Instrument,
    InstrumentType,
    Activity,
    ActivityType,
    Condition,
    ConditionGroup,
    SourceReference,
    NormativeContent,
)
from .relations import Relation, RelationType
from .scenario import Scenario

__all__ = [
    "Provision",
    "ProvisionType",
    "Obligation",
    "Permission",
    "Prohibition",
    "Actor",
    "ActorType",
    "Instrument",
    "InstrumentType",
    "Activity",
    "ActivityType",
    "Condition",
    "ConditionGroup",
    "SourceReference",
    "NormativeContent",
    "Relation",
    "RelationType",
    "Scenario",
]
