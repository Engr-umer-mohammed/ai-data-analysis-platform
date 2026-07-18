# customization/logistics.py
# Logistics domain customization — delivery performance, route analysis

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


class LogisticsDomain(BaseDomain):
    """Logistics-specific report sections for delivery data."""

    DEFAULT_ON_TIME_DELIVERY_TARGET = 95
    DEFAULT_COST_PER_KG_TARGET = 10
    DEFAULT_DISTANCE_EFFICIENCY = 80

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load logistics thresholds from config."""
        self.on_time_delivery_target = config.get_threshold(
            'logistics', 'on_time_delivery_target', self.client_name
        ) or self.DEFAULT_ON_TIME_DELIVERY_TARGET

        self.cost_per_kg_target = config.get_threshold(
            'logistics', 'cost_per_kg_target', self.client_name
        ) or self.DEFAULT_COST_PER_KG_TARGET

        self.distance_efficiency = config.get_threshold(
            'logistics', 'distance_efficiency', self.client_name
        ) or self.DEFAULT_DISTANCE_EFFICIENCY

    def detect(self) -> bool:
        """Detect if this is logistics data."""
        text_cols = [col.lower() for col in self.profile.text_columns]
        numeric_cols = [col.lower() for col in self.profile.numeric_columns]

        keywords = ['delivery', 'shipment', 'route', 'distance', 'carrier', 'warehouse']
        has_keywords = any(k in ' '.join(text_cols + numeric_cols).lower() for k in keywords)

        return has_keywords

    def get_section_header(self) -> str:
        return "LOGISTICS ANALYSIS"

    def get_priority(self) -> int:
        return 65

    def generate_content(self) -> str:
        """Generate logistics-specific content."""
        df = self.df.copy()

        delivery_col = self._find_delivery_column(df)
        cost_col = self._find_cost_column(df)
        route_col = self._find_route_column(df)

        content = []

        content.append(self._get_config_summary())
        content.append(self._get_delivery_summary(df, delivery_col, cost_col))
        content.append(self._get_route_performance_text(df, route_col, delivery_col))

        return "\n\n".join(content)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return logistics-specific Excel sheets."""
        df = self.df.copy()
        route_col = self._find_route_column(df)
        delivery_col = self._find_delivery_column(df)

        sheets = {}

        if route_col and delivery_col:
            route_df = df.groupby(route_col)[delivery_col].agg(['mean', 'min', 'max']).reset_index()
            sheets['Route Performance'] = route_df

        return sheets

    # ─── Helper Methods ──────────────────────────────────────────

    def _get_config_summary(self) -> str:
        return f"""
  CONFIGURATION SUMMARY
  {'-' * 40}
    Client               : {self.client_name or 'Default'}
    On-Time Target       : {self.on_time_delivery_target}%
    Cost/kg Target       : ${self.cost_per_kg_target:.2f}
"""

    def _find_delivery_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'delivery' in col.lower() or 'status' in col.lower():
                return col
        return None

    def _find_cost_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'cost' in col.lower():
                return col
        return None

    def _find_route_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'route' in col.lower():
                return col
        return None

    def _get_delivery_summary(self, df: pd.DataFrame, delivery_col: str, cost_col: str) -> str:
        lines = ["  DELIVERY SUMMARY", "  " + "-" * 40]

        total = len(df)
        lines.append(f"    Total Deliveries  : {total}")

        if delivery_col:
            # Assume 1 = on-time, 0 = late
            on_time = df[delivery_col].sum() if delivery_col else 0
            on_time_pct = on_time / total * 100 if total > 0 else 0
            status = "✅ On Target" if on_time_pct >= self.on_time_delivery_target else "⚠️ Below Target"
            lines.append(f"    On-Time Deliveries: {on_time:.0f} ({on_time_pct:.1f}%) {status}")

        if cost_col:
            total_cost = df[cost_col].sum()
            avg_cost = df[cost_col].mean()
            lines.append(f"    Total Cost        : ${total_cost:,.2f}")
            lines.append(f"    Avg Cost          : ${avg_cost:,.2f}")

        return "\n".join(lines)

    def _get_route_performance_text(self, df: pd.DataFrame, route_col: str, delivery_col: str) -> str:
        if not route_col:
            return "  No route column found."

        lines = ["  ROUTE PERFORMANCE", "  " + "-" * 40]

        for route in df[route_col].unique():
            route_df = df[df[route_col] == route]
            if delivery_col:
                on_time_pct = route_df[delivery_col].mean() * 100
                status = "✅" if on_time_pct >= self.on_time_delivery_target else "⚠️"
                lines.append(
                    f"    {route:<20}: {on_time_pct:.1f}% on-time {status} "
                    f"({len(route_df)} deliveries)"
                )

        return "\n".join(lines)