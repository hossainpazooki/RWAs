"""Decoder service implementations."""

from .decoder import DecoderService
from .counterfactual import CounterfactualEngine
from .citations import CitationInjector
from .templates import TemplateRegistry
from .delta import DeltaAnalyzer
from .schemas import (
    ExplanationTier,
    Citation,
    Explanation,
    ExplanationSummary,
    AuditInfo,
    DecoderRequest,
    DecoderResponse,
    CounterfactualRequest,
    CounterfactualResponse,
    CounterfactualExplanation,
    ScenarioType,
    Scenario,
    OutcomeSummary,
    DeltaAnalysis,
    ComparisonRequest,
    ComparisonMatrix,
    MatrixInsight,
    ExplanationTemplate,
    TemplateSection,
    TemplateVariable,
    CitationSlot,
)

__all__ = [
    # Services
    "DecoderService",
    "CounterfactualEngine",
    "CitationInjector",
    "TemplateRegistry",
    "DeltaAnalyzer",
    # Enums
    "ExplanationTier",
    "ScenarioType",
    # Decoder schemas
    "Citation",
    "Explanation",
    "ExplanationSummary",
    "AuditInfo",
    "DecoderRequest",
    "DecoderResponse",
    # Counterfactual schemas
    "CounterfactualRequest",
    "CounterfactualResponse",
    "CounterfactualExplanation",
    "Scenario",
    "OutcomeSummary",
    "DeltaAnalysis",
    "ComparisonRequest",
    "ComparisonMatrix",
    "MatrixInsight",
    # Template schemas
    "ExplanationTemplate",
    "TemplateSection",
    "TemplateVariable",
    "CitationSlot",
]
