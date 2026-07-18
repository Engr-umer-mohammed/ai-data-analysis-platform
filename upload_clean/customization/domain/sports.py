# customization/sports.py
# Sports domain customization — player/team performance

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


class SportsDomain(BaseDomain):
    """Sports-specific report sections for player/team data."""

    DEFAULT_WIN_TARGET = 50
    DEFAULT_GOAL_TARGET = 2
    DEFAULT_ASSIST_RATIO = 0.5

    def __init__(self, profile, stats, df, client_name: str = None):
        super().__init__(profile, stats, df)
        self.client_name = client_name
        self._load_config()

    def _load_config(self):
        """Load sports thresholds from config."""
        self.win_target = config.get_threshold(
            'sport', 'win_target', self.client_name
        ) or self.DEFAULT_WIN_TARGET

        self.goal_target