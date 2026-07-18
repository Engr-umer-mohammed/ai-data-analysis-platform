# statistical_analyzer.py
# Statistical Analysis Engine
# AI Data Analysis Agent — Version 1.1
# Changes from v1.0:
#   Defensive dtype validation before all calculations
#   Timestamp coercion error eliminated at source
#   Non-numeric column exclusion logged explicitly
#   Trend analysis protected against datetime values
#   Anomaly detection guarded per-column

import logging
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


class StatisticalAnalyzer:
    """
    Computes comprehensive statistical analysis
    across every genuinely numeric column in any
    dataset, regardless of domain or structure.

    The analyzer operates defensively — it verifies
    actual pandas dtypes at runtime rather than
    trusting the profile classification from the
    loader. This ensures that columns which were
    misclassified during profiling, or converted
    to datetime after classification, do not cause
    type coercion failures during computation.

    All analysis results are returned as a single
    structured dictionary that downstream components
    — the visualizer, the report generator, and the
    AI narrator — can access without any knowledge
    of how the calculations were performed.
    """

    # Correlation threshold above which a pair
    # is reported as a significant relationship.
    CORRELATION_THRESHOLD = 0.50

    # IQR multiplier for anomaly boundary calculation.
    # 1.5 is the standard Tukey fence. Higher values
    # produce fewer but more extreme anomaly detections.
    IQR_MULTIPLIER = 1.5

    # Minimum rows required for trend analysis.
    # Below this threshold trends are not meaningful.
    MIN_ROWS_FOR_TREND = 5

    def analyze(self, profile) -> dict:
        """
        Primary entry point. Accepts a DatasetProfile
        from the loader and returns a complete
        statistical results dictionary.

        The results dictionary contains these keys:
            descriptive  — per-column statistics
            anomalies    — outlier detection results
            correlations — significant pair relationships
            trends       — directional movement over time
            summary      — dataset-level aggregate metrics

        Every section is independently computed and
        independently guarded. A failure in one section
        does not prevent results from any other section.
        """

        df = profile.dataframe

        # RUNTIME DTYPE VALIDATION
        # This is the primary fix for the Timestamp error.
        # We verify actual dtypes rather than trusting the
        # profile classification unconditionally.
        numeric_cols = self._get_verified_numeric_cols(
            df, profile
        )

        logger.info(
            f"Statistical analysis starting: "
            f"{len(numeric_cols)} verified numeric columns "
            f"from {profile.total_columns} total"
        )

        results = {
            "descriptive":  {},
            "anomalies":    {},
            "correlations": [],
            "trends":       {},
            "summary":      {}
        }

        if not numeric_cols:
            logger.warning(
                "No verified numeric columns found. "
                "Statistical analysis will be empty."
            )
            results["summary"] = {
                "total_numeric_cols": 0,
                "analysis_note": (
                    "No numeric columns were available "
                    "for statistical analysis."
                )
            }
            return results

        # Run each analysis section independently
        results["descriptive"]  = self._compute_descriptive(
            df, numeric_cols
        )
        results["anomalies"]    = self._detect_anomalies(
            df, numeric_cols
        )
        results["correlations"] = self._compute_correlations(
            df, numeric_cols
        )
        results["trends"]       = self._compute_trends(
            df, numeric_cols, profile
        )
        results["summary"]      = self._compute_summary(
            df, numeric_cols, results
        )

        logger.info("Statistical analysis complete.")
        return results

    # RUNTIME DTYPE VALIDATION
    def _get_verified_numeric_cols(
        self, df: pd.DataFrame, profile
    ) -> list:
        """
        Verify that each column listed in
        profile.numeric_columns is genuinely numeric
        in the actual dataframe at analysis time.

        This resolves the Timestamp coercion error
        that occurs when datetime columns are converted
        after initial profiling but before analysis,
        leaving them listed in numeric_columns despite
        no longer containing numeric data.
        """

        verified = []
        excluded = []

        for col in profile.numeric_columns:
            if col not in df.columns:
                excluded.append(
                    f"{col} (not in dataframe)"
                )
                continue

            if pd.api.types.is_numeric_dtype(df[col]):
                verified.append(col)
            else:
                excluded.append(
                    f"{col} (actual dtype: {df[col].dtype})"
                )

        if excluded:
            logger.warning(
                f"Excluded from numeric analysis: "
                f"{excluded}"
            )

        return verified

    # DESCRIPTIVE STATISTICS

    def _compute_descriptive(
        self,
        df:           pd.DataFrame,
        numeric_cols: list
    ) -> dict:
        """
        Compute the full set of descriptive statistics
        for every verified numeric column. Each metric
        is rounded to four decimal places for report
        readability while preserving meaningful precision.
        """

        results = {}

        for col in numeric_cols:
            try:
                col_data = df[col].dropna()

                if len(col_data) == 0:
                    logger.warning(
                        f"Column '{col}' is entirely "
                        f"empty after dropping NaN. Skipped."
                    )
                    continue

                # Final dtype guard before any computation
                if not pd.api.types.is_numeric_dtype(col_data):
                    logger.warning(
                        f"Column '{col}' is not numeric "
                        f"at computation time. Skipped."
                    )
                    continue

                col_numeric = pd.to_numeric(
                    col_data, errors="coerce"
                ).dropna()

                if len(col_numeric) == 0:
                    continue

                q1  = float(col_numeric.quantile(0.25))
                q3  = float(col_numeric.quantile(0.75))
                iqr = q3 - q1

                try:
                    skewness = float(col_numeric.skew())
                except Exception:
                    skewness = 0.0

                try:
                    kurtosis = float(col_numeric.kurtosis())
                except Exception:
                    kurtosis = 0.0

                results[col] = {
                    "count":    int(len(col_numeric)),
                    "mean":     round(float(col_numeric.mean()),   4),
                    "median":   round(float(col_numeric.median()), 4),
                    "std":      round(float(col_numeric.std()),    4),
                    "variance": round(float(col_numeric.var()),    4),
                    "min":      round(float(col_numeric.min()),    4),
                    "max":      round(float(col_numeric.max()),    4),
                    "range":    round(float(col_numeric.max() - col_numeric.min()), 4),
                    "q1":       round(q1,       4),
                    "q3":       round(q3,       4),
                    "iqr":      round(iqr,      4),
                    "skewness": round(skewness, 4),
                    "kurtosis": round(kurtosis, 4),
                    "missing":  int(df[col].isna().sum()),
                    "unique":   int(col_numeric.nunique()),
                    "cv":       round(
                        float(col_numeric.std() /
                              col_numeric.mean()) * 100, 4
                    ) if col_numeric.mean() != 0 else 0.0,
                }

            except Exception as error:
                logger.error(
                    f"Descriptive stats failed for "
                    f"'{col}': {error}"
                )
                continue

        return results

    # ANOMALY DETECTION

    def _detect_anomalies(
        self,
        df:           pd.DataFrame,
        numeric_cols: list
    ) -> dict:
        """
        Detect statistical outliers using the
        Tukey IQR fence method. For each column,
        values beyond 1.5 × IQR from the quartile
        boundaries are classified as anomalies.

        Severity classification:
            High   — more than 5% of values anomalous
            Medium — 2% to 5% anomalous
            Low    — below 2% anomalous
        """

        results = {}

        for col in numeric_cols:
            try:
                col_data = df[col].dropna()

                # Per-column dtype guard
                if not pd.api.types.is_numeric_dtype(col_data):
                    continue

                col_numeric = pd.to_numeric(
                    col_data, errors="coerce"
                ).dropna()

                if len(col_numeric) < 4:
                    continue

                q1  = float(col_numeric.quantile(0.25))
                q3  = float(col_numeric.quantile(0.75))
                iqr = q3 - q1

                if iqr == 0:
                    continue

                lower = q1 - self.IQR_MULTIPLIER * iqr
                upper = q3 + self.IQR_MULTIPLIER * iqr

                anomaly_mask   = (
                    (col_numeric < lower) |
                    (col_numeric > upper)
                )
                anomaly_values = (
                    col_numeric[anomaly_mask].tolist()
                )
                anomaly_count  = len(anomaly_values)

                if anomaly_count == 0:
                    continue

                anomaly_percent = round(
                    anomaly_count / len(col_numeric) * 100, 4
                )

                if anomaly_percent > 5.0:
                    severity = "High"
                elif anomaly_percent > 2.0:
                    severity = "Medium"
                else:
                    severity = "Low"

                results[col] = {
                    "anomaly_count":   anomaly_count,
                    "anomaly_percent": anomaly_percent,
                    "lower_bound":     round(lower, 4),
                    "upper_bound":     round(upper, 4),
                    "severity":        severity,
                    "anomaly_values":  [
                        round(float(v), 4)
                        for v in sorted(anomaly_values)
                    ],
                    "q1":  round(q1,  4),
                    "q3":  round(q3,  4),
                    "iqr": round(iqr, 4),
                }

            except Exception as error:
                logger.error(
                    f"Anomaly detection failed for "
                    f"'{col}': {error}"
                )
                continue

        return results


    # CORRELATION ANALYSIS

    def _compute_correlations(
        self,
        df:           pd.DataFrame,
        numeric_cols: list
    ) -> list:
        """
        Compute Pearson correlation coefficients
        for all unique column pairs and return
        those exceeding the significance threshold.

        Each result is classified by strength:
            Very Strong — |r| >= 0.90
            Strong      — |r| >= 0.70
            Moderate    — |r| >= 0.50
        """

        if len(numeric_cols) < 2:
            return []

        results = []

        try:
            numeric_df   = df[numeric_cols].apply(
                pd.to_numeric, errors="coerce"
            )
            corr_matrix  = numeric_df.corr(
                method="pearson"
            )

            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    col_a = numeric_cols[i]
                    col_b = numeric_cols[j]

                    try:
                        coeff = float(
                            corr_matrix.loc[col_a, col_b]
                        )
                    except Exception:
                        continue

                    if (
                        np.isnan(coeff) or
                        abs(coeff) < self.CORRELATION_THRESHOLD
                    ):
                        continue

                    abs_coeff = abs(coeff)

                    if abs_coeff >= 0.90:
                        strength = "Very Strong"
                    elif abs_coeff >= 0.70:
                        strength = "Strong"
                    else:
                        strength = "Moderate"

                    results.append({
                        "column_a":    col_a,
                        "column_b":    col_b,
                        "correlation": round(coeff, 4),
                        "strength":    strength,
                        "abs_value":   round(abs_coeff, 4),
                    })

            results.sort(
                key=lambda x: x["abs_value"],
                reverse=True
            )

        except Exception as error:
            logger.error(
                f"Correlation analysis failed: {error}"
            )

        return results

    # TREND ANALYSIS
    def _compute_trends(
        self,
        df:           pd.DataFrame,
        numeric_cols: list,
        profile
    ) -> dict:
        """
        Compute directional trend metrics for datasets
        with a confirmed time series dimension. For each
        numeric column, calculates the net directional
        movement from the first to the last observation
        and classifies it as increasing, decreasing,
        or stable based on the magnitude of change.

        Deliberately skips trend analysis when no time
        column is confirmed, because index-based trends
        in non-temporal data are often misleading and
        should not be presented as meaningful findings.
        """

        if not profile.has_time_series:
            return {}

        if len(df) < self.MIN_ROWS_FOR_TREND:
            logger.info(
                f"Trend analysis skipped: only "
                f"{len(df)} rows, minimum is "
                f"{self.MIN_ROWS_FOR_TREND}."
            )
            return {}

        results = {}
        time_col = profile.time_column

        for col in numeric_cols:
            try:
                subset = df[[time_col, col]].dropna()

                if len(subset) < self.MIN_ROWS_FOR_TREND:
                    continue

                # Per-column dtype guard with explicit
                # float conversion and error handling.
                # This is the fix for Timestamp coercion
                # in the trend section specifically.
                try:
                    start_val = float(
                        pd.to_numeric(
                            subset[col].iloc[0],
                            errors="coerce"
                        )
                    )
                    end_val   = float(
                        pd.to_numeric(
                            subset[col].iloc[-1],
                            errors="coerce"
                        )
                    )
                except (TypeError, ValueError):
                    logger.warning(
                        f"Trend skipped for '{col}': "
                        f"values cannot be converted to float."
                    )
                    continue

                if np.isnan(start_val) or np.isnan(end_val):
                    continue

                if start_val == 0:
                    percent_change = 0.0
                else:
                    percent_change = round(
                        ((end_val - start_val) / abs(start_val))
                        * 100, 4
                    )

                if percent_change > 5.0:
                    direction = "increasing"
                elif percent_change < -5.0:
                    direction = "decreasing"
                else:
                    direction = "stable"

                col_numeric = pd.to_numeric(
                    subset[col], errors="coerce"
                ).dropna()

                results[col] = {
                    "direction":      direction,
                    "start_value":    round(start_val, 4),
                    "end_value":      round(end_val,   4),
                    "percent_change": percent_change,
                    "min_value":      round(float(col_numeric.min()), 4),
                    "max_value":      round(float(col_numeric.max()), 4),
                    "volatility":     round(float(col_numeric.std()), 4),
                }

            except Exception as error:
                logger.error(
                    f"Trend analysis failed for "
                    f"'{col}': {error}"
                )
                continue

        return results

    # SUMMARY METRICS

    def _compute_summary(
        self,
        df:           pd.DataFrame,
        numeric_cols: list,
        results:      dict
    ) -> dict:
        """
        Produce dataset-level aggregate metrics that
        give the AI narrator and the executive summary
        a concise quantitative picture of the analysis
        without requiring access to the full results
        dictionary in every context.
        """

        desc      = results.get("descriptive",  {})
        anomalies = results.get("anomalies",    {})
        corrs     = results.get("correlations", [])

        total_anomalies = sum(
            info.get("anomaly_count", 0)
            for info in anomalies.values()
        )

        high_severity_anomalies = sum(
            1 for info in anomalies.values()
            if info.get("severity") == "High"
        )

        most_anomalous_col = (
            max(
                anomalies,
                key=lambda c: anomalies[c].get(
                    "anomaly_percent", 0
                )
            )
            if anomalies else None
        )

        strongest_correlation = (
            corrs[0] if corrs else None
        )

        avg_completeness = round(
            sum(
                (1 - desc[c].get("missing", 0) / len(df))
                * 100
                for c in desc
                if len(df) > 0
            ) / len(desc) if desc else 0,
            2
        )

        return {
            "total_numeric_cols":       len(numeric_cols),
            "total_anomalies":          total_anomalies,
            "high_severity_anomalies":  high_severity_anomalies,
            "cols_with_anomalies":      len(anomalies),
            "total_correlations":       len(corrs),
            "most_anomalous_col":       most_anomalous_col,
            "strongest_correlation":    strongest_correlation,
            "avg_col_completeness_pct": avg_completeness,
        }