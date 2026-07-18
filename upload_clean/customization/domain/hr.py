# customization/domains/hr.py
# HR / People domain — employees, departments, retention

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


class HRDomain(BaseDomain):
    """HR-specific report sections."""

    DEFAULT_ATTENDANCE_TARGET = 95
    DEFAULT_TURNOVER_THRESHOLD = 0.15

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load HR thresholds from config."""
        self.attendance_target = config.get_threshold(
            'hr', 'attendance_target', self.client_name
        ) or self.DEFAULT_ATTENDANCE_TARGET

        self.turnover_threshold = config.get_threshold(
            'hr', 'turnover_threshold', self.client_name
        ) or self.DEFAULT_TURNOVER_THRESHOLD

    def detect(self) -> bool:
        """Detect if this is HR data."""
        text_cols = [col.lower() for col in self.profile.text_columns]
        numeric_cols = [col.lower() for col in self.profile.numeric_columns]

        hr_keywords = ['employee', 'hire', 'salary', 'department', 'manager',
                      'retention', 'performance', 'attendance', 'absent']
        hr_metrics = ['salary', 'bonus', 'tenure', 'years']

        has_hr = any(k in ' '.join(text_cols).lower() for k in hr_keywords)
        has_metrics = any(k in ' '.join(numeric_cols).lower() for k in hr_metrics)

        return has_hr or has_metrics

    def get_section_header(self) -> str:
        return "HUMAN RESOURCES ANALYSIS"

    def get_priority(self) -> int:
        return 55

    def get_description(self) -> str:
        return f"HR data with workforce analytics (Attendance target: {self.attendance_target}%)"

    def generate_content(self) -> str:
        """Generate HR-specific content."""
        df = self.df.copy()

        content = []

        content.append(self._get_config_summary())
        content.append(self._get_employee_summary(df))
        content.append(self._get_salary_analysis(df))
        content.append(self._get_department_breakdown(df))
        content.append(self._get_tenure_analysis(df))

        return "\n\n".join(content)

    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return HR-specific Excel sheets."""
        df = self.df.copy()
        sheets = {}

        # Department breakdown sheet
        dept_cols = [c for c in df.columns if 'department' in c.lower() or 'team' in c.lower()]
        if dept_cols:
            dept_df = df[dept_cols[0]].value_counts().reset_index()
            dept_df.columns = ['Department', 'Count']
            sheets['Department Breakdown'] = dept_df

        # Salary summary sheet
        salary_cols = [c for c in df.columns if any(k in c.lower() for k in
                       ['salary', 'compensation', 'pay', 'wage'])]
        if salary_cols:
            salary_df = df[salary_cols[0]].describe().reset_index()
            salary_df.columns = ['Metric', 'Value']
            sheets['Salary Summary'] = salary_df

        return sheets

    def _get_config_summary(self) -> str:
        """Show current configuration."""
        return f"""
  CONFIGURATION SUMMARY
  {'-' * 40}
    Client               : {self.client_name or 'Default'}
    Attendance Target    : {self.attendance_target}%
    Turnover Threshold   : {self.turnover_threshold * 100:.0f}%
"""

    def _get_employee_summary(self, df: pd.DataFrame) -> str:
        """Generate employee summary."""
        total_employees = len(df)

        return f"""
  EMPLOYEE SUMMARY
  {'-' * 40}
    Total Employees : {total_employees:,}
    Total Records   : {len(df):,}
"""

    def _get_salary_analysis(self, df: pd.DataFrame) -> str:
        """Generate salary analysis."""
        salary_cols = [c for c in df.columns if any(k in c.lower() for k in
                       ['salary', 'compensation', 'pay', 'wage'])]

        if not salary_cols:
            return "  No salary columns detected."

        col = salary_cols[0]
        avg = df[col].mean()
        min_val = df[col].min()
        max_val = df[col].max()
        median = df[col].median()

        return f"""
  SALARY ANALYSIS
  {'-' * 40}
    Average Salary : ${avg:,.2f}
    Median Salary  : ${median:,.2f}
    Minimum Salary : ${min_val:,.2f}
    Maximum Salary : ${max_val:,.2f}
"""

    def _get_department_breakdown(self, df: pd.DataFrame) -> str:
        """Generate department breakdown."""
        dept_cols = [c for c in df.columns if 'department' in c.lower() or 'team' in c.lower()]

        if not dept_cols:
            return "  No department columns detected."

        breakdown = df[dept_cols[0]].value_counts()

        lines = ["  DEPARTMENT BREAKDOWN", "  " + "-" * 40]
        for dept, count in breakdown.items():
            pct = count / len(df) * 100
            bar = "█" * int(pct / 2)
            lines.append(f"    {dept:<20}: {count:>3} ({pct:>5.1f}%) {bar}")

        return "\n".join(lines)

    def _get_tenure_analysis(self, df: pd.DataFrame) -> str:
        """Generate tenure analysis."""
        tenure_cols = [c for c in df.columns if 'tenure' in c.lower() or 'years' in c.lower()]

        if not tenure_cols:
            return "  No tenure columns detected."

        col = tenure_cols[0]
        avg_tenure = df[col].mean()
        min_tenure = df[col].min()
        max_tenure = df[col].max()

        return f"""
  TENURE ANALYSIS
  {'-' * 40}
    Average Tenure : {avg_tenure:.1f} years
    Minimum Tenure : {min_tenure:.1f} years
    Maximum Tenure : {max_tenure:.1f} years
"""