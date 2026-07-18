# customization/domains/energy.py
# Energy Domain — IEA / EIA Standards

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


class EnergyDomain(BaseDomain):
    """
    Energy-specific analysis based on IEA/EIA standards.
    Covers: Generation, Consumption, Efficiency, Carbon Intensity, Grid Reliability.
    """

    DOMAIN_NAME = "energy"

    DOMAIN_KEYWORDS = [
        "kwh", "mw", "gw", "generation", "consumption", "demand",
        "solar", "wind", "hydro", "nuclear", "thermal", "coal",
        "gas", "renewable", "grid", "transmission", "distribution",
        "efficiency", "carbon", "co2", "emission", "intensity",
        "capacity", "load", "peak", "offpeak", "storage",
        "battery", "smart", "meter", "customer", "utility"
    ]

    GENERATION_KEYWORDS = ["generation", "produced", "output", "mwh", "kwh"]
    CONSUMPTION_KEYWORDS = ["consumption", "used", "demand", "load", "kwh"]
    EFFICIENCY_KEYWORDS = ["efficiency", "loss", "efficiency_factor"]
    CARBON_KEYWORDS = ["carbon", "co2", "emission", "intensity", "ghg"]
    CAPACITY_KEYWORDS = ["capacity", "installed", "peak", "rating", "mw"]

    # IEA / EIA Benchmarks 2024
    BENCHMARK_RENEWABLE_SHARE = 30.0      # % of total generation
    BENCHMARK_CARBON_INTENSITY = 400.0    # g CO2/kWh (global average)
    BENCHMARK_GRID_RELIABILITY = 99.9     # % (5-nines target)
    BENCHMARK_EFFICIENCY = 85.0           # % (power plant average)
    BENCHMARK_PEAK_LOAD_FACTOR = 75.0     # % (average)

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load energy thresholds from config."""
        self.benchmark_renewable = config.get_threshold(
            'energy', 'renewable_benchmark', self.client_name
        ) or self.BENCHMARK_RENEWABLE_SHARE

        self.benchmark_carbon = config.get_threshold(
            'energy', 'carbon_benchmark', self.client_name
        ) or self.BENCHMARK_CARBON_INTENSITY

        self.benchmark_reliability = config.get_threshold(
            'energy', 'reliability_benchmark', self.client_name
        ) or self.BENCHMARK_GRID_RELIABILITY

        self.benchmark_efficiency = config.get_threshold(
            'energy', 'efficiency_benchmark', self.client_name
        ) or self.BENCHMARK_EFFICIENCY

    def detect(self) -> bool:
        """Detect if this is energy data."""
        all_cols_text = " ".join(self._get_all_columns()).lower()
        return any(k in all_cols_text for k in self.DOMAIN_KEYWORDS)

    def get_section_header(self) -> str:
        return "ENERGY DOMAIN ANALYSIS — IEA / EIA STANDARDS"

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
        """Generate energy-specific content for the text report."""

        generation_col = self._detect_column(self.GENERATION_KEYWORDS)
        consumption_col = self._detect_column(self.CONSUMPTION_KEYWORDS)
        efficiency_col = self._detect_column(self.EFFICIENCY_KEYWORDS)
        carbon_col = self._detect_column(self.CARBON_KEYWORDS)
        capacity_col = self._detect_column(self.CAPACITY_KEYWORDS)

        total = len(self.df)
        lines = [
            "",
            "  ENERGY ANALYTICS (IEA / EIA Standards)",
            "  " + "-" * 45,
        ]

        # ─── CONFIGURATION SUMMARY ──────────────────────────────
        lines += [
            "",
            "  CONFIGURATION SUMMARY",
            "  " + "-" * 35,
            f"    Client             : {self.client_name or 'Default'}",
            f"    Renewable Benchmark: {self.benchmark_renewable}%",
            f"    Carbon Benchmark   : {self.benchmark_carbon} gCO2/kWh",
            f"    Reliability Benchmark: {self.benchmark_reliability}%",
            f"    Efficiency Benchmark: {self.benchmark_efficiency}%",
        ]

        # ─── GENERATION ANALYSIS ──────────────────────────────────
        if generation_col:
            generation = self._safe_numeric(generation_col)
            lines += ["", "  GENERATION ANALYSIS", "  " + "-" * 35]
            lines.append(f"    Total generation    : {self._fmt(generation.sum())} MWh")
            lines.append(f"    Average generation  : {self._fmt(generation.mean())} MWh")
            lines.append(f"    Peak generation     : {self._fmt(generation.max())} MWh")

        # ─── CONSUMPTION / DEMAND ──────────────────────────────────
        if consumption_col:
            consumption = self._safe_numeric(consumption_col)
            lines += ["", "  CONSUMPTION / DEMAND", "  " + "-" * 35]
            lines.append(f"    Total consumption   : {self._fmt(consumption.sum())} MWh")
            lines.append(f"    Average consumption : {self._fmt(consumption.mean())} MWh")
            lines.append(f"    Peak demand         : {self._fmt(consumption.max())} MWh")

            if generation_col and generation_col != consumption_col:
                gen = self._safe_numeric(generation_col)
                # Calculate grid loss / difference
                diff = gen.sum() - consumption.sum()
                loss_pct = (diff / gen.sum() * 100) if gen.sum() > 0 else 0
                lines.append(f"    Grid loss           : {self._fmt(diff)} MWh ({self._fmt(loss_pct)}%)")

        # ─── RENEWABLE SHARE ──────────────────────────────────────
        if generation_col:
            # Try to detect renewable columns
            renewable_col = self._detect_column(["solar", "wind", "hydro", "renewable"])
            if renewable_col and generation_col:
                renewable = self._safe_numeric(renewable_col)
                generation = self._safe_numeric(generation_col)
                renewable_share = (renewable.sum() / generation.sum() * 100) if generation.sum() > 0 else 0
                status = "✅" if renewable_share >= self.benchmark_renewable else "⚠️"
                lines += ["", "  RENEWABLE SHARE", "  " + "-" * 35]
                lines.append(
                    f"    {status} Renewable share     : {self._fmt(renewable_share)}% "
                    f"(IEA benchmark: {self.benchmark_renewable}%)"
                )
                lines.append(f"    Renewable generation: {self._fmt(renewable.sum())} MWh")

        # ─── EFFICIENCY ──────────────────────────────────────────────
        if efficiency_col:
            efficiency = self._safe_numeric(efficiency_col)
            avg_efficiency = efficiency.mean()
            status = "✅" if avg_efficiency >= self.benchmark_efficiency else "⚠️"
            lines += ["", "  EFFICIENCY ANALYSIS", "  " + "-" * 35]
            lines.append(
                f"    {status} Average efficiency : {self._fmt(avg_efficiency)}% "
                f"(benchmark: {self.benchmark_efficiency}%)"
            )
            lines.append(f"    Min efficiency      : {self._fmt(efficiency.min())}%")
            lines.append(f"    Max efficiency      : {self._fmt(efficiency.max())}%")

        # ─── CARBON INTENSITY ──────────────────────────────────────
        if carbon_col:
            carbon = self._safe_numeric(carbon_col)
            avg_carbon = carbon.mean()
            status = "✅" if avg_carbon <= self.benchmark_carbon else "⚠️"
            lines += ["", "  CARBON INTENSITY", "  " + "-" * 35]
            lines.append(
                f"    {status} Carbon intensity   : {self._fmt(avg_carbon)} gCO2/kWh "
                f"(IEA benchmark: {self.benchmark_carbon} gCO2/kWh)"
            )
            lines.append(f"    Min intensity       : {self._fmt(carbon.min())} gCO2/kWh")
            lines.append(f"    Max intensity       : {self._fmt(carbon.max())} gCO2/kWh")

        # ─── CAPACITY / INSTALLED ──────────────────────────────────
        if capacity_col:
            capacity = self._safe_numeric(capacity_col)
            lines += ["", "  INSTALLED CAPACITY", "  " + "-" * 35]
            lines.append(f"    Total capacity      : {self._fmt(capacity.sum())} MW")
            lines.append(f"    Average capacity    : {self._fmt(capacity.mean())} MW")
            lines.append(f"    Capacity factor     : {self._fmt(capacity.mean() / capacity.max() * 100 if capacity.max() > 0 else 0)}%")

        # ─── GRID RELIABILITY ──────────────────────────────────────
        grid_col = self._detect_column(["uptime", "availability", "reliability"])
        if grid_col:
            grid = self._safe_numeric(grid_col)
            avg_reliability = grid.mean()
            status = "✅" if avg_reliability >= self.benchmark_reliability else "⚠️"
            lines += ["", "  GRID RELIABILITY", "  " + "-" * 35]
            lines.append(
                f"    {status} Reliability        : {self._fmt(avg_reliability)}% "
                f"(benchmark: {self.benchmark_reliability}%)"
            )
            outages = (grid < 99.0).sum()
            lines.append(f"    Outages (<99%)      : {outages} periods")

        # ─── PEAK LOAD ANALYSIS ──────────────────────────────────
        if consumption_col:
            consumption = self._safe_numeric(consumption_col)
            peak = consumption.max()
            avg = consumption.mean()
            load_factor = (avg / peak * 100) if peak > 0 else 0
            lines += ["", "  PEAK LOAD ANALYSIS", "  " + "-" * 35]
            lines.append(f"    Peak load           : {self._fmt(peak)} MWh")
            lines.append(f"    Average load        : {self._fmt(avg)} MWh")
            lines.append(f"    Load factor         : {self._fmt(load_factor)}%")

        # ─── IEA BENCHMARKS ──────────────────────────────────────
        lines += ["", "  IEA / EIA BENCHMARKS (2024)", "  " + "-" * 35]
        lines.append(f"    Renewable Share     : {self.benchmark_renewable}%")
        lines.append(f"    Carbon Intensity    : {self.benchmark_carbon} gCO2/kWh")
        lines.append(f"    Grid Reliability    : {self.benchmark_reliability}%")
        lines.append(f"    Plant Efficiency    : {self.benchmark_efficiency}%")

        return "\n".join(lines)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return energy-specific Excel sheets."""
        sheets = {}
        generation_col = self._detect_column(self.GENERATION_KEYWORDS)
        consumption_col = self._detect_column(self.CONSUMPTION_KEYWORDS)
        carbon_col = self._detect_column(self.CARBON_KEYWORDS)
        capacity_col = self._detect_column(self.CAPACITY_KEYWORDS)

        # ─── Generation Summary ──────────────────────────────────
        if generation_col:
            gen = self._safe_numeric(generation_col)
            gen_summary = pd.DataFrame({
                "Metric": ["Total Generation", "Average Generation", "Peak Generation", "Min Generation"],
                "Value": [
                    gen.sum(),
                    gen.mean(),
                    gen.max(),
                    gen.min()
                ]
            })
            sheets["Generation Summary"] = gen_summary

        # ─── Source Breakdown ──────────────────────────────────────
        source_col = self._detect_column(["source", "type", "fuel", "technology"])
        if source_col and generation_col:
            source_summary = self.df.groupby(source_col)[generation_col].agg(
                ["sum", "mean"]
            ).reset_index()
            source_summary.columns = ["Source", "Total Generation", "Average Generation"]
            source_summary = source_summary.sort_values("Total Generation", ascending=False)
            sheets["Generation by Source"] = source_summary

        # ─── Carbon Intensity ─────────────────────────────────────
        if carbon_col:
            carbon = self._safe_numeric(carbon_col)
            carbon_summary = pd.DataFrame({
                "Metric": ["Average Carbon Intensity", "Min Carbon Intensity", "Max Carbon Intensity"],
                "Value": [
                    carbon.mean(),
                    carbon.min(),
                    carbon.max()
                ]
            })
            sheets["Carbon Intensity"] = carbon_summary

        # ─── Capacity Utilization ──────────────────────────────────
        if capacity_col:
            capacity = self._safe_numeric(capacity_col)
            util_summary = pd.DataFrame({
                "Metric": ["Total Capacity", "Average Capacity", "Capacity Utilization", "Avg Utilization %"],
                "Value": [
                    capacity.sum(),
                    capacity.mean(),
                    capacity.sum() / len(capacity) if len(capacity) > 0 else 0,
                    (capacity.mean() / capacity.max() * 100) if capacity.max() > 0 else 0
                ]
            })
            sheets["Capacity Summary"] = util_summary

        return sheets