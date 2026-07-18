# customization/real_estate.py
# Real Estate domain customization — properties, prices, locations

import pandas as pd
from customization.base_domain import BaseDomain
from typing import Dict, Any


class RealEstateDomain(BaseDomain):
    """Real Estate-specific report sections."""

    def detect(self) -> bool:
        """Detect if this is real estate data."""
        text_cols = [col.lower() for col in self.profile.text_columns]
        numeric_cols = [col.lower() for col in self.profile.numeric_columns]

        re_keywords = ['property', 'price', 'area', 'bedroom', 'bathroom',
                      'location', 'rent', 'square', 'land', 'building']

        has_re = any(k in ' '.join(text_cols + numeric_cols).lower() for k in re_keywords)

        return has_re

    def get_section_header(self) -> str:
        return "REAL ESTATE MARKET ANALYSIS"

    def get_priority(self) -> int:
        return 55

    def generate_content(self) -> str:
        """Generate real estate-specific content."""
        df = self.df.copy()

        content = []

        # 1. Property Summary
        content.append(self._get_property_summary(df))

        # 2. Price Analysis
        content.append(self._get_price_analysis(df))

        # 3. Location Breakdown
        content.append(self._get_location_breakdown(df))

        return "\n\n".join(content)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return real estate-specific Excel sheets."""
        return {}

    def _get_property_summary(self, df: pd.DataFrame) -> str:
        """Generate property summary."""
        property_cols = [c for c in df.columns if 'property' in c.lower() or 'address' in c.lower()]

        total_properties = len(df)

        return f"""
  PROPERTY SUMMARY
  {'-' * 40}
    Total Properties: {total_properties:,}
    Total Records   : {len(df):,}
"""

    def _get_price_analysis(self, df: pd.DataFrame) -> str:
        """Generate price analysis."""
        price_cols = [c for c in df.columns if any(k in c.lower() for k in
                     ['price', 'rent', 'cost', 'value'])]

        if not price_cols:
            return "  No price columns detected."

        col = price_cols[0]
        avg = df[col].mean()
        min_val = df[col].min()
        max_val = df[col].max()

        return f"""
  PRICE ANALYSIS
  {'-' * 40}
    Average Price   : ${avg:,.2f}
    Minimum Price   : ${min_val:,.2f}
    Maximum Price   : ${max_val:,.2f}
"""

    def _get_location_breakdown(self, df: pd.DataFrame) -> str:
        """Generate location breakdown."""
        location_cols = [c for c in df.columns if any(k in c.lower() for k in
                         ['location', 'area', 'city', 'zip', 'neighborhood'])]

        if not location_cols:
            return "  No location columns detected."

        breakdown = df[location_cols[0]].value_counts()

        lines = ["  LOCATION BREAKDOWN", "  " + "-" * 40]
        for location, count in breakdown.items():
            pct = count / len(df) * 100
            lines.append(f"    {location}: {count} ({pct:.1f}%)")

        return "\n".join(lines)