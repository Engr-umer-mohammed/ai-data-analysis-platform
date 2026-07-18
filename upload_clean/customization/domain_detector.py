# customization/domain_detector.py
# Unified Domain Detection — Professional Version
# Merged with new structure requirements
# Version 2.0 — Production Ready

import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd
import re

logger = logging.getLogger(__name__)


class DomainDetector:
    """
    Unified domain detection system.
    - Multiple detection methods (column names, values, statistics)
    - Confidence scoring (0-1)
    - Explicit domain override via separate method
    - Rich output with descriptions and icons
    - Threshold-based fallback to 'general'
    """

    # ─── DOMAIN CONFIGURATION ──────────────────────────────

    DOMAIN_CONFIG = {
        'education': {
            'keywords': ['student', 'score', 'grade', 'mark', 'attendance', 'subject', 'exam', 'gpa',
                         'math', 'science', 'english', 'history', 'art', 'reading'],
            'icon': '🎓',
            'description': 'Educational data — adds grading, rankings, pass/fail metrics.'
        },
        'healthcare': {
            'keywords': ['patient', 'diagnosis', 'blood', 'pressure', 'glucose', 'bmi', 'medication',
                         'hospital', 'doctor', 'heart', 'cholesterol', 'temperature', 'pulse'],
            'icon': '🏥',
            'description': 'Healthcare data — adds patient outcomes and treatment effectiveness.'
        },
        'sales': {
            'keywords': ['sales', 'revenue', 'profit', 'customer', 'order', 'product', 'region',
                         'invoice', 'price', 'quantity', 'discount', 'margin'],
            'icon': '📈',
            'description': 'Sales data — adds performance analysis and KPI dashboards.'
        },
        'manufacturing': {
            'keywords': ['defect', 'yield', 'oee', 'downtime', 'production', 'quality', 'shift',
                         'machine', 'reject', 'throughput', 'cycle_time', 'efficiency'],
            'icon': '🏭',
            'description': 'Manufacturing data — adds efficiency and quality analysis.'
        },
        'logistics': {
            'keywords': ['delivery', 'shipment', 'route', 'distance', 'weight', 'origin',
                         'destination', 'delay', 'freight', 'carrier', 'warehouse', 'order'],
            'icon': '🚚',
            'description': 'Logistics data — adds delivery performance and route analysis.'
        },
        'hr': {
            'keywords': ['employee', 'salary', 'department', 'tenure', 'turnover', 'headcount',
                         'leave', 'hire', 'performance', 'review', 'bonus', 'payroll'],
            'icon': '👤',
            'description': 'HR data — adds workforce analytics and retention insights.'
        },
        'finance': {
            'keywords': ['revenue', 'profit', 'expense', 'cost', 'margin', 'budget', 'forecast',
                         'actual', 'variance', 'roi', 'ebitda', 'cash', 'asset', 'liability'],
            'icon': '💰',
            'description': 'Finance data — adds financial ratio analysis and risk metrics.'
        },
        'demographics': {
            'keywords': ['age', 'gender', 'income', 'zip', 'address', 'city', 'state',
                         'population', 'household', 'employment', 'race', 'ethnicity'],
            'icon': '🌍',
            'description': 'Demographic data — adds population and socioeconomic analysis.'
        },
        'sports': {  # ← CHANGED: 'sport' → 'sports' to match folder name
            'keywords': ['player', 'team', 'match', 'goal', 'win', 'loss', 'draw', 'season',
                         'league', 'points', 'assists', 'tackles', 'speed', 'rating'],
            'icon': '⚽',
            'description': 'Sports data — adds player performance and team analysis.'
        }
    }

    # ─── MAIN DETECTION METHOD ─────────────────────────────

    @classmethod
    def detect(
        cls,
        profile,
        threshold: int = 2
    ) -> Tuple[str, float]:
        """
        Detect domain with optional explicit override.

        Args:
            profile: DatasetProfile from data_loader
            threshold: Minimum keyword score to accept (default: 2)

        Returns:
            Tuple of (domain_name, confidence) where confidence is 0-1
        """
        if profile is None or profile.column_names is None:
            logger.info("No profile provided. Using general analysis.")
            return "general", 0.0

        # ─── Column Name Matching ────────────────────────────
        all_cols = " ".join(profile.column_names).lower()
        scores = {}

        for domain, config in cls.DOMAIN_CONFIG.items():
            score = sum(1 for kw in config['keywords'] if kw in all_cols)
            if score > 0:
                scores[domain] = score

        if not scores:
            logger.info("No domain detected. Using general analysis.")
            return "general", 0.0

        best_domain = max(scores, key=scores.get)
        best_score = scores[best_domain]

        # ─── Value Pattern Detection (If DataFrame Available) ──
        value_boost = 0
        if profile.dataframe is not None:
            value_boost = cls._check_value_patterns(profile.dataframe, best_domain)

        # ─── Combined Score ──────────────────────────────────
        combined_score = best_score + (value_boost * 1.5)

        if combined_score < threshold:
            logger.info(f"Domain signal weak (score={combined_score:.1f}). Using general.")
            return "general", 0.0

        # ─── Confidence (0-1) ────────────────────────────────
        confidence = min(combined_score / 8, 1.0)  # ← CHANGED: returns 0-1

        logger.info(f"Domain detected: '{best_domain}' (confidence={confidence:.1%})")
        return best_domain, confidence

    # ─── EXPLICIT OVERRIDE METHOD ────────────────────────────

    @classmethod
    def detect_with_override(
        cls,
        profile,
        explicit_domain: str,
        threshold: int = 2
    ) -> Tuple[str, float]:
        """
        Detect domain with manual override.

        Args:
            profile: DatasetProfile from data_loader
            explicit_domain: Manually set domain (skips detection)
            threshold: Minimum keyword score to accept (default: 2)

        Returns:
            Tuple of (domain_name, confidence) where confidence is 0-1
        """
        domain = explicit_domain.lower()
        if domain in cls.DOMAIN_CONFIG:
            logger.info(f"Domain explicitly set: {domain}")
            return domain, 1.0
        logger.warning(f"Domain '{domain}' not recognized. Running detection.")
        return cls.detect(profile, threshold)

    # ─── VALUE PATTERN DETECTION ─────────────────────────────

    @classmethod
    def _check_value_patterns(cls, df: pd.DataFrame, domain: str) -> float:
        """Check values for domain-specific patterns."""
        boost = 0

        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns

        # Education: check for score ranges (0-100)
        if domain == 'education':
            for col in numeric_cols:
                if len(df[col]) > 0:
                    col_min, col_max = df[col].min(), df[col].max()
                    if 0 <= col_min and col_max <= 100:
                        boost += 1
                        break

        # Sales: check for currency patterns
        if domain == 'sales':
            text_cols = df.select_dtypes(include=['object']).columns
            for col in text_cols:
                sample = df[col].dropna().astype(str).head(10)
                for val in sample:
                    if re.search(r'[\$€£]', val):
                        boost += 1
                        break

        return boost

    # ─── UTILITY METHODS ─────────────────────────────────────

    @classmethod
    def get_domain_config(cls, domain: str) -> Optional[Dict]:
        """Get configuration for a domain."""
        return cls.DOMAIN_CONFIG.get(domain)

    @classmethod
    def get_domain_description(cls, domain: str, confidence: float) -> str:
        """Get human-readable description."""
        if domain == "general":
            return "General data — standard statistical analysis applied."

        config = cls.DOMAIN_CONFIG.get(domain)
        if not config:
            return f"Domain '{domain}' not recognized."

        if confidence >= 0.7:
            level = "High confidence"
        elif confidence >= 0.4:
            level = "Medium confidence"
        else:
            level = "Low confidence"

        return f"[{level}] {config['icon']} {config['description']}"

    @classmethod
    def get_domain_icon(cls, domain: str) -> str:
        """Get the icon for a domain."""
        if domain == "general":
            return "📊"
        config = cls.DOMAIN_CONFIG.get(domain)
        return config['icon'] if config else "📊"

    @classmethod
    def get_all_domains(cls) -> List[str]:
        """Get list of all supported domains."""
        return list(cls.DOMAIN_CONFIG.keys())

    @classmethod
    def get_domain_summary(cls, profile, explicit_domain: Optional[str] = None) -> str:
        """
        Get a formatted summary of domain detection results.
        Useful for terminal/Telegram output.
        """
        if explicit_domain:
            domain, confidence = cls.detect_with_override(profile, explicit_domain)
        else:
            domain, confidence = cls.detect(profile)

        lines = [
            "=" * 55,
            "  DATA DOMAIN DETECTION REPORT",
            "=" * 55,
        ]

        if domain == "general":
            lines.append("\n  ℹ️  No specific domain detected.")
            lines.append("  Standard statistical analysis will be applied.")
            lines.append("\n" + "=" * 55)
            return "\n".join(lines)

        lines.append(f"\n  Detected Domain: {domain.upper()}")
        lines.append(f"  Confidence      : {confidence:.1%}")
        lines.append(f"\n  {cls.get_domain_description(domain, confidence)}")
        lines.append("\n" + "=" * 55)

        return "\n".join(lines)

    @classmethod
    def print_report(cls, profile, explicit_domain: Optional[str] = None) -> None:
        """Print formatted domain detection report to console."""
        print(cls.get_domain_summary(profile, explicit_domain))