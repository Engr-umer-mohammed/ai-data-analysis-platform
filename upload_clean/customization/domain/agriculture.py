# customization/domains/agriculture.py
# Agriculture Domain — FAO / USDA Standards

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


class AgricultureDomain(BaseDomain):
    """
    Agriculture-specific analysis based on FAO and USDA standards.
    Covers: Crop Yield, Livestock, Irrigation, Inputs, Harvest.
    """

    DOMAIN_NAME = "agriculture"

    DOMAIN_KEYWORDS = [
        "crop", "yield", "harvest", "acre", "hectare",
        "livestock", "cattle", "poultry", "swine", "sheep",
        "irrigation", "rainfall", "fertilizer", "pesticide",
        "soil", "planting", "growing", "season", "rotation",
        "organic", "conventional", "tillage", "irrigation",
        "silo", "barn", "tractor", "combine", "grain",
        "maize", "wheat", "rice", "soybean", "corn",
        "dairy", "meat", "wool", "egg", "milk"
    ]

    CROP_KEYWORDS = ["crop", "yield", "harvest", "acre", "hectare", "bushel", "tonne"]
    LIVESTOCK_KEYWORDS = ["livestock", "cattle", "herd", "flock", "head", "poultry"]
    INPUT_KEYWORDS = ["fertilizer", "pesticide", "herbicide", "seed", "feed", "fuel"]
    IRRIGATION_KEYWORDS = ["irrigation", "rainfall", "precipitation", "water", "moisture"]
    SOIL_KEYWORDS = ["soil", "ph", "organic", "nitrogen", "phosphorus", "potassium", "carbon"]
    SEASON_KEYWORDS = ["season", "year", "cycle", "spring", "summer", "fall", "winter"]

    # FAO / USDA Benchmarks 2024
    BENCHMARK_YIELD_CORN = 176.0       # bushels/acre (US average)
    BENCHMARK_YIELD_WHEAT = 52.0       # bushels/acre (US average)
    BENCHMARK_CATTLE = 1.2             # cattle per acre (stocking rate)
    BENCHMARK_IRRIGATION_EFFICIENCY = 65.0  # % (target)
    BENCHMARK_CROP_DIVERSITY = 0.7     # Simpson Diversity Index

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load agriculture thresholds from config."""
        self.benchmark_yield = config.get_threshold(
            'agriculture', 'yield_benchmark', self.client_name
        ) or self.BENCHMARK_YIELD_CORN

        self.benchmark_stocking = config.get_threshold(
            'agriculture', 'stocking_benchmark', self.client_name
        ) or self.BENCHMARK_CATTLE

        self.benchmark_irrigation = config.get_threshold(
            'agriculture', 'irrigation_benchmark', self.client_name
        ) or self.BENCHMARK_IRRIGATION_EFFICIENCY

    def detect(self) -> bool:
        """Detect if this is agriculture data."""
        all_cols_text = " ".join(self._get_all_columns()).lower()
        return any(k in all_cols_text for k in self.DOMAIN_KEYWORDS)

    def get_section_header(self) -> str:
        return "AGRICULTURE DOMAIN ANALYSIS — FAO / USDA STANDARDS"

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
        """Generate agriculture-specific content for the text report."""

        crop_col = self._detect_column(self.CROP_KEYWORDS)
        livestock_col = self._detect_column(self.LIVESTOCK_KEYWORDS)
        input_col = self._detect_column(self.INPUT_KEYWORDS)
        irrigation_col = self._detect_column(self.IRRIGATION_KEYWORDS)
        soil_col = self._detect_column(self.SOIL_KEYWORDS)
        season_col = self._detect_column(self.SEASON_KEYWORDS)

        total = len(self.df)
        lines = [
            "",
            "  AGRICULTURE ANALYTICS (FAO / USDA Standards)",
            "  " + "-" * 45,
        ]

        # ─── CONFIGURATION SUMMARY ──────────────────────────────
        lines += [
            "",
            "  CONFIGURATION SUMMARY",
            "  " + "-" * 35,
            f"    Client             : {self.client_name or 'Default'}",
            f"    Yield Benchmark    : {self.benchmark_yield} bushels/acre",
            f"    Stocking Benchmark : {self.benchmark_stocking} head/acre",
            f"    Irrigation Benchmark: {self.benchmark_irrigation}%",
        ]

        # ─── CROP YIELD ANALYSIS ──────────────────────────────────
        if crop_col:
            crop = self._safe_numeric(crop_col)
            avg_yield = crop.mean()
            status = "✅" if avg_yield >= self.benchmark_yield else "⚠️"
            lines += ["", "  CROP YIELD ANALYSIS", "  " + "-" * 35]
            lines.append(
                f"    {status} Average yield        : {self._fmt(avg_yield)} bu/acre "
                f"(USDA benchmark: {self.benchmark_yield} bu/acre)"
            )
            lines.append(f"    Max yield            : {self._fmt(crop.max())} bu/acre")
            lines.append(f"    Min yield            : {self._fmt(crop.min())} bu/acre")
            lines.append(f"    Yield variation      : {self._fmt(crop.std())} bu/acre")
            if avg_yield < self.benchmark_yield * 0.8:
                lines.append("    ⚠️  Significant yield gap detected")

        # ─── LIVESTOCK ANALYSIS ──────────────────────────────────
        if livestock_col:
            livestock = self._safe_numeric(livestock_col)
            avg_stocking = livestock.mean()
            status = "✅" if avg_stocking <= self.benchmark_stocking else "⚠️"
            lines += ["", "  LIVESTOCK ANALYSIS", "  " + "-" * 35]
            lines.append(
                f"    {status} Avg stocking rate   : {self._fmt(avg_stocking)} head/acre "
                f"(benchmark: {self.benchmark_stocking} head/acre)"
            )
            lines.append(f"    Total livestock     : {self._fmt(livestock.sum(), 0)} head")
            lines.append(f"    Max stocking        : {self._fmt(livestock.max())} head/acre")
            if avg_stocking > self.benchmark_stocking * 1.3:
                lines.append("    ⚠️  Overstocking detected (>30% above benchmark)")

        # ─── INPUT ANALYSIS ──────────────────────────────────────
        if input_col:
            inputs = self._safe_numeric(input_col)
            avg_input = inputs.mean()
            lines += ["", "  INPUT ANALYSIS (Fertilizer / Pesticides)", "  " + "-" * 35]
            lines.append(f"    Avg input cost       : ${self._fmt(avg_input)}/acre")
            lines.append(f"    Total input cost    : ${self._fmt(inputs.sum())}")
            lines.append(f"    Input intensity     : {self._fmt(avg_input)} per acre")

        # ─── IRRIGATION ANALYSIS ──────────────────────────────────
        if irrigation_col:
            irrigation = self._safe_numeric(irrigation_col)
            avg_irrigation = irrigation.mean()
            status = "✅" if avg_irrigation >= self.benchmark_irrigation else "⚠️"
            lines += ["", "  IRRIGATION EFFICIENCY", "  " + "-" * 35]
            lines.append(
                f"    {status} Avg efficiency      : {self._fmt(avg_irrigation)}% "
                f"(FAO benchmark: {self.benchmark_irrigation}%)"
            )
            lines.append(f"    Max efficiency       : {self._fmt(irrigation.max())}%")
            lines.append(f"    Min efficiency       : {self._fmt(irrigation.min())}%")

        # ─── SOIL ANALYSIS ──────────────────────────────────────────
        if soil_col:
            soil = self._safe_numeric(soil_col)
            avg_soil = soil.mean()
            lines += ["", "  SOIL QUALITY", "  " + "-" * 35]
            lines.append(f"    Avg soil score      : {self._fmt(avg_soil)}/100")
            lines.append(f"    Good soil (>70)     : {(soil > 70).sum()} fields")
            lines.append(f"    Poor soil (<40)     : {(soil < 40).sum()} fields")

            # Soil components if available
            ph_col = self._detect_column(["ph", "acid", "alkaline"])
            if ph_col:
                ph = self._safe_numeric(ph_col)
                lines.append(f"    Avg pH              : {self._fmt(ph.mean())}")
                lines.append(f"    Ideal pH range (6.0-7.5): {((ph >= 6.0) & (ph <= 7.5)).sum()} fields")

        # ─── SEASONAL ANALYSIS ──────────────────────────────────
        if season_col:
            season_dist = self.df[season_col].value_counts()
            lines += ["", "  SEASONAL DISTRIBUTION", "  " + "-" * 35]
            for season, count in season_dist.items():
                pct = count / total * 100
                bar = "█" * int(pct / 2)
                lines.append(
                    f"    {str(season)[:25]:<25}: "
                    f"{count:>3} ({self._fmt(pct):>5}%) {bar}"
                )

        # ─── FAO BENCHMARKS ──────────────────────────────────────────
        lines += ["", "  FAO / USDA BENCHMARKS (2024)", "  " + "-" * 35]
        lines.append(f"    Corn Yield Target      : {self.benchmark_yield} bu/acre")
        lines.append(f"    Stocking Rate Target   : {self.benchmark_stocking} head/acre")
        lines.append(f"    Irrigation Efficiency  : {self.benchmark_irrigation}%")

        return "\n".join(lines)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return agriculture-specific Excel sheets."""
        sheets = {}
        crop_col = self._detect_column(self.CROP_KEYWORDS)
        livestock_col = self._detect_column(self.LIVESTOCK_KEYWORDS)
        input_col = self._detect_column(self.INPUT_KEYWORDS)
        irrigation_col = self._detect_column(self.IRRIGATION_KEYWORDS)
        season_col = self._detect_column(self.SEASON_KEYWORDS)

        # ─── Crop Yield Summary ──────────────────────────────────
        if crop_col:
            crop = self._safe_numeric(crop_col)
            crop_summary = pd.DataFrame({
                "Metric": ["Count", "Mean", "Median", "Std", "Min", "Max", "P25", "P75"],
                "Value": [
                    len(crop),
                    crop.mean(),
                    crop.median(),
                    crop.std(),
                    crop.min(),
                    crop.max(),
                    crop.quantile(0.25),
                    crop.quantile(0.75)
                ]
            })
            sheets["Crop Yield Summary"] = crop_summary

        # ─── Seasonal Yield Comparison ──────────────────────────
        if season_col and crop_col:
            season_yield = self.df.groupby(season_col)[crop_col].agg(
                ["mean", "max", "min"]
            ).reset_index()
            season_yield.columns = ["Season", "Avg Yield", "Max Yield", "Min Yield"]
            sheets["Seasonal Yield"] = season_yield

        # ─── Input vs Yield ──────────────────────────────────────
        if crop_col and input_col:
            crop = self._safe_numeric(crop_col)
            inputs = self._safe_numeric(input_col)
            input_yield_df = pd.DataFrame({
                "Metric": ["Average Input Cost", "Average Yield", "Cost per Bushel", "Input Efficiency"],
                "Value": [
                    inputs.mean(),
                    crop.mean(),
                    inputs.mean() / crop.mean() if crop.mean() > 0 else 0,
                    crop.mean() / inputs.mean() if inputs.mean() > 0 else 0
                ]
            })
            sheets["Input Efficiency"] = input_yield_df

        # ─── Livestock Summary ──────────────────────────────────
        if livestock_col:
            livestock = self._safe_numeric(livestock_col)
            livestock_summary = pd.DataFrame({
                "Metric": ["Total Head", "Average Stocking Rate", "Max Stocking Rate", "Min Stocking Rate"],
                "Value": [
                    livestock.sum(),
                    livestock.mean(),
                    livestock.max(),
                    livestock.min()
                ]
            })
            sheets["Livestock Summary"] = livestock_summary

        return sheets