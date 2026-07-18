# customization/domains/healthcare.py
# Healthcare domain — patient outcomes, risk factors

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


class HealthcareDomain(BaseDomain):
    """Healthcare-specific report sections for patient data."""

    DEFAULT_BMI_HEALTHY_RANGE = [18.5, 25]
    DEFAULT_BLOOD_PRESSURE_NORMAL = [90, 120]
    DEFAULT_HEART_RATE_NORMAL = [60, 100]

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load healthcare thresholds from config."""
        self.bmi_healthy_range = config.get_threshold(
            'healthcare', 'bmi_healthy_range', self.client_name
        ) or self.DEFAULT_BMI_HEALTHY_RANGE

        self.blood_pressure_normal = config.get_threshold(
            'healthcare', 'blood_pressure_normal', self.client_name
        ) or self.DEFAULT_BLOOD_PRESSURE_NORMAL

        self.heart_rate_normal = config.get_threshold(
            'healthcare', 'heart_rate_normal', self.client_name
        ) or self.DEFAULT_HEART_RATE_NORMAL

        self.risk_factors = config.get_threshold(
            'healthcare', 'risk_factors', self.client_name
        ) or ['age', 'bmi', 'blood_pressure', 'cholesterol']

    def detect(self) -> bool:
        """Detect if this is healthcare data."""
        text_cols = [col.lower() for col in self.profile.text_columns]
        numeric_cols = [col.lower() for col in self.profile.numeric_columns]

        keywords = ['patient', 'diagnosis', 'blood', 'pressure', 'bmi', 'heart', 'cholesterol', 'glucose']
        has_keywords = any(k in ' '.join(text_cols + numeric_cols).lower() for k in keywords)

        return has_keywords

    def get_section_header(self) -> str:
        return "HEALTHCARE ANALYSIS"

    def get_priority(self) -> int:
        return 65

    def generate_content(self) -> str:
        """Generate healthcare-specific content."""
        df = self.df.copy()

        age_col = self._find_age_column(df)
        bmi_col = self._find_bmi_column(df)
        diagnosis_col = self._find_diagnosis_column(df)

        content = []

        content.append(self._get_config_summary())
        content.append(self._get_patient_summary(df, age_col, bmi_col))
        content.append(self._get_risk_assessment_text(df, age_col, bmi_col, diagnosis_col))
        content.append(self._get_diagnosis_breakdown_text(df, diagnosis_col))

        return "\n\n".join(content)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return healthcare-specific Excel sheets."""
        df = self.df.copy()
        diagnosis_col = self._find_diagnosis_column(df)

        sheets = {}

        if diagnosis_col:
            diagnosis_df = df[diagnosis_col].value_counts().reset_index()
            diagnosis_df.columns = ['Diagnosis', 'Count']
            sheets['Diagnosis Breakdown'] = diagnosis_df

        return sheets

    # ─── Helper Methods ──────────────────────────────────────────

    def _get_config_summary(self) -> str:
        return f"""
  CONFIGURATION SUMMARY
  {'-' * 40}
    Client               : {self.client_name or 'Default'}
    BMI Healthy Range    : {self.bmi_healthy_range}
    BP Normal Range      : {self.blood_pressure_normal}
    Heart Rate Normal    : {self.heart_rate_normal}
"""

    def _find_age_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'age' in col.lower():
                return col
        return None

    def _find_bmi_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'bmi' in col.lower():
                return col
        return None

    def _find_diagnosis_column(self, df: pd.DataFrame) -> str:
        for col in df.columns:
            if 'diagnosis' in col.lower() or 'condition' in col.lower():
                return col
        return None

    def _get_patient_summary(self, df: pd.DataFrame, age_col: str, bmi_col: str) -> str:
        lines = ["  PATIENT SUMMARY", "  " + "-" * 40]

        total = len(df)
        lines.append(f"    Total Patients    : {total}")

        if age_col:
            avg_age = df[age_col].mean()
            min_age = df[age_col].min()
            max_age = df[age_col].max()
            lines.append(f"    Age Range         : {min_age:.0f} - {max_age:.0f} (avg: {avg_age:.1f})")

        if bmi_col:
            avg_bmi = df[bmi_col].mean()
            lines.append(f"    Average BMI       : {avg_bmi:.1f}")

        return "\n".join(lines)

    def _get_risk_assessment_text(self, df: pd.DataFrame, age_col: str, bmi_col: str, diagnosis_col: str) -> str:
        lines = ["  RISK ASSESSMENT", "  " + "-" * 40]

        # Count high risk patients (elderly + high BMI)
        high_risk = 0
        if age_col and bmi_col:
            high_risk = len(df[(df[age_col] > 60) & (df[bmi_col] > 30)])
            lines.append(f"    High Risk Patients : {high_risk}")

        if diagnosis_col:
            diagnosis_counts = df[diagnosis_col].value_counts()
            for diag, count in diagnosis_counts.head(5).items():
                pct = count / len(df) * 100
                lines.append(f"    {diag:<20}: {count} ({pct:.0f}%)")

        return "\n".join(lines)

    def _get_diagnosis_breakdown_text(self, df: pd.DataFrame, diagnosis_col: str) -> str:
        if not diagnosis_col:
            return "  No diagnosis column found."

        breakdown = df[diagnosis_col].value_counts()

        lines = ["  DIAGNOSIS BREAKDOWN", "  " + "-" * 40]
        for diag, count in breakdown.head(10).items():
            pct = count / len(df) * 100
            bar = "█" * int(pct / 2)
            lines.append(f"    {diag:<20}: {count:>3} ({pct:>5.1f}%) {bar}")

        return "\n".join(lines)