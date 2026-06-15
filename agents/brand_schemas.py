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
        "colorPalette": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "primary": {"type": "array", "items": _COLOR_SWATCH},
                "secondary": {"type": "array", "items": _COLOR_SWATCH},
                "text": {"type": "array", "items": _COLOR_SWATCH},
                "background": {"type": "array", "items": _COLOR_SWATCH},
                "competitorInspiration": {"type": "string"},
                "rejectPatterns": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["primary", "secondary", "text", "background", "competitorInspiration", "rejectPatterns"],
        },
        "typographySystem": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "display": _FONT_ENTRY,
                "body": _FONT_ENTRY,
                "script": _FONT_ENTRY,
                "badge": _FONT_ENTRY,
                "pairingRationale": {"type": "string"},
                "competitorInspiration": {"type": "string"},
            },
            "required": ["display", "body", "script", "badge", "pairingRationale", "competitorInspiration"],
        },
        "mockupBriefs": {
            "type": "array",
            "items": _MOCKUP_BRIEF,
        },
        "identityMarkdown": {"type": "string"},
        "logoBrief": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "concept": {"type": "string"},
                "markDescription": {"type": "string"},
                "imagePrompts": {"type": "array", "items": _LOGO_IMAGE_PROMPT},
            },
            "required": ["concept", "markDescription", "imagePrompts"],
        },
        "boardBrief": {
            # Direction-appropriate elements for the single editorial brand board.
            # Grounded in the positioning so each direction (functional/lifestyle/
            # social) gets its own motifs and badges, e.g. social -> "0.0%",
            # "social serve" + cocktail garnish; functional -> recovery/macro cues.
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "artDirection": {
                    "type": "string",
                    "description": "One sentence describing the board's visual feel for THIS direction (drawn from the positioning mood/designConcept). No colour names or font names.",
                },
                "motifs": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-6 reusable illustration elements suited to this direction (e.g. mango slice, citrus twist, cocktail garnish, sparkle). No leaves/botanical marks.",
                },
                "badges": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2-4 SHORT direction-appropriate badge labels justified by the positioning (e.g. social -> '0.0%', 'social serve'; functional -> 'high protein'). Do NOT repeat the factual product badges (protein/calories/gluten-free) which are added automatically.",
                },
            },
            "required": ["artDirection", "motifs", "badges"],
        },
    },
    "required": ["colorPalette", "typographySystem", "mockupBriefs", "identityMarkdown", "logoBrief", "boardBrief"],
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
