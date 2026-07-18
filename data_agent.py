# data_agent.py
# AI Data Analysis Agent — Orchestration Brain
# Version 1.0 — Developer reviewed
#
# ARCHITECTURAL ROLE:
#   This is the single entry point for all analysis
#   operations. Every caller — main.py, a Telegram bot,
#   a web API, or any future interface — interacts
#   exclusively with this class. The internal pipeline
#   structure is completely hidden from callers.
#
# PIPELINE MANAGED:
#   UniversalDataLoader      →  load and profile data
#   StatisticalAnalyzer      →  extract all statistics
#   DataVisualizer           →  generate chart suite
#   ReportGenerator          →  produce text and Excel
#
# AGENT CYCLE:
#   PERCEIVE  →  load and validate the dataset
#   THINK     →  analyze statistically and with AI
#   ACT       →  generate all outputs
#   REMEMBER  →  persist session history
#
# SESSION MANAGEMENT:
#   Every analysis run is tracked as a named session.
#   Sessions are stored in analysis_history.json.
#   Each session records inputs, outputs, timing,
#   quality metrics, and pipeline stage results.
#   Past sessions are available for comparison and
#   longitudinal tracking across multiple analyses.

import os
import json
import logging
import time
import traceback
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from data_loader import UniversalDataLoader
from statistical_analyzer import StatisticalAnalyzer
from visualizer import DataVisualizer
from report_generator import ReportGenerator

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════
# ANALYSIS SESSION — Complete record of one run
# ════════════════════════════════════════════════════════

@dataclass
class AnalysisSession:
    """
    The complete record of a single analysis run.
    Returned to callers as the primary output object.
    Contains everything produced during the run —
    component outputs, file paths, timing data,
    quality metrics, and any errors encountered.

    Callers should check pipeline_success before
    attempting to use output paths or AI content.
    Individual stage_completed flags allow callers
    to determine exactly how far the pipeline ran
    when a partial failure occurs.
    """

    session_id:   str = ""
    file_path:    str = ""
    file_name:    str = ""
    started_at:   str = ""
    completed_at: str = ""
    duration_seconds: float = 0.0

    # Pipeline stage completion flags
    stage_loaded:     bool = False
    stage_analyzed:   bool = False
    stage_visualized: bool = False
    stage_reported:   bool = False

    # Component outputs — populated as pipeline runs
    profile    = None
    stats:    dict  = field(default_factory=dict)
    viz_result = None
    report_result = None

    # Derived outputs for caller convenience
    text_report_path:  Optional[str] = None
    excel_report_path: Optional[str] = None
    charts_folder:     Optional[str] = None
    chart_paths:       list = field(default_factory=list)

    # AI content extracted for Telegram delivery
    executive_summary: str = ""
    ai_narrative:      str = ""
    model_used:        str = ""

    # Quality metrics
    total_rows:            int   = 0
    total_columns:         int   = 0
    completeness_percent:  float = 0.0
    anomalies_detected:    int   = 0
    correlations_found:    int   = 0
    charts_generated:      int   = 0

    # Status
    pipeline_success: bool = False
    pipeline_error:   Optional[str] = None
    stage_errors:     dict = field(default_factory=dict)
    warnings:         list = field(default_factory=list)

    def get_telegram_summary(self) -> str:
        """
        Condensed summary formatted for Telegram delivery.
        Respects Telegram character limits and provides
        the essential findings without overwhelming
        the mobile reader.
        """

        status_icon = "✅" if self.pipeline_success else "⚠️"

        duration_str = (
            f"{self.duration_seconds:.1f}s"
            if self.duration_seconds < 60
            else f"{self.duration_seconds / 60:.1f}m"
        )

        summary = (
            f"{status_icon} ANALYSIS COMPLETE\n"
            f"{'─' * 38}\n\n"
            f"File     : {self.file_name}\n"
            f"Records  : {self.total_rows:,}\n"
            f"Columns  : {self.total_columns}\n"
            f"Quality  : {self.completeness_percent:.1f}%\n"
            f"Duration : {duration_str}\n\n"
            f"FINDINGS\n"
            f"  Anomalies     : {self.anomalies_detected}\n"
            f"  Correlations  : {self.correlations_found}\n"
            f"  Charts saved  : {self.charts_generated}\n\n"
            f"OUTPUTS SAVED\n"
        )

        if self.text_report_path:
            summary += (
                f"  Text report   : "
                f"{os.path.basename(self.text_report_path)}\n"
            )
        if self.excel_report_path:
            summary += (
                f"  Excel report  : "
                f"{os.path.basename(self.excel_report_path)}\n"
            )

        if self.executive_summary:
            summary += (
                f"\nEXECUTIVE SUMMARY\n"
                f"{'─' * 38}\n"
                f"{self.executive_summary[:600]}"
                f"{'...' if len(self.executive_summary) > 600 else ''}\n"
            )

        if self.stage_errors:
            summary += f"\nWARNINGS\n"
            for stage, error in self.stage_errors.items():
                summary += (
                    f"  {stage}: {str(error)[:80]}\n"
                )

        return summary

    def get_terminal_summary(self) -> str:
        """
        Detailed summary for terminal display during
        development and testing. Covers every pipeline
        stage with timing and output confirmation.
        """

        width = 60
        sep   = "═" * width

        lines = [
            sep,
            "  AI DATA ANALYSIS AGENT — SESSION REPORT",
            sep,
            f"  Session ID   : {self.session_id}",
            f"  File         : {self.file_name}",
            f"  Started      : {self.started_at}",
            f"  Completed    : {self.completed_at}",
            f"  Duration     : {self.duration_seconds:.2f}s",
            f"  Status       : "
            f"{'SUCCESS' if self.pipeline_success else 'PARTIAL / FAILED'}",
            "",
            "  PIPELINE STAGES",
            f"  {'─' * 38}",
            f"  Load      : {'✔ Complete' if self.stage_loaded else '✗ Failed'}",
            f"  Analyze   : {'✔ Complete' if self.stage_analyzed else '✗ Failed'}",
            f"  Visualize : {'✔ Complete' if self.stage_visualized else '✗ Failed'}",
            f"  Report    : {'✔ Complete' if self.stage_reported else '✗ Failed'}",
            "",
            "  DATASET METRICS",
            f"  {'─' * 38}",
            f"  Records      : {self.total_rows:,}",
            f"  Columns      : {self.total_columns}",
            f"  Completeness : {self.completeness_percent:.2f}%",
            f"  Anomalies    : {self.anomalies_detected}",
            f"  Correlations : {self.correlations_found}",
            f"  Charts       : {self.charts_generated}",
            f"  AI Model     : {self.model_used}",
            "",
            "  OUTPUT FILES",
            f"  {'─' * 38}",
        ]

        lines.append(
            f"  Text report  : "
            f"{self.text_report_path or 'Not generated'}"
        )
        lines.append(
            f"  Excel report : "
            f"{self.excel_report_path or 'Not generated'}"
        )
        lines.append(
            f"  Charts folder: "
            f"{self.charts_folder or 'Not generated'}"
        )

        if self.warnings:
            lines += ["", "  WARNINGS", f"  {'─' * 38}"]
            for w in self.warnings[:5]:
                lines.append(f"  ⚠  {w[:70]}")

        if self.stage_errors:
            lines += [
                "", "  STAGE ERRORS", f"  {'─' * 38}"
            ]
            for stage, err in self.stage_errors.items():
                lines.append(
                    f"  [{stage}] {str(err)[:70]}"
                )

        lines += ["", sep]
        return "\n".join(lines)


# SESSION MEMORY — Persistent session history

class SessionMemory:
    """
    Persists analysis session records to disk.
    Tracks every analysis run the agent has performed,
    enabling longitudinal comparison, audit trails,
    and the ability to retrieve past results without
    re-running the full pipeline.

    Storage format is JSON — human readable, portable,
    and inspectable without any special tools.
    """

    def __init__(
        self,
        history_file: str = "analysis_history.json"
    ):
        self.history_file = history_file
        self.sessions: list = []
        self._load()

    def _load(self) -> None:
        if os.path.exists(self.history_file):
            try:
                with open(
                    self.history_file, "r",
                    encoding="utf-8"
                ) as f:
                    self.sessions = json.load(f)
                logger.info(
                    f"Session history loaded: "
                    f"{len(self.sessions)} past sessions"
                )
            except Exception as error:
                logger.warning(
                    f"Could not load session history: "
                    f"{error}"
                )
                self.sessions = []
        else:
            logger.info(
                "No session history found. "
                "Starting fresh."
            )
            self.sessions = []

    def save_session(self, session: AnalysisSession) -> None:
        record = {
            "session_id":           session.session_id,
            "file_name":            session.file_name,
            "file_path":            session.file_path,
            "started_at":           session.started_at,
            "completed_at":         session.completed_at,
            "duration_seconds":     session.duration_seconds,
            "pipeline_success":     session.pipeline_success,
            "total_rows":           session.total_rows,
            "total_columns":        session.total_columns,
            "completeness_percent": session.completeness_percent,
            "anomalies_detected":   session.anomalies_detected,
            "correlations_found":   session.correlations_found,
            "charts_generated":     session.charts_generated,
            "model_used":           session.model_used,
            "text_report_path":     session.text_report_path,
            "excel_report_path":    session.excel_report_path,
            "charts_folder":        session.charts_folder,
            "stage_errors":         session.stage_errors,
            "warnings":             session.warnings[:10],
        }

        self.sessions.append(record)

        try:
            with open(
                self.history_file, "w",
                encoding="utf-8"
            ) as f:
                json.dump(self.sessions, f, indent=4)
            logger.info(
                f"Session saved: {session.session_id}"
            )
        except Exception as error:
            logger.error(
                f"Could not save session: {error}"
            )

    def get_total_sessions(self) -> int:
        return len(self.sessions)

    def get_recent_sessions(self, count: int = 5) -> list:
        return self.sessions[-count:]

    def get_session_summary(self) -> str:
        total = self.get_total_sessions()

        if total == 0:
            return (
                "No analysis sessions in history yet."
            )

        successful = sum(
            1 for s in self.sessions
            if s.get("pipeline_success", False)
        )
        total_rows = sum(
            s.get("total_rows", 0)
            for s in self.sessions
        )

        lines = [
            "SESSION HISTORY",
            "=" * 45,
            f"Total sessions    : {total}",
            f"Successful        : {successful}",
            f"Total rows analyzed: {total_rows:,}",
            "",
            "RECENT SESSIONS",
            "─" * 45,
        ]

        for s in self.get_recent_sessions(5):
            status = (
                "✔" if s.get("pipeline_success")
                else "✗"
            )
            lines.append(
                f"  {status} {s.get('started_at', '')[:16]} | "
                f"{s.get('file_name', '')[:25]} | "
                f"{s.get('total_rows', 0):,} rows"
            )

        return "\n".join(lines)

# DATA AGENT — The unified orchestration brain
class DataAnalysisAgent:
    """
    The single interface through which all analysis
    operations are initiated and managed.

    Callers provide a file path and receive an
    AnalysisSession object containing every output
    the pipeline produced. The internal complexity
    of coordinating four specialized components,
    managing failures, tracking timing, and persisting
    history is completely invisible to callers.

    This is the contract the deployment layer
    — Telegram bot, web API, scheduled job —
    will rely on. Its interface must never change
    even as the internal implementation evolves.

    Initialization:
        agent = DataAnalysisAgent()

    Analysis:
        session = agent.analyze("path/to/data.csv")

    Results:
        print(session.get_terminal_summary())
        print(session.text_report_path)
        print(session.executive_summary)
    """

    def __init__(
        self,
        charts_folder:        str = "charts",
        reports_folder:       str = "reports",
        excel_reports_folder: str = "excel_reports",
        history_file:         str = "analysis_history.json"
    ):
        logger.info("Initializing Data Analysis Agent...")

        self.loader     = UniversalDataLoader()
        self.analyzer   = StatisticalAnalyzer()
        self.visualizer = DataVisualizer(
            output_base_folder=charts_folder
        )
        self.generator  = ReportGenerator(
            reports_folder=reports_folder,
            excel_reports_folder=excel_reports_folder
        )
        self.memory     = SessionMemory(
            history_file=history_file
        )

        self.charts_folder        = charts_folder
        self.reports_folder       = reports_folder
        self.excel_reports_folder = excel_reports_folder

        self._create_output_directories()

        logger.info(
            f"Data Analysis Agent ready. "
            f"Past sessions: "
            f"{self.memory.get_total_sessions()}"
        )
        print(
            f"\nData Analysis Agent initialized.\n"
            f"Past sessions: "
            f"{self.memory.get_total_sessions()}"
        )

    def _create_output_directories(self) -> None:
        for folder in [
            self.charts_folder,
            self.reports_folder,
            self.excel_reports_folder,
        ]:
            os.makedirs(folder, exist_ok=True)

    # PRIMARY PUBLIC METHOD
    def analyze(self, file_path: str) -> AnalysisSession:
        """
        Run the complete analysis pipeline on any file.

        This is the only method callers need. It accepts
        a file path, orchestrates all four pipeline
        stages, handles failures at each stage without
        propagating exceptions to the caller, persists
        the session record to history, and returns a
        fully populated AnalysisSession object.

        The pipeline is designed to deliver maximum
        value even under partial failure conditions.
        If visualization fails, reporting continues
        with the statistical results that are available.
        If AI narrative generation fails, the report
        is still written with all quantitative findings.
        A caller will always receive a session object
        with whatever the pipeline successfully produced.

        Parameters:
            file_path — absolute or relative path to
                        any CSV, Excel, JSON, or TXT file

        Returns:
            AnalysisSession — complete record of the run
        """

        session            = AnalysisSession()
        session.session_id = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )[:19]
        session.file_path  = file_path
        session.file_name  = os.path.basename(file_path)
        session.started_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        start_time = time.time()

        logger.info(
            f"Analysis starting — "
            f"session: {session.session_id} | "
            f"file: {session.file_name}"
        )

        print(
            f"\n{'═' * 55}\n"
            f"  DATA ANALYSIS AGENT — STARTING\n"
            f"  Session : {session.session_id}\n"
            f"  File    : {session.file_name}\n"
            f"{'═' * 55}"
        )

        # ─STAGE 1—PERCEIVE
        session = self._stage_load(session)

        if not session.stage_loaded:
            session = self._finalize_session(
                session, start_time
            )
            return session

        # ─ STAGE 2—THINK
        session = self._stage_analyze(session)

        # ─STAGE 3 — ACT (Visualize)
        session = self._stage_visualize(session)

        # ─STAGE 4 — ACT (Report)
        session = self._stage_report(session)

        # ─ FINALIZE
        session = self._finalize_session(
            session, start_time
        )

        return session

    # PIPELINE STAGES — Each isolated and independently
    # recoverable. A failure in any stage is recorded
    # in session.stage_errors and execution continues
    # to deliver whatever partial results are possible.

    def _stage_load(
        self, session: AnalysisSession
    ) -> AnalysisSession:
        """
        PERCEIVE — Load and profile the dataset.
        Validates file existence before delegating
        to the loader. Records profile statistics
        in the session for downstream access.
        """

        print("\n[1/4] Loading and profiling dataset...")

        try:
            if not os.path.exists(session.file_path):
                raise FileNotFoundError(
                    f"File not found: {session.file_path}"
                )

            profile = self.loader.load(session.file_path)

            if not profile.load_success:
                raise ValueError(
                    profile.load_error or
                    "File loaded but no data found."
                )

            session.profile              = profile
            session.total_rows           = profile.total_rows
            session.total_columns        = profile.total_columns
            session.completeness_percent = (
                profile.completeness_percent
            )
            session.warnings.extend(profile.warnings)
            session.stage_loaded = True

            logger.info(
                f"Stage 1 complete: "
                f"{profile.total_rows:,} rows loaded"
            )
            print(
                f"     ✔ {profile.total_rows:,} rows | "
                f"{profile.total_columns} columns | "
                f"{profile.completeness_percent:.1f}% complete"
            )

        except Exception as error:
            session.stage_errors["load"] = str(error)
            session.pipeline_error = str(error)
            logger.error(
                f"Stage 1 failed: {error}",
                exc_info=True
            )
            print(f"     ✗ Load failed: {error}")

        return session

    def _stage_analyze(
        self, session: AnalysisSession
    ) -> AnalysisSession:
        """
        THINK — Run complete statistical analysis.
        Passes the loaded profile to the analyzer
        and extracts quality metrics into the session.
        """

        print("\n[2/4] Running statistical analysis...")

        try:
            stats = self.analyzer.analyze(session.profile)

            session.stats = stats

            session.anomalies_detected = sum(
                info.get("anomaly_count", 0)
                for info in stats.get(
                    "anomalies", {}
                ).values()
            )
            session.correlations_found = len(
                stats.get("correlations", [])
            )
            session.stage_analyzed = True

            logger.info(
                f"Stage 2 complete: "
                f"{session.anomalies_detected} anomalies | "
                f"{session.correlations_found} correlations"
            )
            print(
                f"     ✔ {session.anomalies_detected} "
                f"anomalies detected | "
                f"{session.correlations_found} correlations"
            )

        except Exception as error:
            session.stage_errors["analyze"] = str(error)
            logger.error(
                f"Stage 2 failed: {error}",
                exc_info=True
            )
            print(f"     ✗ Analysis failed: {error}")

        return session

    def _stage_visualize(
        self, session: AnalysisSession
    ) -> AnalysisSession:
        """
        ACT (visual) — Generate the complete chart suite.
        Skips gracefully if analysis stage did not
        complete. Chart generation failures for
        individual chart types are handled internally
        by the visualizer — this stage only fails
        if the visualizer itself raises unexpectedly.
        """

        print("\n[3/4] Generating visualizations...")

        if not session.stage_analyzed:
            print(
                "     — Skipped: analysis stage incomplete"
            )
            session.stage_errors["visualize"] = (
                "Skipped: analysis stage did not complete"
            )
            return session

        try:
            viz_result = self.visualizer.generate_all_charts(
                dataframe  = session.profile.dataframe,
                profile    = session.profile,
                stats      = session.stats,
                session_id = session.session_id
            )

            session.viz_result        = viz_result
            session.charts_generated  = (
                viz_result.total_charts_generated
            )
            session.charts_folder     = viz_result.charts_folder
            session.chart_paths       = (
                viz_result.get_all_chart_paths()
            )
            session.warnings.extend(
                viz_result.generation_errors
            )
            session.stage_visualized = True

            logger.info(
                f"Stage 3 complete: "
                f"{session.charts_generated} charts saved"
            )
            print(
                f"     ✔ {session.charts_generated} "
                f"charts saved to "
                f"{viz_result.charts_folder}"
            )

        except Exception as error:
            session.stage_errors["visualize"] = str(error)
            logger.error(
                f"Stage 3 failed: {error}",
                exc_info=True
            )
            print(
                f"     ✗ Visualization failed: {error}"
            )

        return session

    def _stage_report(
            self, session: AnalysisSession
    ) -> AnalysisSession:
        """
        ACT (report) — Generate text and Excel reports
        with AI-powered narrative analysis. Can run
        even if visualization failed — the report will
        note that charts are unavailable but will still
        contain the full statistical analysis and the
        complete AI written intelligence layer.
        """

        print("\n[4/4] Generating reports...")

        if not session.stage_analyzed:
            print(
                "     — Skipped: analysis stage incomplete"
            )
            session.stage_errors["report"] = (
                "Skipped: analysis stage did not complete"
            )
            return session

        try:
            report_result = self.generator.generate(
                profile=session.profile,
                stats=session.stats,
                viz_result=session.viz_result,
                session_id=session.session_id,
                df=session.profile.dataframe  # ← NEW
            )

            session.report_result = report_result
            session.text_report_path = (
                report_result.text_report_path
            )
            session.excel_report_path = (
                report_result.excel_report_path
            )
            session.executive_summary = (
                report_result.executive_summary
            )
            session.ai_narrative = (
                report_result.ai_narrative
            )
            session.model_used = (
                report_result.model_used
            )
            session.warnings.extend(
                report_result.generation_warnings
            )
            session.stage_reported = True

            logger.info(
                f"Stage 4 complete: "
                f"text={session.text_report_path is not None} | "
                f"excel={session.excel_report_path is not None}"
            )
            print(
                f"     ✔ Text report  : "
                f"{os.path.basename(session.text_report_path or 'none')}\n"
                f"     ✔ Excel report : "
                f"{os.path.basename(session.excel_report_path or 'none')}"
            )

        except Exception as error:
            session.stage_errors["report"] = str(error)
            logger.error(
                f"Stage 4 failed: {error}",
                exc_info=True
            )
            print(f"     ✗ Report generation failed: {error}")

        return session

    def _finalize_session(
        self,
        session:    AnalysisSession,
        start_time: float
    ) -> AnalysisSession:
        """
        Finalize session metadata, determine overall
        pipeline success status, persist to history,
        and log the completion summary.
        """

        session.completed_at     = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        session.duration_seconds = round(
            time.time() - start_time, 2
        )
        session.pipeline_success = (
            session.stage_loaded and
            session.stage_analyzed and
            (
                session.text_report_path is not None or
                session.excel_report_path is not None
            )
        )

        self.memory.save_session(session)

        logger.info(
            f"Session finalized: "
            f"success={session.pipeline_success} | "
            f"duration={session.duration_seconds}s"
        )

        return session

    # SECONDARY PUBLIC METHODS
    def get_session_history(self) -> str:
        """
        Return formatted session history summary.
        Used by Telegram /history command and
        terminal status displays.
        """
        return self.memory.get_session_summary()

    def get_total_sessions(self) -> int:
        return self.memory.get_total_sessions()

    def get_recent_sessions(self, count: int = 5) -> list:
        return self.memory.get_recent_sessions(count)

    def validate_file(self, file_path: str) -> tuple:
        """
        Validate a file before running full analysis.
        Returns (is_valid, message) tuple.
        Used by Telegram bot to give early feedback
        before committing to the full pipeline run.
        """

        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        extension = os.path.splitext(file_path)[1].lower()
        supported = [".csv", ".xlsx", ".xls", ".json", ".txt"]

        if extension not in supported:
            return False, (
                f"Unsupported format: {extension}. "
                f"Supported formats: "
                f"CSV, Excel, JSON, TXT."
            )

        size_kb = os.path.getsize(file_path) / 1024
        if size_kb > 50_000:
            return False, (
                f"File too large: {size_kb:.0f} KB. "
                f"Maximum supported size is 50 MB."
            )

        if size_kb == 0:
            return False, "File is empty."

        return True, (
            f"File valid: {os.path.basename(file_path)} "
            f"({size_kb:.1f} KB)"
        )