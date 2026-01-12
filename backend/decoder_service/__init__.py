"""Decoder Service - Regulatory explanation and counterfactual analysis."""

from backend.decoder_service.app.services.decoder import DecoderService
from backend.decoder_service.app.services.counterfactual import CounterfactualEngine
from backend.decoder_service.app.services.citations import CitationInjector
from backend.decoder_service.app.services.templates import TemplateRegistry
from backend.decoder_service.app.services.delta import DeltaAnalyzer
from backend.decoder_service.app.services.schemas import (
    ExplanationTier,
    Citation,
    Explanation,
    DecoderRequest,
    DecoderResponse,
    CounterfactualRequest,
    CounterfactualResponse,
    ScenarioType,
    Scenario as CounterfactualScenario,
    DeltaAnalysis,
    ComparisonMatrix,
)

__all__ = [
    "DecoderService",
    "CounterfactualEngine",
    "CitationInjector",
    "TemplateRegistry",
    "DeltaAnalyzer",
    "ExplanationTier",
    "Citation",
    "Explanation",
    "DecoderRequest",
    "DecoderResponse",
    "CounterfactualRequest",
    "CounterfactualResponse",
    "ScenarioType",
    "CounterfactualScenario",
    "DeltaAnalysis",
    "ComparisonMatrix",
]
