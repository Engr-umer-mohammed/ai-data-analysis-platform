# customization/domain_registry.py
# Auto-discovery and registration of all domain customizations

from customization.domains.education import EducationDomain
from customization.domains.finance import FinanceDomain
from customization.domains.healthcare import HealthcareDomain
from customization.domains.hr import HRDomain
from customization.domains.logistics import LogisticsDomain
from customization.domains.manufacturing import ManufacturingDomain
from customization.domains.marketing import MarketingDomain
from customization.domains.real_estate import RealEstateDomain
from customization.domains.sales import SalesDomain

# ─── NEW DOMAINS ────────────────────────────────────────────────
from customization.domains.telecommunications import TelecommunicationsDomain
from customization.domains.hospitality import HospitalityDomain
from customization.domains.ecommerce import EcommerceDomain
from customization.domains.insurance import InsuranceDomain
from customization.domains.it_devops import ITDevOpsDomain
from customization.domains.social_media import SocialMediaDomain
from customization.domains.energy import EnergyDomain
from customization.domains.retail import RetailDomain
# from customization.domains.sports import SportsDomain  # ← Commented out (not fully implemented)


def get_all_domains():
    """
    Return all available domains.
    Add new domains here as you create them.
    """
    return {
        # ─── Core Domains ──────────────────────────────────────
        EducationDomain,          # Student data
        SalesDomain,              # Sales/revenue data
        HealthcareDomain,         # Patient/medical data
        ManufacturingDomain,      # Production/quality data
        FinanceDomain,            # Financial data
        HRDomain,                 # Employee/HR data
        LogisticsDomain,          # Supply chain data
        MarketingDomain,          # Marketing data
        RealEstateDomain,         # Property data

        # ─── New Domains ──────────────────────────────────────
        TelecommunicationsDomain, # Telecom / ITU-GSMA Standards
        HospitalityDomain,        # Hotel / STR Global Standards
        EcommerceDomain,          # E-Commerce / Shopify-Baymard
        InsuranceDomain,          # Insurance / NAIC-Actuarial
        ITDevOpsDomain,           # IT/DevOps / DORA-SRE
        SocialMediaDomain,        # Social Media / Platform Standards
        EnergyDomain,             # Energy / IEA-EIA Standards
        RetailDomain,             # Retail / NRF Standards

        # SportsDomain,           # ← Commented out (not fully implemented)
    }


def get_applicable_domains(profile, stats, df):
    """
    Get all domains that apply to the current data.
    Returns a list of instantiated domain objects.
    """
    applicable = []

    for DomainClass in get_all_domains():
        try:
            domain = DomainClass(profile, stats, df)
            if domain.detect():
                applicable.append(domain)
        except Exception as e:
            # If a domain fails to detect, skip it quietly
            print(f"Warning: Domain {DomainClass.__name__} failed: {e}")
            continue

    # Sort by priority (higher first)
    applicable.sort(key=lambda d: d.get_priority(), reverse=True)

    return applicable