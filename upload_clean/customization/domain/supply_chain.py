# customization/domains/supply_chain.py
# Supply Chain Domain — SCOR / Gartner Standards

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


class SupplyChainDomain(BaseDomain):
    """
    Supply Chain-specific analysis based on SCOR/Gartner standards.
    Covers: Supplier performance, Lead Time, Procurement Cost, Quality.
    """

    DOMAIN_NAME = "supply_chain"

    DOMAIN_KEYWORDS = [
        "supplier", "vendor", "procurement", "purchase",
        "lead_time", "inventory", "warehouse", "distribution",
        "demand", "forecast", "safety_stock", "reorder",
        "bom", "material", "component", "assembly",
        "quality", "inspection", "rejection", "compliance"
    ]

    SUPPLIER_KEYWORDS = ["supplier", "vendor", "source"]
    LEAD_KEYWORDS = ["lead_time", "delivery_time", "cycle"]
    COST_KEYWORDS = ["cost", "price", "purchase", "spend"]
    QUALITY_KEYWORDS = ["quality", "defect", "reject", "accept"]
    INVENTORY_KEYWORDS = ["inventory", "stock", "quantity", "units"]
    DEMAND_KEYWORDS = ["demand", "forecast", "order", "requirement"]

    # SCOR / Gartner benchmarks 2024
    BENCHMARK_ON_TIME_DELIVERY = 95.0   # %
    BENCHMARK_SUPPLIER_DEFECT = 0.5     # % acceptable defect rate
    BENCHMARK_INVENTORY_DAYS = 45       # days on hand target

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load supply chain thresholds from config."""
        self.benchmark_on_time_delivery = config.get_threshold(
            'supply_chain', 'on_time_delivery_benchmark', self.client_name
        ) or self.BENCHMARK_ON_TIME_DELIVERY

        self.benchmark_supplier_defect = config.get_threshold(
            'supply_chain', 'supplier_defect_benchmark', self.client_name
        ) or self.BENCHMARK_SUPPLIER_DEFECT

        self.benchmark_inventory_days = config.get_threshold(
            'supply_chain', 'inventory_days_benchmark', self.client_name
        ) or self.BENCHMARK_INVENTORY_DAYS

    def detect(self) -> bool:
        """Detect if this is supply chain data."""
        all_cols_text = " ".join(self._get_all_columns()).lower()
        return any(k in all_cols_text for k in self.DOMAIN_KEYWORDS)

    def get_section_header(self) -> str:
        return "SUPPLY CHAIN DOMAIN ANALYSIS — SCOR / GARTNER STANDARDS"

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
        """Generate supply chain-specific content for the text report."""

        supplier_col = self._detect_column(self.SUPPLIER_KEYWORDS)
        lead_col = self._detect_column(self.LEAD_KEYWORDS)
        cost_col = self._detect_column(self.COST_KEYWORDS)
        quality_col = self._detect_column(self.QUALITY_KEYWORDS)
        inv_col = self._detect_column(self.INVENTORY_KEYWORDS)

        total = len(self.df)
        lines = [
            "",
            "  SUPPLY CHAIN ANALYTICS (SCOR Standards)",
            "  " + "-" * 45,
        ]

        # ─── CONFIGURATION SUMMARY ──────────────────────────────
        lines += [
            "",
            "  CONFIGURATION SUMMARY",
            "  " + "-" * 35,
            f"    Client                     : {self.client_name or 'Default'}",
            f"    On-Time Delivery Benchmark : {self.benchmark_on_time_delivery}%",
            f"    Supplier Defect Benchmark  : {self.benchmark_supplier_defect}%",
            f"    Inventory Days Benchmark   : {self.benchmark_inventory_days} days",
        ]

        # ─── SUPPLIER ANALYSIS ──────────────────────────────────
        if supplier_col:
            suppliers = self.df[supplier_col].nunique()
            top_suppliers = self.df[supplier_col].value_counts()
            lines += ["", "  SUPPLIER ANALYSIS", "  " + "-" * 35]
            lines.append(f"    Total unique suppliers: {suppliers}")

            lines += ["", "  TOP SUPPLIERS BY TRANSACTION VOLUME", "  " + "-" * 35]
            for supp, count in top_suppliers.head(10).items():
                pct = count / total * 100
                bar = "█" * int(pct / 2)
                lines.append(
                    f"    {str(supp)[:25]:<25}: "
                    f"{count:>3} orders ({self._fmt(pct)}%) {bar}"
                )

        # ─── LEAD TIME ANALYSIS ──────────────────────────────────
        if lead_col:
            lead = self._safe_numeric(lead_col)
            status = "✅" if lead.mean() <= self.benchmark_inventory_days else "⚠️"
            lines += ["", "  LEAD TIME ANALYSIS (SCOR Benchmark)", "  " + "-" * 35]
            lines.append(f"    {status} Average lead time    : {self._fmt(lead.mean())} days")
            lines.append(f"       (target: {self.benchmark_inventory_days} days)")
            lines.append(f"    Median lead time     : {self._fmt(lead.median())} days")
            lines.append(f"    Lead time range      : {self._fmt(lead.min())} - {self._fmt(lead.max())} days")
            lines.append(f"    Lead time variance   : {self._fmt(lead.std())} days")

        # ─── PROCUREMENT COST ──────────────────────────────────
        if cost_col:
            cost = self._safe_numeric(cost_col)
            lines += ["", "  PROCUREMENT COST ANALYSIS", "  " + "-" * 35]
            lines.append(f"    Total spend           : {self._fmt(cost.sum())}")
            lines.append(f"    Average per order     : {self._fmt(cost.mean())}")
            lines.append(f"    Cost std deviation    : {self._fmt(cost.std())}")
            lines.append(f"    Highest order cost    : {self._fmt(cost.max())}")

            # ─── Spend by Supplier ──────────────────────────────
            if supplier_col:
                supp_cost = self.df.groupby(supplier_col)[cost_col].sum().sort_values(ascending=False)
                total_cost = supp_cost.sum()
                lines += ["", "  SPEND BY SUPPLIER (Top 5)", "  " + "-" * 35]
                for supp, supp_spend in supp_cost.head(5).items():
                    pct = supp_spend / total_cost * 100
                    bar = "█" * int(pct / 2)
                    lines.append(
                        f"    {str(supp)[:25]:<25}: "
                        f"{self._fmt(supp_spend)} ({self._fmt(pct)}%) {bar}"
                    )

        # ─── SUPPLIER QUALITY ───────────────────────────────────
        if quality_col:
            quality = self._safe_numeric(quality_col)
            if quality.max() <= 100:
                defect_rate = 100 - quality.mean()
            else:
                defect_rate = quality.mean()

            status = "✅" if defect_rate <= self.benchmark_supplier_defect else "⚠️"
            lines += ["", "  SUPPLIER QUALITY (Gartner Benchmark)", "  " + "-" * 35]
            lines.append(f"    {status} Average quality      : {self._fmt(quality.mean())}%")
            lines.append(f"    Defect rate          : {self._fmt(defect_rate)}%")
            lines.append(f"       (benchmark: {self.benchmark_supplier_defect}%)")

        # ─── SCOR BENCHMARKS ────────────────────────────────────
        lines += ["", "  SCOR GLOBAL BENCHMARKS (Gartner 2024)", "  " + "-" * 35]
        lines.append(f"    On-time delivery     : {self.benchmark_on_time_delivery}%")
        lines.append(f"    Supplier defect rate : {self.benchmark_supplier_defect}%")
        lines.append(f"    Inventory days target: {self.benchmark_inventory_days} days")

        return "\n".join(lines)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return supply chain-specific Excel sheets."""
        sheets = {}
        supplier_col = self._detect_column(self.SUPPLIER_KEYWORDS)
        cost_col = self._detect_column(self.COST_KEYWORDS)
        lead_col = self._detect_column(self.LEAD_KEYWORDS)
        quality_col = self._detect_column(self.QUALITY_KEYWORDS)

        # ─── Supplier Analysis ──────────────────────────────────
        if supplier_col:
            agg_dict = {"Order Count": (supplier_col, "count")}
            if cost_col:
                agg_dict["Total Spend"] = (cost_col, "sum")
                agg_dict["Avg Spend"] = (cost_col, "mean")
            if lead_col:
                agg_dict["Avg Lead Time"] = (lead_col, "mean")
            if quality_col:
                agg_dict["Avg Quality"] = (quality_col, "mean")

            supp_summary = self.df.groupby(supplier_col).agg(**agg_dict).reset_index()
            supp_summary = supp_summary.sort_values("Total Spend", ascending=False)
            sheets["Supplier Analysis"] = supp_summary

        # ─── Lead Time Summary ──────────────────────────────────
        if lead_col:
            lead = self._safe_numeric(lead_col)
            lead_summary = pd.DataFrame({
                "Metric": ["Average Lead Time", "Median Lead Time", "Min Lead Time", "Max Lead Time", "Std Deviation"],
                "Value": [
                    lead.mean(),
                    lead.median(),
                    lead.min(),
                    lead.max(),
                    lead.std()
                ]
            })
            sheets["Lead Time Summary"] = lead_summary

        # Cost Summary
        if cost_col:
            cost = self._safe_numeric(cost_col)
            cost_summary = pd.DataFrame({
                "Metric": ["Total Spend", "Average Order Cost", "Median Order Cost", "Highest Order", "Lowest Order"],
                "Value": [
                    cost.sum(),
                    cost.mean(),
                    cost.median(),
                    cost.max(),
                    cost.min()
                ]
            })
            sheets["Cost Summary"] = cost_summary

        return sheets