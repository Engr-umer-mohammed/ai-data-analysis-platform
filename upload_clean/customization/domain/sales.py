# customization/sales.py
# Sales domain customization — revenue, KPI, regional analysis

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


class SalesDomain(BaseDomain):
    """Sales-specific report sections for revenue and KPI data."""

    DEFAULT_TARGET_GROWTH = 0.10
    DEFAULT_TOP_PERFORMER_RANKING = 20
    DEFAULT_PRODUCT_PARETO = 80

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load sales thresholds from config."""
        self.target_growth = config.get_threshold(
            'sales', 'target_growth', self.client_name
        ) or self.DEFAULT_TARGET_GROWTH

        self.top_performer_ranking = config.get_threshold(
            'sales', 'top_performer_ranking', self.client_name
        ) or self.DEFAULT_TOP_PERFORMER_RANKING

        self.product_pareto = config.get_threshold(
            'sales', 'product_pareto', self.client_name
        ) or self.DEFAULT_PRODUCT_PARETO

        self.region_comparison = config.get_threshold(
            'sales', 'region_comparison', self.client_name
        ) or True

    def detect(self) -> bool:
        """Detect if this is sales data."""
        text_cols = [col.lower() for col in self.profile.text_columns]
        numeric_cols = [col.lower() for col in self.profile.numeric_columns]

        sales_keywords = ['sales', 'revenue', 'profit', 'customer', 'order', 'product']
        text_keywords = ['region', 'territory', 'branch', 'product']

        has_sales = any(k in ' '.join(numeric_cols).lower() for k in sales_keywords)
        has_text = any(k in ' '.join(text_cols).lower() for k in text_keywords)

        return has_sales and has_text

    def get_section_header(self) -> str:
        return "SALES PERFORMANCE ANALYSIS"

    def get_priority(self) -> int:
        return 70

    def generate_content(self) -> str:
        """Generate sales-specific content for the text report."""
        df = self.df.copy()

        # Find sales and region columns
        sales_col = self._find_sales_column(df)
        region_col = self._find_region_column(df)
        product_col = self._find_product_column(df)

        if not sales_col:
            return "  No sales/revenue column detected."

        content = []

        content.append(self._get_config_summary())
        content.append(self._get_sales_summary(df, sales_col))
        content.append(self._get_top_performers_text(df, sales_col, product_col or region_col))
        content.append(self._get_regional_breakdown_text(df, sales_col, region_col))
        content.append(self._get_product_breakdown_text(df, sales_col, product_col))

        return "\n\n".join(content)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return sales-specific Excel sheets."""
        df = self.df.copy()
        sales_col = self._find_sales_column(df)
        region_col = self._find_region_column(df)
        product_col = self._find_product_column(df)

        sheets = {}

        if sales_col and region_col:
            region_df = df.groupby(region_col)[sales_col].agg(['sum', 'mean', 'count']).reset_index()
            sheets['Regional Breakdown'] = region_df

        if sales_col and product_col:
            product_df = df.groupby(product_col)[sales_col].agg(['sum', 'mean']).reset_index()
            product_df = product_df.sort_values('sum', ascending=False)
            sheets['Product Performance'] = product_df

        return sheets

    # ─── Helper Methods ──────────────────────────────────────────

    def _get_config_summary(self) -> str:
        return f"""
  CONFIGURATION SUMMARY
  {'-' * 40}
    Client             : {self.client_name or 'Default'}
    Target Growth      : {self.target_growth * 100:.0f}%
    Top Performer %    : {self.top_performer_ranking}%
    Pareto Principle   : {self.product_pareto}%
"""

    def _find_sales_column(self, df: pd.DataFrame) -> str:
        """Find the sales/revenue column."""
        keywords = ['sales', 'revenue', 'profit', 'income', 'turnover']
        for col in df.columns:
            if any(k in col.lower() for k in keywords):
                return col
        return None

    def _find_region_column(self, df: pd.DataFrame) -> str:
        """Find the region column."""
        keywords = ['region', 'territory', 'branch', 'area', 'zone']
        for col in df.columns:
            if any(k in col.lower() for k in keywords):
                return col
        return None

    def _find_product_column(self, df: pd.DataFrame) -> str:
        """Find the product column."""
        keywords = ['product', 'item', 'good', 'service', 'sku']
        for col in df.columns:
            if any(k in col.lower() for k in keywords):
                return col
        return None

    def _get_sales_summary(self, df: pd.DataFrame, sales_col: str) -> str:
        total = df[sales_col].sum()
        avg = df[sales_col].mean()
        max_val = df[sales_col].max()
        min_val = df[sales_col].min()

        return f"""
  SALES SUMMARY
  {'-' * 40}
    Total Revenue   : ${total:,.2f}
    Average Sale    : ${avg:,.2f}
    Highest Sale    : ${max_val:,.2f}
    Lowest Sale     : ${min_val:,.2f}
    Total Orders    : {len(df):,}
"""

    def _get_top_performers_text(self, df: pd.DataFrame, sales_col: str, group_col: str) -> str:
        if not group_col:
            return "  No group column found for top performers."

        top = df.nlargest(10, sales_col)[[group_col, sales_col]]

        lines = ["  TOP PERFORMERS", "  " + "-" * 40]
        for _, row in top.iterrows():
            lines.append(f"    {row[group_col]}: ${row[sales_col]:,.2f}")

        return "\n".join(lines)

    def _get_regional_breakdown_text(self, df: pd.DataFrame, sales_col: str, region_col: str) -> str:
        if not region_col:
            return "  No region column found."

        breakdown = df.groupby(region_col)[sales_col].agg(['sum', 'mean', 'count'])

        lines = ["  REGIONAL BREAKDOWN", "  " + "-" * 40]
        for region, row in breakdown.iterrows():
            lines.append(
                f"    {region:<15}: ${row['sum']:>10,.2f} "
                f"({row['count']} orders, avg ${row['mean']:,.2f})"
            )

        return "\n".join(lines)

    def _get_product_breakdown_text(self, df: pd.DataFrame, sales_col: str, product_col: str) -> str:
        if not product_col:
            return "  No product column found."

        breakdown = df.groupby(product_col)[sales_col].agg(['sum', 'mean']).sort_values('sum', ascending=False)

        lines = ["  PRODUCT BREAKDOWN", "  " + "-" * 40]
        for product, row in breakdown.head(10).iterrows():
            lines.append(
                f"    {product:<20}: ${row['sum']:>10,.2f} "
                f"(avg ${row['mean']:,.2f})"
            )

        return "\n".join(lines)