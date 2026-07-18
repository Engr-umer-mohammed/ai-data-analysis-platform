# customization/domains/insurance.py
# Insurance Domain — NAIC / Actuarial Standards

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


class InsuranceDomain(BaseDomain):
    """
    Insurance-specific analysis based on NAIC/Actuarial standards.
    Covers: Premiums, Claims, Loss Ratio, Combined Ratio, Retention.
    """

    DOMAIN_NAME = "insurance"

    DOMAIN_KEYWORDS = [
        "policy", "claim", "premium", "insured", "underwriting",
        "loss", "risk", "deductible", "coverage", "renewal",
        "lapse", "annuity", "life", "auto", "home", "health",
        "commercial", "liability", "property", "casualty",
        "actuarial", "reserve", "reinsurance", "catastrophe"
    ]

    PREMIUM_KEYWORDS = ["premium", "written", "earned", "gwp", "nwp"]
    CLAIM_KEYWORDS = ["claim", "loss", "incurred", "paid", "reported"]
    POLICY_KEYWORDS = ["policy", "contract", "coverage", "line"]
    RISK_KEYWORDS = ["risk", "exposure", "insured", "underwriting"]
    RETENTION_KEYWORDS = ["retention", "renewal", "lapse", "persistency"]

    # NAIC / Actuarial Benchmarks 2024
    BENCHMARK_LOSS_RATIO = 65.0       # % (P&C average)
    BENCHMARK_COMBINED_RATIO = 100.0  # % (breakeven)
    BENCHMARK_RETENTION = 85.0        # % (annual)
    BENCHMARK_EXPENSE_RATIO = 30.0    # % (average)

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load insurance thresholds from config."""
        self.benchmark_loss_ratio = config.get_threshold(
            'insurance', 'loss_ratio_benchmark', self.client_name
        ) or self.BENCHMARK_LOSS_RATIO

        self.benchmark_combined_ratio = config.get_threshold(
            'insurance', 'combined_ratio_benchmark', self.client_name
        ) or self.BENCHMARK_COMBINED_RATIO

        self.benchmark_retention = config.get_threshold(
            'insurance', 'retention_benchmark', self.client_name
        ) or self.BENCHMARK_RETENTION

        self.benchmark_expense_ratio = config.get_threshold(
            'insurance', 'expense_ratio_benchmark', self.client_name
        ) or self.BENCHMARK_EXPENSE_RATIO

    def detect(self) -> bool:
        """Detect if this is insurance data."""
        all_cols_text = " ".join(self._get_all_columns()).lower()
        return any(k in all_cols_text for k in self.DOMAIN_KEYWORDS)

    def get_section_header(self) -> str:
        return "INSURANCE DOMAIN ANALYSIS — NAIC / ACTUARIAL STANDARDS"

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
        """Generate insurance-specific content for the text report."""

        premium_col = self._detect_column(self.PREMIUM_KEYWORDS)
        claim_col = self._detect_column(self.CLAIM_KEYWORDS)
        policy_col = self._detect_column(self.POLICY_KEYWORDS)
        risk_col = self._detect_column(self.RISK_KEYWORDS)
        retention_col = self._detect_column(self.RETENTION_KEYWORDS)

        total = len(self.df)
        lines = [
            "",
            "  INSURANCE ANALYTICS (NAIC / Actuarial Standards)",
            "  " + "-" * 45,
        ]

        # ─── CONFIGURATION SUMMARY ──────────────────────────────
        lines += [
            "",
            "  CONFIGURATION SUMMARY",
            "  " + "-" * 35,
            f"    Client             : {self.client_name or 'Default'}",
            f"    Loss Ratio Benchmark: {self.benchmark_loss_ratio}%",
            f"    Combined Ratio Benchmark: {self.benchmark_combined_ratio}%",
            f"    Retention Benchmark: {self.benchmark_retention}%",
        ]

        # ─── PREMIUM ANALYSIS ──────────────────────────────────
        if premium_col:
            premium = self._safe_numeric(premium_col)
            lines += ["", "  PREMIUM ANALYSIS", "  " + "-" * 35]
            lines.append(f"    Total Written Premium: {self._fmt(premium.sum())}")
            lines.append(f"    Average Premium      : {self._fmt(premium.mean())}")
            lines.append(f"    Median Premium       : {self._fmt(premium.median())}")
            lines.append(f"    Min/Max Premium      : {self._fmt(premium.min())} / {self._fmt(premium.max())}")

        # ─── CLAIM ANALYSIS ─────────────────────────────────────
        if claim_col:
            claims = self._safe_numeric(claim_col)
            claim_ratio = (claims.sum() / premium.sum() * 100) if premium_col and premium.sum() > 0 else 0
            status = "✅" if claim_ratio <= self.benchmark_loss_ratio else "⚠️"
            lines += ["", "  CLAIM & LOSS ANALYSIS", "  " + "-" * 35]
            lines.append(f"    Total Claims Paid   : {self._fmt(claims.sum())}")
            lines.append(f"    Average Claim       : {self._fmt(claims.mean())}")
            lines.append(f"    Claim Frequency     : {(claims > 0).sum()} claims")

            if premium_col and premium.sum() > 0:
                lines.append(
                    f"    {status} Loss Ratio          : {self._fmt(claim_ratio)}% "
                    f"(NAIC benchmark: {self.benchmark_loss_ratio}%)"
                )
                # Combined Ratio (if expense data available, else estimate)
                expense_col = self._detect_column(["expense", "cost", "operating"])
                if expense_col:
                    expense = self._safe_numeric(expense_col)
                    expense_ratio = (expense.sum() / premium.sum() * 100)
                    combined_ratio = claim_ratio + expense_ratio
                    status_combined = "✅" if combined_ratio <= self.benchmark_combined_ratio else "⚠️"
                    lines.append(f"    Expense Ratio        : {self._fmt(expense_ratio)}%")
                    lines.append(
                        f"    {status_combined} Combined Ratio      : {self._fmt(combined_ratio)}% "
                        f"(benchmark: {self.benchmark_combined_ratio}%)"
                    )
                else:
                    # Estimate combined ratio using benchmark expense ratio
                    est_combined = claim_ratio + self.benchmark_expense_ratio
                    lines.append(f"    Est. Expense Ratio   : {self.benchmark_expense_ratio}% (industry average)")
                    lines.append(f"    Est. Combined Ratio  : {self._fmt(est_combined)}%")

        # ─── POLICY DISTRIBUTION ──────────────────────────────────
        if policy_col:
            policy_dist = self.df[policy_col].value_counts()
            lines += ["", "  POLICY DISTRIBUTION", "  " + "-" * 35]
            for policy_type, count in policy_dist.head(10).items():
                pct = count / total * 100
                bar = "█" * int(pct / 2)
                lines.append(
                    f"    {str(policy_type)[:25]:<25}: "
                    f"{count:>3} ({self._fmt(pct):>5}%) {bar}"
                )

        # ─── RETENTION ANALYSIS ──────────────────────────────────
        if retention_col:
            retention = self._safe_numeric(retention_col)
            avg_retention = retention.mean()
            if avg_retention <= 1:
                avg_retention = avg_retention * 100
            status = "✅" if avg_retention >= self.benchmark_retention else "⚠️"
            lines += ["", "  RETENTION ANALYSIS", "  " + "-" * 35]
            lines.append(
                f"    {status} Retention Rate      : {self._fmt(avg_retention)}% "
                f"(benchmark: {self.benchmark_retention}%)"
            )
            lapsed = (retention < 50).sum() if retention_col else 0
            lines.append(f"    Low Retention (<50%)  : {lapsed} policies")

        # ─── RISK EXPOSURE ──────────────────────────────────────
        if risk_col:
            risk = self._safe_numeric(risk_col)
            lines += ["", "  RISK EXPOSURE", "  " + "-" * 35]
            lines.append(f"    Average Risk Score   : {self._fmt(risk.mean())}")
            lines.append(f"    High Risk (>75)      : {(risk > 75).sum()} policies")
            lines.append(f"    Low Risk (<25)       : {(risk < 25).sum()} policies")

        # ─── BENCHMARKS ──────────────────────────────────────────
        lines += ["", "  ACTUARIAL BENCHMARKS (NAIC 2024)", "  " + "-" * 35]
        lines.append(f"    Loss Ratio Target    : {self.benchmark_loss_ratio}%")
        lines.append(f"    Combined Ratio Target: {self.benchmark_combined_ratio}%")
        lines.append(f"    Retention Target     : {self.benchmark_retention}%")

        return "\n".join(lines)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return insurance-specific Excel sheets."""
        sheets = {}
        policy_col = self._detect_column(self.POLICY_KEYWORDS)
        premium_col = self._detect_column(self.PREMIUM_KEYWORDS)
        claim_col = self._detect_column(self.CLAIM_KEYWORDS)
        retention_col = self._detect_column(self.RETENTION_KEYWORDS)

        # ─── Policy Analysis ────────────────────────────────────
        if policy_col:
            agg_dict = {"Count": (policy_col, "count")}
            if premium_col:
                agg_dict["Total Premium"] = (premium_col, "sum")
                agg_dict["Avg Premium"] = (premium_col, "mean")
            if claim_col:
                agg_dict["Total Claims"] = (claim_col, "sum")
                agg_dict["Avg Claim"] = (claim_col, "mean")

            policy_summary = self.df.groupby(policy_col).agg(**agg_dict).reset_index()
            if premium_col and claim_col:
                policy_summary["Loss Ratio"] = (policy_summary["Total Claims"] / policy_summary["Total Premium"]) * 100
            sheets["Policy Analysis"] = policy_summary

        # ─── Loss Ratio Summary ────────────────────────────────
        if premium_col and claim_col:
            premium = self._safe_numeric(premium_col)
            claims = self._safe_numeric(claim_col)
            loss_ratio = (claims.sum() / premium.sum() * 100) if premium.sum() > 0 else 0

            loss_df = pd.DataFrame({
                "Metric": ["Total Premium", "Total Claims", "Loss Ratio (%)", "Combined Ratio (est.)"],
                "Value": [
                    premium.sum(),
                    claims.sum(),
                    loss_ratio,
                    loss_ratio + self.benchmark_expense_ratio
                ]
            })
            sheets["Loss Ratio Summary"] = loss_df

        # ─── Retention Summary ──────────────────────────────────
        if retention_col:
            retention = self._safe_numeric(retention_col)
            if retention.max() <= 1:
                retention_pct = retention * 100
            else:
                retention_pct = retention

            ret_df = pd.DataFrame({
                "Metric": ["Average Retention (%)", "Median Retention (%)", "Min Retention (%)", "Max Retention (%)"],
                "Value": [
                    retention_pct.mean(),
                    retention_pct.median(),
                    retention_pct.min(),
                    retention_pct.max()
                ]
            })
            sheets["Retention Summary"] = ret_df

        return sheets