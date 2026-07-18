# customization/domains/education.py
# Education Domain Module
# AI Data Analysis Platform — Domain Layer

import pandas as pd
import numpy as np
import logging
from dataclasses import dataclass, field
from typing import Optional
from customization.base_domain import BaseDomain

logger = logging.getLogger(__name__)


@dataclass
class EducationDomainResult:
    ranked_students:          pd.DataFrame = None
    at_risk_students:         pd.DataFrame = None
    top_performers:           pd.DataFrame = None
    performance_bands:        dict         = field(default_factory=dict)
    class_statistics:         dict         = field(default_factory=dict)
    subject_comparison:       dict         = field(default_factory=dict)
    attendance_analysis:      dict         = field(default_factory=dict)
    domain_prompt_context:    str          = ""
    domain_insights:          list         = field(default_factory=list)
    domain_recommendations:   list         = field(default_factory=list)
    analysis_success:         bool         = False
    analysis_error:           Optional[str] = None


class EducationDomain(BaseDomain):
    """
    Education domain analysis — student grades, rankings, pass/fail.
    Extends BaseDomain for compatibility with the domain registry.
    """

    PERFORMANCE_BANDS = {
        "Distinction": (90, 100),
        "Merit":       (75, 89),
        "Pass":        (50, 74),
        "Borderline":  (40, 49),
        "Fail":        (0,  39),
    }

    ATTENDANCE_RISK_THRESHOLD = 75.0
    ACADEMIC_RISK_THRESHOLD   = 50.0

    SCORE_KEYWORDS = [
        "score", "grade", "mark", "result",
        "exam", "test", "quiz", "assessment",
        "math", "science", "english", "history",
        "physics", "chemistry", "art", "biology",
        "final", "midterm", "gpa", "cgpa"
    ]

    ATTENDANCE_KEYWORDS = [
        "attendance", "present", "absent",
        "days_attended", "attendance_pct"
    ]

    STUDENT_ID_KEYWORDS = [
        "student_id", "id", "roll", "reg_no",
        "registration", "student_no", "name"
    ]

    def detect(self) -> bool:
        """Detect if this is education data."""
        score_cols = self._detect_score_columns(self.df)
        return len(score_cols) >= 2

    def get_section_header(self) -> str:
        return "GRADING AND STUDENT PERFORMANCE"

    def get_priority(self) -> int:
        return 60

    def generate_content(self) -> str:
        """Generate education-specific content for text report."""
        result = self.analyze(self.profile, self.stats)
        if not result.analysis_success:
            return "  Education analysis failed: " + (result.analysis_error or "Unknown error")

        lines = []

        # Performance bands
        lines.append("  PERFORMANCE BANDS")
        lines.append("  " + "-" * 40)
        for band, info in result.performance_bands.items():
            lines.append(f"    {band}: {info['count']} students ({info['percentage']}%)")

        # Class statistics
        cs = result.class_statistics
        lines.append("")
        lines.append("  CLASS STATISTICS")
        lines.append("  " + "-" * 40)
        lines.append(f"    Class Average   : {cs.get('class_average', 0)}%")
        lines.append(f"    Pass Rate       : {cs.get('pass_rate_pct', 0)}%")
        lines.append(f"    At-Risk Students: {cs.get('at_risk_count', 0)}")
        lines.append(f"    Distinctions    : {cs.get('distinction_count', 0)}")

        # Top performers
        if result.top_performers is not None and not result.top_performers.empty:
            lines.append("")
            lines.append("  TOP PERFORMERS")
            lines.append("  " + "-" * 40)
            for _, row in result.top_performers.head(5).iterrows():
                name = row.get('Student', 'Unknown')
                avg = row.get('Average Score', 0)
                lines.append(f"    {name}: {avg:.1f}%")

        # At-risk students
        if result.at_risk_students is not None and not result.at_risk_students.empty:
            lines.append("")
            lines.append("  AT-RISK STUDENTS")
            lines.append("  " + "-" * 40)
            for _, row in result.at_risk_students.head(5).iterrows():
                name = row.get('Student', 'Unknown')
                avg = row.get('Average Score', 0)
                lines.append(f"    ⚠️ {name}: {avg:.1f}%")

        # Insights
        if result.domain_insights:
            lines.append("")
            lines.append("  KEY INSIGHTS")
            lines.append("  " + "-" * 40)
            for insight in result.domain_insights[:5]:
                lines.append(f"    {insight}")

        return "\n".join(lines)

    def get_excel_sheets(self) -> dict:
        """Return education-specific Excel sheets."""
        result = self.analyze(self.profile, self.stats)

        sheets = {}
        if result.ranked_students is not None and not result.ranked_students.empty:
            sheets["Student Rankings"] = result.ranked_students
        if result.at_risk_students is not None and not result.at_risk_students.empty:
            sheets["At-Risk Students"] = result.at_risk_students
        if result.top_performers is not None and not result.top_performers.empty:
            sheets["Top Performers"] = result.top_performers

        return sheets

    # ─── Analysis Methods ──────────────────────────────────────────

    def analyze(self, profile, stats: dict) -> EducationDomainResult:
        """Primary entry point for education domain analysis."""
        result = EducationDomainResult()
        df = profile.dataframe

        logger.info("Education domain analysis starting...")

        try:
            score_cols = self._detect_score_columns(df)
            attendance_col = self._detect_attendance_column(df)
            student_id_col = self._detect_student_id_column(df)

            if not score_cols:
                result.analysis_error = "No score or grade columns detected."
                logger.warning(result.analysis_error)
                return result

            logger.info(f"Education columns detected: scores={score_cols}")

            df = self._compute_derived_metrics(df, score_cols, attendance_col)

            result.ranked_students = self._rank_students(df, score_cols, student_id_col)
            result.at_risk_students = self._identify_at_risk(df, score_cols, attendance_col, student_id_col)
            result.top_performers = self._identify_top_performers(df, score_cols, student_id_col)
            result.performance_bands = self._classify_performance_bands(df, score_cols)
            result.class_statistics = self._compute_class_statistics(df, score_cols)
            result.subject_comparison = self._compare_subjects(df, score_cols)

            if attendance_col:
                result.attendance_analysis = self._analyze_attendance(df, attendance_col, student_id_col)

            result.domain_insights = self._generate_insights(result, score_cols, attendance_col)
            result.domain_recommendations = self._generate_recommendations(result)
            result.domain_prompt_context = self._build_prompt_context(result, score_cols, attendance_col)

            result.analysis_success = True
            logger.info("Education domain analysis complete.")

        except Exception as error:
            result.analysis_error = str(error)
            logger.error(f"Education domain analysis failed: {error}", exc_info=True)

        return result

    # ─── Column Detection ──────────────────────────────────────────

    def _detect_score_columns(self, df: pd.DataFrame) -> list:
        score_cols = []
        for col in df.columns:
            col_lower = col.lower()
            is_score_named = any(kw in col_lower for kw in self.SCORE_KEYWORDS)
            is_numeric = pd.api.types.is_numeric_dtype(df[col])
            if is_score_named and is_numeric:
                score_cols.append(col)
        return score_cols

    def _detect_attendance_column(self, df: pd.DataFrame) -> Optional[str]:
        for col in df.columns:
            col_lower = col.lower()
            if any(kw in col_lower for kw in self.ATTENDANCE_KEYWORDS):
                if pd.api.types.is_numeric_dtype(df[col]):
                    return col
        return None

    def _detect_student_id_column(self, df: pd.DataFrame) -> Optional[str]:
        for col in df.columns:
            col_lower = col.lower()
            if any(kw in col_lower for kw in self.STUDENT_ID_KEYWORDS):
                return col
        return None

    # ─── Derived Metrics ───────────────────────────────────────────

    def _compute_derived_metrics(self, df, score_cols, attendance_col) -> pd.DataFrame:
        df = df.copy()
        df["__average_score__"] = df[score_cols].mean(axis=1)
        df["__total_score__"] = df[score_cols].sum(axis=1)
        df["__max_score__"] = df[score_cols].max(axis=1)
        df["__min_score__"] = df[score_cols].min(axis=1)
        df["__score_range__"] = df["__max_score__"] - df["__min_score__"]
        df["__performance_band__"] = df["__average_score__"].apply(self._assign_band)
        df["__academic_risk__"] = df["__average_score__"] < self.ACADEMIC_RISK_THRESHOLD
        if attendance_col:
            df["__attendance_risk__"] = df[attendance_col] < self.ATTENDANCE_RISK_THRESHOLD
        return df

    def _assign_band(self, score: float) -> str:
        if pd.isna(score):
            return "Unknown"
        for band, (low, high) in self.PERFORMANCE_BANDS.items():
            if low <= score <= high:
                return band
        return "Unknown"

    # ─── Ranking ────────────────────────────────────────────────────

    def _rank_students(self, df, score_cols, id_col) -> pd.DataFrame:
        cols = []
        if id_col:
            cols.append(id_col)
        cols += score_cols + ["__average_score__", "__total_score__", "__performance_band__"]
        available = [c for c in cols if c in df.columns]
        ranked = df[available].copy().sort_values("__average_score__", ascending=False).reset_index(drop=True)
        ranked.index = ranked.index + 1
        ranked.index.name = "Rank"
        ranked.columns = [c.replace("__", "").replace("_", " ").title() if c.startswith("__") else c for c in ranked.columns]
        return ranked

    def _identify_at_risk(self, df, score_cols, attendance_col, id_col) -> pd.DataFrame:
        academic_risk = df["__academic_risk__"]
        attendance_risk = df["__attendance_risk__"] if "__attendance_risk__" in df.columns else pd.Series(False, index=df.index)
        at_risk_mask = academic_risk | attendance_risk
        cols = []
        if id_col:
            cols.append(id_col)
        cols += score_cols + ["__average_score__"]
        if attendance_col:
            cols.append(attendance_col)
        available = [c for c in cols if c in df.columns]
        at_risk_df = df.loc[at_risk_mask, available].copy()
        at_risk_df.columns = [c.replace("__", "").replace("_", " ").title() if c.startswith("__") else c for c in at_risk_df.columns]
        return at_risk_df

    def _identify_top_performers(self, df, score_cols, id_col) -> pd.DataFrame:
        top_mask = df["__average_score__"] >= 85.0
        cols = []
        if id_col:
            cols.append(id_col)
        cols += score_cols + ["__average_score__"]
        available = [c for c in cols if c in df.columns]
        top_df = df.loc[top_mask, available].copy().sort_values("__average_score__", ascending=False)
        top_df.columns = [c.replace("__", "").replace("_", " ").title() if c.startswith("__") else c for c in top_df.columns]
        return top_df

    def _classify_performance_bands(self, df, score_cols) -> dict:
        band_counts = df["__performance_band__"].value_counts().to_dict()
        total = len(df)
        bands = {}
        for band in self.PERFORMANCE_BANDS:
            count = band_counts.get(band, 0)
            bands[band] = {"count": count, "percentage": round(count / total * 100, 2) if total > 0 else 0.0}
        return bands

    def _compute_class_statistics(self, df, score_cols) -> dict:
        avg = df["__average_score__"]
        return {
            "class_average": round(float(avg.mean()), 2),
            "class_median": round(float(avg.median()), 2),
            "highest_average": round(float(avg.max()), 2),
            "lowest_average": round(float(avg.min()), 2),
            "std_deviation": round(float(avg.std()), 2),
            "pass_rate_pct": round((avg >= self.ACADEMIC_RISK_THRESHOLD).sum() / len(avg) * 100, 2),
            "at_risk_count": int((avg < self.ACADEMIC_RISK_THRESHOLD).sum()),
            "distinction_count": int((avg >= 90).sum()),
            "total_students": len(df),
        }

    def _compare_subjects(self, df, score_cols) -> dict:
        comparison = {}
        for col in score_cols:
            data = df[col].dropna()
            comparison[col] = {
                "mean": round(float(data.mean()), 2),
                "median": round(float(data.median()), 2),
                "std": round(float(data.std()), 2),
                "pass_rate": round((data >= self.ACADEMIC_RISK_THRESHOLD).sum() / len(data) * 100, 2) if len(data) > 0 else 0.0,
                "highest": round(float(data.max()), 2),
                "lowest": round(float(data.min()), 2),
            }
        hardest = min(comparison, key=lambda c: comparison[c]["mean"]) if comparison else None
        easiest = max(comparison, key=lambda c: comparison[c]["mean"]) if comparison else None
        comparison["__meta__"] = {"hardest_subject": hardest, "easiest_subject": easiest}
        return comparison

    def _analyze_attendance(self, df, attendance_col, id_col) -> dict:
        att = df[attendance_col].dropna()
        at_risk_count = int((att < self.ATTENDANCE_RISK_THRESHOLD).sum())
        return {
            "average_attendance": round(float(att.mean()), 2),
            "median_attendance": round(float(att.median()), 2),
            "lowest_attendance": round(float(att.min()), 2),
            "highest_attendance": round(float(att.max()), 2),
            "at_risk_count": at_risk_count,
            "at_risk_percentage": round(at_risk_count / len(att) * 100, 2) if len(att) > 0 else 0.0,
            "threshold_used": self.ATTENDANCE_RISK_THRESHOLD,
        }

    def _generate_insights(self, result, score_cols, attendance_col) -> list:
        insights = []
        cs = result.class_statistics
        if cs.get("class_average", 0) >= 75:
            insights.append(f"The class average of {cs['class_average']}% indicates strong overall academic performance.")
        elif cs.get("class_average", 0) >= 50:
            insights.append(f"The class average of {cs['class_average']}% is adequate but suggests targeted intervention.")
        else:
            insights.append(f"The class average of {cs['class_average']}% is below the pass threshold.")
        return insights

    def _generate_recommendations(self, result) -> list:
        recommendations = []
        cs = result.class_statistics
        at_risk = cs.get("at_risk_count", 0)
        if at_risk > 0:
            recommendations.append(f"Enroll {at_risk} at-risk students in remedial support sessions.")
        return recommendations

    def _build_prompt_context(self, result, score_cols, attendance_col) -> str:
        cs = result.class_statistics
        return f"Total students: {cs.get('total_students', 0)} | Class average: {cs.get('class_average', 0)}%"