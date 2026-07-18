# customization/domains/government.py
# Government / Public Sector Domain — Global Standards (UN, World Bank, OECD)

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


class GovernmentDomain(BaseDomain):
    """
    Government / Public Sector-specific analysis based on UN, World Bank, OECD standards.
    Covers: Budget, Expenditure, Project Completion, Service Delivery, Citizen Satisfaction.
    """

    DOMAIN_NAME = "government"

    DOMAIN_KEYWORDS = [
        "budget", "expenditure", "revenue", "tax", "grant",
        "project", "program", "policy", "service", "citizen",
        "satisfaction", "transparency", "efficiency", "completion",
        "procurement", "contract", "vendor", "grant", "loan",
        "municipality", "state", "federal", "agency", "department",
        "public", "sector", "government", "administration", "governance"
    ]

    BUDGET_KEYWORDS = ["budget", "allocation", "funding", "appropriation"]
    EXPENDITURE_KEYWORDS = ["expenditure", "spent", "disbursement", "outlay"]
    PROJECT_KEYWORDS = ["project", "program", "initiative", "scheme"]
    CITIZEN_KEYWORDS = ["citizen", "resident", "public", "beneficiary"]
    SATISFACTION_KEYWORDS = ["satisfaction", "feedback", "survey", "rating"]
    COMPLETION_KEYWORDS = ["completion", "progress", "milestone", "delivery"]

    # UN / World Bank Benchmarks 2024
    BENCHMARK_BUDGET_UTILIZATION = 85.0     # % (efficient utilization)
    BENCHMARK_PROJECT_COMPLETION = 75.0     # % (on-time completion)
    BENCHMARK_CITIZEN_SATISFACTION = 70.0   # % (satisfied citizens)
    BENCHMARK_TRANSPARENCY = 60.0           # % (transparency index)

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load government thresholds from config."""
        self.benchmark_budget_util = config.get_threshold(
            'government', 'budget_util_benchmark', self.client_name
        ) or self.BENCHMARK_BUDGET_UTILIZATION

        self.benchmark_project_completion = config.get_threshold(
            'government', 'project_completion_benchmark', self.client_name
        ) or self.BENCHMARK_PROJECT_COMPLETION

        self.benchmark_citizen_satisfaction = config.get_threshold(
            'government', 'citizen_satisfaction_benchmark', self.client_name
        ) or self.BENCHMARK_CITIZEN_SATISFACTION

        self.benchmark_transparency = config.get_threshold(
            'government', 'transparency_benchmark', self.client_name
        ) or self.BENCHMARK_TRANSPARENCY

    def detect(self) -> bool:
        """Detect if this is government/public sector data."""
        all_cols_text = " ".join(self._get_all_columns()).lower()
        return any(k in all_cols_text for k in self.DOMAIN_KEYWORDS)

    def get_section_header(self) -> str:
        return "GOVERNMENT / PUBLIC SECTOR ANALYSIS — UN / WORLD BANK STANDARDS"

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
        """Generate government/public sector content for the text report."""

        budget_col = self._detect_column(self.BUDGET_KEYWORDS)
        expenditure_col = self._detect_column(self.EXPENDITURE_KEYWORDS)
        project_col = self._detect_column(self.PROJECT_KEYWORDS)
        citizen_col = self._detect_column(self.CITIZEN_KEYWORDS)
        satisfaction_col = self._detect_column(self.SATISFACTION_KEYWORDS)
        completion_col = self._detect_column(self.COMPLETION_KEYWORDS)

        total = len(self.df)
        lines = [
            "",
            "  GOVERNMENT / PUBLIC SECTOR ANALYTICS (UN / World Bank Standards)",
            "  " + "-" * 45,
        ]

        # ─── CONFIGURATION SUMMARY ──────────────────────────────
        lines += [
            "",
            "  CONFIGURATION SUMMARY",
            "  " + "-" * 35,
            f"    Client             : {self.client_name or 'Default'}",
            f"    Budget Utilization Benchmark: {self.benchmark_budget_util}%",
            f"    Project Completion Benchmark: {self.benchmark_project_completion}%",
            f"    Citizen Satisfaction Benchmark: {self.benchmark_citizen_satisfaction}%",
        ]

        # ─── BUDGET ANALYSIS ──────────────────────────────────────
        if budget_col and expenditure_col:
            budget = self._safe_numeric(budget_col)
            expenditure = self._safe_numeric(expenditure_col)
            total_budget = budget.sum()
            total_expenditure = expenditure.sum()
            utilization = (total_expenditure / total_budget * 100) if total_budget > 0 else 0
            status = "✅" if utilization >= self.benchmark_budget_util else "⚠️"
            lines += ["", "  BUDGET UTILIZATION", "  " + "-" * 35]
            lines.append(
                f"    {status} Budget utilization   : {self._fmt(utilization)}% "
                f"(benchmark: {self.benchmark_budget_util}%)"
            )
            lines.append(f"    Total budget allocated: {self._fmt(total_budget)}")
            lines.append(f"    Total expenditure    : {self._fmt(total_expenditure)}")
            lines.append(f"    Surplus / deficit    : {self._fmt(total_budget - total_expenditure)}")

        # ─── PROJECT COMPLETION ────────────────────────────────────
        if project_col and completion_col:
            projects = self.df.groupby(project_col)
            completion_rate = (completion_col.sum() / len(self.df) * 100) if len(self.df) > 0 else 0
            status = "✅" if completion_rate >= self.benchmark_project_completion else "⚠️"
            lines += ["", "  PROJECT COMPLETION", "  " + "-" * 35]
            lines.append(
                f"    {status} Project completion   : {self._fmt(completion_rate)}% "
                f"(benchmark: {self.benchmark_project_completion}%)"
            )
            # Count completed projects
            completed_projects = (completion_col == 1).sum() if completion_col is not None else 0
            lines.append(f"    Completed projects   : {completed_projects}")

        # ─── CITIZEN SATISFACTION ──────────────────────────────────
        if satisfaction_col:
            satisfaction = self._safe_numeric(satisfaction_col)
            avg_satisfaction = satisfaction.mean()
            status = "✅" if avg_satisfaction >= self.benchmark_citizen_satisfaction else "⚠️"
            lines += ["", "  CITIZEN SATISFACTION", "  " + "-" * 35]
            lines.append(
                f"    {status} Avg satisfaction    : {self._fmt(avg_satisfaction)}% "
                f"(benchmark: {self.benchmark_citizen_satisfaction}%)"
            )
            lines.append(f"    High satisfaction (>80%) : {(satisfaction > 80).sum()} responses")
            lines.append(f"    Low satisfaction (<40%)  : {(satisfaction < 40).sum()} responses")

        # ─── TRANSPARENCY ──────────────────────────────────────────
        transparency_col = self._detect_column(["transparency", "openness", "disclosure"])
        if transparency_col:
            transparency = self._safe_numeric(transparency_col)
            avg_transparency = transparency.mean()
            status = "✅" if avg_transparency >= self.benchmark_transparency else "⚠️"
            lines += ["", "  TRANSPARENCY INDEX", "  " + "-" * 35]
            lines.append(
                f"    {status} Avg transparency   : {self._fmt(avg_transparency)}% "
                f"(benchmark: {self.benchmark_transparency}%)"
            )

        # ─── SERVICE DELIVERY ──────────────────────────────────────
        service_col = self._detect_column(["service", "delivery", "response"])
        if service_col:
            service = self._safe_numeric(service_col)
            avg_service = service.mean()
            lines += ["", "  SERVICE DELIVERY", "  " + "-" * 35]
            lines.append(f"    Avg service score   : {self._fmt(avg_service)}/100")
            lines.append(f"    Service efficiency  : {self._fmt(service.mean())}%")

        # ─── DEPARTMENT / AGENCY BREAKDOWN ──────────────────────────
        dept_col = self._detect_column(["department", "agency", "division"])
        if dept_col:
            dept_dist = self.df[dept_col].value_counts()
            lines += ["", "  DEPARTMENT / AGENCY BREAKDOWN", "  " + "-" * 35]
            for dept, count in dept_dist.head(10).items():
                pct = count / total * 100
                bar = "█" * int(pct / 2)
                lines.append(
                    f"    {str(dept)[:25]:<25}: "
                    f"{count:>3} ({self._fmt(pct):>5}%) {bar}"
                )

        # ─── BENCHMARKS ──────────────────────────────────────────
        lines += ["", "  PUBLIC SECTOR BENCHMARKS (UN / World Bank 2024)", "  " + "-" * 35]
        lines.append(f"    Budget Utilization Target: {self.benchmark_budget_util}%")
        lines.append(f"    Project Completion Target: {self.benchmark_project_completion}%")
        lines.append(f"    Citizen Satisfaction Target: {self.benchmark_citizen_satisfaction}%")
        lines.append(f"    Transparency Index Target: {self.benchmark_transparency}%")

        return "\n".join(lines)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return government-specific Excel sheets."""
        sheets = {}
        dept_col = self._detect_column(["department", "agency", "division"])
        budget_col = self._detect_column(self.BUDGET_KEYWORDS)
        expenditure_col = self._detect_column(self.EXPENDITURE_KEYWORDS)
        satisfaction_col = self._detect_column(self.SATISFACTION_KEYWORDS)
        completion_col = self._detect_column(self.COMPLETION_KEYWORDS)

        # ─── Department/Agency Budget Summary ────────────────────
        if dept_col and budget_col:
            agg_dict = {}
            if budget_col:
                agg_dict["Total Budget"] = (budget_col, "sum")
                agg_dict["Avg Budget"] = (budget_col, "mean")
            if expenditure_col:
                agg_dict["Total Expenditure"] = (expenditure_col, "sum")
                agg_dict["Avg Expenditure"] = (expenditure_col, "mean")
                agg_dict["Utilization %"] = (expenditure_col, lambda x: (x.sum() / budget_col.sum() * 100) if budget_col.sum() > 0 else 0)
            if satisfaction_col:
                agg_dict["Avg Satisfaction"] = (satisfaction_col, "mean")
            if completion_col:
                agg_dict["Completion Rate %"] = (completion_col, lambda x: x.sum() / len(x) * 100)

            dept_summary = self.df.groupby(dept_col).agg(**agg_dict).reset_index()
            sheets["Department Summary"] = dept_summary

        # ─── Budget vs Expenditure ──────────────────────────────
        if budget_col and expenditure_col:
            budget = self._safe_numeric(budget_col)
            expenditure = self._safe_numeric(expenditure_col)
            summary_df = pd.DataFrame({
                "Metric": ["Total Budget", "Total Expenditure", "Utilization %", "Surplus/Deficit"],
                "Value": [
                    budget.sum(),
                    expenditure.sum(),
                    (expenditure.sum() / budget.sum() * 100) if budget.sum() > 0 else 0,
                    budget.sum() - expenditure.sum()
                ]
            })
            sheets["Budget Summary"] = summary_df

        # ─── Citizen Satisfaction Distribution ──────────────────
        if satisfaction_col:
            satisfaction = self._safe_numeric(satisfaction_col)
            bins = [0, 40, 60, 80, 100]
            labels = ["Low (<40)", "Medium (40-60)", "High (60-80)", "Very High (>80)"]
            cat = pd.cut(satisfaction, bins=bins, labels=labels, include_lowest=True)
            dist = cat.value_counts().reset_index()
            dist.columns = ["Satisfaction Level", "Count"]
            sheets["Satisfaction Distribution"] = dist

        return sheets