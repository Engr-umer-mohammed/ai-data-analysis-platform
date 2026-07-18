# customization/domains/marketing.py
# Marketing Domain — Aligned with base domain structure
# Standards: Google/Meta/HubSpot benchmarks 2024

import pandas as pd
from customization.base_domain import BaseDomain


class MarketingDomain(BaseDomain):
    """
    Marketing domain analysis.
    Detects campaign, channel, and ROI data.
    Aligned with BaseDomain structure so the
    registry confidence scoring works correctly.
    """

    DOMAIN_NAME = "marketing"

    # These are the ONLY keywords used for detection.
    # Keep them specific to marketing only.
    # Do NOT use words that appear in other domains.
    DOMAIN_KEYWORDS = [
        "campaign", "impression", "click",
        "ctr", "cpc", "cpa", "roas",
        "ad_spend", "advertisement", "advertis",
        "channel_source", "acquisition_cost",
        "conversion_rate", "click_through",
        "bounce_rate", "engagement_rate",
        "lead_generation", "funnel",
        "retargeting", "sem", "ppc"
    ]

    # Default thresholds — international benchmarks
    DEFAULT_CONVERSION_TARGET = 0.05
    DEFAULT_ROI_TARGET        = 3.0
    DEFAULT_CPA_BENCHMARK     = 50
    DEFAULT_CTR_BENCHMARK     = 0.02
    DEFAULT_ROAS_TARGET       = 4.0

    # Industry benchmarks (Google/Meta 2024)
    BENCHMARK_CTR_SEARCH   = 6.64
    BENCHMARK_CTR_DISPLAY  = 0.46
    BENCHMARK_CONV_RATE    = 3.75
    BENCHMARK_CPC          = 2.69
    BENCHMARK_ROAS         = 200

    def get_section_header(self) -> str:
        return "MARKETING DOMAIN ANALYSIS — GOOGLE/HUBSPOT STANDARDS"

    def generate_content(self) -> str:
        spend_col      = self._detect_column(
            ["spend", "budget", "cost", "ad_spend", "investment"]
        )
        impression_col = self._detect_column(
            ["impression", "reach", "view"]
        )
        click_col      = self._detect_column(
            ["click", "ctr", "interaction"]
        )
        conv_col       = self._detect_column(
            ["conversion", "convert", "lead", "signup"]
        )
        channel_col    = self._detect_column(
            ["channel", "source", "medium", "platform"]
        )
        revenue_col    = self._detect_column(
            ["revenue", "sales", "return", "roas"]
        )
        campaign_col   = self._detect_column(
            ["campaign", "ad_name", "creative"]
        )

        total = len(self.df)
        lines = [
            "MARKETING PERFORMANCE ANALYSIS",
            f"  Total records        : {total:,}",
        ]

        if impression_col and click_col:
            impressions = self._safe_numeric(impression_col)
            clicks      = self._safe_numeric(click_col)
            ctr = (
                clicks.sum() / impressions.sum() * 100
                if impressions.sum() > 0 else 0
            )
            lines += [
                "",
                "REACH AND ENGAGEMENT",
                f"  Total impressions    : "
                f"{self._fmt(impressions.sum(), 0)}",
                f"  Total clicks         : "
                f"{self._fmt(clicks.sum(), 0)}",
                f"  Overall CTR          : "
                f"{self._fmt(ctr)}%",
                f"  Search CTR benchmark : "
                f"{self.BENCHMARK_CTR_SEARCH}%",
                f"  Display CTR benchmark: "
                f"{self.BENCHMARK_CTR_DISPLAY}%",
            ]

        if spend_col:
            spend = self._safe_numeric(spend_col)
            lines += [
                "",
                "SPEND ANALYSIS",
                f"  Total spend          : "
                f"{self._fmt(spend.sum())}",
                f"  Average per campaign : "
                f"{self._fmt(spend.mean())}",
            ]

            if click_col:
                clicks = self._safe_numeric(click_col)
                cpc    = (
                    spend.sum() / clicks.sum()
                    if clicks.sum() > 0 else 0
                )
                lines.append(
                    f"  Cost per click (CPC) : "
                    f"{self._fmt(cpc)} "
                    f"(benchmark: ${self.BENCHMARK_CPC})"
                )

            if conv_col:
                conv = self._safe_numeric(conv_col)
                cpa  = (
                    spend.sum() / conv.sum()
                    if conv.sum() > 0 else 0
                )
                lines.append(
                    f"  Cost per acquisition : "
                    f"{self._fmt(cpa)}"
                )

            if revenue_col:
                revenue = self._safe_numeric(revenue_col)
                roas    = (
                    revenue.sum() / spend.sum() * 100
                    if spend.sum() > 0 else 0
                )
                lines += [
                    "",
                    "RETURN ON AD SPEND (ROAS)",
                    f"  Total revenue        : "
                    f"{self._fmt(revenue.sum())}",
                    f"  ROAS                 : "
                    f"{self._fmt(roas)}%",
                    f"  ROAS benchmark       : "
                    f"{self.BENCHMARK_ROAS}%",
                    f"  ROI                  : "
                    f"{self._fmt(roas - 100)}%",
                ]

        if conv_col and click_col:
            conv   = self._safe_numeric(conv_col)
            clicks = self._safe_numeric(click_col)
            conv_rate = (
                conv.sum() / clicks.sum() * 100
                if clicks.sum() > 0 else 0
            )
            lines += [
                "",
                "CONVERSION ANALYSIS",
                f"  Total conversions    : "
                f"{self._fmt(conv.sum(), 0)}",
                f"  Conversion rate      : "
                f"{self._fmt(conv_rate)}%",
                f"  Industry benchmark   : "
                f"{self.BENCHMARK_CONV_RATE}%",
            ]

        if channel_col and spend_col:
            channel_spend = self.df.groupby(
                channel_col
            )[spend_col].sum().sort_values(
                ascending=False
            )
            lines += ["", "SPEND BY CHANNEL"]
            total_spend = channel_spend.sum()
            for channel, spend in channel_spend.items():
                pct = spend / total_spend * 100
                lines.append(
                    f"  {str(channel):<20}: "
                    f"{self._fmt(spend)} "
                    f"({self._fmt(pct)}%)"
                )

        if campaign_col and revenue_col and spend_col:
            camp_data = self.df.groupby(campaign_col).agg(
                {spend_col: "sum", revenue_col: "sum"}
            )
            camp_data["ROI"] = (
                (camp_data[revenue_col] - camp_data[spend_col])
                / camp_data[spend_col]
            ).round(2)
            camp_data = camp_data.sort_values(
                "ROI", ascending=False
            )
            lines += ["", "TOP CAMPAIGNS BY ROI"]
            for i, (camp, row) in enumerate(
                camp_data.head(10).iterrows(), 1
            ):
                lines.append(
                    f"  {i:>2}. {str(camp)[:20]:<20}: "
                    f"ROI={self._fmt(row['ROI'])}x | "
                    f"Spend={self._fmt(row[spend_col])} | "
                    f"Rev={self._fmt(row[revenue_col])}"
                )

        return "\n".join(lines)

    def get_excel_sheets(self) -> dict:
        sheets      = {}
        channel_col = self._detect_column(
            ["channel", "source", "medium", "platform"]
        )
        spend_col   = self._detect_column(
            ["spend", "budget", "cost", "ad_spend"]
        )
        conv_col    = self._detect_column(
            ["conversion", "convert", "lead"]
        )

        if channel_col:
            agg_dict = {}
            if spend_col:
                agg_dict["Total Spend"] = (spend_col, "sum")
            if conv_col:
                agg_dict["Total Conv"]  = (conv_col, "sum")
            if agg_dict:
                ch_summary = self.df.groupby(
                    channel_col
                ).agg(**agg_dict).reset_index()
                sheets["Channel Analysis"] = ch_summary

        return sheets