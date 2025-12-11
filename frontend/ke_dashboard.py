"""
Knowledge Engineering Dashboard - Interactive Rule Visualization.

A Streamlit app for KE team to inspect decision trees with consistency overlays.

Run from repo root:
    streamlit run frontend/ke_dashboard.py
"""

import sys
from pathlib import Path
from collections import Counter

# Add backend to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

# Backend imports
from backend.rules import RuleLoader, Rule
from backend.rules.schema import DecisionBranch, DecisionLeaf
from backend.verify import ConsistencyEngine
from backend.analytics import ErrorPatternAnalyzer, DriftDetector
from backend.visualization import TreeAdapter, TreeGraph, TreeNode, rule_to_graph

# -----------------------------------------------------------------------------
# Page Configuration
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="KE Workbench",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------

if "rule_loader" not in st.session_state:
    st.session_state.rule_loader = RuleLoader()
    # Load rules from backend/rules directory
    rules_dir = Path(__file__).parent.parent / "backend" / "rules"
    try:
        st.session_state.rule_loader.load_directory(rules_dir)
    except FileNotFoundError:
        pass  # No rules directory yet

if "consistency_engine" not in st.session_state:
    st.session_state.consistency_engine = ConsistencyEngine()

if "selected_rule_id" not in st.session_state:
    st.session_state.selected_rule_id = None

if "selected_node_id" not in st.session_state:
    st.session_state.selected_node_id = None

if "verification_results" not in st.session_state:
    st.session_state.verification_results = {}

if "tree_graphs" not in st.session_state:
    st.session_state.tree_graphs = {}

if "show_consistency" not in st.session_state:
    st.session_state.show_consistency = True


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def get_rule_ids() -> list[str]:
    """Get all available rule IDs."""
    return [r.rule_id for r in st.session_state.rule_loader.get_all_rules()]


def get_selected_rule() -> Rule | None:
    """Get the currently selected rule."""
    rule_id = st.session_state.selected_rule_id
    if rule_id:
        return st.session_state.rule_loader.get_rule(rule_id)
    return None


def verify_current_rule() -> None:
    """Run verification on the current rule and store results."""
    rule = get_selected_rule()
    if rule:
        result = st.session_state.consistency_engine.verify_rule(rule)
        st.session_state.verification_results[rule.rule_id] = result
        # Rebuild tree graph with consistency overlay
        rebuild_tree_graph(rule)


def rebuild_tree_graph(rule: Rule) -> None:
    """Rebuild the tree graph for a rule with current consistency data."""
    adapter = TreeAdapter()

    # Get consistency data if available
    result = st.session_state.verification_results.get(rule.rule_id)
    if result:
        # Create a temporary rule with the verification result
        rule_with_consistency = rule.model_copy()
        rule_with_consistency.consistency = result
        node_map = adapter.build_node_consistency_map(rule_with_consistency)
        graph = adapter.convert(rule_with_consistency, node_map)
    else:
        graph = adapter.convert(rule)

    st.session_state.tree_graphs[rule.rule_id] = graph


def get_tree_graph(rule: Rule) -> TreeGraph:
    """Get or create tree graph for a rule."""
    if rule.rule_id not in st.session_state.tree_graphs:
        rebuild_tree_graph(rule)
    return st.session_state.tree_graphs[rule.rule_id]


def get_status_color(status: str) -> str:
    """Map consistency status to display color."""
    return {
        "verified": "#28a745",      # green
        "needs_review": "#ffc107",  # yellow
        "inconsistent": "#dc3545",  # red
        "unverified": "#6c757d",    # gray
    }.get(status, "#6c757d")


def get_status_emoji(status: str) -> str:
    """Map consistency status to emoji indicator."""
    return {
        "verified": "✓",
        "needs_review": "?",
        "inconsistent": "✗",
        "unverified": "○",
    }.get(status, "○")


def select_node(node_id: str) -> None:
    """Set the selected node ID."""
    st.session_state.selected_node_id = node_id


# -----------------------------------------------------------------------------
# Sidebar: Rule Selection & Controls
# -----------------------------------------------------------------------------

with st.sidebar:
    st.header("Rule Selection")

    # Rule dropdown
    rule_ids = get_rule_ids()

    if rule_ids:
        selected = st.selectbox(
            "Select Rule",
            options=rule_ids,
            index=0 if st.session_state.selected_rule_id is None else (
                rule_ids.index(st.session_state.selected_rule_id)
                if st.session_state.selected_rule_id in rule_ids
                else 0
            ),
            key="rule_selector",
        )
        st.session_state.selected_rule_id = selected
    else:
        st.warning("No rules loaded. Add YAML rules to backend/rules/packs/")
        st.session_state.selected_rule_id = None

    st.divider()

    # Verification controls
    st.header("Verification")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Verify Rule", type="primary", disabled=not rule_ids):
            verify_current_rule()
            st.success("Verified!")

    with col2:
        if st.button("Verify All", disabled=not rule_ids):
            with st.spinner("Verifying all rules..."):
                for rid in rule_ids:
                    rule = st.session_state.rule_loader.get_rule(rid)
                    if rule:
                        result = st.session_state.consistency_engine.verify_rule(rule)
                        st.session_state.verification_results[rid] = result
                        rebuild_tree_graph(rule)
            st.success(f"Verified {len(rule_ids)} rules")

    st.divider()

    # Display options
    st.header("Display")
    st.session_state.show_consistency = st.checkbox(
        "Show Consistency Overlay",
        value=st.session_state.show_consistency,
    )

    st.divider()

    # Quick stats
    st.header("Quick Stats")

    total_rules = len(rule_ids)
    verified_count = sum(
        1 for r in st.session_state.verification_results.values()
        if r.summary.status == "verified"
    )
    needs_review_count = sum(
        1 for r in st.session_state.verification_results.values()
        if r.summary.status == "needs_review"
    )
    inconsistent_count = sum(
        1 for r in st.session_state.verification_results.values()
        if r.summary.status == "inconsistent"
    )

    st.metric("Total Rules", total_rules)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Verified", verified_count)
    with col2:
        st.metric("Review", needs_review_count)
    with col3:
        st.metric("Issues", inconsistent_count)


# -----------------------------------------------------------------------------
# Main Content Area
# -----------------------------------------------------------------------------

st.title("Knowledge Engineering Workbench")

rule = get_selected_rule()

if rule is None:
    st.info("Select a rule from the sidebar to begin.")
else:
    # Rule header with status badge
    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader(f"Rule: {rule.rule_id}")
        if rule.source:
            st.caption(f"Source: {rule.source.document_id} {rule.source.article or ''}")
        elif rule.description:
            st.caption(rule.description)

    with col2:
        # Show verification status if available
        if rule.rule_id in st.session_state.verification_results:
            result = st.session_state.verification_results[rule.rule_id]
            status = result.summary.status
            color = get_status_color(status)
            st.markdown(
                f'<div style="background-color:{color};color:white;'
                f'padding:8px 16px;border-radius:4px;text-align:center;">'
                f'{status.upper()}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="background-color:#6c757d;color:white;'
                'padding:8px 16px;border-radius:4px;text-align:center;">'
                'UNVERIFIED</div>',
                unsafe_allow_html=True,
            )

    st.divider()

    # Get tree graph
    graph = get_tree_graph(rule)

    # ----- Upper Section: Tree + Detail Panel -----
    upper_left, upper_right = st.columns([2, 1])

    with upper_left:
        st.markdown("### Decision Tree")

        # Render tree using Graphviz
        if graph.nodes:
            dot_source = graph.to_dot(show_consistency=st.session_state.show_consistency)
            st.graphviz_chart(dot_source, use_container_width=True)

            # Node selection buttons
            st.markdown("**Select Node:**")
            node_cols = st.columns(min(len(graph.nodes), 5))
            for i, node in enumerate(graph.nodes):
                col_idx = i % min(len(graph.nodes), 5)
                with node_cols[col_idx]:
                    label = node.decision if node.node_type == "leaf" else node.id
                    is_selected = st.session_state.selected_node_id == node.id
                    btn_type = "primary" if is_selected else "secondary"
                    if st.button(
                        f"{get_status_emoji(node.consistency.status)} {label[:15]}",
                        key=f"node_{node.id}",
                        type=btn_type,
                        use_container_width=True,
                    ):
                        select_node(node.id)
                        st.rerun()
        else:
            st.warning("No decision tree defined for this rule.")

        # Show DOT/Mermaid source in expander
        with st.expander("View Source", expanded=False):
            tab1, tab2 = st.tabs(["Graphviz DOT", "Mermaid"])
            with tab1:
                st.code(graph.to_dot(show_consistency=st.session_state.show_consistency), language="dot")
            with tab2:
                st.code(graph.to_mermaid(show_consistency=st.session_state.show_consistency), language="text")

    with upper_right:
        st.markdown("### Node Details")

        # Get selected node
        selected_node = None
        if st.session_state.selected_node_id:
            selected_node = graph.get_node(st.session_state.selected_node_id)

        if selected_node:
            # Node info card
            st.markdown(f"**Node ID:** `{selected_node.id}`")
            st.markdown(f"**Type:** {selected_node.node_type}")

            # Condition or decision
            if selected_node.node_type == "leaf":
                st.markdown(f"**Decision:** {selected_node.decision}")
                if selected_node.obligations:
                    st.markdown("**Obligations:**")
                    for obl in selected_node.obligations:
                        st.markdown(f"- {obl}")
            else:
                if selected_node.condition_field:
                    st.markdown("**Condition:**")
                    st.code(
                        f"{selected_node.condition_field} {selected_node.condition_operator} {selected_node.condition_value}",
                        language="text",
                    )
                if selected_node.description:
                    st.caption(selected_node.description)

            st.divider()

            # Consistency info
            st.markdown("#### Consistency Status")

            status = selected_node.consistency.status
            color = get_status_color(status)
            st.markdown(
                f'<div style="background-color:{color};color:white;'
                f'padding:6px 12px;border-radius:4px;text-align:center;margin-bottom:12px;">'
                f'{get_status_emoji(status)} {status.upper()}</div>',
                unsafe_allow_html=True,
            )

            # Confidence meter
            confidence = selected_node.consistency.confidence
            st.progress(confidence, text=f"Confidence: {confidence:.0%}")

            # Pass/Fail/Warning counts
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Pass", selected_node.consistency.pass_count)
            with col2:
                st.metric("Fail", selected_node.consistency.fail_count)
            with col3:
                st.metric("Warn", selected_node.consistency.warning_count)

            # Evidence list
            if selected_node.consistency.evidence:
                st.markdown("#### Evidence")
                for evidence in selected_node.consistency.evidence:
                    tier_label = f"Tier {evidence.tier}"
                    if evidence.label == "pass":
                        label_color = "#28a745"
                    elif evidence.label == "fail":
                        label_color = "#dc3545"
                    else:
                        label_color = "#ffc107"

                    st.markdown(
                        f'<div style="margin-bottom:8px;">'
                        f'<span style="background:{label_color};color:white;'
                        f'padding:2px 6px;border-radius:3px;font-size:12px;">'
                        f'{evidence.label.upper()}</span> '
                        f'<strong>{evidence.category}</strong> '
                        f'<span style="color:#666;">({tier_label})</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if evidence.details:
                        st.caption(evidence.details[:150])
        else:
            # No node selected - show rule-level verification
            st.info("Click a node button above to see details.")

            if rule.rule_id in st.session_state.verification_results:
                result = st.session_state.verification_results[rule.rule_id]

                st.markdown("#### Rule-Level Evidence")

                # Show first few evidence items
                for evidence in result.evidence[:6]:
                    tier_label = f"Tier {evidence.tier}"
                    if evidence.label == "pass":
                        label_color = "#28a745"
                    elif evidence.label == "fail":
                        label_color = "#dc3545"
                    else:
                        label_color = "#ffc107"

                    st.markdown(
                        f'<div style="margin-bottom:8px;">'
                        f'<span style="background:{label_color};color:white;'
                        f'padding:2px 6px;border-radius:3px;font-size:12px;">'
                        f'{evidence.label.upper()}</span> '
                        f'<strong>{evidence.category}</strong> '
                        f'<span style="color:#666;">({tier_label})</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if evidence.details:
                        st.caption(evidence.details[:100])

                if len(result.evidence) > 6:
                    st.caption(f"... and {len(result.evidence) - 6} more")

    st.divider()

    # ----- Lower Section: Tree-Level Analytics -----
    st.markdown("### Tree-Level Analytics")

    # Analytics columns
    analytics_cols = st.columns(3)

    with analytics_cols[0]:
        st.markdown("#### Status Distribution")

        if rule.rule_id in st.session_state.verification_results:
            result = st.session_state.verification_results[rule.rule_id]

            # Count by label
            label_counts = Counter(e.label for e in result.evidence)

            # Display as colored bars
            total = sum(label_counts.values())
            if total > 0:
                pass_pct = label_counts.get("pass", 0) / total
                fail_pct = label_counts.get("fail", 0) / total
                warn_pct = label_counts.get("warning", 0) / total

                st.markdown(
                    f'<div style="display:flex;height:24px;border-radius:4px;overflow:hidden;">'
                    f'<div style="background:#28a745;width:{pass_pct*100:.1f}%;"></div>'
                    f'<div style="background:#dc3545;width:{fail_pct*100:.1f}%;"></div>'
                    f'<div style="background:#ffc107;width:{warn_pct*100:.1f}%;"></div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Legend
                st.markdown(
                    f'<div style="display:flex;gap:16px;margin-top:8px;font-size:12px;">'
                    f'<span style="color:#28a745;">Pass: {label_counts.get("pass", 0)}</span>'
                    f'<span style="color:#dc3545;">Fail: {label_counts.get("fail", 0)}</span>'
                    f'<span style="color:#ffc107;">Warn: {label_counts.get("warning", 0)}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            # By tier
            st.markdown("**By Tier:**")
            tier_counts = Counter(e.tier for e in result.evidence)
            for tier in sorted(tier_counts.keys()):
                tier_evidence = [e for e in result.evidence if e.tier == tier]
                tier_pass = sum(1 for e in tier_evidence if e.label == "pass")
                tier_fail = sum(1 for e in tier_evidence if e.label == "fail")
                st.markdown(
                    f"Tier {tier}: {tier_pass} pass, {tier_fail} fail"
                )
        else:
            st.info("Run verification to see status distribution.")

    with analytics_cols[1]:
        st.markdown("#### Confidence Scores")

        if graph.nodes:
            # Get confidence values from nodes
            confidences = [n.consistency.confidence for n in graph.nodes]

            if any(c > 0 for c in confidences):
                # Simple bar representation
                for node in graph.nodes:
                    label = node.decision if node.node_type == "leaf" else node.id
                    conf = node.consistency.confidence
                    color = get_status_color(node.consistency.status)

                    st.markdown(
                        f'<div style="margin-bottom:6px;">'
                        f'<div style="font-size:12px;margin-bottom:2px;">{label[:20]}</div>'
                        f'<div style="background:#e9ecef;border-radius:4px;overflow:hidden;height:16px;">'
                        f'<div style="background:{color};width:{conf*100:.1f}%;height:100%;"></div>'
                        f'</div>'
                        f'<div style="font-size:10px;color:#666;">{conf:.0%}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No confidence scores available yet.")
        else:
            st.info("No tree nodes to analyze.")

    with analytics_cols[2]:
        st.markdown("#### Error Patterns")

        if rule.rule_id in st.session_state.verification_results:
            result = st.session_state.verification_results[rule.rule_id]

            # Group failures by category
            fail_categories = Counter(
                e.category for e in result.evidence if e.label == "fail"
            )

            if fail_categories:
                st.markdown("**Failed Checks:**")
                for category, count in fail_categories.most_common(5):
                    st.markdown(
                        f'<div style="margin-bottom:4px;">'
                        f'<span style="background:#dc3545;color:white;'
                        f'padding:2px 6px;border-radius:3px;font-size:11px;margin-right:6px;">'
                        f'{count}</span>'
                        f'{category}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.success("No failed checks!")

            # Warnings
            warn_categories = Counter(
                e.category for e in result.evidence if e.label == "warning"
            )

            if warn_categories:
                st.markdown("**Warnings:**")
                for category, count in warn_categories.most_common(3):
                    st.markdown(
                        f'<div style="margin-bottom:4px;">'
                        f'<span style="background:#ffc107;color:black;'
                        f'padding:2px 6px;border-radius:3px;font-size:11px;margin-right:6px;">'
                        f'{count}</span>'
                        f'{category}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.info("Run verification to detect error patterns.")

    # Verification summary table (all rules)
    if st.session_state.verification_results:
        with st.expander("All Rules Summary", expanded=False):
            summary_data = []
            for rid, result in st.session_state.verification_results.items():
                pass_count = sum(1 for e in result.evidence if e.label == "pass")
                fail_count = sum(1 for e in result.evidence if e.label == "fail")
                warn_count = sum(1 for e in result.evidence if e.label == "warning")
                summary_data.append({
                    "Rule ID": rid,
                    "Status": result.summary.status,
                    "Confidence": f"{result.summary.confidence:.2f}",
                    "Pass": pass_count,
                    "Fail": fail_count,
                    "Warn": warn_count,
                })

            if summary_data:
                st.dataframe(summary_data, use_container_width=True)


# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------

st.divider()
st.caption("KE Workbench v0.1 | Internal Use Only")
