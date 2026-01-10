"""
Versioned rule service for temporal rule management.

Coordinates version creation with event sourcing for audit trails.
Inspired by Temporal.io's workflow versioning patterns.
"""

from __future__ import annotations

import json
from typing import Any

from backend.database_service.app.services.repositories import (
    RuleVersionRepository,
    RuleEventRepository,
)
from backend.core.models import (
    RuleVersionRecord,
    RuleEventRecord,
    RuleEventType,
)
from backend.rule_service.app.services.loader import RuleLoader


class VersionedRuleService:
    """Service for managing rule versions with event sourcing.

    Provides:
    - Immutable version snapshots
    - Event-sourced audit trail
    - Point-in-time queries
    - Version comparison
    """

    def __init__(
        self,
        version_repo: RuleVersionRepository | None = None,
        event_repo: RuleEventRepository | None = None,
        loader: RuleLoader | None = None,
    ):
        """Initialize the versioned rule service.

        Args:
            version_repo: Repository for version storage (creates default if None)
            event_repo: Repository for event storage (creates default if None)
            loader: Rule loader for parsing YAML (creates default if None)
        """
        self.version_repo = version_repo or RuleVersionRepository()
        self.event_repo = event_repo or RuleEventRepository()
        self.loader = loader or RuleLoader()

    # =========================================================================
    # Write Operations
    # =========================================================================

    def create_rule(
        self,
        rule_id: str,
        content_yaml: str,
        actor: str | None = None,
        reason: str | None = None,
        effective_from: str | None = None,
        jurisdiction_code: str | None = None,
        regime_id: str | None = None,
    ) -> RuleVersionRecord:
        """Create a new rule (version 1).

        Args:
            rule_id: Unique rule identifier
            content_yaml: YAML content for the rule
            actor: Who is creating the rule
            reason: Why the rule is being created
            effective_from: When the rule becomes effective
            jurisdiction_code: Jurisdiction code (EU, UK, etc.)
            regime_id: Regulatory regime ID

        Returns:
            The created RuleVersionRecord

        Raises:
            ValueError: If a rule with this ID already exists
        """
        # Check if rule already exists
        existing = self.version_repo.get_latest_version(rule_id)
        if existing:
            raise ValueError(f"Rule '{rule_id}' already exists. Use update_rule instead.")

        # Create version
        version = self.version_repo.create_version(
            rule_id=rule_id,
            content_yaml=content_yaml,
            effective_from=effective_from,
            created_by=actor,
            jurisdiction_code=jurisdiction_code,
            regime_id=regime_id,
        )

        # Record event
        self.event_repo.append_event(
            rule_id=rule_id,
            version=version.version,
            event_type=RuleEventType.RULE_CREATED,
            event_data={
                "content_hash": version.content_hash,
                "effective_from": effective_from,
                "jurisdiction_code": jurisdiction_code,
                "regime_id": regime_id,
            },
            actor=actor,
            reason=reason,
        )

        return version

    def update_rule(
        self,
        rule_id: str,
        content_yaml: str,
        actor: str | None = None,
        reason: str | None = None,
        effective_from: str | None = None,
    ) -> RuleVersionRecord:
        """Update a rule (creates a new version).

        Args:
            rule_id: The rule identifier
            content_yaml: New YAML content
            actor: Who is updating the rule
            reason: Why the rule is being updated
            effective_from: When the new version becomes effective

        Returns:
            The new RuleVersionRecord

        Raises:
            ValueError: If the rule doesn't exist
        """
        # Get current version
        current = self.version_repo.get_latest_version(rule_id)
        if not current:
            raise ValueError(f"Rule '{rule_id}' not found. Use create_rule instead.")

        # Create new version
        version = self.version_repo.create_version(
            rule_id=rule_id,
            content_yaml=content_yaml,
            effective_from=effective_from,
            created_by=actor,
            jurisdiction_code=current.jurisdiction_code,
            regime_id=current.regime_id,
        )

        # Record event
        self.event_repo.append_event(
            rule_id=rule_id,
            version=version.version,
            event_type=RuleEventType.RULE_UPDATED,
            event_data={
                "previous_version": current.version,
                "previous_hash": current.content_hash,
                "new_hash": version.content_hash,
                "effective_from": effective_from,
            },
            actor=actor,
            reason=reason,
        )

        return version

    def deprecate_rule(
        self,
        rule_id: str,
        actor: str | None = None,
        reason: str | None = None,
    ) -> RuleEventRecord:
        """Mark a rule as deprecated.

        This doesn't delete the rule but records a deprecation event.

        Args:
            rule_id: The rule identifier
            actor: Who is deprecating the rule
            reason: Why the rule is being deprecated

        Returns:
            The deprecation event record

        Raises:
            ValueError: If the rule doesn't exist
        """
        current = self.version_repo.get_latest_version(rule_id)
        if not current:
            raise ValueError(f"Rule '{rule_id}' not found.")

        # Record deprecation event
        event = self.event_repo.append_event(
            rule_id=rule_id,
            version=current.version,
            event_type=RuleEventType.RULE_DEPRECATED,
            event_data={
                "final_version": current.version,
                "final_hash": current.content_hash,
            },
            actor=actor,
            reason=reason,
        )

        return event

    # =========================================================================
    # Read Operations
    # =========================================================================

    def get_rule_at_version(self, rule_id: str, version: int) -> dict[str, Any] | None:
        """Get a parsed rule at a specific version.

        Args:
            rule_id: The rule identifier
            version: The version number

        Returns:
            Parsed rule dictionary if found, None otherwise
        """
        record = self.version_repo.get_version(rule_id, version)
        if not record:
            return None

        return self.loader.parse_yaml(record.content_yaml)

    def get_rule_at_timestamp(
        self, rule_id: str, timestamp: str
    ) -> dict[str, Any] | None:
        """Get a parsed rule effective at a specific timestamp.

        Args:
            rule_id: The rule identifier
            timestamp: ISO 8601 timestamp

        Returns:
            Parsed rule dictionary if found, None otherwise
        """
        record = self.version_repo.get_version_at_timestamp(rule_id, timestamp)
        if not record:
            return None

        return self.loader.parse_yaml(record.content_yaml)

    def get_rule_history(self, rule_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get the history of a rule including versions and events.

        Args:
            rule_id: The rule identifier
            limit: Maximum number of versions to return

        Returns:
            List of version info dictionaries with events
        """
        versions = self.version_repo.get_version_history(rule_id, limit)
        events = self.event_repo.get_events_for_rule(rule_id)

        # Build event index by version
        events_by_version: dict[int, list[dict]] = {}
        for event in events:
            v = event.version
            if v not in events_by_version:
                events_by_version[v] = []
            events_by_version[v].append({
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "actor": event.actor,
                "reason": event.reason,
            })

        # Build history
        history = []
        for version in versions:
            history.append({
                "version": version.version,
                "content_hash": version.content_hash,
                "created_at": version.created_at,
                "created_by": version.created_by,
                "effective_from": version.effective_from,
                "effective_to": version.effective_to,
                "superseded_by": version.superseded_by,
                "events": events_by_version.get(version.version, []),
            })

        return history

    def compare_versions(
        self, rule_id: str, version_a: int, version_b: int
    ) -> dict[str, Any]:
        """Compare two versions of a rule.

        Args:
            rule_id: The rule identifier
            version_a: First version number
            version_b: Second version number

        Returns:
            Comparison result with both versions and diff summary

        Raises:
            ValueError: If either version is not found
        """
        record_a = self.version_repo.get_version(rule_id, version_a)
        record_b = self.version_repo.get_version(rule_id, version_b)

        if not record_a:
            raise ValueError(f"Version {version_a} not found for rule '{rule_id}'")
        if not record_b:
            raise ValueError(f"Version {version_b} not found for rule '{rule_id}'")

        return {
            "rule_id": rule_id,
            "version_a": {
                "version": version_a,
                "content_hash": record_a.content_hash,
                "created_at": record_a.created_at,
                "content_yaml": record_a.content_yaml,
            },
            "version_b": {
                "version": version_b,
                "content_hash": record_b.content_hash,
                "created_at": record_b.created_at,
                "content_yaml": record_b.content_yaml,
            },
            "same_content": record_a.content_hash == record_b.content_hash,
        }

    # =========================================================================
    # Decision Engine Integration
    # =========================================================================

    def evaluate_with_version(
        self,
        scenario: dict[str, Any],
        rule_id: str,
        version: int | None = None,
    ) -> dict[str, Any]:
        """Evaluate a scenario against a specific rule version.

        Args:
            scenario: The scenario to evaluate
            rule_id: The rule identifier
            version: Version number (None = latest)

        Returns:
            Decision result from the engine

        Raises:
            ValueError: If the rule/version is not found
            NotImplementedError: Stub - requires engine integration
        """
        # Get the rule at version
        if version is None:
            record = self.version_repo.get_latest_version(rule_id)
        else:
            record = self.version_repo.get_version(rule_id, version)

        if not record:
            raise ValueError(f"Rule '{rule_id}' version {version} not found")

        # TODO: Integrate with DecisionEngine when ready
        raise NotImplementedError(
            "evaluate_with_version requires DecisionEngine integration"
        )
