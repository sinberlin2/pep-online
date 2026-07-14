"""JSON schemas for brand_run and brand_identity outputs."""

# ---------------------------------------------------------------------------
# brand_identity sub-schemas (inlined — OpenAI strict mode has no $ref)
# ---------------------------------------------------------------------------

_LOGO_IMAGE_PROMPT = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "prompt": {"type": "string"},
        "size": {"type": "string"},
    },
    "required": ["id", "name", "prompt", "size"],
}

_COLOR_SWATCH = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "name": {"type": "string"},
        "hex": {"type": "string"},
        "role": {"type": "string"},
        "inspiredBy": {"type": "string"},
    },
    "required": ["name", "hex", "role", "inspiredBy"],
}

# One recurring visual "look" observed across competitor packs/sites. Extracted from
# the attached competitor images BEFORE the palette is invented, so the palette can be
# grounded in a named theme (e.g. social -> "white base + shiny colour element").
_DESIGN_THEME = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string", "description": "Short evocative label, e.g. 'White base + shiny accent'."},
        "baseTreatment": {"type": "string", "description": "Base/background treatment: white/light, solid/saturated colour, gradient, photographic, etc."},
        "colorTreatment": {"type": "string", "description": "How colour is used: pastel, bright/saturated, muted, monochrome, duotone."},
        "finish": {"type": "string", "description": "Surface finish/texture: shiny, gloss, metallic, matte, satin, or a mix."},
        "typographyFeel": {"type": "string", "description": "Type character: bold sans, elegant serif, playful, condensed, etc."},
        "energy": {"type": "string", "description": "Overall energy/mood the look projects."},
        "exampleBrands": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "brand": {"type": "string"},
                    "variant": {"type": "string", "description": "Specific product line/variant if the look is line-specific (e.g. 'Juuz shiny line'); empty string otherwise."},
                },
                "required": ["brand", "variant"],
            },
        },
        "positioningLeaning": {"type": "integer", "description": "Which positioning this look most reads as: 1=functional, 2=lifestyle/wellness, 3=social."},
        "relevanceToActiveDirection": {"type": "string", "description": "How much and in what way this theme applies to PEP's active direction."},
    },
    "required": [
        "id", "name", "baseTreatment", "colorTreatment", "finish",
        "typographyFeel", "energy", "exampleBrands", "positioningLeaning",
        "relevanceToActiveDirection",
    ],
}

_FONT_ENTRY = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "family": {"type": "string"},
        "weight": {"type": "string"},
        "usage": {"type": "string"},
        "webFallback": {"type": "string"},
        "licenseNote": {"type": "string"},
    },
    "required": ["family", "weight", "usage", "webFallback", "licenseNote"],
}

_MOCKUP_BRIEF = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "context": {"type": "string"},
        "layout": {"type": "string"},
        "colorUsage": {"type": "string"},
        "typographyUsage": {"type": "string"},
        "imagePrompt": {"type": "string"},
        "inspiredBy": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["id", "name", "context", "layout", "colorUsage", "typographyUsage", "imagePrompt", "inspiredBy"],
}

BRAND_IDENTITY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "observedDesignThemes": {
            "type": "array",
            "items": _DESIGN_THEME,
            "description": "2-4 recurring visual looks observed across the attached competitor images, each tagged with the positioning it most reads as.",
        },
    },
    "required": ["observedDesignThemes"],
}

# ---------------------------------------------------------------------------
# brand_run schema
# ---------------------------------------------------------------------------

BRAND_BUNDLE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "positioning": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "version": {"type": "integer"},
                "activeId": {"type": "integer"},
                "activeSlug": {"type": "string"},
                "activeName": {"type": "string"},
                "brand": {"type": "string"},
                "domain": {"type": "string"},
                "oneLiner": {"type": "string"},
                "positioningStatement": {"type": "string"},
                "audience": {"type": "array", "items": {"type": "string"}},
                "occasions": {"type": "array", "items": {"type": "string"}},
                "personalityAdjectives": {"type": "array", "items": {"type": "string"}},
                "voice": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "tone": {"type": "string"},
                        "tagline": {"type": "string"},
                        "avoidWords": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["tone", "tagline", "avoidWords"],
                },
                "visual": {
                    "type": "object",
                    "additionalProperties": False,
                    # Design tokens (colours, hex, fonts) are intentionally absent — they are
                    # invented downstream by brand_identity from a clean slate. mood/designConcept/
                    # rejectLooks describe emotional/occasion/layout feel only, never colours/fonts.
                    "properties": {
                        "mood": {"type": "string"},
                        "photography": {"type": "string"},
                        "designConcept": {"type": "string"},
                        "rejectLooks": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": [
                        "mood",
                        "photography",
                        "designConcept",
                        "rejectLooks",
                    ],
                },
                "inLineBrands": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "url": {"type": "string"},
                            "category": {"type": "string"},
                            "drinkTypeFit": {"type": "string"},
                            "why": {"type": "string"},
                            "adjectives": {"type": "array", "items": {"type": "string"}},
                            "designPatterns": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": [
                            "name",
                            "why",
                            "adjectives",
                            "designPatterns",
                            "category",
                            "url",
                            "drinkTypeFit",
                        ],
                    },
                },
                "positioningFitTypeMismatch": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "url": {"type": "string"},
                            "category": {"type": "string"},
                            "drinkTypeFit": {"type": "string"},
                            "whyBrandingFits": {"type": "string"},
                            "positioningMismatch": {"type": "string"},
                            "typeMismatch": {"type": "string"},
                        },
                        "required": [
                            "name",
                            "url",
                            "category",
                            "drinkTypeFit",
                            "whyBrandingFits",
                            "positioningMismatch",
                            "typeMismatch",
                        ],
                    },
                },
                "peerBrandsOtherPositionings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "positioning_id": {"type": "integer"},
                            "drinkTypeFit": {"type": "string"},
                            "positioningMismatch": {"type": "string"},
                            "whyNotActive": {"type": "string"},
                        },
                        "required": [
                            "name",
                            "positioning_id",
                            "drinkTypeFit",
                            "positioningMismatch",
                            "whyNotActive",
                        ],
                    },
                },
                "antiReferences": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "why": {"type": "string"},
                        },
                        "required": ["name", "why"],
                    },
                },
                "layoutOnlyReferences": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "name": {"type": "string"},
                            "url": {"type": "string"},
                            "patterns": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["name", "patterns", "url"],
                    },
                },
                "brandFitRules": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "version",
                "activeId",
                "activeSlug",
                "activeName",
                "brand",
                "domain",
                "oneLiner",
                "positioningStatement",
                "audience",
                "occasions",
                "personalityAdjectives",
                "voice",
                "visual",
                "inLineBrands",
                "positioningFitTypeMismatch",
                "peerBrandsOtherPositionings",
                "antiReferences",
                "layoutOnlyReferences",
                "brandFitRules",
            ],
        },
        "brandGuidelinesMarkdown": {"type": "string"},
    },
    "required": ["positioning", "brandGuidelinesMarkdown"],
}
