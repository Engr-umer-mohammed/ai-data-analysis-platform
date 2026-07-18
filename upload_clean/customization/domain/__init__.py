# customization/domains/__init__.py
# Domain package — marks this folder as a Python package
# Exports all domain classes for explicit imports

from .education import EducationDomain
from .sales import SalesDomain
from .healthcare import HealthcareDomain
from .manufacturing import ManufacturingDomain
from .finance import FinanceDomain
from .hr import HRDomain
from .logistics import LogisticsDomain
from .sports import SportsDomain
from .marketing import  MarketingDomain

__all__ = [
    'EducationDomain',
    'SalesDomain',
    'HealthcareDomain',
    'ManufacturingDomain',
    'FinanceDomain',
    'HRDomain',
    'LogisticsDomain',
    'SportsDomain',
    'MarketingDomain',
]