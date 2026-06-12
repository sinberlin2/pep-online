"""JSON schemas for OpenAI structured outputs (strict mode — no $ref)."""

# --- Hero composition agent ---------------------------------------------------

HERO_LAYER = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        # Asset key from the allow-listed manifest (e.g. can, glass,
        # lemon-slice, orange-wedge, mint-large). Never a raw file path.
        "key": {"type": "string"},
        # Width of the layer as a percentage of the hero canvas width.
        "widthPct": {"type": "number"},
        # Horizontal centre of the layer, 0 (left edge) to 100 (right edge).
        "centerXPct": {"type": "number"},
        # Distance from the layer's bottom edge to the canvas bottom, as a
        # percentage of canvas height. May be negative to bleed off-canvas.
        "bottomPct": {"type": "number"},
        # Stacking order (higher = in front).
        "z": {"type": "integer"},
        "rotationDeg": {"type": "number"},
        "opacity": {"type": "number"},
    },
    "required": [
        "key",
        "widthPct",
        "centerXPct",
        "bottomPct",
        "z",
        "rotationDeg",
        "opacity",
    ],
}

HERO_LAYOUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string"},
        "label": {"type": "string"},
        "canvasBackground": {"type": "string"},
        "layers": {"type": "array", "items": HERO_LAYER},
        "rationale": {"type": "string"},
    },
    "required": ["id", "label", "canvasBackground", "layers", "rationale"],
}

HERO_REVIEW_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "verdict": {"type": "string", "enum": ["pass", "revise"]},
        "overallScore": {"type": "integer"},
        "scores": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "composition": {"type": "integer"},
                "overlap": {"type": "integer"},
                "balance": {"type": "integer"},
                "realism": {"type": "integer"},
                "brandFit": {"type": "integer"},
            },
            "required": [
                "composition",
                "overlap",
                "balance",
                "realism",
                "brandFit",
            ],
        },
        "strengths": {"type": "array", "items": {"type": "string"}},
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                    },
                    "finding": {"type": "string"},
                    "suggestion": {"type": "string"},
                },
                "required": ["severity", "finding", "suggestion"],
            },
        },
        "revisionBrief": {"type": "string"},
    },
    "required": [
        "verdict",
        "overallScore",
        "scores",
        "strengths",
        "issues",
        "revisionBrief",
    ],
}



SECTION = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string"},
        "purpose": {"type": "string"},
        "layoutPattern": {"type": "string"},
        "copyTone": {"type": "string"},
        "imagery": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    },
    "required": ["id", "purpose", "layoutPattern", "copyTone", "imagery", "notes"],
}

PAGE = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "narrativeArc": {"type": "array", "items": {"type": "string"}},
        "sections": {"type": "array", "items": SECTION},
        "visualLinkToIndex": {"type": "string"},
    },
    "required": ["narrativeArc", "sections", "visualLinkToIndex"],
}

CONCEPT_BUNDLE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "siteConcept": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "id": {"type": "string"},
                "positioning": {"type": "string"},
                "inspiredBy": {"type": "array", "items": {"type": "string"}},
                "differentiators": {"type": "array", "items": {"type": "string"}},
                "anchoredReferences": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "url": {"type": "string"},
                            "label": {"type": "string"},
                            "nameCollision": {"type": "boolean"},
                            "patternsToAdapt": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["url", "label", "nameCollision", "patternsToAdapt"],
                    },
                },
                "pages": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "index": PAGE,
                        "forVenues": PAGE,
                    },
                    "required": ["index", "forVenues"],
                },
                "designTokens": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "colorsFromBrandJson": {"type": "boolean"},
                        "spacingScale": {"type": "string"},
                        "heroDensity": {"type": "string"},
                        "sectionRhythm": {"type": "string"},
                    },
                    "required": [
                        "colorsFromBrandJson",
                        "spacingScale",
                        "heroDensity",
                        "sectionRhythm",
                    ],
                },
                "typography": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "display": {"type": "string"},
                        "badges": {"type": "string"},
                        "script": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["display", "badges", "script", "body"],
                },
                "harmonyPrinciples": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "avoid": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "id",
                "positioning",
                "inspiredBy",
                "differentiators",
                "anchoredReferences",
                "pages",
                "designTokens",
                "typography",
                "harmonyPrinciples",
                "avoid",
            ],
        },
        "conceptMarkdown": {"type": "string"},
        "discoveredReferences": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "searchQueriesUsed": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "discovered": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "url": {"type": "string"},
                            "brandName": {"type": "string"},
                            "lane": {"type": "string"},
                            "relevance": {"type": "string"},
                            "patternsToAdapt": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "avoid": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": [
                            "url",
                            "brandName",
                            "lane",
                            "relevance",
                            "patternsToAdapt",
                            "avoid",
                        ],
                    },
                },
            },
            "required": ["searchQueriesUsed", "discovered"],
        },
    },
    "required": ["siteConcept", "conceptMarkdown", "discoveredReferences"],
}
