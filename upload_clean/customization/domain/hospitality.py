# customization/domains/hospitality.py
# Hospitality Domain — STR / RevPAR Standards

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


class HospitalityDomain(BaseDomain):
    """
    Hospitality-specific analysis based on STR Global standards.
    Covers: Occupancy, ADR (Average Daily Rate), RevPAR, Guest Satisfaction.
    """

    DOMAIN_NAME = "hospitality"

    DOMAIN_KEYWORDS = [
        "hotel", "room", "guest", "booking", "reservation",
        "checkin", "checkout", "occupancy", "revpar",
        "adr", "rating", "review", "service", "amenity",
        "restaurant", "bar", "spa", "concierge", "housekeeping",
        "cancellation", "noshow", "loyalty", "rate_plan"
    ]

    REVENUE_KEYWORDS = ["revenue", "rate", "adr", "tariff", "price"]
    OCCUPANCY_KEYWORDS = ["occupancy", "occupied", "available", "rooms"]
    RATING_KEYWORDS = ["rating", "score", "review", "satisfaction"]
    BOOKING_KEYWORDS = ["booking", "reservation", "stay", "night"]
    ROOM_KEYWORDS = ["room", "suite", "category", "type"]
    CHANNEL_KEYWORDS = ["channel", "source", "ota", "direct"]

    # STR Global Benchmarks 2024
    BENCHMARK_OCCUPANCY = 66.0    # % global average
    BENCHMARK_ADR = 150.0          # USD global average
    BENCHMARK_REVPAR = 99.0        # USD global average
    BENCHMARK_RATING = 4.2         # /5 TripAdvisor average

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load hospitality thresholds from config."""
        self.benchmark_occupancy = config.get_threshold(
            'hospitality', 'occupancy_benchmark', self.client_name
        ) or self.BENCHMARK_OCCUPANCY

        self.benchmark_adr = config.get_threshold(
            'hospitality', 'adr_benchmark', self.client_name
        ) or self.BENCHMARK_ADR

        self.benchmark_revpar = config.get_threshold(
            'hospitality', 'revpar_benchmark', self.client_name
        ) or self.BENCHMARK_REVPAR

        self.benchmark_rating = config.get_threshold(
            'hospitality', 'rating_benchmark', self.client_name
        ) or self.BENCHMARK_RATING

    def detect(self) -> bool:
        """Detect if this is hospitality data."""
        all_cols_text = " ".join(self._get_all_columns()).lower()
        return any(k in all_cols_text for k in self.DOMAIN_KEYWORDS)

    def get_section_header(self) -> str:
        return "HOSPITALITY DOMAIN ANALYSIS — STR / REVPAR STANDARDS"

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
        """Generate hospitality-specific content for the text report."""

        revenue_col = self._detect_column(self.REVENUE_KEYWORDS)
        occupancy_col = self._detect_column(self.OCCUPANCY_KEYWORDS)
        rating_col = self._detect_column(self.RATING_KEYWORDS)
        booking_col = self._detect_column(self.BOOKING_KEYWORDS)
        room_col = self._detect_column(self.ROOM_KEYWORDS)
        channel_col = self._detect_column(self.CHANNEL_KEYWORDS)

        total = len(self.df)
        lines = [
            "",
            "  HOSPITALITY ANALYTICS (STR Global Standards)",
            "  " + "-" * 45,
        ]

        # ─── CONFIGURATION SUMMARY ──────────────────────────────
        lines += [
            "",
            "  CONFIGURATION SUMMARY",
            "  " + "-" * 35,
            f"    Client             : {self.client_name or 'Default'}",
            f"    Occupancy Benchmark: {self.benchmark_occupancy}%",
            f"    ADR Benchmark      : ${self.benchmark_adr}",
            f"    RevPAR Benchmark   : ${self.benchmark_revpar}",
            f"    Rating Benchmark   : {self.benchmark_rating}/5",
        ]

        # ─── REVENUE ANALYSIS ──────────────────────────────────
        if revenue_col:
            rev = self._safe_numeric(revenue_col)
            adr = rev.mean()
            status = "✅" if adr >= self.benchmark_adr else "⚠️"
            lines += ["", "  REVENUE ANALYSIS (ADR/RevPAR)", "  " + "-" * 35]
            lines.append(f"    {status} Average Daily Rate : {self._fmt(adr)}")
            lines.append(f"       (STR benchmark: ${self.benchmark_adr})")
            lines.append(f"    Total revenue        : {self._fmt(rev.sum())}")
            lines.append(f"    Revenue variance     : {self._fmt(rev.std())}")

        # ─── OCCUPANCY ANALYSIS ─────────────────────────────────
        if occupancy_col:
            occ = self._safe_numeric(occupancy_col)
            avg_occ = occ.mean()
            status = "✅" if avg_occ >= self.benchmark_occupancy else "⚠️"
            lines += ["", "  OCCUPANCY ANALYSIS", "  " + "-" * 35]
            lines.append(
                f"    {status} Average occupancy    : {self._fmt(avg_occ)}% "
                f"(STR benchmark: {self.benchmark_occupancy}%)"
            )
            lines.append(f"    Peak occupancy       : {self._fmt(occ.max())}%")
            lines.append(f"    Low occupancy (<50%)  : {(occ < 50).sum()} periods")
            lines.append(f"    High occupancy (>85%) : {(occ > 85).sum()} periods")

            # RevPAR calculation
            if revenue_col:
                rev = self._safe_numeric(revenue_col)
                revpar = rev.mean() * avg_occ / 100
                status_revpar = "✅" if revpar >= self.benchmark_revpar else "⚠️"
                lines.append(
                    f"    {status_revpar} RevPAR estimate     : {self._fmt(revpar)} "
                    f"(STR benchmark: ${self.benchmark_revpar})"
                )

        # ─── GUEST SATISFACTION ─────────────────────────────────
        if rating_col:
            rating = self._safe_numeric(rating_col)
            avg_rating = rating.mean()
            status = "✅" if avg_rating >= self.benchmark_rating else "⚠️"
            lines += ["", "  GUEST SATISFACTION", "  " + "-" * 35]
            lines.append(
                f"    {status} Average rating       : {self._fmt(avg_rating)} / 5 "
                f"(benchmark: {self.benchmark_rating} / 5)"
            )
            lines.append(f"    Excellent (5.0)      : {(rating >= 5.0).sum()} reviews")
            lines.append(f"    Good (4.0-4.9)       : {((rating >= 4.0) & (rating < 5.0)).sum()} reviews")
            lines.append(f"    Average (3.0-3.9)    : {((rating >= 3.0) & (rating < 4.0)).sum()} reviews")
            lines.append(f"    Poor (<3.0)          : {(rating < 3.0).sum()} reviews")

        # ─── ROOM TYPE PERFORMANCE ─────────────────────────────
        if room_col and revenue_col:
            room_rev = self.df.groupby(room_col)[revenue_col].mean().sort_values(ascending=False)
            lines += ["", "  AVERAGE RATE BY ROOM TYPE", "  " + "-" * 35]
            for room_type, avg_rate in room_rev.head(10).items():
                lines.append(f"    {str(room_type)[:25]:<25}: {self._fmt(avg_rate)}")

        # ─── BOOKING CHANNEL DISTRIBUTION ──────────────────────
        if channel_col:
            channel_dist = self.df[channel_col].value_counts()
            lines += ["", "  BOOKINGS BY CHANNEL", "  " + "-" * 35]
            for channel, count in channel_dist.head(10).items():
                pct = count / total * 100
                bar = "█" * int(pct / 2)
                lines.append(
                    f"    {str(channel)[:25]:<25}: "
                    f"{count:>3} ({self._fmt(pct):>5}%) {bar}"
                )

        return "\n".join(lines)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return hospitality-specific Excel sheets."""
        sheets = {}
        room_col = self._detect_column(self.ROOM_KEYWORDS)
        revenue_col = self._detect_column(self.REVENUE_KEYWORDS)
        rating_col = self._detect_column(self.RATING_KEYWORDS)
        channel_col = self._detect_column(self.CHANNEL_KEYWORDS)

        # ─── Room Type Analysis ─────────────────────────────────
        if room_col:
            agg_dict = {"Count": (room_col, "count")}
            if revenue_col:
                agg_dict["Avg Revenue"] = (revenue_col, "mean")
                agg_dict["Total Revenue"] = (revenue_col, "sum")
            if rating_col:
                agg_dict["Avg Rating"] = (rating_col, "mean")

            room_summary = self.df.groupby(room_col).agg(**agg_dict).reset_index()
            sheets["Room Type Analysis"] = room_summary

        # ─── Channel Analysis ──────────────────────────────────
        if channel_col:
            agg_dict = {"Bookings": (channel_col, "count")}
            if revenue_col:
                agg_dict["Avg Revenue"] = (revenue_col, "mean")
                agg_dict["Total Revenue"] = (revenue_col, "sum")

            channel_summary = self.df.groupby(channel_col).agg(**agg_dict).reset_index()
            sheets["Channel Analysis"] = channel_summary

        # ─── Rating Distribution ────────────────────────────────
        if rating_col:
            rating = self._safe_numeric(rating_col)
            rating_dist = pd.DataFrame({
                "Rating Range": ["Excellent (5.0)", "Good (4.0-4.9)", "Average (3.0-3.9)", "Poor (<3.0)"],
                "Count": [
                    (rating >= 5.0).sum(),
                    ((rating >= 4.0) & (rating < 5.0)).sum(),
                    ((rating >= 3.0) & (rating < 4.0)).sum(),
                    (rating < 3.0).sum()
                ]
            })
            sheets["Rating Distribution"] = rating_dist

        return sheets