# visualizer.py
# Professional Chart Generation Engine
# for AI Data Analysis Agent
# Version 1.0 — Developer reviewed
#
# PURPOSE:
#   Receive analyzed dataset and statistical results
#   Automatically determine which charts add value
#   Generate professional publication-quality visuals
#   Save all charts to organized output folder
#   Return chart paths for downstream report generation
#
# DESIGN PRINCIPLES:
#   Never generate a chart that does not add insight
#   Never fail to generate one that does
#   Every chart must be readable without explanation
#   All styling is consistent and professional
#   Charts work for any domain and any dataset

import os
import logging
import warnings
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import MaxNLocator
import seaborn as sns

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════
# VISUALIZATION RESULT — What the visualizer returns
# ════════════════════════════════════════════════════════

@dataclass
class VisualizationResult:
    """
    Standardized output from the visualizer.
    Contains paths to every generated chart
    and metadata about what was produced.
    """

    # Chart file paths — None if not generated
    overview_chart: Optional[str] = None
    distribution_chart: Optional[str] = None
    correlation_chart: Optional[str] = None
    anomaly_chart: Optional[str] = None
    trend_chart: Optional[str] = None
    categorical_chart: Optional[str] = None

    # Generation metadata
    total_charts_generated: int = 0
    charts_folder: str = ""
    generated_at: str = ""
    generation_errors: list = field(default_factory=list)
    generation_notes: list = field(default_factory=list)

    def get_all_chart_paths(self) -> list:
        """Return list of all successfully generated chart paths."""
        paths = [
            self.overview_chart,
            self.distribution_chart,
            self.correlation_chart,
            self.anomaly_chart,
            self.trend_chart,
            self.categorical_chart
        ]
        return [p for p in paths if p is not None]


# ════════════════════════════════════════════════════════
# PROFESSIONAL STYLE CONFIGURATION
# ════════════════════════════════════════════════════════

class ChartStyle:
    """
    Centralized style configuration.
    All charts use these values ensuring
    visual consistency across the entire report.
    """

    # Color palette — professional and accessible
    PRIMARY_COLOR   = "#2C5F8A"
    SECONDARY_COLOR = "#E8832A"
    SUCCESS_COLOR   = "#2E8B57"
    WARNING_COLOR   = "#DAA520"
    DANGER_COLOR    = "#C0392B"
    NEUTRAL_COLOR   = "#7F8C8D"
    BACKGROUND      = "#FAFAFA"
    GRID_COLOR      = "#E8E8E8"

    # Sequential palette for multi-series charts
    PALETTE = [
        "#2C5F8A", "#E8832A", "#2E8B57",
        "#8E44AD", "#DAA520", "#C0392B",
        "#1ABC9C", "#E74C3C", "#3498DB",
        "#F39C12"
    ]

    # Typography
    TITLE_FONT_SIZE    = 13
    SUBTITLE_FONT_SIZE = 10
    LABEL_FONT_SIZE    = 9
    TICK_FONT_SIZE     = 8
    ANNOTATION_SIZE    = 7

    # Figure dimensions
    FIGURE_DPI         = 150
    SINGLE_FIGURE_SIZE = (12, 6)
    GRID_FIGURE_SIZE   = (14, 10)
    WIDE_FIGURE_SIZE   = (16, 8)

    @classmethod
    def apply_global_style(cls):
        """Apply consistent style to all matplotlib figures."""
        plt.rcParams.update({
            "figure.facecolor":     cls.BACKGROUND,
            "axes.facecolor":       cls.BACKGROUND,
            "axes.grid":            True,
            "grid.color":           cls.GRID_COLOR,
            "grid.linewidth":       0.7,
            "grid.alpha":           0.8,
            "axes.spines.top":      False,
            "axes.spines.right":    False,
            "axes.spines.left":     True,
            "axes.spines.bottom":   True,
            "axes.labelsize":       cls.LABEL_FONT_SIZE,
            "axes.titlesize":       cls.TITLE_FONT_SIZE,
            "xtick.labelsize":      cls.TICK_FONT_SIZE,
            "ytick.labelsize":      cls.TICK_FONT_SIZE,
            "font.family":          "DejaVu Sans",
            "figure.dpi":           cls.FIGURE_DPI,
            "savefig.bbox":         "tight",
            "savefig.facecolor":    cls.BACKGROUND,
        })


# ════════════════════════════════════════════════════════
# MAIN VISUALIZER CLASS
# ════════════════════════════════════════════════════════

class DataVisualizer:
    """
    Generates a complete suite of professional charts
    from any analyzed dataset automatically.

    The visualizer examines the dataset profile
    and statistical results to determine which
    chart types will deliver the most insight,
    then generates each one with consistent
    professional styling.

    Usage:
        viz = DataVisualizer()
        result = viz.generate_all_charts(
            dataframe=df,
            profile=profile,
            stats=statistical_results,
            output_folder="charts/run_001"
        )

        for path in result.get_all_chart_paths():
            print(path)
    """

    def __init__(self, output_base_folder: str = "charts"):
        self.output_base_folder = output_base_folder
        ChartStyle.apply_global_style()

    # ════════════════════════════════════════════════════
    # MAIN ORCHESTRATION METHOD
    # ════════════════════════════════════════════════════

    def generate_all_charts(
        self,
        dataframe: pd.DataFrame,
        profile,
        stats: dict,
        session_id: str = None
    ) -> VisualizationResult:
        """
        Main entry point.
        Generates the complete chart suite
        appropriate for the given dataset.
        Each chart type is attempted independently
        so a failure in one never stops the others.

        Parameters:
            dataframe   — cleaned pandas DataFrame
            profile     — DatasetProfile from data_loader
            stats       — dict from statistical_analyzer
            session_id  — optional identifier for output folder
        """

        result = VisualizationResult()
        result.generated_at = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Create session output folder
        if session_id is None:
            session_id = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )

        charts_folder = os.path.join(
            self.output_base_folder, session_id
        )
        os.makedirs(charts_folder, exist_ok=True)
        result.charts_folder = charts_folder

        numeric_cols = profile.numeric_columns
        text_cols    = profile.text_columns

        logger.info(
            f"Generating charts — "
            f"{len(numeric_cols)} numeric columns | "
            f"time_series={profile.has_time_series}"
        )

        # Generate each chart type independently
        # Minimum 2 numeric columns needed for overview
        if len(numeric_cols) >= 1:
            result.overview_chart = self._safe_generate(
                self._create_overview_chart,
                result, "overview",
                dataframe, profile, stats, charts_folder
            )

        if len(numeric_cols) >= 1:
            result.distribution_chart = self._safe_generate(
                self._create_distribution_chart,
                result, "distribution",
                dataframe, profile, stats, charts_folder
            )

        if len(numeric_cols) >= 2:
            result.correlation_chart = self._safe_generate(
                self._create_correlation_chart,
                result, "correlation",
                dataframe, profile, stats, charts_folder
            )

        anomalies = stats.get("anomalies", {})
        if anomalies and len(numeric_cols) >= 1:
            result.anomaly_chart = self._safe_generate(
                self._create_anomaly_chart,
                result, "anomaly",
                dataframe, profile, stats, charts_folder
            )

        if profile.has_time_series and len(numeric_cols) >= 1:
            result.trend_chart = self._safe_generate(
                self._create_trend_chart,
                result, "trend",
                dataframe, profile, stats, charts_folder
            )

        if len(text_cols) >= 1:
            result.categorical_chart = self._safe_generate(
                self._create_categorical_chart,
                result, "categorical",
                dataframe, profile, stats, charts_folder
            )

        result.total_charts_generated = len(
            result.get_all_chart_paths()
        )

        logger.info(
            f"Chart generation complete: "
            f"{result.total_charts_generated} charts saved "
            f"to {charts_folder}"
        )

        return result

    def _safe_generate(
        self,
        chart_function,
        result: VisualizationResult,
        chart_name: str,
        *args
    ) -> Optional[str]:
        """
        Wraps every chart generation call in error handling.
        A failure in one chart never propagates to others.
        All matplotlib state is cleaned up after each chart.
        """
        try:
            path = chart_function(*args)
            if path:
                result.generation_notes.append(
                    f"{chart_name} chart generated: "
                    f"{os.path.basename(path)}"
                )
            return path
        except Exception as error:
            result.generation_errors.append(
                f"{chart_name} chart failed: {str(error)}"
            )
            logger.warning(
                f"Chart generation failed [{chart_name}]: "
                f"{error}"
            )
            return None
        finally:
            plt.close("all")

    # ════════════════════════════════════════════════════
    # CHART 1 — OVERVIEW
    # ════════════════════════════════════════════════════

    def _create_overview_chart(
        self,
        df: pd.DataFrame,
        profile,
        stats: dict,
        folder: str
    ) -> str:
        """
        Multi-panel overview showing all numeric columns
        as time series or index plots.
        Gives the analyst an immediate visual impression
        of the entire dataset in one view.
        """

        numeric_cols = profile.numeric_columns[:8]
        n_cols = len(numeric_cols)

        if n_cols == 0:
            return None

        # Determine grid layout
        n_rows = (n_cols + 1) // 2 if n_cols > 2 else n_cols
        n_grid_cols = 2 if n_cols > 1 else 1

        fig = plt.figure(
            figsize=(14, max(4, 3.5 * n_rows)),
            facecolor=ChartStyle.BACKGROUND
        )
        fig.suptitle(
            f"Dataset Overview — {profile.file_name}",
            fontsize=ChartStyle.TITLE_FONT_SIZE + 2,
            fontweight="bold",
            y=1.01
        )

        x_axis = (
            df[profile.time_column]
            if profile.has_time_series
            else df.index
        )

        for idx, col in enumerate(numeric_cols):
            ax = fig.add_subplot(n_rows, n_grid_cols, idx + 1)

            col_data = df[col].dropna()
            x_data = (
                df.loc[col_data.index, profile.time_column]
                if profile.has_time_series
                else col_data.index
            )

            color = ChartStyle.PALETTE[
                idx % len(ChartStyle.PALETTE)
            ]

            ax.plot(
                x_data,
                col_data,
                color=color,
                linewidth=1.4,
                alpha=0.85,
                zorder=2
            )

            # Shade area under line for visual weight
            ax.fill_between(
                x_data,
                col_data,
                alpha=0.08,
                color=color
            )

            # Add mean reference line
            mean_val = col_data.mean()
            ax.axhline(
                y=mean_val,
                color=ChartStyle.NEUTRAL_COLOR,
                linestyle="--",
                linewidth=0.9,
                alpha=0.7,
                label=f"Mean: {mean_val:.2f}"
            )

            ax.set_title(
                col.replace("_", " ").title(),
                fontsize=ChartStyle.SUBTITLE_FONT_SIZE,
                fontweight="bold",
                pad=6
            )
            ax.set_ylabel(
                col.replace("_", " "),
                fontsize=ChartStyle.LABEL_FONT_SIZE
            )
            ax.legend(
                fontsize=ChartStyle.ANNOTATION_SIZE,
                loc="upper right"
            )
            ax.yaxis.set_major_locator(
                MaxNLocator(nbins=5)
            )

            if profile.has_time_series:
                ax.tick_params(
                    axis="x",
                    rotation=30,
                    labelsize=ChartStyle.TICK_FONT_SIZE
                )

        plt.tight_layout()

        path = os.path.join(folder, "01_overview.png")
        plt.savefig(path, dpi=ChartStyle.FIGURE_DPI)
        plt.close()

        logger.info(f"Overview chart saved: {path}")
        return path

    # ════════════════════════════════════════════════════
    # CHART 2 — DISTRIBUTION
    # ════════════════════════════════════════════════════

    def _create_distribution_chart(
        self,
        df: pd.DataFrame,
        profile,
        stats: dict,
        folder: str
    ) -> str:
        """
        Combined histogram and KDE plot for every
        numeric column showing the full distribution
        shape, skewness, and key statistical markers.
        Box plots alongside each histogram reveal
        outlier positions and quartile structure.
        """

        numeric_cols = profile.numeric_columns[:6]
        n_cols = len(numeric_cols)

        if n_cols == 0:
            return None

        fig, axes = plt.subplots(
            n_cols, 2,
            figsize=(14, max(4, 3.5 * n_cols)),
            facecolor=ChartStyle.BACKGROUND
        )

        if n_cols == 1:
            axes = [axes]

        fig.suptitle(
            "Statistical Distribution Analysis",
            fontsize=ChartStyle.TITLE_FONT_SIZE + 2,
            fontweight="bold"
        )

        for idx, col in enumerate(numeric_cols):
            data = df[col].dropna()
            color = ChartStyle.PALETTE[
                idx % len(ChartStyle.PALETTE)
            ]

            ax_hist = axes[idx][0]
            ax_box  = axes[idx][1]

            # Histogram with KDE overlay
            ax_hist.hist(
                data,
                bins=min(30, max(10, len(data) // 10)),
                color=color,
                alpha=0.6,
                edgecolor="white",
                linewidth=0.5,
                density=True,
                label="Distribution"
            )

            # KDE curve
            try:
                from scipy.stats import gaussian_kde
                kde = gaussian_kde(data)
                x_range = np.linspace(
                    data.min(), data.max(), 200
                )
                ax_hist.plot(
                    x_range,
                    kde(x_range),
                    color=color,
                    linewidth=2.0,
                    label="KDE"
                )
            except Exception:
                pass

            # Statistical markers
            mean_val   = data.mean()
            median_val = data.median()

            ax_hist.axvline(
                mean_val,
                color=ChartStyle.DANGER_COLOR,
                linestyle="--",
                linewidth=1.2,
                label=f"Mean: {mean_val:.2f}"
            )
            ax_hist.axvline(
                median_val,
                color=ChartStyle.SUCCESS_COLOR,
                linestyle="-.",
                linewidth=1.2,
                label=f"Median: {median_val:.2f}"
            )

            ax_hist.set_title(
                f"{col.replace('_', ' ').title()} — Histogram",
                fontsize=ChartStyle.SUBTITLE_FONT_SIZE,
                fontweight="bold"
            )
            ax_hist.legend(
                fontsize=ChartStyle.ANNOTATION_SIZE
            )
            ax_hist.set_ylabel(
                "Density",
                fontsize=ChartStyle.LABEL_FONT_SIZE
            )

            # Box plot
            bp = ax_box.boxplot(
                data,
                patch_artist=True,
                widths=0.5,
                notch=False
            )

            bp["boxes"][0].set_facecolor(color)
            bp["boxes"][0].set_alpha(0.6)
            bp["medians"][0].set_color(
                ChartStyle.DANGER_COLOR
            )
            bp["medians"][0].set_linewidth(2)

            for whisker in bp["whiskers"]:
                whisker.set_color(color)
                whisker.set_linewidth(1.2)

            for flier in bp["fliers"]:
                flier.set(
                    marker="o",
                    color=ChartStyle.WARNING_COLOR,
                    alpha=0.6,
                    markersize=4
                )

            # Annotate quartiles
            q1  = data.quantile(0.25)
            q3  = data.quantile(0.75)
            iqr = q3 - q1

            ax_box.annotate(
                f"Q1: {q1:.2f}",
                xy=(1, q1),
                xytext=(1.35, q1),
                fontsize=ChartStyle.ANNOTATION_SIZE,
                color=ChartStyle.NEUTRAL_COLOR
            )
            ax_box.annotate(
                f"Q3: {q3:.2f}",
                xy=(1, q3),
                xytext=(1.35, q3),
                fontsize=ChartStyle.ANNOTATION_SIZE,
                color=ChartStyle.NEUTRAL_COLOR
            )
            ax_box.annotate(
                f"IQR: {iqr:.2f}",
                xy=(1, q1 + iqr / 2),
                xytext=(1.35, q1 + iqr / 2),
                fontsize=ChartStyle.ANNOTATION_SIZE,
                color=ChartStyle.PRIMARY_COLOR,
                fontweight="bold"
            )

            ax_box.set_title(
                f"{col.replace('_', ' ').title()} — Box Plot",
                fontsize=ChartStyle.SUBTITLE_FONT_SIZE,
                fontweight="bold"
            )
            ax_box.set_xticks([])
            ax_box.set_ylabel(
                col.replace("_", " "),
                fontsize=ChartStyle.LABEL_FONT_SIZE
            )

        plt.tight_layout()

        path = os.path.join(
            folder, "02_distributions.png"
        )
        plt.savefig(path, dpi=ChartStyle.FIGURE_DPI)
        plt.close()

        logger.info(f"Distribution chart saved: {path}")
        return path

    # ════════════════════════════════════════════════════
    # CHART 3 — CORRELATION HEATMAP
    # ════════════════════════════════════════════════════

    def _create_correlation_chart(
        self,
        df: pd.DataFrame,
        profile,
        stats: dict,
        folder: str
    ) -> str:
        """
        Correlation heatmap showing pairwise relationships
        between all numeric variables simultaneously.
        Strong correlations annotated with coefficients.
        Scatter plots for the top three strongest
        relationships shown alongside the heatmap.
        """

        numeric_cols = profile.numeric_columns
        if len(numeric_cols) < 2:
            return None

        corr_matrix = df[numeric_cols].corr()

        # Layout: heatmap left, scatter plots right
        n_scatter = min(
            3,
            len([
                (i, j)
                for i in range(len(numeric_cols))
                for j in range(i + 1, len(numeric_cols))
                if abs(corr_matrix.iloc[i, j]) > 0.5
            ])
        )

        if n_scatter > 0:
            fig = plt.figure(
                figsize=(16, max(8, 3 * n_scatter)),
                facecolor=ChartStyle.BACKGROUND
            )
            gs = gridspec.GridSpec(
                max(n_scatter, 1), 2,
                width_ratios=[1.2, 1],
                figure=fig
            )
            ax_heatmap = fig.add_subplot(gs[:, 0])
        else:
            fig, ax_heatmap = plt.subplots(
                figsize=(10, 8),
                facecolor=ChartStyle.BACKGROUND
            )

        # Generate heatmap
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))

        sns.heatmap(
            corr_matrix,
            mask=mask,
            ax=ax_heatmap,
            annot=True,
            fmt=".2f",
            cmap="RdYlGn",
            center=0,
            vmin=-1,
            vmax=1,
            linewidths=0.5,
            linecolor="white",
            annot_kws={
                "size": ChartStyle.ANNOTATION_SIZE + 1
            },
            cbar_kws={"shrink": 0.8}
        )

        ax_heatmap.set_title(
            "Correlation Matrix — All Numeric Variables",
            fontsize=ChartStyle.TITLE_FONT_SIZE,
            fontweight="bold",
            pad=12
        )
        ax_heatmap.tick_params(
            axis="x",
            rotation=45,
            labelsize=ChartStyle.TICK_FONT_SIZE
        )
        ax_heatmap.tick_params(
            axis="y",
            rotation=0,
            labelsize=ChartStyle.TICK_FONT_SIZE
        )

        # Scatter plots for strongest correlations
        if n_scatter > 0:
            strong_pairs = []
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    coeff = corr_matrix.iloc[i, j]
                    if abs(coeff) > 0.5:
                        strong_pairs.append((
                            numeric_cols[i],
                            numeric_cols[j],
                            coeff
                        ))

            strong_pairs.sort(
                key=lambda x: abs(x[2]), reverse=True
            )

            for scatter_idx, (col_a, col_b, coeff) in enumerate(
                strong_pairs[:3]
            ):
                ax_scatter = fig.add_subplot(
                    gs[scatter_idx, 1]
                )

                color = (
                    ChartStyle.SUCCESS_COLOR
                    if coeff > 0
                    else ChartStyle.DANGER_COLOR
                )

                ax_scatter.scatter(
                    df[col_a],
                    df[col_b],
                    alpha=0.5,
                    color=color,
                    s=25,
                    edgecolors="white",
                    linewidth=0.3
                )

                # Trend line
                try:
                    valid = df[[col_a, col_b]].dropna()
                    z = np.polyfit(
                        valid[col_a], valid[col_b], 1
                    )
                    p = np.poly1d(z)
                    x_line = np.linspace(
                        valid[col_a].min(),
                        valid[col_a].max(),
                        100
                    )
                    ax_scatter.plot(
                        x_line,
                        p(x_line),
                        color=ChartStyle.NEUTRAL_COLOR,
                        linewidth=1.5,
                        linestyle="--",
                        alpha=0.8
                    )
                except Exception:
                    pass

                direction = (
                    "positive" if coeff > 0 else "negative"
                )
                ax_scatter.set_title(
                    f"r = {coeff:.3f} ({direction})",
                    fontsize=ChartStyle.SUBTITLE_FONT_SIZE,
                    fontweight="bold"
                )
                ax_scatter.set_xlabel(
                    col_a.replace("_", " "),
                    fontsize=ChartStyle.LABEL_FONT_SIZE
                )
                ax_scatter.set_ylabel(
                    col_b.replace("_", " "),
                    fontsize=ChartStyle.LABEL_FONT_SIZE
                )

        fig.suptitle(
            "Correlation Analysis",
            fontsize=ChartStyle.TITLE_FONT_SIZE + 2,
            fontweight="bold",
            y=1.01
        )

        plt.tight_layout()

        path = os.path.join(
            folder, "03_correlations.png"
        )
        plt.savefig(path, dpi=ChartStyle.FIGURE_DPI)
        plt.close()

        logger.info(f"Correlation chart saved: {path}")
        return path

    # ════════════════════════════════════════════════════
    # CHART 4 — ANOMALY DETECTION
    # ════════════════════════════════════════════════════

    def _create_anomaly_chart(
        self,
        df: pd.DataFrame,
        profile,
        stats: dict,
        folder: str
    ) -> str:
        """
        Visualizes detected anomalies and outliers
        across the columns where they were found.
        Normal values are shown in one color,
        anomalous values highlighted prominently
        so the analyst can immediately see
        where, when, and how severely the data
        deviates from expected behavior.
        """

        anomalies = stats.get("anomalies", {})
        if not anomalies:
            return None

        # Limit to four most anomalous columns
        cols_to_show = list(anomalies.keys())[:4]
        n_panels = len(cols_to_show)

        fig, axes = plt.subplots(
            n_panels, 1,
            figsize=(14, max(4, 3.5 * n_panels)),
            facecolor=ChartStyle.BACKGROUND,
            squeeze=False
        )

        fig.suptitle(
            "Anomaly Detection — Outlier Visualization",
            fontsize=ChartStyle.TITLE_FONT_SIZE + 2,
            fontweight="bold"
        )

        x_axis = (
            df[profile.time_column]
            if profile.has_time_series
            else df.index
        )

        for panel_idx, col in enumerate(cols_to_show):
            ax = axes[panel_idx][0]
            anomaly_info = anomalies[col]

            lower = anomaly_info.get("lower_bound")
            upper = anomaly_info.get("upper_bound")
            anomaly_vals = anomaly_info.get(
                "anomaly_values", []
            )

            col_data = df[col]

            # Identify anomaly positions
            is_anomaly = (
                (col_data < lower) | (col_data > upper)
            )
            normal_data  = col_data[~is_anomaly]
            anomaly_data = col_data[is_anomaly]

            x_normal  = (
                df.loc[normal_data.index, profile.time_column]
                if profile.has_time_series
                else normal_data.index
            )
            x_anomaly = (
                df.loc[anomaly_data.index, profile.time_column]
                if profile.has_time_series
                else anomaly_data.index
            )

            # Plot normal values as line
            ax.plot(
                x_normal if len(x_normal) > 0 else normal_data.index,
                normal_data,
                color=ChartStyle.PRIMARY_COLOR,
                linewidth=1.3,
                alpha=0.75,
                label="Normal",
                zorder=2
            )

            # Highlight anomalies as prominent markers
            if len(anomaly_data) > 0:
                ax.scatter(
                    x_anomaly if len(x_anomaly) > 0 else anomaly_data.index,
                    anomaly_data,
                    color=ChartStyle.DANGER_COLOR,
                    s=80,
                    zorder=5,
                    label=f"Anomalies ({len(anomaly_data)})",
                    marker="^",
                    edgecolors="white",
                    linewidth=0.8
                )

            # Draw boundary lines
            if lower is not None:
                ax.axhline(
                    y=lower,
                    color=ChartStyle.WARNING_COLOR,
                    linestyle="--",
                    linewidth=1.0,
                    alpha=0.8,
                    label=f"Lower bound: {lower:.2f}"
                )
            if upper is not None:
                ax.axhline(
                    y=upper,
                    color=ChartStyle.WARNING_COLOR,
                    linestyle="--",
                    linewidth=1.0,
                    alpha=0.8,
                    label=f"Upper bound: {upper:.2f}"
                )

            # Shade anomaly zone
            if lower is not None and upper is not None:
                full_x = (
                    df[profile.time_column]
                    if profile.has_time_series
                    else df.index
                )
                ax.fill_between(
                    full_x,
                    lower,
                    col_data.min() * 0.95
                    if col_data.min() < lower
                    else lower * 0.95,
                    alpha=0.05,
                    color=ChartStyle.DANGER_COLOR
                )
                ax.fill_between(
                    full_x,
                    upper,
                    col_data.max() * 1.05
                    if col_data.max() > upper
                    else upper * 1.05,
                    alpha=0.05,
                    color=ChartStyle.DANGER_COLOR
                )

            count = len(anomaly_data)
            pct   = round(count / len(col_data) * 100, 1)

            ax.set_title(
                f"{col.replace('_', ' ').title()} — "
                f"{count} anomalies detected ({pct}% of data)",
                fontsize=ChartStyle.SUBTITLE_FONT_SIZE,
                fontweight="bold"
            )
            ax.set_ylabel(
                col.replace("_", " "),
                fontsize=ChartStyle.LABEL_FONT_SIZE
            )
            ax.legend(
                fontsize=ChartStyle.ANNOTATION_SIZE,
                loc="upper right"
            )

            if profile.has_time_series:
                ax.tick_params(
                    axis="x",
                    rotation=30,
                    labelsize=ChartStyle.TICK_FONT_SIZE
                )

        plt.tight_layout()

        path = os.path.join(folder, "04_anomalies.png")
        plt.savefig(path, dpi=ChartStyle.FIGURE_DPI)
        plt.close()

        logger.info(f"Anomaly chart saved: {path}")
        return path

    # ════════════════════════════════════════════════════
    # CHART 5 — TREND ANALYSIS
    # ════════════════════════════════════════════════════

    def _create_trend_chart(
        self,
        df: pd.DataFrame,
        profile,
        stats: dict,
        folder: str
    ) -> str:
        """
        Time series trend analysis for datasets
        with a detected time dimension.
        Shows raw data, rolling average to smooth noise,
        and a polynomial trend line to reveal
        the underlying directional movement.
        Only generated when time series is confirmed.
        """

        if not profile.has_time_series:
            return None

        numeric_cols = profile.numeric_columns[:4]
        if not numeric_cols:
            return None

        time_col = profile.time_column
        n_panels = len(numeric_cols)

        fig, axes = plt.subplots(
            n_panels, 1,
            figsize=(14, max(4, 3.5 * n_panels)),
            facecolor=ChartStyle.BACKGROUND,
            squeeze=False
        )

        fig.suptitle(
            "Time Series Trend Analysis",
            fontsize=ChartStyle.TITLE_FONT_SIZE + 2,
            fontweight="bold"
        )

        for panel_idx, col in enumerate(numeric_cols):
            ax = axes[panel_idx][0]

            subset = df[[time_col, col]].dropna()
            if len(subset) < 3:
                continue

            x_times = subset[time_col]
            y_vals  = subset[col]
            color   = ChartStyle.PALETTE[
                panel_idx % len(ChartStyle.PALETTE)
            ]

            # Raw data — light and thin
            ax.plot(
                x_times,
                y_vals,
                color=color,
                linewidth=0.9,
                alpha=0.35,
                label="Raw data",
                zorder=1
            )

            # Rolling average — window adapts to data size
            window = max(3, len(y_vals) // 10)
            rolling = y_vals.rolling(
                window=window, center=True
            ).mean()
            ax.plot(
                x_times,
                rolling,
                color=color,
                linewidth=2.2,
                alpha=0.9,
                label=f"Rolling avg (n={window})",
                zorder=3
            )

            # Polynomial trend line
            try:
                x_numeric = np.arange(len(y_vals))
                z = np.polyfit(
                    x_numeric,
                    y_vals.values,
                    deg=min(3, len(y_vals) - 1)
                )
                p = np.poly1d(z)
                ax.plot(
                    x_times,
                    p(x_numeric),
                    color=ChartStyle.DANGER_COLOR,
                    linewidth=1.8,
                    linestyle="--",
                    alpha=0.8,
                    label="Trend",
                    zorder=4
                )
            except Exception:
                pass

            # Min and max annotations
            max_idx = y_vals.idxmax()
            min_idx = y_vals.idxmin()

            ax.annotate(
                f"Max: {y_vals[max_idx]:.2f}",
                xy=(x_times[max_idx], y_vals[max_idx]),
                xytext=(5, 8),
                textcoords="offset points",
                fontsize=ChartStyle.ANNOTATION_SIZE,
                color=ChartStyle.SUCCESS_COLOR,
                fontweight="bold",
                arrowprops=dict(
                    arrowstyle="->",
                    color=ChartStyle.SUCCESS_COLOR,
                    lw=0.8
                )
            )

            ax.annotate(
                f"Min: {y_vals[min_idx]:.2f}",
                xy=(x_times[min_idx], y_vals[min_idx]),
                xytext=(5, -14),
                textcoords="offset points",
                fontsize=ChartStyle.ANNOTATION_SIZE,
                color=ChartStyle.DANGER_COLOR,
                fontweight="bold",
                arrowprops=dict(
                    arrowstyle="->",
                    color=ChartStyle.DANGER_COLOR,
                    lw=0.8
                )
            )

            ax.set_title(
                f"{col.replace('_', ' ').title()} — "
                f"Trend Over Time",
                fontsize=ChartStyle.SUBTITLE_FONT_SIZE,
                fontweight="bold"
            )
            ax.set_ylabel(
                col.replace("_", " "),
                fontsize=ChartStyle.LABEL_FONT_SIZE
            )
            ax.legend(
                fontsize=ChartStyle.ANNOTATION_SIZE,
                loc="upper right"
            )
            ax.tick_params(
                axis="x",
                rotation=30,
                labelsize=ChartStyle.TICK_FONT_SIZE
            )

        plt.tight_layout()

        path = os.path.join(folder, "05_trends.png")
        plt.savefig(path, dpi=ChartStyle.FIGURE_DPI)
        plt.close()

        logger.info(f"Trend chart saved: {path}")
        return path

    # ════════════════════════════════════════════════════
    # CHART 6 — CATEGORICAL ANALYSIS
    # ════════════════════════════════════════════════════

    def _create_categorical_chart(
        self,
        df: pd.DataFrame,
        profile,
        stats: dict,
        folder: str
    ) -> str:
        """
        Analyzes text and categorical columns.
        Shows value frequency distributions
        and where categorical variables intersect
        with the numeric variables — revealing
        whether category membership correlates
        with performance differences.
        """

        text_cols    = profile.text_columns
        numeric_cols = profile.numeric_columns

        if not text_cols:
            return None

        # Use first categorical column with
        # reasonable cardinality
        target_col = None
        for col in text_cols:
            n_unique = df[col].nunique()
            if 2 <= n_unique <= 20:
                target_col = col
                break

        if target_col is None:
            target_col = text_cols[0]

        n_unique     = df[target_col].nunique()
        has_numerics = len(numeric_cols) >= 1

        n_rows = 2 if has_numerics else 1
        fig, axes = plt.subplots(
            n_rows,
            min(2, len(numeric_cols) + 1),
            figsize=(14, max(5, 4.5 * n_rows)),
            facecolor=ChartStyle.BACKGROUND,
            squeeze=False
        )

        fig.suptitle(
            f"Categorical Analysis — "
            f"{target_col.replace('_', ' ').title()}",
            fontsize=ChartStyle.TITLE_FONT_SIZE + 2,
            fontweight="bold"
        )

        # Panel 1 — value frequency bar chart
        ax_freq = axes[0][0]
        value_counts = (
            df[target_col]
            .value_counts()
            .head(15)
        )

        colors = [
            ChartStyle.PALETTE[i % len(ChartStyle.PALETTE)]
            for i in range(len(value_counts))
        ]

        bars = ax_freq.bar(
            range(len(value_counts)),
            value_counts.values,
            color=colors,
            edgecolor="white",
            linewidth=0.5,
            alpha=0.85
        )

        # Value labels on bars
        for bar_obj, val in zip(
            bars, value_counts.values
        ):
            ax_freq.text(
                bar_obj.get_x() + bar_obj.get_width() / 2,
                bar_obj.get_height() + 0.3,
                str(val),
                ha="center",
                va="bottom",
                fontsize=ChartStyle.ANNOTATION_SIZE,
                fontweight="bold"
            )

        ax_freq.set_xticks(range(len(value_counts)))
        ax_freq.set_xticklabels(
            value_counts.index,
            rotation=35,
            ha="right",
            fontsize=ChartStyle.TICK_FONT_SIZE
        )
        ax_freq.set_title(
            f"Frequency Distribution",
            fontsize=ChartStyle.SUBTITLE_FONT_SIZE,
            fontweight="bold"
        )
        ax_freq.set_ylabel(
            "Count",
            fontsize=ChartStyle.LABEL_FONT_SIZE
        )

        # Panel 2 — pie chart for proportion view
        if len(axes[0]) > 1:
            ax_pie = axes[0][1]
            top_n = value_counts.head(8)
            others = value_counts.iloc[8:].sum()

            if others > 0:
                top_n["Other"] = others

            ax_pie.pie(
                top_n.values,
                labels=top_n.index,
                colors=[
                    ChartStyle.PALETTE[i % len(ChartStyle.PALETTE)]
                    for i in range(len(top_n))
                ],
                autopct="%1.1f%%",
                startangle=90,
                pctdistance=0.82,
                textprops={
                    "fontsize": ChartStyle.ANNOTATION_SIZE
                }
            )
            ax_pie.set_title(
                "Proportion Share",
                fontsize=ChartStyle.SUBTITLE_FONT_SIZE,
                fontweight="bold"
            )

        # Row 2 — numeric distributions by category
        if has_numerics and n_rows > 1:
            numeric_to_show = numeric_cols[:2]

            for num_idx, num_col in enumerate(
                numeric_to_show
            ):
                if num_idx >= len(axes[1]):
                    break

                ax_box = axes[1][num_idx]

                categories = (
                    df[target_col]
                    .value_counts()
                    .head(10)
                    .index
                    .tolist()
                )

                box_data = [
                    df.loc[
                        df[target_col] == cat,
                        num_col
                    ].dropna().values
                    for cat in categories
                ]

                box_data = [
                    d for d in box_data if len(d) > 0
                ]
                valid_cats = [
                    cat for cat, d in zip(
                        categories, box_data
                    )
                    if len(d) > 0
                ]

                if box_data:
                    bp = ax_box.boxplot(
                        box_data,
                        patch_artist=True,
                        widths=0.5
                    )

                    for patch_idx, patch in enumerate(
                        bp["boxes"]
                    ):
                        patch.set_facecolor(
                            ChartStyle.PALETTE[
                                patch_idx
                                % len(ChartStyle.PALETTE)
                            ]
                        )
                        patch.set_alpha(0.65)

                    ax_box.set_xticks(
                        range(1, len(valid_cats) + 1)
                    )
                    ax_box.set_xticklabels(
                        valid_cats,
                        rotation=35,
                        ha="right",
                        fontsize=ChartStyle.TICK_FONT_SIZE
                    )
                    ax_box.set_title(
                        f"{num_col.replace('_', ' ').title()} "
                        f"by {target_col.replace('_', ' ').title()}",
                        fontsize=ChartStyle.SUBTITLE_FONT_SIZE,
                        fontweight="bold"
                    )
                    ax_box.set_ylabel(
                        num_col.replace("_", " "),
                        fontsize=ChartStyle.LABEL_FONT_SIZE
                    )

        plt.tight_layout()

        path = os.path.join(
            folder, "06_categorical.png"
        )
        plt.savefig(path, dpi=ChartStyle.FIGURE_DPI)
        plt.close()

        logger.info(
            f"Categorical chart saved: {path}"
        )
        return path

    # ════════════════════════════════════════════════════
    # UTILITY — RESULT SUMMARY
    # ════════════════════════════════════════════════════

    def get_result_summary(
        self,
        result: VisualizationResult
    ) -> str:
        """
        Human readable summary of visualization results.
        Used in terminal output and reports.
        """

        lines = [
            "VISUALIZATION RESULTS",
            "=" * 45,
            f"Generated at : {result.generated_at}",
            f"Output folder: {result.charts_folder}",
            f"Total charts : {result.total_charts_generated}",
            "",
            "CHARTS GENERATED",
        ]

        chart_map = {
            "Overview"     : result.overview_chart,
            "Distributions": result.distribution_chart,
            "Correlations" : result.correlation_chart,
            "Anomalies"    : result.anomaly_chart,
            "Trends"       : result.trend_chart,
            "Categorical"  : result.categorical_chart,
        }

        for name, path in chart_map.items():
            status = (
                f"✔  {os.path.basename(path)}"
                if path
                else "—  Not generated"
            )
            lines.append(f"  {name:<15}: {status}")

        if result.generation_errors:
            lines += ["", "WARNINGS"]
            for err in result.generation_errors:
                lines.append(f"  ⚠  {err}")

        lines += ["", "=" * 45]
        return "\n".join(lines)