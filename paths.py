"""Canonical paths for the brand pipeline (inputs + outputs).

Layout (see docs/ASSETS.md):
  brand/inputs/     — all pipeline INPUTS (external-designs, competition, product/positioning)
  brand/directions/ — generated OUTPUTS per direction
  site/             — the deployed website (separate; not referenced from here)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Brand pipeline root
BRAND = ROOT / "brand"
INPUTS = BRAND / "inputs"

# --- Inputs: product definition, positioning, research ---
PRODUCT_PROFILE = INPUTS / "product-profile.json"
CHOICE = INPUTS / "choice.json"
POSITIONING = INPUTS / "positioning"
POSITIONING_SOURCE_CSV = POSITIONING / "product-positioning-options.csv"
POSITIONING_OPTIONS = INPUTS / "positioning-options.json"
SCHEMAS = INPUTS / "schemas"
RESEARCH_BUNDLE = INPUTS / "research-bundle.md"

# --- Inputs: competition research ---
COMPETITION = INPUTS / "competition"
COMPETITION_SOURCES = COMPETITION / "sources"
CHARACTERISTICS_CSV = COMPETITION / "characteristics.csv"
CHARACTERISTICS_TEMPLATE = COMPETITION / "characteristics.template.csv"
MANUAL_COMPETITORS = COMPETITION / "manual-competitors.csv"
COMPETITION_EXTRACTED = COMPETITION / "competition-extracted.json"
ENRICHMENT_LOG = COMPETITION / "competitor-enrichment-log.json"
COMPETITION_IMAGES = COMPETITION / "images"
COMPETITION_IMAGES_MANIFEST = COMPETITION_IMAGES / "images-manifest.json"
COMPETITION_IMAGE_OVERRIDES = COMPETITION / "image-overrides.json"

# --- Inputs: external designs (existing design sets to extract from, --from-design) ---
EXTERNAL_DESIGNS = INPUTS / "external-designs"
DEFAULT_DESIGN_SLUG = "pep-original"
PEP_ORIGINAL = EXTERNAL_DESIGNS / "pep-original"


def external_design_dir(slug: str) -> Path:
    """brand/inputs/external-designs/<slug> — a design set to extract from (--from-design)."""
    return EXTERNAL_DESIGNS / slug


def external_design_manifest(slug: str) -> Path:
    """Curated reference images fed to the vision model in extraction mode.

    Data-driven: edit this JSON (paths relative to the external-design folder) instead of
    the agent code. One manifest per design set.
    """
    return EXTERNAL_DESIGNS / slug / "extraction-images.json"


# --- Outputs: generated per direction ---
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


# --- Legacy aliases (back-compat for older references) ---
COMPANY = INPUTS
RESEARCH = INPUTS
MURAL = POSITIONING
MURAL_SOURCES = POSITIONING
COMPETITORS = COMPETITION
PROVIDED = EXTERNAL_DESIGNS
DEFAULT_PROVIDED_SLUG = DEFAULT_DESIGN_SLUG
provided_dir = external_design_dir
provided_extraction_manifest = external_design_manifest
