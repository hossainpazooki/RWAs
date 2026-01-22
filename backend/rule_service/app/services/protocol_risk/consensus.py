"""
Blockchain protocol risk assessment module.

Provides risk scoring for blockchain protocols based on:
- Consensus mechanism characteristics
- Decentralization metrics (Nakamoto coefficient, validator count)
- Settlement finality guarantees
- Operational metrics (TPS, uptime, upgrade history)

Relevant for institutional risk management and regulatory compliance.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ConsensusMechanism(str, Enum):
    """Blockchain consensus mechanisms."""

    POW = "proof_of_work"           # Bitcoin, Litecoin
    POS = "proof_of_stake"          # Ethereum 2.0, Cardano
    DPOS = "delegated_proof_of_stake"  # EOS, Tron
    POA = "proof_of_authority"      # Private/consortium chains
    POH = "proof_of_history"        # Solana (combined with PoS)
    PBFT = "practical_bft"          # Hyperledger, Tendermint
    HYBRID = "hybrid"               # Multiple mechanisms


class SettlementFinality(str, Enum):
    """Settlement finality types for blockchain transactions."""

    PROBABILISTIC = "probabilistic"   # PoW chains - finality increases over time
    DETERMINISTIC = "deterministic"   # BFT-based - instant finality
    ECONOMIC = "economic"             # PoS - finality backed by stake slashing


class RiskTier(str, Enum):
    """Protocol risk tier classification."""

    TIER_1 = "tier_1"  # Institutional grade (Bitcoin, Ethereum)
    TIER_2 = "tier_2"  # Established protocols (Solana, Polygon, Avalanche)
    TIER_3 = "tier_3"  # Emerging protocols (newer L1s, L2s)
    TIER_4 = "tier_4"  # High risk (unproven, centralized)


class ProtocolRiskProfile(BaseModel):
    """
    Protocol metrics for risk assessment.

    Based on quantitative blockchain health indicators used by
    institutional investors and risk managers.
    """

    protocol_id: str = Field(..., description="Protocol identifier (e.g., 'ethereum', 'solana')")
    consensus: ConsensusMechanism
    finality_type: SettlementFinality

    # Decentralization metrics
    validator_count: int = Field(
        ...,
        ge=1,
        description="Number of active validators/miners",
    )
    nakamoto_coefficient: int = Field(
        ...,
        ge=1,
        description="Minimum entities to control 51% of network",
    )
    top_10_stake_pct: float = Field(
        0.0,
        ge=0,
        le=100,
        description="Percentage of stake held by top 10 validators",
    )

    # Performance metrics
    finality_time_seconds: float = Field(
        ...,
        gt=0,
        description="Time to transaction finality in seconds",
    )
    tps_average: float = Field(
        ...,
        gt=0,
        description="Average transactions per second",
    )
    tps_peak: float = Field(
        ...,
        gt=0,
        description="Peak transactions per second observed",
    )

    # Operational metrics
    uptime_30d_pct: float = Field(
        99.9,
        ge=0,
        le=100,
        description="Network uptime percentage over 30 days",
    )
    major_incidents_12m: int = Field(
        0,
        ge=0,
        description="Major incidents (outages, exploits) in past 12 months",
    )

    # Security metrics
    has_bug_bounty: bool = Field(True, description="Active bug bounty program")
    audit_count: int = Field(0, ge=0, description="Number of security audits")
    time_since_last_upgrade_days: int = Field(
        30,
        ge=0,
        description="Days since last protocol upgrade",
    )

    # Economic security (for PoS)
    total_staked_usd: Optional[float] = Field(
        None,
        ge=0,
        description="Total value staked in USD (PoS chains)",
    )
    slashing_enabled: bool = Field(
        True,
        description="Whether validator slashing is enabled",
    )


class ProtocolRiskAssessment(BaseModel):
    """
    Comprehensive protocol risk assessment result.

    Provides individual dimension scores and overall risk tier,
    suitable for institutional risk reporting.
    """

    protocol_id: str
    risk_tier: RiskTier

    # Dimension scores (0-100, higher = better/safer)
    consensus_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Consensus mechanism security score",
    )
    decentralization_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Network decentralization score",
    )
    settlement_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Settlement finality assurance score",
    )
    operational_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Operational reliability score",
    )
    security_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Security posture score",
    )

    # Composite
    overall_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Weighted overall risk score",
    )

    # Risk factors identified
    risk_factors: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)

    # Regulatory considerations
    regulatory_notes: list[str] = Field(default_factory=list)

    # Raw metrics for transparency
    metrics_summary: dict = Field(default_factory=dict)


# Consensus mechanism base scores (out of 100)
CONSENSUS_BASE_SCORES: dict[ConsensusMechanism, float] = {
    ConsensusMechanism.POW: 95.0,      # Battle-tested, highest security
    ConsensusMechanism.POS: 85.0,      # Proven, economic security
    ConsensusMechanism.PBFT: 80.0,     # Deterministic but trust assumptions
    ConsensusMechanism.POH: 75.0,      # Novel, combined with PoS
    ConsensusMechanism.DPOS: 70.0,     # Trade-off: speed vs decentralization
    ConsensusMechanism.POA: 50.0,      # Centralized trust model
    ConsensusMechanism.HYBRID: 75.0,   # Depends on implementation
}

# Finality type adjustments
FINALITY_ADJUSTMENTS: dict[SettlementFinality, float] = {
    SettlementFinality.DETERMINISTIC: 10.0,   # Bonus for instant finality
    SettlementFinality.ECONOMIC: 5.0,         # Moderate bonus
    SettlementFinality.PROBABILISTIC: 0.0,    # Baseline
}


# Default protocol configurations for common chains
PROTOCOL_DEFAULTS: dict[str, dict] = {
    "bitcoin": {
        "consensus": ConsensusMechanism.POW,
        "finality_type": SettlementFinality.PROBABILISTIC,
        "validator_count": 15000,  # Mining pools
        "nakamoto_coefficient": 4,
        "top_10_stake_pct": 85.0,  # Mining pool concentration
        "finality_time_seconds": 3600,  # ~6 blocks
        "tps_average": 7.0,
        "tps_peak": 10.0,
        "uptime_30d_pct": 99.99,
        "major_incidents_12m": 0,
        "has_bug_bounty": True,
        "audit_count": 50,
        "time_since_last_upgrade_days": 180,
        "total_staked_usd": None,
        "slashing_enabled": False,
    },
    "ethereum": {
        "consensus": ConsensusMechanism.POS,
        "finality_type": SettlementFinality.ECONOMIC,
        "validator_count": 900000,
        "nakamoto_coefficient": 5,
        "top_10_stake_pct": 45.0,
        "finality_time_seconds": 768,  # 2 epochs
        "tps_average": 15.0,
        "tps_peak": 30.0,
        "uptime_30d_pct": 99.99,
        "major_incidents_12m": 0,
        "has_bug_bounty": True,
        "audit_count": 100,
        "time_since_last_upgrade_days": 60,
        "total_staked_usd": 100_000_000_000,
        "slashing_enabled": True,
    },
    "solana": {
        "consensus": ConsensusMechanism.POH,
        "finality_type": SettlementFinality.DETERMINISTIC,
        "validator_count": 1900,
        "nakamoto_coefficient": 31,
        "top_10_stake_pct": 35.0,
        "finality_time_seconds": 0.4,
        "tps_average": 3000.0,
        "tps_peak": 65000.0,
        "uptime_30d_pct": 99.5,
        "major_incidents_12m": 2,
        "has_bug_bounty": True,
        "audit_count": 20,
        "time_since_last_upgrade_days": 30,
        "total_staked_usd": 50_000_000_000,
        "slashing_enabled": True,
    },
    "polygon": {
        "consensus": ConsensusMechanism.POS,
        "finality_type": SettlementFinality.ECONOMIC,
        "validator_count": 100,
        "nakamoto_coefficient": 5,
        "top_10_stake_pct": 55.0,
        "finality_time_seconds": 2.0,
        "tps_average": 65.0,
        "tps_peak": 7000.0,
        "uptime_30d_pct": 99.9,
        "major_incidents_12m": 0,
        "has_bug_bounty": True,
        "audit_count": 30,
        "time_since_last_upgrade_days": 45,
        "total_staked_usd": 3_000_000_000,
        "slashing_enabled": True,
    },
    "avalanche": {
        "consensus": ConsensusMechanism.POS,
        "finality_type": SettlementFinality.DETERMINISTIC,
        "validator_count": 1200,
        "nakamoto_coefficient": 26,
        "top_10_stake_pct": 30.0,
        "finality_time_seconds": 1.0,
        "tps_average": 4500.0,
        "tps_peak": 6000.0,
        "uptime_30d_pct": 99.9,
        "major_incidents_12m": 0,
        "has_bug_bounty": True,
        "audit_count": 25,
        "time_since_last_upgrade_days": 60,
        "total_staked_usd": 8_000_000_000,
        "slashing_enabled": True,
    },
    "bnb_chain": {
        "consensus": ConsensusMechanism.DPOS,
        "finality_type": SettlementFinality.DETERMINISTIC,
        "validator_count": 21,
        "nakamoto_coefficient": 7,
        "top_10_stake_pct": 70.0,
        "finality_time_seconds": 3.0,
        "tps_average": 100.0,
        "tps_peak": 2000.0,
        "uptime_30d_pct": 99.95,
        "major_incidents_12m": 1,
        "has_bug_bounty": True,
        "audit_count": 15,
        "time_since_last_upgrade_days": 30,
        "total_staked_usd": 5_000_000_000,
        "slashing_enabled": True,
    },
    "tron": {
        "consensus": ConsensusMechanism.DPOS,
        "finality_type": SettlementFinality.DETERMINISTIC,
        "validator_count": 27,
        "nakamoto_coefficient": 9,
        "top_10_stake_pct": 65.0,
        "finality_time_seconds": 3.0,
        "tps_average": 2000.0,
        "tps_peak": 10000.0,
        "uptime_30d_pct": 99.9,
        "major_incidents_12m": 0,
        "has_bug_bounty": True,
        "audit_count": 10,
        "time_since_last_upgrade_days": 90,
        "total_staked_usd": 10_000_000_000,
        "slashing_enabled": False,
    },
}


def get_protocol_defaults(protocol_id: str) -> Optional[dict]:
    """Get default configuration for a known protocol."""
    return PROTOCOL_DEFAULTS.get(protocol_id.lower())


def _calculate_consensus_score(profile: ProtocolRiskProfile) -> tuple[float, list[str], list[str]]:
    """
    Calculate consensus mechanism score.

    Returns (score, risk_factors, strengths).
    """
    risks = []
    strengths = []

    # Base score from consensus type
    score = CONSENSUS_BASE_SCORES.get(profile.consensus, 50.0)

    # Adjust for finality type
    score += FINALITY_ADJUSTMENTS.get(profile.finality_type, 0.0)

    # PoW specific
    if profile.consensus == ConsensusMechanism.POW:
        strengths.append("Battle-tested PoW consensus with 15+ years of security")
        if profile.finality_time_seconds > 3600:
            risks.append("Long probabilistic finality time (>1 hour for high confidence)")

    # PoS specific
    elif profile.consensus == ConsensusMechanism.POS:
        if profile.slashing_enabled:
            strengths.append("Economic finality backed by slashing mechanism")
            score += 5
        else:
            risks.append("No slashing mechanism - reduced economic security")
            score -= 10

        if profile.total_staked_usd and profile.total_staked_usd > 10_000_000_000:
            strengths.append(f"High economic security (>${profile.total_staked_usd/1e9:.0f}B staked)")
            score += 5

    # DPoS concerns
    elif profile.consensus == ConsensusMechanism.DPOS:
        risks.append("DPoS trades decentralization for throughput - governance concentration risk")
        if profile.validator_count < 50:
            risks.append(f"Limited validator set ({profile.validator_count}) - collusion risk")
            score -= 10

    # PoA concerns
    elif profile.consensus == ConsensusMechanism.POA:
        risks.append("Proof of Authority relies on trusted validators - centralization risk")

    return min(100, max(0, score)), risks, strengths


def _calculate_decentralization_score(profile: ProtocolRiskProfile) -> tuple[float, list[str], list[str]]:
    """
    Calculate decentralization score based on validator distribution.

    Nakamoto coefficient is key - higher = more decentralized.
    """
    risks = []
    strengths = []
    score = 50.0  # Base score

    # Nakamoto coefficient scoring
    if profile.nakamoto_coefficient >= 20:
        score += 30
        strengths.append(f"High Nakamoto coefficient ({profile.nakamoto_coefficient}) - strong decentralization")
    elif profile.nakamoto_coefficient >= 10:
        score += 20
        strengths.append(f"Good Nakamoto coefficient ({profile.nakamoto_coefficient})")
    elif profile.nakamoto_coefficient >= 5:
        score += 10
    else:
        risks.append(f"Low Nakamoto coefficient ({profile.nakamoto_coefficient}) - concentration risk")
        score -= 10

    # Validator count
    if profile.validator_count >= 1000:
        score += 15
        strengths.append(f"Large validator set ({profile.validator_count:,})")
    elif profile.validator_count >= 100:
        score += 10
    elif profile.validator_count < 50:
        risks.append(f"Small validator set ({profile.validator_count}) - limited decentralization")
        score -= 15

    # Top 10 concentration
    if profile.top_10_stake_pct > 60:
        risks.append(f"High concentration: top 10 control {profile.top_10_stake_pct:.0f}% of network")
        score -= 15
    elif profile.top_10_stake_pct > 40:
        score -= 5
    elif profile.top_10_stake_pct < 30:
        strengths.append("Well-distributed stake among validators")
        score += 10

    return min(100, max(0, score)), risks, strengths


def _calculate_settlement_score(profile: ProtocolRiskProfile) -> tuple[float, list[str], list[str]]:
    """
    Calculate settlement finality score.

    Fast, deterministic finality scores highest for institutional use.
    """
    risks = []
    strengths = []
    score = 50.0

    # Finality time scoring
    if profile.finality_time_seconds <= 2:
        score += 30
        strengths.append(f"Sub-second finality ({profile.finality_time_seconds}s) - suitable for high-frequency settlement")
    elif profile.finality_time_seconds <= 60:
        score += 20
        strengths.append(f"Fast finality ({profile.finality_time_seconds}s)")
    elif profile.finality_time_seconds <= 600:
        score += 10
    else:
        risks.append(f"Slow finality ({profile.finality_time_seconds/60:.0f} minutes) - not suitable for time-sensitive settlements")
        score -= 10

    # Finality type
    if profile.finality_type == SettlementFinality.DETERMINISTIC:
        strengths.append("Deterministic finality - no reorg risk after confirmation")
        score += 15
    elif profile.finality_type == SettlementFinality.ECONOMIC:
        score += 10
    elif profile.finality_type == SettlementFinality.PROBABILISTIC:
        risks.append("Probabilistic finality - transactions can theoretically be reorged")
        score -= 5

    return min(100, max(0, score)), risks, strengths


def _calculate_operational_score(profile: ProtocolRiskProfile) -> tuple[float, list[str], list[str]]:
    """
    Calculate operational reliability score.

    Based on uptime, incident history, and throughput capacity.
    """
    risks = []
    strengths = []
    score = 50.0

    # Uptime scoring
    if profile.uptime_30d_pct >= 99.99:
        score += 25
        strengths.append(f"Excellent uptime ({profile.uptime_30d_pct}%)")
    elif profile.uptime_30d_pct >= 99.9:
        score += 20
    elif profile.uptime_30d_pct >= 99.0:
        score += 10
    else:
        risks.append(f"Uptime concerns ({profile.uptime_30d_pct}%) - reliability risk")
        score -= 20

    # Incident history
    if profile.major_incidents_12m == 0:
        score += 15
        strengths.append("No major incidents in past 12 months")
    elif profile.major_incidents_12m <= 2:
        score += 5
        risks.append(f"{profile.major_incidents_12m} major incident(s) in past 12 months")
    else:
        risks.append(f"Frequent incidents ({profile.major_incidents_12m} in 12 months) - operational risk")
        score -= 15

    # Throughput capacity
    if profile.tps_average >= 1000:
        score += 10
        strengths.append(f"High throughput capacity ({profile.tps_average:.0f} TPS average)")
    elif profile.tps_average < 20:
        risks.append(f"Limited throughput ({profile.tps_average:.0f} TPS) - congestion risk")
        score -= 5

    return min(100, max(0, score)), risks, strengths


def _calculate_security_score(profile: ProtocolRiskProfile) -> tuple[float, list[str], list[str]]:
    """
    Calculate security posture score.

    Based on audits, bug bounty, and upgrade cadence.
    """
    risks = []
    strengths = []
    score = 50.0

    # Bug bounty
    if profile.has_bug_bounty:
        score += 15
        strengths.append("Active bug bounty program")
    else:
        risks.append("No bug bounty program - reduced security incentives")
        score -= 10

    # Audit history
    if profile.audit_count >= 20:
        score += 20
        strengths.append(f"Extensively audited ({profile.audit_count} audits)")
    elif profile.audit_count >= 5:
        score += 10
    elif profile.audit_count == 0:
        risks.append("No security audits - unverified security")
        score -= 25

    # Upgrade cadence (too frequent = risk, too stale = risk)
    if 30 <= profile.time_since_last_upgrade_days <= 180:
        score += 10
        strengths.append("Active development with stable upgrade cadence")
    elif profile.time_since_last_upgrade_days < 14:
        risks.append("Very recent upgrade - potential instability")
        score -= 5
    elif profile.time_since_last_upgrade_days > 365:
        risks.append("Stale protocol - may lack security patches")
        score -= 10

    return min(100, max(0, score)), risks, strengths


def _determine_risk_tier(overall_score: float, profile: ProtocolRiskProfile) -> RiskTier:
    """Determine risk tier from overall score and key metrics."""

    # Tier 1 requirements: high score + battle-tested
    if overall_score >= 80 and profile.nakamoto_coefficient >= 4:
        if profile.protocol_id.lower() in ["bitcoin", "ethereum"]:
            return RiskTier.TIER_1
        if profile.validator_count >= 500 and profile.major_incidents_12m == 0:
            return RiskTier.TIER_1

    # Tier 2: established protocols
    if overall_score >= 65:
        return RiskTier.TIER_2

    # Tier 3: emerging
    if overall_score >= 50:
        return RiskTier.TIER_3

    # Tier 4: high risk
    return RiskTier.TIER_4


def _generate_regulatory_notes(profile: ProtocolRiskProfile, risk_tier: RiskTier) -> list[str]:
    """Generate regulatory considerations based on profile."""
    notes = []

    # SEC considerations
    if profile.consensus == ConsensusMechanism.POS:
        notes.append("PoS staking may trigger securities analysis under SEC guidance")

    # Decentralization for commodity treatment
    if profile.nakamoto_coefficient < 5:
        notes.append("Low decentralization may affect commodity vs security classification")

    # Finality for settlement regulations
    if profile.finality_time_seconds > 600:
        notes.append("Long finality may not meet T+1 settlement requirements")

    # Tier-based notes
    if risk_tier == RiskTier.TIER_1:
        notes.append("Tier 1 protocol - suitable for institutional custody frameworks")
    elif risk_tier == RiskTier.TIER_4:
        notes.append("Tier 4 protocol - enhanced due diligence required for institutional use")

    return notes


def assess_protocol_risk(
    protocol_id: str,
    consensus: ConsensusMechanism,
    finality_type: SettlementFinality,
    validator_count: int,
    nakamoto_coefficient: int,
    finality_time_seconds: float,
    tps_average: float,
    tps_peak: float,
    uptime_30d_pct: float = 99.9,
    major_incidents_12m: int = 0,
    has_bug_bounty: bool = True,
    audit_count: int = 0,
    time_since_last_upgrade_days: int = 30,
    top_10_stake_pct: float = 50.0,
    total_staked_usd: Optional[float] = None,
    slashing_enabled: bool = True,
) -> ProtocolRiskAssessment:
    """
    Assess blockchain protocol risk.

    Provides a comprehensive risk assessment suitable for institutional
    risk management and regulatory compliance reporting.

    Args:
        protocol_id: Protocol identifier (e.g., 'ethereum', 'solana')
        consensus: Consensus mechanism type
        finality_type: Settlement finality type
        validator_count: Number of active validators
        nakamoto_coefficient: Minimum entities to control 51%
        finality_time_seconds: Time to finality
        tps_average: Average transactions per second
        tps_peak: Peak TPS observed
        uptime_30d_pct: 30-day uptime percentage
        major_incidents_12m: Major incidents in past 12 months
        has_bug_bounty: Whether bug bounty exists
        audit_count: Number of security audits
        time_since_last_upgrade_days: Days since last upgrade
        top_10_stake_pct: Stake concentration in top 10
        total_staked_usd: Total value staked (PoS)
        slashing_enabled: Whether slashing is enabled

    Returns:
        ProtocolRiskAssessment with scores and risk factors
    """
    # Build profile
    profile = ProtocolRiskProfile(
        protocol_id=protocol_id,
        consensus=consensus,
        finality_type=finality_type,
        validator_count=validator_count,
        nakamoto_coefficient=nakamoto_coefficient,
        top_10_stake_pct=top_10_stake_pct,
        finality_time_seconds=finality_time_seconds,
        tps_average=tps_average,
        tps_peak=tps_peak,
        uptime_30d_pct=uptime_30d_pct,
        major_incidents_12m=major_incidents_12m,
        has_bug_bounty=has_bug_bounty,
        audit_count=audit_count,
        time_since_last_upgrade_days=time_since_last_upgrade_days,
        total_staked_usd=total_staked_usd,
        slashing_enabled=slashing_enabled,
    )

    # Calculate dimension scores
    all_risks = []
    all_strengths = []

    consensus_score, c_risks, c_strengths = _calculate_consensus_score(profile)
    all_risks.extend(c_risks)
    all_strengths.extend(c_strengths)

    decentralization_score, d_risks, d_strengths = _calculate_decentralization_score(profile)
    all_risks.extend(d_risks)
    all_strengths.extend(d_strengths)

    settlement_score, s_risks, s_strengths = _calculate_settlement_score(profile)
    all_risks.extend(s_risks)
    all_strengths.extend(s_strengths)

    operational_score, o_risks, o_strengths = _calculate_operational_score(profile)
    all_risks.extend(o_risks)
    all_strengths.extend(o_strengths)

    security_score, sec_risks, sec_strengths = _calculate_security_score(profile)
    all_risks.extend(sec_risks)
    all_strengths.extend(sec_strengths)

    # Weighted overall score
    # Weights reflect institutional risk priorities
    weights = {
        "consensus": 0.25,
        "decentralization": 0.20,
        "settlement": 0.20,
        "operational": 0.20,
        "security": 0.15,
    }

    overall_score = (
        consensus_score * weights["consensus"] +
        decentralization_score * weights["decentralization"] +
        settlement_score * weights["settlement"] +
        operational_score * weights["operational"] +
        security_score * weights["security"]
    )

    # Determine risk tier
    risk_tier = _determine_risk_tier(overall_score, profile)

    # Regulatory notes
    regulatory_notes = _generate_regulatory_notes(profile, risk_tier)

    return ProtocolRiskAssessment(
        protocol_id=protocol_id,
        risk_tier=risk_tier,
        consensus_score=round(consensus_score, 1),
        decentralization_score=round(decentralization_score, 1),
        settlement_score=round(settlement_score, 1),
        operational_score=round(operational_score, 1),
        security_score=round(security_score, 1),
        overall_score=round(overall_score, 1),
        risk_factors=all_risks,
        strengths=all_strengths,
        regulatory_notes=regulatory_notes,
        metrics_summary={
            "consensus": profile.consensus.value,
            "finality_type": profile.finality_type.value,
            "validator_count": profile.validator_count,
            "nakamoto_coefficient": profile.nakamoto_coefficient,
            "finality_time_seconds": profile.finality_time_seconds,
            "tps_average": profile.tps_average,
            "uptime_30d_pct": profile.uptime_30d_pct,
        },
    )
