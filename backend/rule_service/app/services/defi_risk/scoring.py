"""
DeFi protocol risk scoring module.

Provides comprehensive risk assessment for DeFi protocols across:
- Smart contract risk (audits, upgradeability, admin functions)
- Economic risk (token concentration, treasury, impermanent loss)
- Oracle risk (providers, fallbacks, manipulation resistance)
- Governance risk (centralization, timelocks, multisig)

Produces A-F letter grades with regulatory flags for compliance reporting.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class DeFiCategory(str, Enum):
    """DeFi protocol categories."""

    STAKING = "staking"                 # Liquid staking (Lido, Rocket Pool)
    LIQUIDITY_POOL = "liquidity_pool"   # AMM pools (Uniswap, Curve)
    LENDING = "lending"                 # Lending/borrowing (Aave, Compound)
    BRIDGE = "bridge"                   # Cross-chain bridges
    DEX = "dex"                         # Decentralized exchanges
    YIELD_AGGREGATOR = "yield_aggregator"  # Yield farming (Yearn)
    DERIVATIVES = "derivatives"         # Perps, options (dYdX, GMX)
    STABLECOIN = "stablecoin"          # Algorithmic/collateralized stables
    INSURANCE = "insurance"             # DeFi insurance (Nexus Mutual)
    RESTAKING = "restaking"             # Restaking protocols (EigenLayer)


class GovernanceType(str, Enum):
    """Governance mechanism types."""

    TOKEN_VOTING = "token_voting"       # Standard token-based governance
    MULTISIG = "multisig"               # Multi-signature wallet control
    OPTIMISTIC = "optimistic"           # Optimistic governance (veto-based)
    IMMUTABLE = "immutable"             # No governance, immutable contracts
    CENTRALIZED = "centralized"         # Single admin/team control
    HYBRID = "hybrid"                   # Combination of mechanisms


class OracleProvider(str, Enum):
    """Oracle service providers."""

    CHAINLINK = "chainlink"
    PYTH = "pyth"
    BAND = "band"
    UNISWAP_TWAP = "uniswap_twap"
    CUSTOM = "custom"
    NONE = "none"


class RiskGrade(str, Enum):
    """Letter grade risk rating (A=lowest risk, F=highest risk)."""

    A = "A"   # Excellent - institutional grade
    B = "B"   # Good - acceptable for most use cases
    C = "C"   # Fair - elevated risk, requires monitoring
    D = "D"   # Poor - significant concerns
    F = "F"   # Fail - critical risks identified


class SmartContractRisk(BaseModel):
    """
    Smart contract risk assessment inputs.

    Evaluates code security, upgradeability, and admin privileges.
    """

    # Audit status
    audit_count: int = Field(
        0,
        ge=0,
        description="Number of independent security audits",
    )
    auditors: list[str] = Field(
        default_factory=list,
        description="Names of audit firms (e.g., 'Trail of Bits', 'OpenZeppelin')",
    )
    last_audit_days_ago: int = Field(
        365,
        ge=0,
        description="Days since last security audit",
    )
    formal_verification: bool = Field(
        False,
        description="Whether formal verification was performed",
    )

    # Contract characteristics
    is_upgradeable: bool = Field(
        True,
        description="Whether contracts are upgradeable (proxy pattern)",
    )
    upgrade_timelock_hours: int = Field(
        0,
        ge=0,
        description="Timelock delay for upgrades in hours",
    )
    has_admin_functions: bool = Field(
        True,
        description="Whether admin-only functions exist",
    )
    admin_can_pause: bool = Field(
        True,
        description="Whether admin can pause the protocol",
    )
    admin_can_drain: bool = Field(
        False,
        description="Whether admin can withdraw user funds (critical)",
    )

    # Track record
    tvl_usd: float = Field(
        0,
        ge=0,
        description="Total Value Locked in USD",
    )
    contract_age_days: int = Field(
        0,
        ge=0,
        description="Days since mainnet deployment",
    )
    exploit_history_count: int = Field(
        0,
        ge=0,
        description="Number of historical exploits",
    )
    total_exploit_loss_usd: float = Field(
        0,
        ge=0,
        description="Total USD lost to exploits",
    )
    bug_bounty_max_usd: float = Field(
        0,
        ge=0,
        description="Maximum bug bounty payout",
    )


class EconomicRisk(BaseModel):
    """
    Economic and tokenomics risk assessment.

    Evaluates token distribution, treasury health, and mechanism risks.
    """

    # Token distribution
    token_concentration_top10_pct: float = Field(
        50.0,
        ge=0,
        le=100,
        description="Percentage of tokens held by top 10 addresses",
    )
    team_token_pct: float = Field(
        20.0,
        ge=0,
        le=100,
        description="Percentage of tokens allocated to team",
    )
    vesting_remaining_pct: float = Field(
        50.0,
        ge=0,
        le=100,
        description="Percentage of team/investor tokens still vesting",
    )

    # Treasury
    treasury_runway_months: float = Field(
        24.0,
        ge=0,
        description="Estimated treasury runway in months",
    )
    treasury_diversified: bool = Field(
        False,
        description="Whether treasury holds multiple assets",
    )

    # Protocol revenue
    has_protocol_revenue: bool = Field(
        True,
        description="Whether protocol generates revenue",
    )
    revenue_30d_usd: float = Field(
        0,
        ge=0,
        description="Protocol revenue in last 30 days (USD)",
    )

    # Mechanism-specific risks
    has_impermanent_loss: bool = Field(
        False,
        description="Whether users face impermanent loss risk",
    )
    has_liquidation_risk: bool = Field(
        False,
        description="Whether users face liquidation risk",
    )
    max_leverage: float = Field(
        1.0,
        ge=1.0,
        description="Maximum leverage available",
    )


class OracleRisk(BaseModel):
    """
    Oracle dependency risk assessment.

    Critical for protocols relying on external price feeds.
    """

    # Oracle setup
    primary_oracle: OracleProvider = Field(
        OracleProvider.CHAINLINK,
        description="Primary oracle provider",
    )
    has_fallback_oracle: bool = Field(
        False,
        description="Whether fallback oracle exists",
    )
    oracle_update_frequency_seconds: int = Field(
        3600,
        ge=1,
        description="How often oracle updates (heartbeat)",
    )

    # Oracle security
    oracle_manipulation_resistant: bool = Field(
        True,
        description="Whether TWAP or other manipulation resistance exists",
    )
    oracle_decentralized: bool = Field(
        True,
        description="Whether oracle is decentralized",
    )

    # Historical
    oracle_failure_count_12m: int = Field(
        0,
        ge=0,
        description="Oracle-related failures in past 12 months",
    )
    oracle_deviation_threshold_pct: float = Field(
        1.0,
        gt=0,
        description="Maximum allowed deviation before circuit breaker",
    )


class GovernanceRisk(BaseModel):
    """
    Governance and centralization risk assessment.

    Evaluates control mechanisms and decentralization of decision-making.
    """

    # Governance structure
    governance_type: GovernanceType = Field(
        GovernanceType.TOKEN_VOTING,
        description="Primary governance mechanism",
    )
    has_timelock: bool = Field(
        True,
        description="Whether governance actions have timelock",
    )
    timelock_hours: int = Field(
        48,
        ge=0,
        description="Timelock delay for governance actions",
    )

    # Multisig details
    multisig_threshold: Optional[str] = Field(
        None,
        description="Multisig configuration (e.g., '3/5', '4/7')",
    )
    multisig_signers_doxxed: bool = Field(
        False,
        description="Whether multisig signers are publicly known",
    )

    # Participation
    governance_participation_pct: float = Field(
        10.0,
        ge=0,
        le=100,
        description="Average governance participation rate",
    )
    quorum_pct: float = Field(
        4.0,
        ge=0,
        le=100,
        description="Quorum requirement for proposals",
    )

    # Emergency powers
    has_emergency_admin: bool = Field(
        True,
        description="Whether emergency admin powers exist",
    )
    emergency_actions_12m: int = Field(
        0,
        ge=0,
        description="Emergency actions taken in past 12 months",
    )


class DeFiRiskScore(BaseModel):
    """
    Comprehensive DeFi protocol risk score.

    Provides letter grade ratings across dimensions with
    regulatory flags for compliance reporting.
    """

    protocol_id: str
    category: DeFiCategory

    # Dimension grades
    smart_contract_grade: RiskGrade
    economic_grade: RiskGrade
    oracle_grade: RiskGrade
    governance_grade: RiskGrade

    # Overall
    overall_grade: RiskGrade
    overall_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Numeric score (0-100)",
    )

    # Dimension scores (0-100)
    smart_contract_score: float
    economic_score: float
    oracle_score: float
    governance_score: float

    # Risk factors
    critical_risks: list[str] = Field(default_factory=list)
    high_risks: list[str] = Field(default_factory=list)
    medium_risks: list[str] = Field(default_factory=list)

    # Strengths
    strengths: list[str] = Field(default_factory=list)

    # Regulatory flags
    regulatory_flags: list[str] = Field(default_factory=list)

    # Summary metrics
    metrics_summary: dict = Field(default_factory=dict)


# Reputable auditors with weight
REPUTABLE_AUDITORS = {
    "trail of bits": 1.0,
    "openzeppelin": 1.0,
    "consensys diligence": 1.0,
    "certik": 0.8,
    "hacken": 0.7,
    "peckshield": 0.7,
    "slowmist": 0.7,
    "quantstamp": 0.8,
    "code4rena": 0.9,
    "sherlock": 0.9,
    "spearbit": 1.0,
}


def _score_to_grade(score: float) -> RiskGrade:
    """Convert numeric score to letter grade."""
    if score >= 85:
        return RiskGrade.A
    elif score >= 70:
        return RiskGrade.B
    elif score >= 55:
        return RiskGrade.C
    elif score >= 40:
        return RiskGrade.D
    else:
        return RiskGrade.F


def _calculate_smart_contract_score(
    risk: SmartContractRisk,
) -> tuple[float, list[str], list[str], list[str], list[str]]:
    """
    Calculate smart contract risk score.

    Returns (score, critical_risks, high_risks, medium_risks, strengths).
    """
    score = 50.0  # Base score
    critical = []
    high = []
    medium = []
    strengths = []

    # Audit scoring
    if risk.audit_count >= 3:
        score += 15
        strengths.append(f"Multiple independent audits ({risk.audit_count})")
    elif risk.audit_count >= 1:
        score += 8
    else:
        high.append("No security audits performed")
        score -= 20

    # Reputable auditors bonus
    auditor_bonus = 0
    for auditor in risk.auditors:
        auditor_lower = auditor.lower()
        if auditor_lower in REPUTABLE_AUDITORS:
            auditor_bonus += REPUTABLE_AUDITORS[auditor_lower] * 5
    score += min(auditor_bonus, 15)  # Cap at 15 points

    if auditor_bonus > 10:
        strengths.append(f"Audited by reputable firms: {', '.join(risk.auditors[:3])}")

    # Formal verification
    if risk.formal_verification:
        score += 10
        strengths.append("Formal verification completed")

    # Audit recency
    if risk.last_audit_days_ago > 365:
        medium.append("Audit is over 1 year old")
        score -= 5
    elif risk.last_audit_days_ago > 180:
        score -= 2

    # Upgradeability
    if risk.is_upgradeable:
        if risk.upgrade_timelock_hours >= 48:
            score += 5
            strengths.append(f"{risk.upgrade_timelock_hours}h upgrade timelock")
        elif risk.upgrade_timelock_hours < 24:
            medium.append("Short upgrade timelock (<24h)")
            score -= 5
    else:
        score += 10
        strengths.append("Immutable contracts")

    # Admin powers
    if risk.admin_can_drain:
        critical.append("CRITICAL: Admin can drain user funds")
        score -= 30

    if risk.admin_can_pause and not risk.has_admin_functions:
        score += 5  # Pause-only is acceptable

    # Track record
    if risk.exploit_history_count > 0:
        if risk.total_exploit_loss_usd > 10_000_000:
            critical.append(f"Major exploit history: ${risk.total_exploit_loss_usd/1e6:.0f}M lost")
            score -= 25
        else:
            high.append(f"Exploit history: {risk.exploit_history_count} incidents")
            score -= 15

    if risk.contract_age_days >= 365 and risk.exploit_history_count == 0:
        score += 10
        strengths.append("1+ year track record with no exploits")
    elif risk.contract_age_days < 90:
        medium.append("New protocol (<90 days)")
        score -= 5

    # TVL as proxy for Lindy effect
    if risk.tvl_usd > 1_000_000_000:
        score += 5
        strengths.append(f"High TVL (${risk.tvl_usd/1e9:.1f}B) - battle-tested")

    # Bug bounty
    if risk.bug_bounty_max_usd >= 1_000_000:
        score += 5
        strengths.append(f"${risk.bug_bounty_max_usd/1e6:.0f}M bug bounty program")
    elif risk.bug_bounty_max_usd == 0:
        medium.append("No bug bounty program")
        score -= 3

    return min(100, max(0, score)), critical, high, medium, strengths


def _calculate_economic_score(
    risk: EconomicRisk,
    category: DeFiCategory,
) -> tuple[float, list[str], list[str], list[str], list[str]]:
    """Calculate economic risk score."""
    score = 50.0
    critical = []
    high = []
    medium = []
    strengths = []

    # Token concentration
    if risk.token_concentration_top10_pct > 80:
        high.append(f"High token concentration: top 10 hold {risk.token_concentration_top10_pct:.0f}%")
        score -= 15
    elif risk.token_concentration_top10_pct > 60:
        medium.append(f"Moderate token concentration ({risk.token_concentration_top10_pct:.0f}%)")
        score -= 5
    elif risk.token_concentration_top10_pct < 40:
        score += 10
        strengths.append("Well-distributed token supply")

    # Team allocation
    if risk.team_token_pct > 30:
        medium.append(f"High team allocation ({risk.team_token_pct:.0f}%)")
        score -= 5
    if risk.vesting_remaining_pct < 20 and risk.team_token_pct > 15:
        medium.append("Most team tokens already unlocked")
        score -= 5

    # Treasury health
    if risk.treasury_runway_months >= 36:
        score += 10
        strengths.append(f"{risk.treasury_runway_months:.0f} month treasury runway")
    elif risk.treasury_runway_months < 12:
        high.append(f"Short treasury runway ({risk.treasury_runway_months:.0f} months)")
        score -= 10

    if risk.treasury_diversified:
        score += 5
        strengths.append("Diversified treasury holdings")

    # Revenue
    if risk.has_protocol_revenue and risk.revenue_30d_usd > 1_000_000:
        score += 10
        strengths.append(f"Strong protocol revenue (${risk.revenue_30d_usd/1e6:.1f}M/30d)")
    elif not risk.has_protocol_revenue:
        medium.append("No protocol revenue model")
        score -= 5

    # Category-specific risks
    if category == DeFiCategory.LIQUIDITY_POOL and risk.has_impermanent_loss:
        medium.append("Impermanent loss exposure for LPs")

    if risk.has_liquidation_risk:
        if risk.max_leverage > 10:
            high.append(f"High leverage available ({risk.max_leverage}x) with liquidation risk")
            score -= 10
        else:
            medium.append("Liquidation risk present")

    if category == DeFiCategory.STABLECOIN:
        # Extra scrutiny for stablecoins
        if risk.token_concentration_top10_pct > 50:
            high.append("Stablecoin: High holder concentration risk")
            score -= 10

    return min(100, max(0, score)), critical, high, medium, strengths


def _calculate_oracle_score(
    risk: OracleRisk,
    category: DeFiCategory,
) -> tuple[float, list[str], list[str], list[str], list[str]]:
    """Calculate oracle dependency risk score."""
    score = 50.0
    critical = []
    high = []
    medium = []
    strengths = []

    # Oracle provider scoring
    if risk.primary_oracle == OracleProvider.CHAINLINK:
        score += 20
        strengths.append("Chainlink oracle (industry standard)")
    elif risk.primary_oracle == OracleProvider.PYTH:
        score += 15
        strengths.append("Pyth oracle (low latency)")
    elif risk.primary_oracle == OracleProvider.UNISWAP_TWAP:
        score += 10
    elif risk.primary_oracle == OracleProvider.CUSTOM:
        medium.append("Custom oracle implementation")
        score -= 5
    elif risk.primary_oracle == OracleProvider.NONE:
        # Some protocols don't need oracles
        if category in [DeFiCategory.DEX, DeFiCategory.LIQUIDITY_POOL]:
            score += 15
            strengths.append("No oracle dependency (AMM-based pricing)")
        else:
            high.append("No oracle - potential pricing issues")
            score -= 15

    # Fallback
    if risk.has_fallback_oracle:
        score += 10
        strengths.append("Fallback oracle configured")
    elif risk.primary_oracle != OracleProvider.NONE:
        medium.append("No fallback oracle")
        score -= 5

    # Update frequency
    if risk.oracle_update_frequency_seconds <= 60:
        score += 5
    elif risk.oracle_update_frequency_seconds > 3600:
        medium.append("Slow oracle updates (>1 hour)")
        score -= 5

    # Manipulation resistance
    if risk.oracle_manipulation_resistant:
        score += 10
        strengths.append("Oracle manipulation resistance (TWAP/multi-source)")
    else:
        high.append("Potential oracle manipulation vulnerability")
        score -= 15

    # Decentralization
    if risk.oracle_decentralized:
        score += 5
    else:
        medium.append("Centralized oracle")
        score -= 5

    # Historical failures
    if risk.oracle_failure_count_12m > 0:
        high.append(f"Oracle failures in past 12m: {risk.oracle_failure_count_12m}")
        score -= 10 * risk.oracle_failure_count_12m

    return min(100, max(0, score)), critical, high, medium, strengths


def _calculate_governance_score(
    risk: GovernanceRisk,
) -> tuple[float, list[str], list[str], list[str], list[str]]:
    """Calculate governance risk score."""
    score = 50.0
    critical = []
    high = []
    medium = []
    strengths = []

    # Governance type
    if risk.governance_type == GovernanceType.IMMUTABLE:
        score += 20
        strengths.append("Immutable contracts - no governance risk")
    elif risk.governance_type == GovernanceType.TOKEN_VOTING:
        score += 10
        if risk.governance_participation_pct >= 20:
            score += 5
            strengths.append(f"Active governance ({risk.governance_participation_pct:.0f}% participation)")
        elif risk.governance_participation_pct < 5:
            medium.append("Low governance participation")
            score -= 5
    elif risk.governance_type == GovernanceType.MULTISIG:
        if risk.multisig_threshold:
            parts = risk.multisig_threshold.split("/")
            if len(parts) == 2:
                required, total = int(parts[0]), int(parts[1])
                if required >= 3 and total >= 5:
                    score += 10
                    strengths.append(f"Robust multisig ({risk.multisig_threshold})")
                elif required < 2:
                    high.append(f"Weak multisig ({risk.multisig_threshold})")
                    score -= 10
        if risk.multisig_signers_doxxed:
            score += 5
            strengths.append("Multisig signers publicly known")
    elif risk.governance_type == GovernanceType.CENTRALIZED:
        critical.append("Centralized control - single point of failure")
        score -= 25

    # Timelock
    if risk.has_timelock:
        if risk.timelock_hours >= 48:
            score += 10
            strengths.append(f"{risk.timelock_hours}h governance timelock")
        elif risk.timelock_hours >= 24:
            score += 5
        else:
            medium.append(f"Short timelock ({risk.timelock_hours}h)")
    else:
        high.append("No governance timelock")
        score -= 15

    # Emergency powers
    if risk.has_emergency_admin:
        if risk.emergency_actions_12m > 3:
            high.append(f"Frequent emergency actions ({risk.emergency_actions_12m} in 12m)")
            score -= 10
        else:
            medium.append("Emergency admin powers exist")
            score -= 3
    else:
        score += 5

    return min(100, max(0, score)), critical, high, medium, strengths


def _generate_regulatory_flags(
    category: DeFiCategory,
    smart_contract: SmartContractRisk,
    economic: EconomicRisk,
    governance: GovernanceRisk,
    overall_grade: RiskGrade,
) -> list[str]:
    """Generate regulatory compliance flags."""
    flags = []

    # SEC concerns
    if governance.governance_type == GovernanceType.CENTRALIZED:
        flags.append("SEC: Centralized control may indicate security classification")

    if economic.team_token_pct > 25:
        flags.append("SEC: High team allocation may affect Howey test analysis")

    # Category-specific
    if category == DeFiCategory.LENDING:
        flags.append("Regulatory: Lending protocol may require state licensing in US")

    if category == DeFiCategory.DERIVATIVES:
        flags.append("CFTC: Derivatives protocol subject to CFTC jurisdiction")

    if category == DeFiCategory.STABLECOIN:
        flags.append("GENIUS Act: Stablecoin requires reserve attestation")

    if category == DeFiCategory.BRIDGE:
        flags.append("AML/KYC: Bridge protocols face enhanced scrutiny for cross-chain transfers")

    # Risk-based flags
    if overall_grade in [RiskGrade.D, RiskGrade.F]:
        flags.append("Risk: Protocol does not meet institutional due diligence standards")

    if smart_contract.exploit_history_count > 0:
        flags.append("Disclosure: Historical exploit must be disclosed to investors")

    if smart_contract.admin_can_drain:
        flags.append("Custody: Admin withdrawal capability creates custodial concerns")

    return flags


# Default configurations for major DeFi protocols
DEFI_PROTOCOL_DEFAULTS: dict[str, dict] = {
    "aave_v3": {
        "category": DeFiCategory.LENDING,
        "smart_contract": {
            "audit_count": 5,
            "auditors": ["Trail of Bits", "OpenZeppelin", "SigmaPrime", "Certik"],
            "last_audit_days_ago": 90,
            "formal_verification": True,
            "is_upgradeable": True,
            "upgrade_timelock_hours": 48,
            "has_admin_functions": True,
            "admin_can_pause": True,
            "admin_can_drain": False,
            "tvl_usd": 12_000_000_000,
            "contract_age_days": 800,
            "exploit_history_count": 0,
            "bug_bounty_max_usd": 1_000_000,
        },
        "economic": {
            "token_concentration_top10_pct": 35,
            "team_token_pct": 23,
            "treasury_runway_months": 48,
            "treasury_diversified": True,
            "has_protocol_revenue": True,
            "revenue_30d_usd": 5_000_000,
            "has_liquidation_risk": True,
            "max_leverage": 1.0,
        },
        "oracle": {
            "primary_oracle": OracleProvider.CHAINLINK,
            "has_fallback_oracle": True,
            "oracle_manipulation_resistant": True,
            "oracle_decentralized": True,
        },
        "governance": {
            "governance_type": GovernanceType.TOKEN_VOTING,
            "has_timelock": True,
            "timelock_hours": 48,
            "governance_participation_pct": 15,
            "has_emergency_admin": True,
        },
    },
    "uniswap_v3": {
        "category": DeFiCategory.DEX,
        "smart_contract": {
            "audit_count": 4,
            "auditors": ["Trail of Bits", "ABDK", "OpenZeppelin"],
            "last_audit_days_ago": 180,
            "formal_verification": True,
            "is_upgradeable": False,
            "has_admin_functions": False,
            "admin_can_pause": False,
            "admin_can_drain": False,
            "tvl_usd": 5_000_000_000,
            "contract_age_days": 1000,
            "exploit_history_count": 0,
            "bug_bounty_max_usd": 3_000_000,
        },
        "economic": {
            "token_concentration_top10_pct": 45,
            "team_token_pct": 21,
            "treasury_runway_months": 60,
            "treasury_diversified": True,
            "has_protocol_revenue": True,
            "revenue_30d_usd": 50_000_000,
            "has_impermanent_loss": True,
        },
        "oracle": {
            "primary_oracle": OracleProvider.NONE,
        },
        "governance": {
            "governance_type": GovernanceType.TOKEN_VOTING,
            "has_timelock": True,
            "timelock_hours": 168,
            "governance_participation_pct": 8,
        },
    },
    "lido": {
        "category": DeFiCategory.STAKING,
        "smart_contract": {
            "audit_count": 6,
            "auditors": ["Quantstamp", "MixBytes", "Certora", "Statemind"],
            "last_audit_days_ago": 60,
            "formal_verification": True,
            "is_upgradeable": True,
            "upgrade_timelock_hours": 72,
            "has_admin_functions": True,
            "admin_can_pause": True,
            "admin_can_drain": False,
            "tvl_usd": 25_000_000_000,
            "contract_age_days": 1200,
            "exploit_history_count": 0,
            "bug_bounty_max_usd": 2_000_000,
        },
        "economic": {
            "token_concentration_top10_pct": 40,
            "team_token_pct": 20,
            "treasury_runway_months": 36,
            "has_protocol_revenue": True,
            "revenue_30d_usd": 30_000_000,
        },
        "oracle": {
            "primary_oracle": OracleProvider.CHAINLINK,
            "has_fallback_oracle": True,
            "oracle_manipulation_resistant": True,
        },
        "governance": {
            "governance_type": GovernanceType.TOKEN_VOTING,
            "has_timelock": True,
            "timelock_hours": 72,
            "governance_participation_pct": 12,
            "has_emergency_admin": True,
        },
    },
    "gmx": {
        "category": DeFiCategory.DERIVATIVES,
        "smart_contract": {
            "audit_count": 3,
            "auditors": ["ABDK", "Quantstamp"],
            "last_audit_days_ago": 120,
            "is_upgradeable": True,
            "upgrade_timelock_hours": 24,
            "has_admin_functions": True,
            "admin_can_pause": True,
            "admin_can_drain": False,
            "tvl_usd": 500_000_000,
            "contract_age_days": 600,
            "exploit_history_count": 0,
            "bug_bounty_max_usd": 500_000,
        },
        "economic": {
            "token_concentration_top10_pct": 55,
            "team_token_pct": 15,
            "treasury_runway_months": 24,
            "has_protocol_revenue": True,
            "revenue_30d_usd": 8_000_000,
            "has_liquidation_risk": True,
            "max_leverage": 50,
        },
        "oracle": {
            "primary_oracle": OracleProvider.CHAINLINK,
            "has_fallback_oracle": True,
            "oracle_manipulation_resistant": True,
        },
        "governance": {
            "governance_type": GovernanceType.MULTISIG,
            "multisig_threshold": "4/6",
            "has_timelock": True,
            "timelock_hours": 24,
            "has_emergency_admin": True,
        },
    },
}


def score_defi_protocol(
    protocol_id: str,
    category: DeFiCategory,
    smart_contract: SmartContractRisk,
    economic: EconomicRisk,
    oracle: OracleRisk,
    governance: GovernanceRisk,
) -> DeFiRiskScore:
    """
    Score a DeFi protocol across risk dimensions.

    Provides letter grades (A-F) for each dimension and overall,
    with detailed risk factors and regulatory flags.

    Args:
        protocol_id: Protocol identifier
        category: DeFi protocol category
        smart_contract: Smart contract risk inputs
        economic: Economic/tokenomics risk inputs
        oracle: Oracle dependency risk inputs
        governance: Governance risk inputs

    Returns:
        DeFiRiskScore with grades, risk factors, and regulatory flags
    """
    # Calculate dimension scores
    all_critical = []
    all_high = []
    all_medium = []
    all_strengths = []

    sc_score, sc_crit, sc_high, sc_med, sc_str = _calculate_smart_contract_score(smart_contract)
    all_critical.extend(sc_crit)
    all_high.extend(sc_high)
    all_medium.extend(sc_med)
    all_strengths.extend(sc_str)

    econ_score, econ_crit, econ_high, econ_med, econ_str = _calculate_economic_score(economic, category)
    all_critical.extend(econ_crit)
    all_high.extend(econ_high)
    all_medium.extend(econ_med)
    all_strengths.extend(econ_str)

    oracle_score, ora_crit, ora_high, ora_med, ora_str = _calculate_oracle_score(oracle, category)
    all_critical.extend(ora_crit)
    all_high.extend(ora_high)
    all_medium.extend(ora_med)
    all_strengths.extend(ora_str)

    gov_score, gov_crit, gov_high, gov_med, gov_str = _calculate_governance_score(governance)
    all_critical.extend(gov_crit)
    all_high.extend(gov_high)
    all_medium.extend(gov_med)
    all_strengths.extend(gov_str)

    # Weighted overall score
    # Smart contract weighted highest for DeFi
    weights = {
        "smart_contract": 0.35,
        "economic": 0.25,
        "oracle": 0.20,
        "governance": 0.20,
    }

    overall_score = (
        sc_score * weights["smart_contract"] +
        econ_score * weights["economic"] +
        oracle_score * weights["oracle"] +
        gov_score * weights["governance"]
    )

    # Critical risks cap the grade
    if all_critical:
        overall_score = min(overall_score, 35)  # F grade max

    # Convert to grades
    overall_grade = _score_to_grade(overall_score)

    # Regulatory flags
    regulatory_flags = _generate_regulatory_flags(
        category, smart_contract, economic, governance, overall_grade
    )

    return DeFiRiskScore(
        protocol_id=protocol_id,
        category=category,
        smart_contract_grade=_score_to_grade(sc_score),
        economic_grade=_score_to_grade(econ_score),
        oracle_grade=_score_to_grade(oracle_score),
        governance_grade=_score_to_grade(gov_score),
        overall_grade=overall_grade,
        overall_score=round(overall_score, 1),
        smart_contract_score=round(sc_score, 1),
        economic_score=round(econ_score, 1),
        oracle_score=round(oracle_score, 1),
        governance_score=round(gov_score, 1),
        critical_risks=all_critical,
        high_risks=all_high,
        medium_risks=all_medium,
        strengths=all_strengths,
        regulatory_flags=regulatory_flags,
        metrics_summary={
            "category": category.value,
            "tvl_usd": smart_contract.tvl_usd,
            "audit_count": smart_contract.audit_count,
            "contract_age_days": smart_contract.contract_age_days,
            "governance_type": governance.governance_type.value,
        },
    )
