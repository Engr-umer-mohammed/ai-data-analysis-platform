# customization/domains/social_media.py
# Social Media Domain — Platform Standards & Benchmarks

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


class SocialMediaDomain(BaseDomain):
    """
    Social Media-specific analysis based on platform standards.
    Covers: Engagement, Reach, Followers, Impressions, Conversion.
    """

    DOMAIN_NAME = "social_media"

    DOMAIN_KEYWORDS = [
        "post", "like", "share", "comment", "view",
        "follower", "reach", "impression", "engagement",
        "click", "ctr", "conversion", "retention",
        "reel", "story", "tweet", "video", "image",
        "influencer", "campaign", "ad", "spend", "roas",
        "page", "profile", "channel", "platform", "social"
    ]

    ENGAGEMENT_KEYWORDS = ["engagement", "interaction", "like", "share", "comment", "reaction"]
    REACH_KEYWORDS = ["reach", "impression", "view", "exposure"]
    FOLLOWER_KEYWORDS = ["follower", "subscriber", "fan", "audience"]
    POST_KEYWORDS = ["post", "content", "tweet", "reel", "story"]
    CLICK_KEYWORDS = ["click", "ctr", "link", "tap", "swipe"]
    CONVERSION_KEYWORDS = ["conversion", "purchase", "signup", "lead", "download"]
    SPEND_KEYWORDS = ["spend", "cost", "budget", "ad_cost", "cpm", "cpc"]

    # Social Media Benchmarks 2024
    BENCHMARK_ENGAGEMENT_RATE = 3.5       # % (average across platforms)
    BENCHMARK_CTR = 2.0                   # % (average)
    BENCHMARK_CONVERSION_RATE = 3.0       # % (e-commerce average)
    BENCHMARK_CPC = 1.0                   # USD (average)
    BENCHMARK_IMPRESSIONS_PER_POST = 1000 # average

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load social media thresholds from config."""
        self.benchmark_engagement = config.get_threshold(
            'social_media', 'engagement_benchmark', self.client_name
        ) or self.BENCHMARK_ENGAGEMENT_RATE

        self.benchmark_ctr = config.get_threshold(
            'social_media', 'ctr_benchmark', self.client_name
        ) or self.BENCHMARK_CTR

        self.benchmark_conversion = config.get_threshold(
            'social_media', 'conversion_benchmark', self.client_name
        ) or self.BENCHMARK_CONVERSION_RATE

        self.benchmark_cpc = config.get_threshold(
            'social_media', 'cpc_benchmark', self.client_name
        ) or self.BENCHMARK_CPC

    def detect(self) -> bool:
        """Detect if this is social media data."""
        all_cols_text = " ".join(self._get_all_columns()).lower()
        return any(k in all_cols_text for k in self.DOMAIN_KEYWORDS)

    def get_section_header(self) -> str:
        return "SOCIAL MEDIA DOMAIN ANALYSIS — PLATFORM STANDARDS"

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
        """Generate social media-specific content for the text report."""

        engagement_col = self._detect_column(self.ENGAGEMENT_KEYWORDS)
        reach_col = self._detect_column(self.REACH_KEYWORDS)
        follower_col = self._detect_column(self.FOLLOWER_KEYWORDS)
        post_col = self._detect_column(self.POST_KEYWORDS)
        click_col = self._detect_column(self.CLICK_KEYWORDS)
        conversion_col = self._detect_column(self.CONVERSION_KEYWORDS)
        spend_col = self._detect_column(self.SPEND_KEYWORDS)

        total = len(self.df)
        lines = [
            "",
            "  SOCIAL MEDIA ANALYTICS (Platform Standards)",
            "  " + "-" * 45,
        ]

        # ─── CONFIGURATION SUMMARY ──────────────────────────────
        lines += [
            "",
            "  CONFIGURATION SUMMARY",
            "  " + "-" * 35,
            f"    Client             : {self.client_name or 'Default'}",
            f"    Engagement Benchmark: {self.benchmark_engagement}%",
            f"    CTR Benchmark       : {self.benchmark_ctr}%",
            f"    Conversion Benchmark: {self.benchmark_conversion}%",
            f"    CPC Benchmark       : ${self.benchmark_cpc}",
        ]

        # ─── ENGAGEMENT ANALYSIS ──────────────────────────────────
        if engagement_col:
            engagement = self._safe_numeric(engagement_col)
            avg_engagement = engagement.mean()
            status = "✅" if avg_engagement >= self.benchmark_engagement else "⚠️"
            lines += ["", "  ENGAGEMENT ANALYSIS", "  " + "-" * 35]
            lines.append(
                f"    {status} Avg engagement rate : {self._fmt(avg_engagement)}% "
                f"(benchmark: {self.benchmark_engagement}%)"
            )
            lines.append(f"    Max engagement       : {self._fmt(engagement.max())}%")
            lines.append(f"    Min engagement       : {self._fmt(engagement.min())}%")
            if avg_engagement < 1.0:
                lines.append("    ⚠️  Very low engagement (<1%)")

        # ─── REACH ANALYSIS ────────────────────────────────────────
        if reach_col:
            reach = self._safe_numeric(reach_col)
            lines += ["", "  REACH & IMPRESSIONS", "  " + "-" * 35]
            lines.append(f"    Total reach          : {self._fmt(reach.sum(), 0)}")
            lines.append(f"    Average reach        : {self._fmt(reach.mean())}")
            lines.append(f"    Max reach per post   : {self._fmt(reach.max())}")

        # ─── FOLLOWER ANALYSIS ────────────────────────────────────
        if follower_col:
            followers = self._safe_numeric(follower_col)
            avg_followers = followers.mean()
            lines += ["", "  FOLLOWER / AUDIENCE ANALYSIS", "  " + "-" * 35]
            lines.append(f"    Total followers      : {self._fmt(followers.sum(), 0)}")
            lines.append(f"    Average followers    : {self._fmt(avg_followers)}")
            lines.append(f"    Follower growth      : {self._fmt(followers.max() - followers.min())}")

        # ─── CONTENT PERFORMANCE ──────────────────────────────────
        if post_col:
            post_dist = self.df[post_col].value_counts()
            lines += ["", "  CONTENT PERFORMANCE", "  " + "-" * 35]
            # Most frequent content types
            top_posts = post_dist.head(5)
            for content_type, count in top_posts.items():
                pct = count / total * 100
                bar = "█" * int(pct / 2)
                lines.append(
                    f"    {str(content_type)[:25]:<25}: "
                    f"{count} ({self._fmt(pct)}%) {bar}"
                )

        # ─── CLICK-THROUGH RATE (CTR) ──────────────────────────────
        if click_col and reach_col:
            clicks = self._safe_numeric(click_col)
            reach = self._safe_numeric(reach_col)
            ctr = (clicks.sum() / reach.sum() * 100) if reach.sum() > 0 else 0
            status = "✅" if ctr >= self.benchmark_ctr else "⚠️"
            lines += ["", "  CLICK-THROUGH RATE (CTR)", "  " + "-" * 35]
            lines.append(
                f"    {status} Average CTR          : {self._fmt(ctr)}% "
                f"(benchmark: {self.benchmark_ctr}%)"
            )
            lines.append(f"    Total clicks         : {self._fmt(clicks.sum(), 0)}")
            if ctr < 1.0:
                lines.append("    ⚠️  Low CTR (<1%)")

        # ─── CONVERSION ANALYSIS ────────────────────────────────────
        if conversion_col and click_col:
            conversions = self._safe_numeric(conversion_col)
            clicks = self._safe_numeric(click_col)
            conv_rate = (conversions.sum() / clicks.sum() * 100) if clicks.sum() > 0 else 0
            status = "✅" if conv_rate >= self.benchmark_conversion else "⚠️"
            lines += ["", "  CONVERSION ANALYSIS", "  " + "-" * 35]
            lines.append(
                f"    {status} Conversion rate     : {self._fmt(conv_rate)}% "
                f"(benchmark: {self.benchmark_conversion}%)"
            )
            lines.append(f"    Total conversions   : {self._fmt(conversions.sum(), 0)}")

        # ─── SPEND / ROAS ANALYSIS ─────────────────────────────────
        if spend_col:
            spend = self._safe_numeric(spend_col)
            avg_spend = spend.mean()
            lines += ["", "  AD SPEND ANALYSIS", "  " + "-" * 35]
            lines.append(f"    Total spend          : ${self._fmt(spend.sum())}")
            lines.append(f"    Average spend        : ${self._fmt(avg_spend)}")
            lines.append(f"    CPC average          : ${self._fmt(avg_spend)} (benchmark: ${self.benchmark_cpc})")

            # ROAS if revenue data available
            revenue_col = self._detect_column(["revenue", "sales", "roi"])
            if revenue_col:
                revenue = self._safe_numeric(revenue_col)
                roas = revenue.sum() / spend.sum() if spend.sum() > 0 else 0
                lines.append(f"    ROAS (Return on Ad)  : {self._fmt(roas)}x")

        # ─── PLATFORM BENCHMARKS ────────────────────────────────────
        lines += ["", "  PLATFORM BENCHMARKS (2024)", "  " + "-" * 35]
        lines.append(f"    Avg Engagement Rate  : {self.benchmark_engagement}%")
        lines.append(f"    Avg CTR               : {self.benchmark_ctr}%")
        lines.append(f"    Avg Conversion Rate   : {self.benchmark_conversion}%")
        lines.append(f"    Avg CPC               : ${self.benchmark_cpc}")

        return "\n".join(lines)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return social media-specific Excel sheets."""
        sheets = {}
        post_col = self._detect_column(self.POST_KEYWORDS)
        engagement_col = self._detect_column(self.ENGAGEMENT_KEYWORDS)
        reach_col = self._detect_column(self.REACH_KEYWORDS)
        click_col = self._detect_column(self.CLICK_KEYWORDS)
        conversion_col = self._detect_column(self.CONVERSION_KEYWORDS)
        follower_col = self._detect_column(self.FOLLOWER_KEYWORDS)
        spend_col = self._detect_column(self.SPEND_KEYWORDS)

        # ─── Post Performance ──────────────────────────────────────
        if post_col and engagement_col:
            post_summary = self.df.groupby(post_col)[engagement_col].agg(
                ["mean", "max", "min", "count"]
            ).reset_index()
            post_summary.columns = ["Content Type", "Avg Engagement", "Max Engagement", "Min Engagement", "Count"]
            post_summary = post_summary.sort_values("Avg Engagement", ascending=False)
            sheets["Post Performance"] = post_summary

        # ─── Engagement Summary ───────────────────────────────────
        if engagement_col:
            engagement = self._safe_numeric(engagement_col)
            eng_summary = pd.DataFrame({
                "Metric": ["Average Engagement Rate", "Max Engagement Rate", "Min Engagement Rate", "Median"],
                "Value": [
                    engagement.mean(),
                    engagement.max(),
                    engagement.min(),
                    engagement.median()
                ]
            })
            sheets["Engagement Summary"] = eng_summary

        # ─── Follower Growth ──────────────────────────────────────
        if follower_col:
            followers = self._safe_numeric(follower_col)
            if len(followers) > 1:
                follower_df = pd.DataFrame({
                    "Period": range(1, len(followers) + 1),
                    "Followers": followers.values,
                    "Growth": followers.diff().fillna(0).values
                })
                sheets["Follower Growth"] = follower_df

        # ─── ROI / Spend Summary ──────────────────────────────────
        if spend_col:
            spend = self._safe_numeric(spend_col)
            revenue_col = self._detect_column(["revenue", "sales", "roi"])
            if revenue_col:
                revenue = self._safe_numeric(revenue_col)
                roi_data = {
                    "Metric": ["Total Spend", "Total Revenue", "ROAS (Revenue/Spend)", "ROI %"],
                    "Value": [
                        spend.sum(),
                        revenue.sum(),
                        revenue.sum() / spend.sum() if spend.sum() > 0 else 0,
                        ((revenue.sum() - spend.sum()) / spend.sum() * 100) if spend.sum() > 0 else 0
                    ]
                }
                sheets["ROI Summary"] = pd.DataFrame(roi_data)

        return sheets