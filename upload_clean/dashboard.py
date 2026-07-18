# dashboard.py
# AI Data Analysis Platform — Web Dashboard
# Built with Streamlit
# Version 1.0
#
# HOW TO RUN LOCALLY:
#   pip install streamlit
#   streamlit run dashboard.py
#
# HOW TO DEPLOY FREE:
#   Push to GitHub
#   Go to streamlit.io/cloud
#   Connect your repository
#   Select dashboard.py as main file
#   Deploy — your dashboard is live

import os
import io
import time
import tempfile
import logging
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from data_agent import DataAnalysisAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════
# PAGE CONFIGURATION
# ════════════════════════════════════════════════════════

st.set_page_config(
    page_title    = "AI Data Analysis Platform",
    page_icon     = "📊",
    layout        = "wide",
    initial_sidebar_state = "expanded"
)


# ════════════════════════════════════════════════════════
# CUSTOM STYLING
# ════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* Main background */
    .main {
        background-color: #0E1117;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background-color: #1C2333;
        border: 1px solid #2D3748;
        border-radius: 8px;
        padding: 16px;
    }

    /* Section headers */
    .section-header {
        background: linear-gradient(
            90deg, #1C2333, #2D3748
        );
        border-left: 4px solid #3B82F6;
        padding: 12px 16px;
        border-radius: 4px;
        margin: 16px 0 8px 0;
        font-size: 16px;
        font-weight: bold;
        color: #E2E8F0;
    }

    /* Domain badge */
    .domain-badge {
        background: linear-gradient(
            135deg, #1E40AF, #3B82F6
        );
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
        display: inline-block;
    }

    /* Executive summary box */
    .exec-summary {
        background-color: #1C2333;
        border: 1px solid #3B82F6;
        border-radius: 8px;
        padding: 20px;
        color: #E2E8F0;
        line-height: 1.7;
        font-size: 14px;
    }

    /* Warning box */
    .warning-box {
        background-color: #2D1B00;
        border: 1px solid #D97706;
        border-radius: 8px;
        padding: 12px 16px;
        color: #FCD34D;
        font-size: 13px;
    }

    /* Download button */
    .stDownloadButton button {
        background-color: #1D4ED8;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 20px;
        font-weight: bold;
        width: 100%;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab"] {
        background-color: #1C2333;
        border-radius: 6px;
        color: #94A3B8;
        font-weight: bold;
    }

    .stTabs [aria-selected="true"] {
        background-color: #1D4ED8;
        color: white;
    }

    /* Progress bar color */
    .stProgress .st-bo {
        background-color: #3B82F6;
    }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ════════════════════════════════════════════════════════

def init_session_state():
    """
    Initialize all session state variables.
    Streamlit reruns the script on every interaction
    so session state is how we preserve results
    between interactions.
    """
    defaults = {
        "agent":           None,
        "session":         None,
        "analysis_done":   False,
        "file_name":       None,
        "show_raw_data":   False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ════════════════════════════════════════════════════════
# AGENT INITIALIZATION
# ════════════════════════════════════════════════════════

@st.cache_resource
def get_agent():
    """
    Initialize the DataAnalysisAgent once and cache it.
    @st.cache_resource means this only runs once
    per session — not on every page interaction.
    """
    try:
        return DataAnalysisAgent(
            charts_folder        = "charts",
            reports_folder       = "reports",
            excel_reports_folder = "excel_reports",
            history_file         = "analysis_history.json"
        )
    except Exception as error:
        st.error(f"Agent initialization failed: {error}")
        return None


# ════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════

def render_sidebar(agent):
    """Render the sidebar with controls and history."""

    with st.sidebar:
        st.markdown("## ⚙️ Controls")
        st.markdown("---")

        # Session history
        total_sessions = agent.get_total_sessions()
        st.metric("Total Analyses Run", total_sessions)

        st.markdown("---")

        # Recent sessions
        if total_sessions > 0:
            st.markdown("### 📋 Recent Analyses")
            recent = agent.get_recent_sessions(count=5)
            for session in reversed(recent):
                status = (
                    "✅" if session.get("pipeline_success")
                    else "⚠️"
                )
                file   = session.get("file_name", "Unknown")
                date   = session.get(
                    "started_at", ""
                )[:16]
                rows   = session.get("total_rows", 0)
                st.markdown(
                    f"{status} **{file[:20]}**\n"
                    f"*{date} — {rows:,} rows*"
                )
                st.markdown("---")

        # Settings
        st.markdown("### 🔧 Settings")

        show_raw = st.checkbox(
            "Show raw data table",
            value=st.session_state.show_raw_data
        )
        st.session_state.show_raw_data = show_raw

        st.markdown("---")
        st.markdown(
            "**AI Data Analysis Platform**\n\n"
            "22 Domain Modules\n\n"
            "International Standards\n\n"
            "Built with Python + Gemini AI"
        )


# ════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════

def render_header():
    """Render the main header."""

    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(
            "# 📊 AI Data Analysis Platform"
        )
        st.markdown(
            "Upload any dataset and receive a complete "
            "professional analysis with AI-powered insights, "
            "statistical breakdowns, and domain-specific "
            "benchmarks from international standards."
        )

    with col2:
        st.markdown(
            "<br><br>"
            "<div style='text-align:right; "
            "color:#64748B; font-size:12px;'>"
            f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            "<br>22 Domains Active"
            "<br>Gemini AI Ready"
            "</div>",
            unsafe_allow_html=True
        )


# ════════════════════════════════════════════════════════
# FILE UPLOAD SECTION
# ════════════════════════════════════════════════════════

def render_upload_section():
    """Render the file upload interface."""

    st.markdown(
        "<div class='section-header'>"
        "📁 Upload Your Dataset"
        "</div>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "Choose a file to analyze",
            type=["csv", "xlsx", "xls", "json", "txt"],
            help=(
                "Supported formats: CSV, Excel, JSON, TXT\n"
                "Any domain, any industry, any size up to 50MB"
            )
        )

    with col2:
        st.markdown(
            "<br>"
            "<div style='color:#94A3B8; font-size:13px;'>"
            "✅ CSV files<br>"
            "✅ Excel workbooks<br>"
            "✅ JSON datasets<br>"
            "✅ Plain text files<br>"
            "<br>"
            "🔍 22 domains auto-detected<br>"
            "📊 6 chart types generated<br>"
            "📄 Full report exported"
            "</div>",
            unsafe_allow_html=True
        )

    return uploaded_file


# ════════════════════════════════════════════════════════
# ANALYSIS RUNNER
# ════════════════════════════════════════════════════════

def run_analysis(agent, uploaded_file):
    """
    Save uploaded file to temp location and run
    the complete analysis pipeline. Updates
    session state with results.
    """

    # Save uploaded file to temp directory
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        # Progress display
        progress_bar  = st.progress(0)
        status_text   = st.empty()

        status_text.text("🔍 Loading and profiling dataset...")
        progress_bar.progress(10)
        time.sleep(0.3)

        status_text.text("📊 Running statistical analysis...")
        progress_bar.progress(30)
        time.sleep(0.3)

        status_text.text("🎨 Generating visualizations...")
        progress_bar.progress(55)
        time.sleep(0.3)

        status_text.text("🤖 AI generating insights...")
        progress_bar.progress(75)

        # Run the actual pipeline
        session = agent.analyze(tmp_path)

        progress_bar.progress(95)
        status_text.text("📝 Finalizing reports...")
        time.sleep(0.3)

        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        time.sleep(0.5)

        progress_bar.empty()
        status_text.empty()

        # Store in session state
        st.session_state.session       = session
        st.session_state.analysis_done = True
        st.session_state.file_name     = uploaded_file.name

    finally:
        # Always clean temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# ════════════════════════════════════════════════════════
# RESULTS DISPLAY
# ════════════════════════════════════════════════════════

def render_overview_metrics(session):
    """Render the top-level metric cards."""

    st.markdown(
        "<div class='section-header'>"
        "📈 Dataset Overview"
        "</div>",
        unsafe_allow_html=True
    )

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric(
            "Total Records",
            f"{session.total_rows:,}"
        )
    with col2:
        st.metric(
            "Columns",
            session.total_columns
        )
    with col3:
        st.metric(
            "Completeness",
            f"{session.completeness_percent:.1f}%"
        )
    with col4:
        st.metric(
            "Anomalies",
            session.anomalies_detected
        )
    with col5:
        st.metric(
            "Correlations",
            session.correlations_found
        )
    with col6:
        st.metric(
            "Charts Generated",
            session.charts_generated
        )


def render_domain_detection(session):
    """Show which domain was detected."""

    domain = getattr(session, "domain", "general")
    if not domain:
        domain = "general"

    domain_icons = {
        "education":       "🎓",
        "healthcare":      "🏥",
        "finance":         "💰",
        "sales":           "📈",
        "hr":              "👥",
        "manufacturing":   "🏭",
        "logistics":       "🚚",
        "sports":          "⚽",
        "marketing":       "📣",
        "real_estate":     "🏠",
        "retail":          "🛒",
        "energy":          "⚡",
        "agriculture":     "🌾",
        "government":      "🏛",
        "insurance":       "🛡",
        "it_devops":       "💻",
        "social_media":    "📱",
        "cybersecurity":   "🔒",
        "ecommerce":       "🛍",
        "supply_chain":    "⛓",
        "hospitality":     "🏨",
        "telecommunications": "📡",
        "general":         "📊",
    }

    icon   = domain_icons.get(domain, "📊")
    label  = domain.replace("_", " ").upper()

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            f"<div style='text-align:center; padding:16px;'>"
            f"<div class='domain-badge'>"
            f"{icon} {label} DOMAIN DETECTED"
            f"</div>"
            f"<div style='color:#64748B; margin-top:8px; "
            f"font-size:12px;'>"
            f"International standards automatically applied"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True
        )


def render_executive_summary(session):
    """Display the AI executive summary."""

    st.markdown(
        "<div class='section-header'>"
        "🤖 AI Executive Summary"
        "</div>",
        unsafe_allow_html=True
    )

    if session.executive_summary:
        st.markdown(
            f"<div class='exec-summary'>"
            f"{session.executive_summary}"
            f"</div>",
            unsafe_allow_html=True
        )
    else:
        st.info(
            "Executive summary was not generated. "
            "Check AI API connection."
        )


def render_charts(session):
    """Display all generated charts in tabs."""

    if not session.chart_paths:
        st.warning(
            "No charts were generated for this dataset."
        )
        return

    st.markdown(
        "<div class='section-header'>"
        "📊 Visual Analysis"
        "</div>",
        unsafe_allow_html=True
    )

    chart_labels = {
        "01_overview":      "📈 Overview",
        "02_distributions": "📊 Distributions",
        "03_correlations":  "🔗 Correlations",
        "04_anomalies":     "⚠️ Anomalies",
        "05_trends":        "📉 Trends",
        "06_categorical":   "🏷️ Categorical",
    }

    available_charts = {}
    for path in session.chart_paths:
        for key, label in chart_labels.items():
            if key in path and os.path.exists(path):
                available_charts[label] = path
                break

    if not available_charts:
        st.warning("Chart files not found.")
        return

    tabs = st.tabs(list(available_charts.keys()))

    for tab, (label, chart_path) in zip(
        tabs, available_charts.items()
    ):
        with tab:
            try:
                st.image(
                    chart_path,
                    use_column_width=True
                )
            except Exception as error:
                st.error(
                    f"Could not load chart: {error}"
                )


def render_column_analysis(session):
    """Display column classification breakdown."""

    if not session.profile:
        return

    profile = session.profile

    st.markdown(
        "<div class='section-header'>"
        "🔍 Column Analysis"
        "</div>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📊 Numeric Columns**")
        if profile.numeric_columns:
            for col in profile.numeric_columns:
                st.markdown(f"• {col}")
        else:
            st.markdown("*None detected*")

    with col2:
        st.markdown("**📝 Text Columns**")
        if profile.text_columns:
            for col in profile.text_columns:
                st.markdown(f"• {col}")
        else:
            st.markdown("*None detected*")

    with col3:
        st.markdown("**📅 Datetime Columns**")
        if profile.datetime_columns:
            for col in profile.datetime_columns:
                st.markdown(f"• {col}")
        else:
            st.markdown("*None detected*")

        if profile.has_time_series:
            st.markdown(
                f"**Time range:**\n"
                f"{profile.time_range_start}\n"
                f"to {profile.time_range_end}"
            )


def render_statistical_summary(session):
    """Display statistical summary as an interactive table."""

    if not session.stats:
        return

    desc = session.stats.get("descriptive", {})
    if not desc:
        return

    st.markdown(
        "<div class='section-header'>"
        "📐 Statistical Summary"
        "</div>",
        unsafe_allow_html=True
    )

    # Build summary dataframe
    rows = []
    for col, stats in desc.items():
        rows.append({
            "Column":   col,
            "Count":    int(stats.get("count",    0)),
            "Mean":     round(float(stats.get("mean",     0)), 3),
            "Median":   round(float(stats.get("median",   0)), 3),
            "Std Dev":  round(float(stats.get("std",      0)), 3),
            "Min":      round(float(stats.get("min",      0)), 3),
            "Max":      round(float(stats.get("max",      0)), 3),
            "Skewness": round(float(stats.get("skewness", 0)), 3),
            "Missing":  int(stats.get("missing",  0)),
        })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


def render_anomalies(session):
    """Display detected anomalies."""

    if not session.stats:
        return

    anomalies = session.stats.get("anomalies", {})

    st.markdown(
        "<div class='section-header'>"
        "⚠️ Anomaly Detection"
        "</div>",
        unsafe_allow_html=True
    )

    if not anomalies:
        st.success(
            "✅ No significant anomalies detected "
            "in any variable using IQR method."
        )
        return

    rows = []
    for col, info in anomalies.items():
        rows.append({
            "Column":         col,
            "Anomaly Count":  info.get("anomaly_count", 0),
            "Anomaly %":      round(float(
                info.get("anomaly_percent", 0)
            ), 2),
            "Lower Bound":    round(float(
                info.get("lower_bound", 0)
            ), 3),
            "Upper Bound":    round(float(
                info.get("upper_bound", 0)
            ), 3),
            "Severity":       info.get("severity", ""),
        })

    df = pd.DataFrame(rows)

    def color_severity(val):
        colors = {
            "High":   "background-color: #7F1D1D; color: white",
            "Medium": "background-color: #78350F; color: white",
            "Low":    "background-color: #1C3A1C; color: white",
        }
        return colors.get(val, "")

    styled = df.style.applymap(
        color_severity,
        subset=["Severity"]
    )
    st.dataframe(styled, use_container_width=True, hide_index=True)


def render_correlations(session):
    """Display correlation findings."""

    if not session.stats:
        return

    correlations = session.stats.get("correlations", [])

    st.markdown(
        "<div class='section-header'>"
        "🔗 Correlation Analysis"
        "</div>",
        unsafe_allow_html=True
    )

    if not correlations:
        st.info(
            "No strong correlations (|r| > 0.5) "
            "detected between numeric variables."
        )
        return

    rows = []
    for corr in correlations:
        coeff     = corr.get("correlation", 0)
        direction = "Positive ↑" if coeff > 0 else "Negative ↓"
        rows.append({
            "Variable A":    corr.get("column_a", ""),
            "Variable B":    corr.get("column_b", ""),
            "Correlation r": round(float(coeff), 4),
            "Strength":      corr.get("strength", ""),
            "Direction":     direction,
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def render_raw_data(session):
    """Display raw data table when enabled."""

    if (
        not st.session_state.show_raw_data or
        session.profile is None or
        session.profile.dataframe is None
    ):
        return

    st.markdown(
        "<div class='section-header'>"
        "📋 Raw Data Preview"
        "</div>",
        unsafe_allow_html=True
    )

    df    = session.profile.dataframe
    total = len(df)

    st.caption(
        f"Showing first 100 rows of {total:,} total records"
    )
    st.dataframe(
        df.head(100),
        use_container_width=True
    )


def render_downloads(session):
    """Render download buttons for all outputs."""

    st.markdown(
        "<div class='section-header'>"
        "⬇️ Download Reports"
        "</div>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        if (
            session.text_report_path and
            os.path.exists(session.text_report_path)
        ):
            with open(
                session.text_report_path,
                "r", encoding="utf-8"
            ) as f:
                text_content = f.read()

            st.download_button(
                label      = "📄 Download Text Report",
                data       = text_content,
                file_name  = f"analysis_report_{session.session_id}.txt",
                mime       = "text/plain",
                use_container_width=True
            )
        else:
            st.button(
                "📄 Text Report Not Available",
                disabled=True,
                use_container_width=True
            )

    with col2:
        if (
            session.excel_report_path and
            os.path.exists(session.excel_report_path)
        ):
            with open(
                session.excel_report_path, "rb"
            ) as f:
                excel_content = f.read()

            st.download_button(
                label      = "📊 Download Excel Report",
                data       = excel_content,
                file_name  = f"analysis_report_{session.session_id}.xlsx",
                mime       = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.button(
                "📊 Excel Report Not Available",
                disabled=True,
                use_container_width=True
            )

    with col3:
        if session.chart_paths:
            # Create zip of all charts
            import zipfile
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(
                zip_buffer, "w",
                zipfile.ZIP_DEFLATED
            ) as zip_file:
                for chart_path in session.chart_paths:
                    if os.path.exists(chart_path):
                        zip_file.write(
                            chart_path,
                            os.path.basename(chart_path)
                        )
            zip_buffer.seek(0)

            st.download_button(
                label      = "🖼️ Download All Charts",
                data       = zip_buffer.getvalue(),
                file_name  = f"charts_{session.session_id}.zip",
                mime       = "application/zip",
                use_container_width=True
            )
        else:
            st.button(
                "🖼️ No Charts Available",
                disabled=True,
                use_container_width=True
            )


def render_ai_narrative(session):
    """Display the full AI narrative in an expandable section."""

    if not session.ai_narrative:
        return

    with st.expander(
        "📖 View Full AI Intelligence Analysis",
        expanded=False
    ):
        st.markdown(
            "<div style='color:#E2E8F0; "
            "line-height:1.8; font-size:14px;'>"
            + session.ai_narrative.replace("\n", "<br>") +
            "</div>",
            unsafe_allow_html=True
        )


def render_pipeline_status(session):
    """Show which pipeline stages completed."""

    with st.expander("⚙️ Pipeline Status", expanded=False):
        stages = [
            ("Data Load",      session.stage_loaded),
            ("Statistics",     session.stage_analyzed),
            ("Visualization",  session.stage_visualized),
            ("Report",         session.stage_reported),
        ]

        col1, col2, col3, col4 = st.columns(4)
        cols = [col1, col2, col3, col4]

        for col, (stage_name, completed) in zip(cols, stages):
            with col:
                icon   = "✅" if completed else "❌"
                color  = "#22C55E" if completed else "#EF4444"
                st.markdown(
                    f"<div style='text-align:center; "
                    f"padding:12px; background:#1C2333; "
                    f"border-radius:8px; "
                    f"border:1px solid {color};'>"
                    f"<div style='font-size:24px;'>{icon}</div>"
                    f"<div style='color:#E2E8F0; "
                    f"font-size:12px; margin-top:4px;'>"
                    f"{stage_name}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

        if session.stage_errors:
            st.markdown("**Stage Errors:**")
            for stage, error in session.stage_errors.items():
                st.markdown(
                    f"<div class='warning-box'>"
                    f"⚠️ [{stage}] {error}"
                    f"</div>",
                    unsafe_allow_html=True
                )

        duration = session.duration_seconds
        duration_str = (
            f"{duration:.1f} seconds"
            if duration < 60
            else f"{duration/60:.1f} minutes"
        )
        st.markdown(
            f"**Total duration:** {duration_str} | "
            f"**AI model:** {session.model_used or 'N/A'} | "
            f"**Session:** {session.session_id}"
        )


# ════════════════════════════════════════════════════════
# MAIN APPLICATION
# ════════════════════════════════════════════════════════

def main():
    """Main dashboard application entry point."""

    init_session_state()

    agent = get_agent()
    if agent is None:
        st.error(
            "Failed to initialize the AI agent. "
            "Check that GEMINI_API_KEY is set "
            "in your environment or .env file."
        )
        st.stop()

    render_sidebar(agent)
    render_header()

    st.markdown("---")

    uploaded_file = render_upload_section()

    if uploaded_file is not None:

        file_changed = (
            uploaded_file.name !=
            st.session_state.file_name
        )

        if file_changed:
            st.session_state.analysis_done = False

        if not st.session_state.analysis_done:
            st.markdown("---")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                analyze_clicked = st.button(
                    "🚀 Run Complete Analysis",
                    use_container_width=True,
                    type="primary"
                )

            if analyze_clicked:
                with st.spinner(
                    "Running AI analysis pipeline..."
                ):
                    run_analysis(agent, uploaded_file)
                st.rerun()

        if st.session_state.analysis_done:
            session = st.session_state.session

            if session is None:
                st.error("Analysis session not found.")
                return

            st.markdown("---")

            render_domain_detection(session)
            st.markdown("---")

            render_overview_metrics(session)
            st.markdown("---")

            render_executive_summary(session)
            st.markdown("---")

            render_charts(session)
            st.markdown("---")

            tab1, tab2, tab3, tab4 = st.tabs([
                "📐 Statistics",
                "⚠️ Anomalies",
                "🔗 Correlations",
                "🔍 Columns"
            ])

            with tab1:
                render_statistical_summary(session)

            with tab2:
                render_anomalies(session)

            with tab3:
                render_correlations(session)

            with tab4:
                render_column_analysis(session)

            st.markdown("---")
            render_ai_narrative(session)
            st.markdown("---")
            render_downloads(session)
            st.markdown("---")
            render_pipeline_status(session)

            if st.session_state.show_raw_data:
                st.markdown("---")
                render_raw_data(session)

    else:
        # Welcome screen when no file uploaded
        st.markdown("---")
        st.markdown(
            "<div style='text-align:center; "
            "padding:60px 20px; color:#64748B;'>"
            "<div style='font-size:48px;'>📊</div>"
            "<h2 style='color:#94A3B8;'>"
            "Upload a dataset to begin</h2>"
            "<p>Drag and drop or click Browse "
            "to select your file</p>"
            "<p style='font-size:13px;'>"
            "CSV · Excel · JSON · TXT"
            "</p>"
            "</div>",
            unsafe_allow_html=True
        )

        # Domain showcase
        st.markdown(
            "<div class='section-header'>"
            "🌍 Supported Domains"
            "</div>",
            unsafe_allow_html=True
        )

        domains = [
            ("🎓", "Education",    "UNESCO/OECD"),
            ("🏥", "Healthcare",   "WHO/HIMSS"),
            ("💰", "Finance",      "IFRS/CFA"),
            ("📈", "Sales",        "Salesforce"),
            ("👥", "HR",           "SHRM/ISO 30414"),
            ("🏭", "Manufacturing","ISO 22400"),
            ("🚚", "Logistics",    "CSCMP"),
            ("⚽", "Sports",       "Opta/FIFA"),
            ("📣", "Marketing",    "Google/HubSpot"),
            ("🏠", "Real Estate",  "NAR/RICS"),
            ("🛒", "Retail",       "NRF"),
            ("⚡", "Energy",       "IEA/IRENA"),
            ("🌾", "Agriculture",  "FAO/USDA"),
            ("🏛", "Government",   "OECD"),
            ("🛡", "Insurance",    "IAIS"),
            ("💻", "IT/DevOps",    "DORA/ITIL"),
            ("📱", "Social Media", "Sprout Social"),
            ("🔒", "Cybersecurity","NIST/ISO 27001"),
            ("🛍", "E-Commerce",   "Shopify/Baymard"),
            ("⛓", "Supply Chain", "SCOR/Gartner"),
            ("🏨", "Hospitality",  "STR"),
            ("📡", "Telecom",      "ITU/GSMA"),
        ]

        cols = st.columns(4)
        for i, (icon, name, standard) in enumerate(domains):
            with cols[i % 4]:
                st.markdown(
                    f"<div style='background:#1C2333; "
                    f"border:1px solid #2D3748; "
                    f"border-radius:8px; "
                    f"padding:12px; margin:4px 0; "
                    f"text-align:center;'>"
                    f"<div style='font-size:20px;'>{icon}</div>"
                    f"<div style='color:#E2E8F0; "
                    f"font-weight:bold; font-size:13px;'>"
                    f"{name}</div>"
                    f"<div style='color:#64748B; "
                    f"font-size:10px;'>{standard}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )


if __name__ == "__main__":
    main()