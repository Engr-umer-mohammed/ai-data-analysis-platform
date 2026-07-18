# customization/domains/finance.py
# Finance domain — stock prices, ratios, risk

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


class FinanceDomain(BaseDomain):
    """Finance-specific report sections for stock/investment data."""

    DEFAULT_PE_RATIO_BENCHMARK = 25
    DEFAULT_VOLATILITY_THRESHOLD = 0.15
    DEFAULT_VOLUME_THRESHOLD = 1000000

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load finance thresholds from config."""
        self.pe_ratio_benchmark = config.get_threshold(
            'finance', 'pe_ratio_benchmark', self.client_name
        ) or self.DEFAULT_PE_RATIO_BENCHMARK

        self.volatility_threshold = config.get_threshold(
            'finance', 'volatility_threshold', self.client_name
        ) or self.DEFAULT_VOLATILITY_THRESHOLD

        self.volume_threshold = config.get_threshold(
            'finance', 'volume_threshold', self.client_name
        ) or self.DEFAULT_VOLUME_THRESHOLD

    def detect(self) -> bool:
        """Detect if this is finance data."""
        text_cols = [col.lower() for col in self.profile.text_columns]
        numeric_cols = [col.lower() for col in self.profile.numeric_columns]

        keywords = ['stock', 'price', 'volume', 'return', 'dividend', 'investment', 'budget']
        has_keywords = any(k in ' '.join(text_cols + numeric_cols).lower() for k in keywords)

        return has_keywords

    def get_section_header(self) -> str:
        return "FINANCIAL ANALYSIS"

    def get_priority(self) -> int:
        return 60

    def generate_content(self) -> str:
        """Generate finance-specific content."""
        df = self.df.copy()

        price_col = self._find_price_column(df)
        volume_col = self._find_volume_column(df)
        stock_col = self._find_stock_column(df)

        content = []

        content.append(self._get_config_summary())
        content.append(self._get_price_summary(df, price_col, volume_col))
        content.append(self._get_stock_analysis_text(df, stock_col, price_col, volume_col))

        return "\n\n".join(content)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return finance-specific Excel sheets."""
        df = self.df.copy()
        stock_col = self._find_stock_column(df)
        price_col = self._find_price_column(df)

        sheets = {}

        if stock_col and price_col:
            stock_df = df.groupby(stock_col)[price_col].agg(['mean', 'min', 'max']).reset_index()
            sheets['Stock Summary'] = stock_df

        return sheets

    # ─── Helper Methods ──────────────────────────────────────────

    def _get_config_summary(self) -> str:
        return f"""
  CONFIGURATION SUMMARY
  {'-' * 40}
    Client               : {self.client_name or 'Default'}
    P/E Benchmark        : {self.pe_ratio_benchmark}
    Volatility Threshold : {self.volatility_threshold * 100:.0f}%
    Volume Threshold     : {self.volume_threshold:,}
"""

    def _find_price_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'price' in col.lower() or 'close' in col.lower() or 'open' in col.lower():
                return col
        return None

    def _find_volume_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'volume' in col.lower():
                return col
        return None

    def _find_stock_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'stock' in col.lower() or 'symbol' in col.lower() or 'ticker' in col.lower():
                return col
        return None

    def _get_price_summary(self, df: pd.DataFrame, price_col: str, volume_col: str) -> str:
        lines = ["  PRICE SUMMARY", "  " + "-" * 40]

        if price_col:
            avg_price = df[price_col].mean()
            min_price = df[price_col].min()
            max_price = df[price_col].max()
            volatility = df[price_col].std() / avg_price if avg_price > 0 else 0
            lines.append(f"    Average Price     : ${avg_price:.2f}")
            lines.append(f"    Price Range       : ${min_price:.2f} - ${max_price:.2f}")
            lines.append(f"    Volatility        : {volatility * 100:.1f}%")

        if volume_col:
            avg_volume = df[volume_col].mean()
            lines.append(f"    Avg Volume        : {avg_volume:,.0f}")

        return "\n".join(lines)

    def _get_stock_analysis_text(self, df: pd.DataFrame, stock_col: str, price_col: str, volume_col: str) -> str:
        if not stock_col:
            return "  No stock column found."

        lines = ["  STOCK PERFORMANCE", "  " + "-" * 40]

        for stock in df[stock_col].unique():
            stock_df = df[df[stock_col] == stock]
            if price_col and len(stock_df) > 0:
                start_price = stock_df[price_col].iloc[0]
                end_price = stock_df[price_col].iloc[-1]
                change = ((end_price - start_price) / start_price * 100) if start_price > 0 else 0
                lines.append(f"    {stock:<10}: ${end_price:.2f} ({change:+.1f}%)")

        return "\n".join(lines)