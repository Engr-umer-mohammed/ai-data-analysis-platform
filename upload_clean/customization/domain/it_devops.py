# customization/domains/it_devops.py
# IT / DevOps Domain — DORA & Google SRE Standards

import pandas as pd
from typing import Dict, Any, Optional
from customization.base_domain import BaseDomain

try:
    from config.config import config
except ImportError:
    class _ConfigFallback:
        def get_threshold(self, domain, key, client=None):
            return None
    config = _ConfigFallback()


class ITDevOpsDomain(BaseDomain):
    """
    IT / DevOps-specific analysis based on DORA and Google SRE standards.
    Covers: Deployments, Incidents, MTTR, Error Rates, Resource Utilization.
    """

    DOMAIN_NAME = "it_devops"

    DOMAIN_KEYWORDS = [
        "server", "deployment", "incident", "uptime", "latency",
        "error", "cpu", "memory", "disk", "network",
        "response", "request", "duration", "availability",
        "recovery", "mtbf", "mttr", "sla", "sli", "slo",
        "monitoring", "alert", "log", "trace", "metric",
        "container", "kubernetes", "docker", "pod", "cluster",
        "database", "cache", "queue", "message", "service"
    ]

    DEPLOY_KEYWORDS = ["deploy", "release", "build", "pipeline", "delivery"]
    INCIDENT_KEYWORDS = ["incident", "outage", "downtime", "failure", "error"]
    LATENCY_KEYWORDS = ["latency", "duration", "response", "time", "ms"]
    ERROR_KEYWORDS = ["error", "fail", "exception", "timeout", "retry"]
    RESOURCE_KEYWORDS = ["cpu", "memory", "ram", "disk", "storage"]
    UPTIME_KEYWORDS = ["uptime", "availability", "sla", "sli"]

    # DORA Benchmarks 2024
    BENCHMARK_DEPLOY_FREQ = 30.0       # deployments/day (elite)
    BENCHMARK_MTTR = 60.0              # minutes (elite)
    BENCHMARK_CHANGE_FAILURE = 5.0     # % (elite)
    BENCHMARK_LEAD_TIME = 60.0         # minutes (elite)

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load IT/DevOps thresholds from config."""
        self.benchmark_deploy_freq = config.get_threshold(
            'it_devops', 'deploy_freq_benchmark', self.client_name
        ) or self.BENCHMARK_DEPLOY_FREQ

        self.benchmark_mttr = config.get_threshold(
            'it_devops', 'mttr_benchmark', self.client_name
        ) or self.BENCHMARK_MTTR

        self.benchmark_change_failure = config.get_threshold(
            'it_devops', 'change_failure_benchmark', self.client_name
        ) or self.BENCHMARK_CHANGE_FAILURE

        self.benchmark_lead_time = config.get_threshold(
            'it_devops', 'lead_time_benchmark', self.client_name
        ) or self.BENCHMARK_LEAD_TIME

    def detect(self) -> bool:
        """Detect if this is IT/DevOps data."""
        all_cols_text = " ".join(self._get_all_columns()).lower()
        return any(k in all_cols_text for k in self.DOMAIN_KEYWORDS)

    def get_section_header(self) -> str:
        return "IT / DEVOPS DOMAIN ANALYSIS — DORA & SRE STANDARDS"

    def get_priority(self) -> int:
        return 55

    def _detect_column(self, keywords: list) -> Optional[str]:
        """Find the first column that matches any keyword."""
        for col in self.df.columns:
            col_lower = col.lower()
            for kw in keywords:
                if kw in col_lower:
                    return col
        return None

    def _safe_numeric(self, col: str) -> pd.Series:
        """Convert column to numeric, coercing errors."""
        return pd.to_numeric(self.df[col], errors='coerce')

    def _fmt(self, value: float, decimals: int = 2) -> str:
        """Format a numeric value consistently."""
        if pd.isna(value):
            return "N/A"
        if decimals == 0:
            return f"{value:,.0f}"
        return f"{value:,.{decimals}f}"

    def generate_content(self) -> str:
        """Generate IT/DevOps-specific content for the text report."""

        deploy_col = self._detect_column(self.DEPLOY_KEYWORDS)
        incident_col = self._detect_column(self.INCIDENT_KEYWORDS)
        latency_col = self._detect_column(self.LATENCY_KEYWORDS)
        error_col = self._detect_column(self.ERROR_KEYWORDS)
        resource_col = self._detect_column(self.RESOURCE_KEYWORDS)
        uptime_col = self._detect_column(self.UPTIME_KEYWORDS)

        total = len(self.df)
        lines = [
            "",
            "  IT / DEVOPS ANALYTICS (DORA / Google SRE Standards)",
            "  " + "-" * 45,
        ]

        # ─── CONFIGURATION SUMMARY ──────────────────────────────
        lines += [
            "",
            "  CONFIGURATION SUMMARY",
            "  " + "-" * 35,
            f"    Client             : {self.client_name or 'Default'}",
            f"    Deploy Freq Benchmark: {self.benchmark_deploy_freq}/day",
            f"    MTTR Benchmark      : {self.benchmark_mttr} min",
            f"    Change Failure Benchmark: {self.benchmark_change_failure}%",
            f"    Lead Time Benchmark : {self.benchmark_lead_time} min",
        ]

        # ─── DEPLOYMENT ANALYSIS ──────────────────────────────────
        if deploy_col:
            deploy = self._safe_numeric(deploy_col)
            freq = deploy.sum() / total if total > 0 else 0
            status = "✅" if freq >= self.benchmark_deploy_freq else "⚠️"
            lines += ["", "  DEPLOYMENT FREQUENCY (DORA)", "  " + "-" * 35]
            lines.append(
                f"    {status} Average deployments/day: {self._fmt(freq)} "
                f"(elite benchmark: {self.benchmark_deploy_freq}/day)"
            )
            lines.append(f"    Total deployments      : {self._fmt(deploy.sum(), 0)}")
            lines.append(f"    Peak deployments/day   : {self._fmt(deploy.max())}")

        # ─── INCIDENT ANALYSIS ────────────────────────────────────
        if incident_col:
            incident = self._safe_numeric(incident_col)
            total_incidents = incident.sum()
            incident_rate = total_incidents / total if total > 0 else 0
            lines += ["", "  INCIDENT & OUTAGE ANALYSIS", "  " + "-" * 35]
            lines.append(f"    Total incidents       : {self._fmt(total_incidents, 0)}")
            lines.append(f"    Incident rate (per day): {self._fmt(incident_rate)}")
            lines.append(f"    Critical incidents    : {(incident > 1).sum()}")

        # ─── MTTR (Mean Time to Restore) ─────────────────────────
        if incident_col and latency_col:
            # Assume latency column represents recovery time
            recovery = self._safe_numeric(latency_col)
            mttr = recovery.mean()
            status = "✅" if mttr <= self.benchmark_mttr else "⚠️"
            lines += ["", "  MTTR (Mean Time to Restore)", "  " + "-" * 35]
            lines.append(
                f"    {status} Average MTTR          : {self._fmt(mttr)} min "
                f"(elite benchmark: {self.benchmark_mttr} min)"
            )
            lines.append(f"    Min MTTR              : {self._fmt(recovery.min())} min")
            lines.append(f"    Max MTTR              : {self._fmt(recovery.max())} min")

        # ─── LATENCY / RESPONSE TIME ─────────────────────────────
        if latency_col:
            latency = self._safe_numeric(latency_col)
            p95 = latency.quantile(0.95)
            lines += ["", "  LATENCY / RESPONSE TIME", "  " + "-" * 35]
            lines.append(f"    Average latency       : {self._fmt(latency.mean())} ms")
            lines.append(f"    p95 latency           : {self._fmt(p95)} ms")
            lines.append(f"    p50 latency           : {self._fmt(latency.median())} ms")

        # ─── ERROR RATE ───────────────────────────────────────────
        if error_col:
            error = self._safe_numeric(error_col)
            error_rate = (error.sum() / total * 100) if total > 0 else 0
            status = "✅" if error_rate <= self.benchmark_change_failure else "⚠️"
            lines += ["", "  ERROR / CHANGE FAILURE RATE", "  " + "-" * 35]
            lines.append(
                f"    {status} Change failure rate : {self._fmt(error_rate)}% "
                f"(elite benchmark: {self.benchmark_change_failure}%)"
            )
            lines.append(f"    Total errors          : {self._fmt(error.sum(), 0)}")

        # ─── UPTIME / AVAILABILITY ──────────────────────────────
        if uptime_col:
            uptime = self._safe_numeric(uptime_col)
            avg_uptime = uptime.mean()
            lines += ["", "  UPTIME / AVAILABILITY", "  " + "-" * 35]
            lines.append(f"    Average uptime        : {self._fmt(avg_uptime)}%")
            lines.append(f"    Min uptime            : {self._fmt(uptime.min())}%")
            lines.append(f"    Max uptime            : {self._fmt(uptime.max())}%")
            if avg_uptime < 99.9:
                lines.append("    ⚠️  Below 99.9% availability target")

        # ─── RESOURCE UTILIZATION ─────────────────────────────────
        if resource_col:
            resource = self._safe_numeric(resource_col)
            avg_util = resource.mean()
            lines += ["", "  RESOURCE UTILIZATION", "  " + "-" * 35]
            lines.append(f"    Average utilization   : {self._fmt(avg_util)}%")
            lines.append(f"    Peak utilization      : {self._fmt(resource.max())}%")
            if avg_util > 80:
                lines.append("    ⚠️  High utilization (>80%)")
            if avg_util < 20:
                lines.append("    ℹ️  Low utilization (<20%)")

        # ─── DORA BENCHMARKS ──────────────────────────────────────
        lines += ["", "  DORA BENCHMARKS (2024)", "  " + "-" * 35]
        lines.append(f"    Elite Deployment Frequency: >{self.benchmark_deploy_freq}/day")
        lines.append(f"    Elite MTTR               : <{self.benchmark_mttr} min")
        lines.append(f"    Elite Change Failure Rate: <{self.benchmark_change_failure}%")
        lines.append(f"    Elite Lead Time          : <{self.benchmark_lead_time} min")

        return "\n".join(lines)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return IT/DevOps-specific Excel sheets."""
        sheets = {}
        deploy_col = self._detect_column(self.DEPLOY_KEYWORDS)
        incident_col = self._detect_column(self.INCIDENT_KEYWORDS)
        latency_col = self._detect_column(self.LATENCY_KEYWORDS)
        error_col = self._detect_column(self.ERROR_KEYWORDS)
        resource_col = self._detect_column(self.RESOURCE_KEYWORDS)
        uptime_col = self._detect_column(self.UPTIME_KEYWORDS)

        # ─── DORA Metrics Summary ────────────────────────────────
        dora_data = []
        if deploy_col:
            deploy = self._safe_numeric(deploy_col)
            dora_data.append(["Deploy Frequency (per day)", deploy.sum() / len(self.df)])
        if incident_col:
            incident = self._safe_numeric(incident_col)
            dora_data.append(["Total Incidents", incident.sum()])
        if latency_col:
            latency = self._safe_numeric(latency_col)
            dora_data.append(["MTTR (min)", latency.mean()])
            dora_data.append(["p95 Latency (ms)", latency.quantile(0.95)])
        if error_col:
            error = self._safe_numeric(error_col)
            dora_data.append(["Error Rate (%)", (error.sum() / len(self.df)) * 100])
        if uptime_col:
            uptime = self._safe_numeric(uptime_col)
            dora_data.append(["Avg Uptime (%)", uptime.mean()])
        if resource_col:
            resource = self._safe_numeric(resource_col)
            dora_data.append(["Avg Resource Utilization (%)", resource.mean()])

        if dora_data:
            dora_df = pd.DataFrame(dora_data, columns=["Metric", "Value"])
            sheets["DORA Metrics"] = dora_df

        # ─── Service / Resource Breakdown ─────────────────────────
        service_col = self._detect_column(["service", "application", "app", "component"])
        if service_col:
            agg_dict = {}
            if deploy_col:
                agg_dict["Deployments"] = (deploy_col, "sum")
            if incident_col:
                agg_dict["Incidents"] = (incident_col, "sum")
            if error_col:
                agg_dict["Errors"] = (error_col, "sum")
            if latency_col:
                agg_dict["Avg Latency"] = (latency_col, "mean")

            service_summary = self.df.groupby(service_col).agg(**agg_dict).reset_index()
            sheets["Service Breakdown"] = service_summary

        # ─── Resource Utilization Trend ──────────────────────────
        if resource_col:
            resource = self._safe_numeric(resource_col)
            util_summary = pd.DataFrame({
                "Metric": ["Min", "Max", "Mean", "Median"],
                "Utilization (%)": [
                    resource.min(),
                    resource.max(),
                    resource.mean(),
                    resource.median()
                ]
            })
            sheets["Resource Utilization"] = util_summary

        return sheets