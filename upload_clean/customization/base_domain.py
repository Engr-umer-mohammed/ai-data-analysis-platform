# customization/base_domain.py
# Base class for all domain-specific customizations

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseDomain(ABC):
    """
    Base class for domain-specific report customizations.
    Every domain adds its own section to the report.
    """

    def __init__(self, profile, stats, df, client_name: str = None):
        """
        Args:
            profile: DatasetProfile from data_loader
            stats: AnalysisResult from statistical_analyzer
            df: pandas DataFrame (cleaned)
            client_name: Optional client name for config loading
        """
        self.profile = profile
        self.stats = stats
        self.df = df
        self.client_name = client_name

    @abstractmethod
    def get_section_header(self) -> str:
        """Return the header for this domain section."""
        pass

    @abstractmethod
    def generate_content(self) -> str:
        """Generate the content for this domain section."""
        pass

    @abstractmethod
    def get_excel_sheets(self) -> Dict[str, Any]:
        """Return Excel sheets for this domain."""
        pass

    def get_priority(self) -> int:
        """Higher priority = appears higher in report. Default 50."""
        return 50

    def get_description(self) -> str:
        """Return a human-readable description of this domain."""
        return "Generic data domain"

    # ─── Helper Methods ──────────────────────────────────────────

    def _get_all_columns(self) -> list:
        """Get ALL column names (text + numeric + datetime)."""
        return (
            self.profile.text_columns +
            self.profile.numeric_columns +
            self.profile.datetime_columns
        )

    def _has_keyword_in_any_column(self, keywords: list) -> bool:
        """Check if ANY keyword appears in ANY column name."""
        all_cols_text = " ".join(self._get_all_columns()).lower()
        return any(k in all_cols_text for k in keywords)

    def _get_config_value(self, key: str, default: Any) -> Any:
        """Get a configuration value with fallback."""
        return self.config.get(key, default) if hasattr(self, 'config') else default