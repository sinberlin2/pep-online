"""Canonical paths for company inputs and branding outputs."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Company — product definition, positioning options, competition research
COMPANY = ROOT / "company"
PRODUCT_PROFILE = COMPANY / "product-profile.json"
CHOICE = COMPANY / "choice.json"
COMPANY_ASSETS = COMPANY / "assets"
POSITIONING = COMPANY / "positioning"
POSITIONING_SOURCE_CSV = POSITIONING / "product-positioning-options.csv"
POSITIONING_OPTIONS = COMPANY / "positioning-options.json"
COMPETITION = COMPANY / "competition"
COMPETITION_SOURCES = COMPETITION / "sources"
CHARACTERISTICS_CSV = COMPETITION / "characteristics.csv"
CHARACTERISTICS_TEMPLATE = COMPETITION / "characteristics.template.csv"
MANUAL_COMPETITORS = COMPETITION / "manual-competitors.csv"
COMPETITION_EXTRACTED = COMPETITION / "competition-extracted.json"
ENRICHMENT_LOG = COMPETITION / "competitor-enrichment-log.json"
SCHEMAS = COMPANY / "schemas"
RESEARCH_BUNDLE = COMPANY / "research-bundle.md"

# Branding module (outputs + provided design assets)
BRAND = ROOT / "brand"
PROVIDED = BRAND / "provided"
DIRECTIONS = BRAND / "directions"
BRANDINGS_INDEX = BRAND / "brandings.json"
RUNS = BRAND / "runs"


def direction_strategy(slug: str) -> Path:
    """brand/directions/<slug>/strategy/ — brand_run outputs."""
    return DIRECTIONS / slug / "strategy"


def direction_identity(slug: str) -> Path:
    """brand/directions/<slug>/identity/ — brand_identity outputs."""
    return DIRECTIONS / slug / "identity"


def direction_package(slug: str) -> Path:
    """brand/directions/<slug>/brand-package/ — brand_package outputs."""
    return DIRECTIONS / slug / "brand-package"

# Legacy aliases (scripts migrating off research/)
MURAL = POSITIONING
MURAL_SOURCES = POSITIONING
COMPETITORS = COMPETITION
RESEARCH = COMPANY
