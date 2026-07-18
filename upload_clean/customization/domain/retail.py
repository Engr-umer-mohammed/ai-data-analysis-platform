# customization/domains/retail.py
# Retail Domain — NRF / Retail Industry Standards

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


class RetailDomain(BaseDomain):
    """
    Retail-specific analysis based on NRF and retail industry standards.
    Covers: Sales, Inventory, Foot Traffic, Basket Size, Store Performance.
    """

    DOMAIN_NAME = "retail"

    DOMAIN_KEYWORDS = [
        "store", "sku", "sales", "inventory", "stock",
        "footfall", "traffic", "basket", "transaction",
        "conversion", "shrink", "markdown", "promotion",
        "foot_traffic", "sales_per_sqft", "turnover",
        "category", "aisle", "associate", "cashier",
        "coupon", "loyalty", "omnichannel", "fulfillment"
    ]

    SALES_KEYWORDS = ["sales", "revenue", "turnover", "gmv", "transaction"]
    INVENTORY_KEYWORDS = ["inventory", "stock", "units", "quantity", "turnover"]
    CUSTOMER_KEYWORDS = ["customer", "shopper", "visitor", "footfall", "traffic"]
    PRODUCT_KEYWORDS = ["product", "sku", "item", "category"]
    STORE_KEYWORDS = ["store", "location", "branch", "outlet"]
    PROMOTION_KEYWORDS = ["promotion", "discount", "coupon", "markdown"]

    # NRF / Retail Benchmarks 2024
    BENCHMARK_SALES_PER_SQFT = 400.0     # USD (average)
    BENCHMARK_INVENTORY_TURNOVER = 6.0   # annual turns
    BENCHMARK_SHRINK_RATE = 1.5          # % (average)
    BENCHMARK_CUSTOMER_RETENTION = 65.0  # % (average)
    BENCHMARK_CONVERSION_RATE = 25.0     # % (foot traffic to sales)

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load retail thresholds from config."""
        self.benchmark_sales_per_sqft = config.get_threshold(
            'retail', 'sales_per_sqft_benchmark', self.client_name
        ) or self.BENCHMARK_SALES_PER_SQFT

        self.benchmark_inventory_turnover = config.get_threshold(
            'retail', 'inventory_turnover_benchmark', self.client_name
        ) or self.BENCHMARK_INVENTORY_TURNOVER

        self.benchmark_shrink_rate = config.get_threshold(
            'retail', 'shrink_rate_benchmark', self.client_name
        ) or self.BENCHMARK_SHRINK_RATE

        self.benchmark_customer_retention = config.get_threshold(
            'retail', 'customer_retention_benchmark', self.client_name
        ) or self.BENCHMARK_CUSTOMER_RETENTION

        self.benchmark_conversion = config.get_threshold(
            'retail', 'conversion_benchmark', self.client_name
        ) or self.BENCHMARK_CONVERSION_RATE

    def detect(self) -> bool:
        """Detect if this is retail data."""
        all_cols_text = " ".join(self._get_all_columns()).lower()
        return any(k in all_cols_text for k in self.DOMAIN_KEYWORDS)

    def get_section_header(self) -> str:
        return "RETAIL DOMAIN ANALYSIS — NRF / INDUSTRY STANDARDS"

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
        """Generate retail-specific content for the text report."""

        sales_col = self._detect_column(self.SALES_KEYWORDS)
        inventory_col = self._detect_column(self.INVENTORY_KEYWORDS)
        customer_col = self._detect_column(self.CUSTOMER_KEYWORDS)
        product_col = self._detect_column(self.PRODUCT_KEYWORDS)
        store_col = self._detect_column(self.STORE_KEYWORDS)
        promotion_col = self._detect_column(self.PROMOTION_KEYWORDS)

        total = len(self.df)
        lines = [
            "",
            "  RETAIL ANALYTICS (NRF / Industry Standards)",
            "  " + "-" * 45,
        ]

        # ─── CONFIGURATION SUMMARY ──────────────────────────────
        lines += [
            "",
            "  CONFIGURATION SUMMARY",
            "  " + "-" * 35,
            f"    Client                : {self.client_name or 'Default'}",
            f"    Sales/sq ft Benchmark : ${self.benchmark_sales_per_sqft}",
            f"    Inventory Turnover    : {self.benchmark_inventory_turnover}x",
            f"    Shrink Rate Benchmark : {self.benchmark_shrink_rate}%",
            f"    Retention Benchmark   : {self.benchmark_customer_retention}%",
            f"    Conversion Benchmark  : {self.benchmark_conversion}%",
        ]

        # ─── SALES PERFORMANCE ──────────────────────────────────
        if sales_col:
            sales = self._safe_numeric(sales_col)
            total_sales = sales.sum()
            avg_sales = sales.mean()
            lines += ["", "  SALES PERFORMANCE", "  " + "-" * 35]
            lines.append(f"    Total sales          : ${self._fmt(total_sales)}")
            lines.append(f"    Average sale         : ${self._fmt(avg_sales)}")
            lines.append(f"    Highest sale         : ${self._fmt(sales.max())}")
            lines.append(f"    Lowest sale          : ${self._fmt(sales.min())}")

            # Sales per sq ft if store area column exists
            area_col = self._detect_column(["area", "sqft", "size", "square_footage"])
            if area_col and store_col:
                area = self._safe_numeric(area_col)
                sales_per_sqft = sales.sum() / area.sum() if area.sum() > 0 else 0
                status = "✅" if sales_per_sqft >= self.benchmark_sales_per_sqft else "⚠️"
                lines.append(
                    f"    {status} Sales per sq ft     : ${self._fmt(sales_per_sqft)} "
                    f"(benchmark: ${self.benchmark_sales_per_sqft})"
                )

        # ─── INVENTORY ANALYSIS ──────────────────────────────────
        if inventory_col:
            inventory = self._safe_numeric(inventory_col)
            avg_inventory = inventory.mean()
            lines += ["", "  INVENTORY ANALYSIS", "  " + "-" * 35]
            lines.append(f"    Total inventory      : {self._fmt(inventory.sum())} units")
            lines.append(f"    Average inventory    : {self._fmt(avg_inventory)} units")
            lines.append(f"    Max inventory        : {self._fmt(inventory.max())} units")

            # Inventory Turnover if sales/COGS available
            if sales_col:
                sales = self._safe_numeric(sales_col)
                turnover = sales.sum() / inventory.mean() if inventory.mean() > 0 else 0
                status = "✅" if turnover >= self.benchmark_inventory_turnover else "⚠️"
                lines.append(
                    f"    {status} Inventory turnover  : {self._fmt(turnover)}x "
                    f"(benchmark: {self.benchmark_inventory_turnover}x)"
                )

        # ─── CUSTOMER / FOOT TRAFFIC ─────────────────────────────
        if customer_col:
            customers = self._safe_numeric(customer_col)
            total_customers = customers.sum()
            avg_customers = customers.mean()
            lines += ["", "  CUSTOMER & FOOT TRAFFIC", "  " + "-" * 35]
            lines.append(f"    Total customers      : {self._fmt(total_customers, 0)}")
            lines.append(f"    Average customers    : {self._fmt(avg_customers)}")
            lines.append(f"    Peak traffic         : {self._fmt(customers.max())}")

            # Conversion Rate
            if sales_col and customer_col:
                transactions = self._detect_column(["transaction", "ticket", "order"])
                if transactions:
                    tx = self._safe_numeric(transactions)
                    conv_rate = (tx.sum() / customers.sum() * 100) if customers.sum() > 0 else 0
                    status = "✅" if conv_rate >= self.benchmark_conversion else "⚠️"
                    lines.append(
                        f"    {status} Conversion rate     : {self._fmt(conv_rate)}% "
                        f"(benchmark: {self.benchmark_conversion}%)"
                    )

        # ─── SHRINK / LOSS ──────────────────────────────────────
        shrink_col = self._detect_column(["shrink", "loss", "damage", "theft"])
        if shrink_col:
            shrink = self._safe_numeric(shrink_col)
            shrink_rate = (shrink.sum() / sales.sum() * 100) if sales_col and sales.sum() > 0 else 0
            status = "✅" if shrink_rate <= self.benchmark_shrink_rate else "⚠️"
            lines += ["", "  SHRINK & LOSS ANALYSIS", "  " + "-" * 35]
            lines.append(
                f"    {status} Shrink rate          : {self._fmt(shrink_rate)}% "
                f"(benchmark: {self.benchmark_shrink_rate}%)"
            )
            lines.append(f"    Total shrink loss    : ${self._fmt(shrink.sum())}")

        # ─── PRODUCT CATEGORY PERFORMANCE ──────────────────────
        if product_col and sales_col:
            prod_sales = self.df.groupby(product_col)[sales_col].agg(
                ["sum", "mean", "count"]
            ).sort_values("sum", ascending=False)
            lines += ["", "  PRODUCT CATEGORY PERFORMANCE", "  " + "-" * 35]
            for i, (prod, row) in enumerate(prod_sales.head(10).items(), 1):
                pct = row["sum"] / sales.sum() * 100 if sales.sum() > 0 else 0
                bar = "█" * int(pct / 2)
                lines.append(
                    f"    {i:>2}. {str(prod)[:25]:<25}: "
                    f"${self._fmt(row['sum'])} ({self._fmt(pct)}%) {bar}"
                )

        # ─── STORE PERFORMANCE ──────────────────────────────────
        if store_col and sales_col:
            store_perf = self.df.groupby(store_col)[sales_col].agg(
                ["sum", "mean", "count"]
            ).sort_values("sum", ascending=False)
            lines += ["", "  STORE PERFORMANCE", "  " + "-" * 35]
            for store, row in store_perf.head(10).items():
                lines.append(
                    f"    {str(store)[:20]:<20}: "
                    f"${self._fmt(row['sum'])} (avg ${self._fmt(row['mean'])})"
                )

        # ─── PROMOTION EFFECTIVENESS ────────────────────────────
        if promotion_col and sales_col:
            promo_impact = self.df.groupby(promotion_col)[sales_col].agg(
                ["mean", "count", "sum"]
            ).sort_values("mean", ascending=False)
            lines += ["", "  PROMOTION EFFECTIVENESS", "  " + "-" * 35]
            for promo, row in promo_impact.head(5).items():
                lines.append(
                    f"    {str(promo)[:20]:<20}: "
                    f"avg ${self._fmt(row['mean'])} ({row['count']} transactions)"
                )

        # ─── RETAIL BENCHMARKS ──────────────────────────────────
        lines += ["", "  RETAIL BENCHMARKS (NRF 2024)", "  " + "-" * 35]
        lines.append(f"    Sales per sq ft      : ${self.benchmark_sales_per_sqft}")
        lines.append(f"    Inventory Turnover   : {self.benchmark_inventory_turnover}x")
        lines.append(f"    Shrink Rate          : {self.benchmark_shrink_rate}%")
        lines.append(f"    Customer Retention   : {self.benchmark_customer_retention}%")
        lines.append(f"    Conversion Rate      : {self.benchmark_conversion}%")

        return "\n".join(lines)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return retail-specific Excel sheets."""
        sheets = {}
        store_col = self._detect_column(self.STORE_KEYWORDS)
        product_col = self._detect_column(self.PRODUCT_KEYWORDS)
        sales_col = self._detect_column(self.SALES_KEYWORDS)
        inventory_col = self._detect_column(self.INVENTORY_KEYWORDS)
        customer_col = self._detect_column(self.CUSTOMER_KEYWORDS)

        # ─── Store Performance ────────────────────────────────────
        if store_col and sales_col:
            store_summary = self.df.groupby(store_col)[sales_col].agg(
                ["sum", "mean", "count"]
            ).reset_index()
            store_summary.columns = ["Store", "Total Sales", "Avg Sale", "Transactions"]
            store_summary = store_summary.sort_values("Total Sales", ascending=False)
            sheets["Store Performance"] = store_summary

        # ─── Product Performance ──────────────────────────────────
        if product_col and sales_col:
            prod_summary = self.df.groupby(product_col)[sales_col].agg(
                ["sum", "mean", "count"]
            ).reset_index()
            prod_summary.columns = ["Product", "Revenue", "Avg Sale", "Units Sold"]
            prod_summary = prod_summary.sort_values("Revenue", ascending=False)
            sheets["Product Performance"] = prod_summary

        # ─── Inventory Status ─────────────────────────────────────
        if inventory_col:
            inv = self._safe_numeric(inventory_col)
            inv_summary = pd.DataFrame({
                "Metric": ["Total Inventory", "Average Inventory", "Max Inventory", "Min Inventory"],
                "Value": [
                    inv.sum(),
                    inv.mean(),
                    inv.max(),
                    inv.min()
                ]
            })
            sheets["Inventory Status"] = inv_summary

        # ─── Customer Traffic ──────────────────────────────────────
        if customer_col:
            cust = self._safe_numeric(customer_col)
            cust_summary = pd.DataFrame({
                "Metric": ["Total Customers", "Average Daily Traffic", "Peak Traffic"],
                "Value": [
                    cust.sum(),
                    cust.mean(),
                    cust.max()
                ]
            })
            sheets["Customer Traffic"] = cust_summary

        return sheets