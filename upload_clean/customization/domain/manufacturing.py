# customization/domains/manufacturing.py
# Manufacturing domain — quality, defects, OEE

import pandas as pd
from typing import Dict, Any
from customization.base_domain import BaseDomain

try:
    from config.config import config
except ImportError:
    class _ConfigFallback:
        def get_threshold(self, domain, key, client=None):
            return None
    config = _ConfigFallback()


class ManufacturingDomain(BaseDomain):
    """Manufacturing-specific report sections for production data."""

    DEFAULT_DEFECT_RATE_THRESHOLD = 0.05
    DEFAULT_QUALITY_TARGET = 95
    DEFAULT_OEE_TARGET = 85

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load manufacturing thresholds from config."""
        self.defect_rate_threshold = config.get_threshold(
            'manufacturing', 'defect_rate_threshold', self.client_name
        ) or self.DEFAULT_DEFECT_RATE_THRESHOLD

        self.quality_target = config.get_threshold(
            'manufacturing', 'quality_target', self.client_name
        ) or self.DEFAULT_QUALITY_TARGET

        self.oee_target = config.get_threshold(
            'manufacturing', 'oee_target', self.client_name
        ) or self.DEFAULT_OEE_TARGET

        self.shift_comparison = config.get_threshold(
            'manufacturing', 'shift_comparison', self.client_name
        ) or True

    def detect(self) -> bool:
        """Detect if this is manufacturing data."""
        text_cols = [col.lower() for col in self.profile.text_columns]
        numeric_cols = [col.lower() for col in self.profile.numeric_columns]

        keywords = ['production', 'defect', 'quality', 'machine', 'batch', 'shift', 'oee']
        has_keywords = any(k in ' '.join(text_cols + numeric_cols).lower() for k in keywords)

        return has_keywords

    def get_section_header(self) -> str:
        return "MANUFACTURING ANALYSIS"

    def get_priority(self) -> int:
        return 65

    def generate_content(self) -> str:
        """Generate manufacturing-specific content."""
        df = self.df.copy()

        quality_col = self._find_quality_column(df)
        defect_col = self._find_defect_column(df)
        shift_col = self._find_shift_column(df)
        product_col = self._find_product_column(df)

        content = []

        content.append(self._get_config_summary())
        content.append(self._get_quality_summary(df, quality_col, defect_col))
        content.append(self._get_shift_performance_text(df, shift_col, quality_col or defect_col))
        content.append(self._get_product_quality_text(df, product_col, quality_col or defect_col))

        return "\n\n".join(content)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return manufacturing-specific Excel sheets."""
        df = self.df.copy()
        product_col = self._find_product_column(df)
        quality_col = self._find_quality_column(df)

        sheets = {}

        if product_col and quality_col:
            product_df = df.groupby(product_col)[quality_col].agg(['mean', 'min', 'max']).reset_index()
            sheets['Product Quality'] = product_df

        return sheets

    # ─── Helper Methods ──────────────────────────────────────────

    def _get_config_summary(self) -> str:
        return f"""
  CONFIGURATION SUMMARY
  {'-' * 40}
    Client               : {self.client_name or 'Default'}
    Defect Rate Target   : {self.defect_rate_threshold * 100:.0f}%
    Quality Target       : {self.quality_target}%
    OEE Target           : {self.oee_target}%
"""

    def _find_quality_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'quality' in col.lower() or 'score' in col.lower():
                return col
        return None

    def _find_defect_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'defect' in col.lower() or 'reject' in col.lower() or 'scrap' in col.lower():
                return col
        return None

    def _find_shift_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'shift' in col.lower():
                return col
        return None

    def _find_product_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'product' in col.lower() or 'batch' in col.lower():
                return col
        return None

    def _get_quality_summary(self, df: pd.DataFrame, quality_col: str, defect_col: str) -> str:
        lines = ["  QUALITY SUMMARY", "  " + "-" * 40]

        if quality_col:
            avg_quality = df[quality_col].mean()
            min_quality = df[quality_col].min()
            max_quality = df[quality_col].max()
            status = "✅ On Target" if avg_quality >= self.quality_target else "⚠️ Below Target"
            lines.append(f"    Average Quality   : {avg_quality:.1f}% ({status})")
            lines.append(f"    Quality Range     : {min_quality:.0f}% - {max_quality:.0f}%")

        if defect_col:
            total_defects = df[defect_col].sum()
            avg_defects = df[defect_col].mean()
            defect_rate = total_defects / len(df) if len(df) > 0 else 0
            status = "✅ Acceptable" if defect_rate <= self.defect_rate_threshold else "⚠️ Exceeds Target"
            lines.append(f"    Total Defects     : {total_defects}")
            lines.append(f"    Defect Rate       : {defect_rate:.3f} ({status})")

        return "\n".join(lines)

    def _get_shift_performance_text(self, df: pd.DataFrame, shift_col: str, metric_col: str) -> str:
        if not shift_col or not metric_col:
            return "  No shift or metric column found."

        breakdown = df.groupby(shift_col)[metric_col].mean().sort_values(ascending=False)

        lines = ["  SHIFT PERFORMANCE", "  " + "-" * 40]
        for shift, value in breakdown.items():
            lines.append(f"    {shift}: {value:.1f}")

        return "\n".join(lines)

    def _get_product_quality_text(self, df: pd.DataFrame, product_col: str, metric_col: str) -> str:
        if not product_col or not metric_col:
            return "  No product or metric column found."

        breakdown = df.groupby(product_col)[metric_col].mean().sort_values(ascending=False)

        lines = ["  PRODUCT QUALITY", "  " + "-" * 40]
        for product, value in breakdown.head(10).items():
            lines.append(f"    {product:<20}: {value:.1f}%")

        return "\n".join(lines)