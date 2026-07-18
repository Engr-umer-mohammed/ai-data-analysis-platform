# customization/domains/ecommerce.py
# E-Commerce Domain — Shopify / Baymard Standards

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


class EcommerceDomain(BaseDomain):
    """
    E-Commerce-specific analysis based on Shopify/Baymard standards.
    Covers: Revenue, AOV, Customer Value, Returns, Ratings.
    """

    DOMAIN_NAME = "ecommerce"

    DOMAIN_KEYWORDS = [
        "cart", "checkout", "order", "product", "sku",
        "customer", "session", "conversion", "abandon",
        "aov", "ltv", "clv", "gmv", "return",
        "refund", "shipping", "fulfillment", "review",
        "rating", "wishlist", "coupon", "discount",
        "upsell", "cross_sell", "category", "search"
    ]

    ORDER_KEYWORDS = ["order", "purchase", "transaction", "gmv"]
    REVENUE_KEYWORDS = ["revenue", "sales", "amount", "value"]
    PRODUCT_KEYWORDS = ["product", "sku", "item", "category"]
    CUSTOMER_KEYWORDS = ["customer", "user", "buyer", "client"]
    CART_KEYWORDS = ["cart", "basket", "checkout"]
    RETURN_KEYWORDS = ["return", "refund", "chargeback"]
    RATING_KEYWORDS = ["rating", "review", "score", "star"]
    SHIPPING_KEYWORDS = ["shipping", "delivery", "fulfillment"]

    # Shopify / Baymard Benchmarks 2024
    BENCHMARK_CART_ABANDON = 70.19   # % average
    BENCHMARK_CONV_RATE = 2.5        # % average
    BENCHMARK_AOV = 150              # USD average
    BENCHMARK_RETURN_RATE = 20.0     # % average

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load e-commerce thresholds from config."""
        self.benchmark_cart_abandon = config.get_threshold(
            'ecommerce', 'cart_abandon_benchmark', self.client_name
        ) or self.BENCHMARK_CART_ABANDON

        self.benchmark_conv_rate = config.get_threshold(
            'ecommerce', 'conv_rate_benchmark', self.client_name
        ) or self.BENCHMARK_CONV_RATE

        self.benchmark_aov = config.get_threshold(
            'ecommerce', 'aov_benchmark', self.client_name
        ) or self.BENCHMARK_AOV

        self.benchmark_return_rate = config.get_threshold(
            'ecommerce', 'return_rate_benchmark', self.client_name
        ) or self.BENCHMARK_RETURN_RATE

    def detect(self) -> bool:
        """Detect if this is e-commerce data."""
        all_cols_text = " ".join(self._get_all_columns()).lower()
        return any(k in all_cols_text for k in self.DOMAIN_KEYWORDS)

    def get_section_header(self) -> str:
        return "E-COMMERCE DOMAIN ANALYSIS — SHOPIFY / BAYMARD STANDARDS"

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
        """Generate e-commerce-specific content for the text report."""

        order_col = self._detect_column(self.ORDER_KEYWORDS)
        revenue_col = self._detect_column(self.REVENUE_KEYWORDS)
        product_col = self._detect_column(self.PRODUCT_KEYWORDS)
        customer_col = self._detect_column(self.CUSTOMER_KEYWORDS)
        return_col = self._detect_column(self.RETURN_KEYWORDS)
        rating_col = self._detect_column(self.RATING_KEYWORDS)

        total = len(self.df)
        lines = [
            "",
            "  E-COMMERCE ANALYTICS (Shopify/Baymard Standards)",
            "  " + "-" * 45,
        ]

        # ─── CONFIGURATION SUMMARY ──────────────────────────────
        lines += [
            "",
            "  CONFIGURATION SUMMARY",
            "  " + "-" * 35,
            f"    Client             : {self.client_name or 'Default'}",
            f"    Cart Abandon Benchmark: {self.benchmark_cart_abandon}%",
            f"    Conv Rate Benchmark : {self.benchmark_conv_rate}%",
            f"    AOV Benchmark       : ${self.benchmark_aov}",
            f"    Return Rate Benchmark: {self.benchmark_return_rate}%",
        ]

        # ─── REVENUE ANALYSIS ──────────────────────────────────
        if revenue_col:
            revenue = self._safe_numeric(revenue_col)
            aov = revenue.mean()
            status = "✅" if aov >= self.benchmark_aov else "⚠️"
            lines += ["", "  REVENUE ANALYSIS", "  " + "-" * 35]
            lines.append(f"    {status} Average order value : {self._fmt(aov)}")
            lines.append(f"       (benchmark: ${self.benchmark_aov})")
            lines.append(f"    Total revenue (GMV)  : {self._fmt(revenue.sum())}")
            lines.append(f"    Median order value   : {self._fmt(revenue.median())}")
            lines.append(f"    Highest order        : {self._fmt(revenue.max())}")

        # ─── TOP PRODUCTS ──────────────────────────────────────
        if product_col and revenue_col:
            prod_rev = self.df.groupby(product_col)[revenue_col].sum().sort_values(ascending=False)
            total_rev = prod_rev.sum()
            lines += ["", "  TOP PRODUCTS BY REVENUE", "  " + "-" * 35]
            for i, (prod, rev) in enumerate(prod_rev.head(10).items(), 1):
                pct = rev / total_rev * 100
                bar = "█" * int(pct / 2)
                lines.append(
                    f"    {i:>2}. {str(prod)[:20]:<20}: "
                    f"{self._fmt(rev)} ({self._fmt(pct)}%) {bar}"
                )

        # ─── CUSTOMER VALUE ────────────────────────────────────
        if customer_col and revenue_col:
            cust_rev = self.df.groupby(customer_col)[revenue_col].sum().sort_values(ascending=False)
            lines += ["", "  CUSTOMER VALUE ANALYSIS", "  " + "-" * 35]
            lines.append(f"    Unique customers     : {len(cust_rev):,}")
            lines.append(f"    Avg revenue/customer : {self._fmt(cust_rev.mean())}")
            lines.append(f"    Top customer revenue : {self._fmt(cust_rev.max())}")

            # Pareto — top 20% customers
            top_20 = max(1, int(len(cust_rev) * 0.20))
            top_20_rev = cust_rev.head(top_20).sum()
            pareto_pct = top_20_rev / cust_rev.sum() * 100
            lines.append(f"    Top 20% generate     : {self._fmt(pareto_pct)}% of revenue")

        # ─── RETURNS ANALYSIS ──────────────────────────────────
        if return_col:
            returns = self._safe_numeric(return_col)
            return_count = returns.sum()
            return_rate = (return_count / total * 100) if total > 0 else 0
            status = "✅" if return_rate <= self.benchmark_return_rate else "⚠️"
            lines += ["", "  RETURNS ANALYSIS", "  " + "-" * 35]
            lines.append(
                f"    {status} Return rate          : {self._fmt(return_rate)}% "
                f"(benchmark: {self.benchmark_return_rate}%)"
            )
            lines.append(f"    Total returns        : {self._fmt(return_count, 0)}")

        # ─── PRODUCT RATINGS ────────────────────────────────────
        if rating_col:
            rating = self._safe_numeric(rating_col)
            lines += ["", "  PRODUCT RATINGS", "  " + "-" * 35]
            lines.append(f"    Average rating       : {self._fmt(rating.mean())} / 5")
            lines.append(f"    5-star reviews       : {(rating >= 5).sum()}")
            lines.append(f"    4-star reviews       : {((rating >= 4) & (rating < 5)).sum()}")
            lines.append(f"    Low ratings (<3)     : {(rating < 3).sum()}")

        # ─── BENCHMARKS ─────────────────────────────────────────
        lines += ["", "  E-COMMERCE BENCHMARKS (Baymard 2024)", "  " + "-" * 35]
        lines.append(f"    Cart abandonment avg : {self.benchmark_cart_abandon}%")
        lines.append(f"    Conversion rate avg  : {self.benchmark_conv_rate}%")
        lines.append(f"    Average order value  : ${self.benchmark_aov}")
        lines.append(f"    Return rate avg      : {self.benchmark_return_rate}%")

        return "\n".join(lines)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return e-commerce-specific Excel sheets."""
        sheets = {}
        product_col = self._detect_column(self.PRODUCT_KEYWORDS)
        revenue_col = self._detect_column(self.REVENUE_KEYWORDS)
        customer_col = self._detect_column(self.CUSTOMER_KEYWORDS)

        # ─── Product Rankings ──────────────────────────────────
        if product_col and revenue_col:
            prod_summary = self.df.groupby(product_col)[revenue_col].agg(
                ["count", "sum", "mean"]
            ).reset_index()
            prod_summary.columns = ["Product", "Orders", "Revenue", "AOV"]
            prod_summary = prod_summary.sort_values("Revenue", ascending=False).reset_index(drop=True)
            prod_summary.index = prod_summary.index + 1
            prod_summary.index.name = "Rank"
            sheets["Product Rankings"] = prod_summary

        # ─── Customer Value ────────────────────────────────────
        if customer_col and revenue_col:
            cust_summary = self.df.groupby(customer_col)[revenue_col].agg(
                ["sum", "count", "mean"]
            ).reset_index()
            cust_summary.columns = ["Customer", "Total Revenue", "Orders", "AOV"]
            cust_summary = cust_summary.sort_values("Total Revenue", ascending=False)
            sheets["Customer Value"] = cust_summary

        # ─── Revenue Summary ────────────────────────────────────
        if revenue_col:
            revenue = self._safe_numeric(revenue_col)
            rev_summary = pd.DataFrame({
                "Metric": ["Total Revenue", "Average Order Value", "Median Order Value", "Highest Order", "Lowest Order"],
                "Value": [
                    revenue.sum(),
                    revenue.mean(),
                    revenue.median(),
                    revenue.max(),
                    revenue.min()
                ]
            })
            sheets["Revenue Summary"] = rev_summary

        return sheets