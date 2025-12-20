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
import pandas as pd

# Backend imports
from backend.rules import RuleLoader, Rule
from backend.rules.schema import DecisionBranch, DecisionLeaf
from backend.verify import ConsistencyEngine
from backend.analytics import ErrorPatternAnalyzer, DriftDetector
from backend.visualization import TreeAdapter, TreeGraph, TreeNode, rule_to_graph
from backend.rag.frontend_helpers import (
    get_rule_context,
    get_related_provisions,
    search_corpus,
    RuleContextPayload,
    RelatedProvision,
    SearchResult,
)

# Try to import Plotly for interactive charts
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

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

if "rule_context_cache" not in st.session_state:
    st.session_state.rule_context_cache = {}

if "last_search" not in st.session_state:
    st.session_state.last_search = None

if "indexed_documents" not in st.session_state:
    st.session_state.indexed_documents = []

if "rag_initialized" not in st.session_state:
    st.session_state.rag_initialized = False


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def initialize_rag() -> list[str]:
    """Initialize RAG by indexing documents from data/ folder."""
    from backend.rag.rule_context import RuleContextRetriever

    rule_ids = get_rule_ids()
    if rule_ids:
        get_rule_context(rule_ids[0])

    from backend.rag import frontend_helpers
    if frontend_helpers._context_retriever:
        return list(frontend_helpers._context_retriever.indexed_documents)
    return []


def get_cached_rule_context(rule_id: str) -> RuleContextPayload | None:
    """Get rule context with caching."""
    if rule_id not in st.session_state.rule_context_cache:
        ctx = get_rule_context(rule_id)
        st.session_state.rule_context_cache[rule_id] = ctx
    return st.session_state.rule_context_cache[rule_id]


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
        rebuild_tree_graph(rule)


def rebuild_tree_graph(rule: Rule) -> None:
    """Rebuild the tree graph for a rule with current consistency data."""
    adapter = TreeAdapter()
    result = st.session_state.verification_results.get(rule.rule_id)
    if result:
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
        "verified": "#28a745",
        "needs_review": "#ffc107",
        "inconsistent": "#dc3545",
        "unverified": "#6c757d",
    }.get(status, "#6c757d")


def get_status_emoji(status: str) -> str:
    """Map consistency status to emoji indicator."""
    return {
        "verified": "✓",
        "needs_review": "?",
        "inconsistent": "✗",
        "unverified": "○",
    }.get(status, "○")


def reset_selection() -> None:
    """Reset rule selection and clear caches."""
    st.session_state.selected_rule_id = None
    st.session_state.selected_node_id = None
    st.session_state.rule_context_cache = {}
    st.session_state.last_search = None


def select_node(node_id: str) -> None:
    """Set the selected node ID."""
    st.session_state.selected_node_id = node_id


# -----------------------------------------------------------------------------
# Sidebar: Organized with Expanders
# -----------------------------------------------------------------------------

with st.sidebar:
    # Initialize RAG on first load
    if not st.session_state.rag_initialized:
        with st.spinner("Indexing documents..."):
            st.session_state.indexed_documents = initialize_rag()
            st.session_state.rag_initialized = True

    st.header("Rule Selection")

    # Build rule options with metadata
    all_rules = st.session_state.rule_loader.get_all_rules()
    rule_ids = [r.rule_id for r in all_rules]

    # Create searchable display options
    rule_options = [""] + rule_ids  # Empty option for "none selected"
    rule_display_map = {"": "-- Select a rule --"}
    for r in all_rules:
        source_label = ""
        if r.source:
            doc = r.source.document_id.replace("_", " ").title()
            if r.source.article:
                source_label = f"[{doc} Art.{r.source.article}]"
            else:
                source_label = f"[{doc}]"
        desc = (r.description or "")[:35] + "..." if len(r.description or "") > 35 else (r.description or "")
        rule_display_map[r.rule_id] = f"{r.rule_id} {source_label}"

    if rule_ids:
        # Determine current index
        current_idx = 0
        if st.session_state.selected_rule_id and st.session_state.selected_rule_id in rule_ids:
            current_idx = rule_ids.index(st.session_state.selected_rule_id) + 1  # +1 for empty option

        selected = st.selectbox(
            "Select Rule",
            options=rule_options,
            format_func=lambda x: rule_display_map.get(x, x),
            index=current_idx,
            key="rule_selector",
            help="Choose a rule to inspect. Use the search box to filter.",
        )

        if selected:
            st.session_state.selected_rule_id = selected
        else:
            st.session_state.selected_rule_id = None

        # Rule count and Reset button
        col1, col2 = st.columns([2, 1])
        with col1:
            st.caption(f"{len(rule_ids)} rules loaded")
        with col2:
            if st.button("Reset", help="Clear selection and caches"):
                reset_selection()
                st.rerun()
    else:
        st.warning("No rules loaded. Add YAML rules to backend/rules/")

    st.divider()

    # Verification Controls in Expander
    with st.expander("Verification Actions", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Verify Rule", type="primary", disabled=not st.session_state.selected_rule_id, use_container_width=True):
                verify_current_rule()
                st.success("Done!")
        with col2:
            if st.button("Verify All", disabled=not rule_ids, use_container_width=True):
                with st.spinner("Verifying..."):
                    for rid in rule_ids:
                        rule = st.session_state.rule_loader.get_rule(rid)
                        if rule:
                            result = st.session_state.consistency_engine.verify_rule(rule)
                            st.session_state.verification_results[rid] = result
                            rebuild_tree_graph(rule)
                st.success(f"Verified {len(rule_ids)} rules")

        st.session_state.show_consistency = st.checkbox(
            "Show Consistency Overlay",
            value=st.session_state.show_consistency,
            help="Display consistency status colors on the decision tree",
        )

    # Corpus Search in Expander
    with st.expander("Corpus Search", expanded=False):
        search_query = st.text_input(
            "Search",
            placeholder="Art. 36(1) or 'reserve assets'",
            key="corpus_search_input",
            help="Search by article reference or keywords",
        )

        if search_query and st.button("Search", key="search_btn", use_container_width=True):
            with st.spinner("Searching..."):
                st.session_state.last_search = search_corpus(search_query)

        if st.session_state.last_search:
            result = st.session_state.last_search
            st.caption(f"Mode: {'Article lookup' if result.mode == 'article' else 'Semantic'}")

            if result.mode == "article" and result.article_hits:
                for hit in result.article_hits[:5]:
                    if st.button(f"→ {hit.rule_id}", key=f"sh_{hit.rule_id}", use_container_width=True):
                        st.session_state.selected_rule_id = hit.rule_id
                        st.rerun()
            elif result.semantic_hits:
                for i, hit in enumerate(result.semantic_hits[:5]):
                    label = f"{hit.document_id or 'Doc'} Art.{hit.article or '?'} ({hit.score:.2f})"
                    if hit.rule_id:
                        if st.button(f"→ {label}", key=f"sem_{i}", use_container_width=True):
                            st.session_state.selected_rule_id = hit.rule_id
                            st.rerun()
                    else:
                        st.caption(label)

            if st.button("Clear", key="clear_search", use_container_width=True):
                st.session_state.last_search = None
                st.rerun()

    # Quick Stats in Expander
    with st.expander("Quick Stats", expanded=True):
        total_rules = len(rule_ids)
        verified = sum(1 for r in st.session_state.verification_results.values() if r.summary.status == "verified")
        needs_review = sum(1 for r in st.session_state.verification_results.values() if r.summary.status == "needs_review")
        inconsistent = sum(1 for r in st.session_state.verification_results.values() if r.summary.status == "inconsistent")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total", total_rules)
            st.metric("Verified", verified)
        with col2:
            st.metric("Review", needs_review)
            st.metric("Issues", inconsistent)

    # Indexed Documents in Expander
    with st.expander("Indexed Documents", expanded=False):
        if st.session_state.indexed_documents:
            for doc_id in st.session_state.indexed_documents:
                st.markdown(f"✓ {doc_id}")
        else:
            st.info("No documents indexed.")


# -----------------------------------------------------------------------------
# Main Content Area
# -----------------------------------------------------------------------------

st.title("Knowledge Engineering Workbench")

rule = get_selected_rule()

if rule is None:
    st.info("Select a rule from the sidebar to begin.")

    # Show all rules summary if any verified
    if st.session_state.verification_results:
        st.markdown("### All Rules Summary")
        summary_data = []
        for rid, result in st.session_state.verification_results.items():
            pass_count = sum(1 for e in result.evidence if e.label == "pass")
            fail_count = sum(1 for e in result.evidence if e.label == "fail")
            warn_count = sum(1 for e in result.evidence if e.label == "warning")
            summary_data.append({
                "Rule ID": rid,
                "Status": result.summary.status,
                "Confidence": result.summary.confidence,
                "Pass": pass_count,
                "Fail": fail_count,
                "Warnings": warn_count,
            })

        df = pd.DataFrame(summary_data)
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "Confidence": st.column_config.ProgressColumn(
                    "Confidence",
                    min_value=0,
                    max_value=1,
                    format="%.2f",
                ),
                "Status": st.column_config.TextColumn("Status"),
            },
        )
else:
    # Rule header with status badge
    header_col1, header_col2 = st.columns([4, 1])

    with header_col1:
        st.subheader(f"Rule: {rule.rule_id}")
        if rule.source:
            st.caption(f"Source: {rule.source.document_id} {rule.source.article or ''}")

    with header_col2:
        if rule.rule_id in st.session_state.verification_results:
            result = st.session_state.verification_results[rule.rule_id]
            status = result.summary.status
            color = get_status_color(status)
            st.markdown(
                f'<div style="background-color:{color};color:white;'
                f'padding:8px 16px;border-radius:4px;text-align:center;font-weight:bold;">'
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

    # Rule description in expander if long
    if rule.description and len(rule.description) > 100:
        with st.expander("Description", expanded=False):
            st.markdown(rule.description)
    elif rule.description:
        st.caption(rule.description)

    st.divider()

    # Get tree graph
    graph = get_tree_graph(rule)

    # ----- TABS: Decision Tree | Node Details | Analytics -----
    tab_tree, tab_details, tab_analytics = st.tabs(["Decision Tree", "Node Details", "Analytics"])

    # ----- TAB 1: Decision Tree -----
    with tab_tree:
        tree_col, context_col = st.columns([2, 1])

        with tree_col:
            if graph.nodes:
                dot_source = graph.to_dot(show_consistency=st.session_state.show_consistency)
                st.graphviz_chart(dot_source, use_container_width=True)

                # Node selection as dataframe instead of button grid
                st.markdown("**Select a node to view details:**")
                node_data = []
                for node in graph.nodes:
                    label = node.decision if node.node_type == "leaf" else node.id
                    node_data.append({
                        "Node": label,
                        "Type": node.node_type,
                        "Status": node.consistency.status,
                        "Confidence": node.consistency.confidence,
                    })

                node_df = pd.DataFrame(node_data)

                # Use selectbox for node selection
                node_labels = [n.decision if n.node_type == "leaf" else n.id for n in graph.nodes]
                selected_node_label = st.selectbox(
                    "Select Node",
                    options=[""] + node_labels,
                    format_func=lambda x: x if x else "-- Select a node --",
                    key="node_selector",
                )

                if selected_node_label:
                    # Find the node by label
                    for node in graph.nodes:
                        label = node.decision if node.node_type == "leaf" else node.id
                        if label == selected_node_label:
                            st.session_state.selected_node_id = node.id
                            break
            else:
                st.warning("No decision tree defined for this rule.")

        with context_col:
            st.markdown("**Source & Context**")
            ctx = get_cached_rule_context(rule.rule_id)
            if ctx:
                st.markdown(f"**{ctx.document_id}** — Article {ctx.article or 'N/A'}")

                with st.expander("Primary span", expanded=True):
                    st.markdown(
                        f'<div style="background:#f8f9fa;padding:12px;border-radius:4px;'
                        f'border-left:3px solid #007bff;">{ctx.primary_span}</div>',
                        unsafe_allow_html=True,
                    )

                if ctx.before:
                    with st.expander("Preceding context"):
                        for para in ctx.before:
                            st.caption(para)

                if ctx.after:
                    with st.expander("Following context"):
                        for para in ctx.after:
                            st.caption(para)

                if ctx.pages:
                    st.caption(f"Pages: {', '.join(map(str, ctx.pages))}")
            else:
                st.info("No source context available.")

            # Tree source code
            with st.expander("Tree Source (DOT/Mermaid)"):
                source_tab1, source_tab2 = st.tabs(["DOT", "Mermaid"])
                with source_tab1:
                    st.code(graph.to_dot(show_consistency=st.session_state.show_consistency), language="dot")
                with source_tab2:
                    st.code(graph.to_mermaid(show_consistency=st.session_state.show_consistency), language="text")

    # ----- TAB 2: Node Details -----
    with tab_details:
        detail_col, related_col = st.columns([1, 1])

        with detail_col:
            selected_node = None
            if st.session_state.selected_node_id:
                selected_node = graph.get_node(st.session_state.selected_node_id)

            if selected_node:
                st.markdown(f"### Node: `{selected_node.id}`")
                st.markdown(f"**Type:** {selected_node.node_type}")

                if selected_node.node_type == "leaf":
                    st.markdown(f"**Decision:** `{selected_node.decision}`")
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

                st.divider()

                # Consistency info
                st.markdown("### Consistency Status")
                status = selected_node.consistency.status
                color = get_status_color(status)
                st.markdown(
                    f'<div style="background-color:{color};color:white;'
                    f'padding:8px 16px;border-radius:4px;text-align:center;margin-bottom:12px;">'
                    f'{get_status_emoji(status)} {status.upper()}</div>',
                    unsafe_allow_html=True,
                )

                st.progress(selected_node.consistency.confidence, text=f"Confidence: {selected_node.consistency.confidence:.0%}")

                # Evidence as dataframe
                if selected_node.consistency.evidence:
                    st.markdown("### Evidence")
                    evidence_data = []
                    for ev in selected_node.consistency.evidence:
                        evidence_data.append({
                            "Tier": ev.tier,
                            "Category": ev.category,
                            "Label": ev.label,
                            "Score": ev.score,
                            "Details": ev.details[:80] + "..." if len(ev.details or "") > 80 else (ev.details or ""),
                        })

                    ev_df = pd.DataFrame(evidence_data)
                    st.dataframe(ev_df, use_container_width=True, hide_index=True)
            else:
                st.info("Select a node from the Decision Tree tab to view details.")

                # Show rule-level evidence if available
                if rule.rule_id in st.session_state.verification_results:
                    result = st.session_state.verification_results[rule.rule_id]
                    st.markdown("### Rule-Level Evidence")

                    evidence_data = []
                    for ev in result.evidence:
                        evidence_data.append({
                            "Tier": ev.tier,
                            "Category": ev.category,
                            "Label": ev.label,
                            "Score": ev.score,
                            "Details": ev.details[:60] + "..." if len(ev.details or "") > 60 else (ev.details or ""),
                        })

                    ev_df = pd.DataFrame(evidence_data)
                    st.dataframe(
                        ev_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=1),
                        },
                    )

        with related_col:
            st.markdown("### Related Provisions")
            st.caption("Provisions with similarity score above 0.50")

            related = get_related_provisions(rule.rule_id, threshold=0.5, limit=10)
            if not related:
                st.info("No related provisions above threshold.")
            else:
                related_data = []
                for rp in related:
                    related_data.append({
                        "Document": rp.document_id,
                        "Article": rp.article or "N/A",
                        "Score": rp.score,
                        "Snippet": rp.snippet[:80] + "..." if len(rp.snippet) > 80 else rp.snippet,
                        "Rule ID": rp.rule_id or "",
                    })

                rel_df = pd.DataFrame(related_data)
                st.dataframe(
                    rel_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=1, format="%.2f"),
                    },
                )

                # Quick navigation buttons for related rules
                st.markdown("**Navigate to related rule:**")
                for rp in related:
                    if rp.rule_id and rp.rule_id != rule.rule_id:
                        if st.button(f"→ {rp.rule_id}", key=f"rel_{rp.rule_id}"):
                            st.session_state.selected_rule_id = rp.rule_id
                            st.rerun()

    # ----- TAB 3: Analytics -----
    with tab_analytics:
        if rule.rule_id not in st.session_state.verification_results:
            st.info("Run verification to see analytics.")
        else:
            result = st.session_state.verification_results[rule.rule_id]

            analytics_col1, analytics_col2 = st.columns(2)

            with analytics_col1:
                st.markdown("### Status Distribution")

                # Count by label
                label_counts = Counter(e.label for e in result.evidence)
                pass_count = label_counts.get("pass", 0)
                fail_count = label_counts.get("fail", 0)
                warn_count = label_counts.get("warning", 0)

                if PLOTLY_AVAILABLE:
                    # Interactive pie chart with Plotly
                    fig = go.Figure(data=[go.Pie(
                        labels=["Pass", "Fail", "Warning"],
                        values=[pass_count, fail_count, warn_count],
                        marker=dict(colors=["#28a745", "#dc3545", "#ffc107"]),
                        hole=0.4,
                        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
                    )])
                    fig.update_layout(
                        showlegend=True,
                        height=300,
                        margin=dict(t=20, b=20, l=20, r=20),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Fallback: metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Pass", pass_count)
                    with col2:
                        st.metric("Fail", fail_count)
                    with col3:
                        st.metric("Warnings", warn_count)

                # By tier breakdown
                st.markdown("**By Tier:**")
                tier_data = []
                for tier in sorted(set(e.tier for e in result.evidence)):
                    tier_ev = [e for e in result.evidence if e.tier == tier]
                    tier_data.append({
                        "Tier": f"Tier {tier}",
                        "Pass": sum(1 for e in tier_ev if e.label == "pass"),
                        "Fail": sum(1 for e in tier_ev if e.label == "fail"),
                        "Warning": sum(1 for e in tier_ev if e.label == "warning"),
                    })

                tier_df = pd.DataFrame(tier_data)
                st.dataframe(tier_df, use_container_width=True, hide_index=True)

            with analytics_col2:
                st.markdown("### Confidence Scores")

                if graph.nodes and any(n.consistency.confidence > 0 for n in graph.nodes):
                    if PLOTLY_AVAILABLE:
                        # Interactive bar chart with Plotly
                        node_labels = [n.decision if n.node_type == "leaf" else n.id for n in graph.nodes]
                        confidences = [n.consistency.confidence for n in graph.nodes]
                        colors = [get_status_color(n.consistency.status) for n in graph.nodes]

                        fig = go.Figure(data=[go.Bar(
                            x=node_labels,
                            y=confidences,
                            marker_color=colors,
                            hovertemplate="<b>%{x}</b><br>Confidence: %{y:.2%}<extra></extra>",
                        )])
                        fig.update_layout(
                            yaxis=dict(tickformat=".0%", range=[0, 1]),
                            height=300,
                            margin=dict(t=20, b=20, l=20, r=20),
                            xaxis_tickangle=-45,
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        # Fallback: dataframe
                        conf_data = []
                        for node in graph.nodes:
                            label = node.decision if node.node_type == "leaf" else node.id
                            conf_data.append({
                                "Node": label,
                                "Confidence": node.consistency.confidence,
                                "Status": node.consistency.status,
                            })
                        conf_df = pd.DataFrame(conf_data)
                        st.dataframe(
                            conf_df,
                            use_container_width=True,
                            column_config={
                                "Confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1),
                            },
                        )
                else:
                    st.info("No confidence scores available.")

                st.divider()

                st.markdown("### Error Patterns")

                fail_categories = Counter(e.category for e in result.evidence if e.label == "fail")
                warn_categories = Counter(e.category for e in result.evidence if e.label == "warning")

                if fail_categories:
                    st.markdown("**Failed Checks:**")
                    for cat, count in fail_categories.most_common(5):
                        st.error(f"{cat}: {count}")
                else:
                    st.success("No failed checks!")

                if warn_categories:
                    st.markdown("**Warnings:**")
                    for cat, count in warn_categories.most_common(3):
                        st.warning(f"{cat}: {count}")

        # All Rules Summary at bottom of analytics
        if st.session_state.verification_results:
            st.divider()
            with st.expander("All Rules Summary", expanded=False):
                summary_data = []
                for rid, res in st.session_state.verification_results.items():
                    pass_count = sum(1 for e in res.evidence if e.label == "pass")
                    fail_count = sum(1 for e in res.evidence if e.label == "fail")
                    warn_count = sum(1 for e in res.evidence if e.label == "warning")
                    summary_data.append({
                        "Rule ID": rid,
                        "Status": res.summary.status,
                        "Confidence": res.summary.confidence,
                        "Pass": pass_count,
                        "Fail": fail_count,
                        "Warnings": warn_count,
                    })

                df = pd.DataFrame(summary_data)
                st.dataframe(
                    df,
                    use_container_width=True,
                    column_config={
                        "Confidence": st.column_config.ProgressColumn("Confidence", min_value=0, max_value=1),
                    },
                )


# -----------------------------------------------------------------------------
# Footer
# -----------------------------------------------------------------------------

st.divider()
st.caption("KE Workbench v0.2 | Internal Use Only")
