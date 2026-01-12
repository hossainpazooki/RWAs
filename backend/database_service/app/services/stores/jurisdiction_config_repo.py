"""
Jurisdiction configuration repository.

Provides CRUD operations for jurisdiction-specific configurations,
replacing hardcoded dictionaries in pathway.py and conflicts.py.
"""

from __future__ import annotations

from typing import Any

from backend.database_service.app.services.database import get_db


class JurisdictionConfigRepository:
    """Repository for jurisdiction configuration data.

    Manages:
    - Step timelines for compliance pathways
    - Step dependencies
    - Obligation conflict pairs
    """

    # =========================================================================
    # Step Timeline Operations
    # =========================================================================

    def get_step_timeline(
        self, step_id: str, jurisdiction_code: str = "*"
    ) -> dict[str, Any] | None:
        """Get timeline for a specific step and jurisdiction.

        Args:
            step_id: The step identifier
            jurisdiction_code: Jurisdiction code ('*' for default)

        Returns:
            Timeline dict with min_days, max_days, description if found
        """
        with get_db() as conn:
            # Try jurisdiction-specific first
            cursor = conn.execute(
                """
                SELECT * FROM step_timelines
                WHERE step_id = ? AND jurisdiction_code = ?
                """,
                (step_id, jurisdiction_code),
            )
            row = cursor.fetchone()

            # Fall back to default if not found
            if not row and jurisdiction_code != "*":
                cursor = conn.execute(
                    """
                    SELECT * FROM step_timelines
                    WHERE step_id = ? AND jurisdiction_code = '*'
                    """,
                    (step_id,),
                )
                row = cursor.fetchone()

            if row:
                return {
                    "step_id": row["step_id"],
                    "jurisdiction_code": row["jurisdiction_code"],
                    "min_days": row["min_days"],
                    "max_days": row["max_days"],
                    "description": row["description"],
                }
            return None

    def get_all_step_timelines(
        self, jurisdiction_code: str | None = None
    ) -> list[dict[str, Any]]:
        """Get all step timelines.

        Args:
            jurisdiction_code: Filter by jurisdiction (None for all)

        Returns:
            List of timeline dictionaries
        """
        with get_db() as conn:
            if jurisdiction_code:
                cursor = conn.execute(
                    "SELECT * FROM step_timelines WHERE jurisdiction_code = ? ORDER BY step_id",
                    (jurisdiction_code,),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM step_timelines ORDER BY step_id, jurisdiction_code"
                )

            return [
                {
                    "step_id": row["step_id"],
                    "jurisdiction_code": row["jurisdiction_code"],
                    "min_days": row["min_days"],
                    "max_days": row["max_days"],
                    "description": row["description"],
                }
                for row in cursor.fetchall()
            ]

    def set_step_timeline(
        self,
        step_id: str,
        min_days: int,
        max_days: int,
        jurisdiction_code: str = "*",
        description: str | None = None,
    ) -> None:
        """Set or update a step timeline.

        Args:
            step_id: The step identifier
            min_days: Minimum days for this step
            max_days: Maximum days for this step
            jurisdiction_code: Jurisdiction code ('*' for default)
            description: Optional description
        """
        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO step_timelines
                (step_id, jurisdiction_code, min_days, max_days, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (step_id, jurisdiction_code, min_days, max_days, description),
            )
            conn.commit()

    # =========================================================================
    # Step Dependency Operations
    # =========================================================================

    def get_step_dependencies(self, step_id: str) -> list[str]:
        """Get dependencies for a step.

        Args:
            step_id: The step identifier

        Returns:
            List of step IDs this step depends on
        """
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT depends_on FROM step_dependencies WHERE step_id = ? ORDER BY depends_on",
                (step_id,),
            )
            return [row["depends_on"] for row in cursor.fetchall()]

    def get_all_dependencies(self) -> dict[str, list[str]]:
        """Get all step dependencies.

        Returns:
            Dictionary mapping step_id to list of dependencies
        """
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT step_id, depends_on FROM step_dependencies ORDER BY step_id, depends_on"
            )

            deps: dict[str, list[str]] = {}
            for row in cursor.fetchall():
                step_id = row["step_id"]
                if step_id not in deps:
                    deps[step_id] = []
                deps[step_id].append(row["depends_on"])

            return deps

    def set_step_dependency(self, step_id: str, depends_on: str) -> None:
        """Add a step dependency.

        Args:
            step_id: The step identifier
            depends_on: The step this step depends on
        """
        with get_db() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO step_dependencies (step_id, depends_on)
                VALUES (?, ?)
                """,
                (step_id, depends_on),
            )
            conn.commit()

    def remove_step_dependency(self, step_id: str, depends_on: str) -> bool:
        """Remove a step dependency.

        Args:
            step_id: The step identifier
            depends_on: The step to remove as dependency

        Returns:
            True if a dependency was removed
        """
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM step_dependencies WHERE step_id = ? AND depends_on = ?",
                (step_id, depends_on),
            )
            conn.commit()
            return cursor.rowcount > 0

    # =========================================================================
    # Obligation Conflict Operations
    # =========================================================================

    def get_obligation_conflicts(self, obligation: str) -> list[dict[str, Any]]:
        """Get conflicts for a specific obligation.

        Args:
            obligation: The obligation to check

        Returns:
            List of conflict dictionaries
        """
        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM obligation_conflicts
                WHERE obligation_a = ? OR obligation_b = ?
                ORDER BY obligation_a, obligation_b
                """,
                (obligation, obligation),
            )

            return [
                {
                    "obligation_a": row["obligation_a"],
                    "obligation_b": row["obligation_b"],
                    "conflict_type": row["conflict_type"],
                    "severity": row["severity"],
                    "resolution_hint": row["resolution_hint"],
                }
                for row in cursor.fetchall()
            ]

    def get_all_obligation_conflicts(self) -> list[dict[str, Any]]:
        """Get all obligation conflicts.

        Returns:
            List of conflict dictionaries
        """
        with get_db() as conn:
            cursor = conn.execute(
                "SELECT * FROM obligation_conflicts ORDER BY obligation_a, obligation_b"
            )

            return [
                {
                    "obligation_a": row["obligation_a"],
                    "obligation_b": row["obligation_b"],
                    "conflict_type": row["conflict_type"],
                    "severity": row["severity"],
                    "resolution_hint": row["resolution_hint"],
                }
                for row in cursor.fetchall()
            ]

    def are_obligations_conflicting(
        self, obligation_a: str, obligation_b: str
    ) -> dict[str, Any] | None:
        """Check if two obligations conflict.

        Args:
            obligation_a: First obligation
            obligation_b: Second obligation

        Returns:
            Conflict dict if found, None otherwise
        """
        # Normalize order for lookup
        a, b = sorted([obligation_a, obligation_b])

        with get_db() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM obligation_conflicts
                WHERE obligation_a = ? AND obligation_b = ?
                """,
                (a, b),
            )
            row = cursor.fetchone()

            if row:
                return {
                    "obligation_a": row["obligation_a"],
                    "obligation_b": row["obligation_b"],
                    "conflict_type": row["conflict_type"],
                    "severity": row["severity"],
                    "resolution_hint": row["resolution_hint"],
                }
            return None

    def set_obligation_conflict(
        self,
        obligation_a: str,
        obligation_b: str,
        conflict_type: str,
        severity: str,
        resolution_hint: str | None = None,
    ) -> None:
        """Set or update an obligation conflict.

        Args:
            obligation_a: First obligation
            obligation_b: Second obligation
            conflict_type: Type of conflict
            severity: Conflict severity
            resolution_hint: Optional resolution guidance
        """
        # Normalize order for storage
        a, b = sorted([obligation_a, obligation_b])

        with get_db() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO obligation_conflicts
                (obligation_a, obligation_b, conflict_type, severity, resolution_hint)
                VALUES (?, ?, ?, ?, ?)
                """,
                (a, b, conflict_type, severity, resolution_hint),
            )
            conn.commit()

    # =========================================================================
    # Seed Operations
    # =========================================================================

    def seed_defaults(self) -> None:
        """Seed default configuration values.

        Migrates hardcoded values from pathway.py and conflicts.py to the database.
        """
        # Default step timelines (from pathway.py STEP_TIMELINES)
        default_timelines = [
            ("classify_instrument", 5, 15, "Initial instrument classification"),
            ("determine_jurisdiction", 3, 10, "Jurisdiction determination"),
            ("prepare_whitepaper", 30, 90, "Whitepaper preparation"),
            ("submit_authorization", 60, 180, "Authorization submission"),
            ("nca_review", 90, 270, "NCA review period"),
            ("ongoing_compliance", 0, 0, "Ongoing compliance (continuous)"),
        ]

        for step_id, min_days, max_days, description in default_timelines:
            self.set_step_timeline(step_id, min_days, max_days, "*", description)

        # Default step dependencies (from pathway.py STEP_DEPENDENCIES)
        default_dependencies = [
            ("determine_jurisdiction", "classify_instrument"),
            ("prepare_whitepaper", "classify_instrument"),
            ("submit_authorization", "prepare_whitepaper"),
            ("submit_authorization", "determine_jurisdiction"),
            ("nca_review", "submit_authorization"),
            ("ongoing_compliance", "nca_review"),
        ]

        for step_id, depends_on in default_dependencies:
            self.set_step_dependency(step_id, depends_on)

        # Default obligation conflicts (from conflicts.py EXCLUSIVE_OBLIGATION_PAIRS)
        default_conflicts = [
            ("exempt", "authorized", "classification", "blocking",
             "A token cannot be both exempt and require authorization"),
            ("custodial", "self_custodial", "custody", "blocking",
             "Custody model must be one or the other"),
            ("prospectus_required", "prospectus_exempt", "disclosure", "blocking",
             "Prospectus requirement is binary"),
        ]

        for obl_a, obl_b, conflict_type, severity, hint in default_conflicts:
            self.set_obligation_conflict(obl_a, obl_b, conflict_type, severity, hint)
