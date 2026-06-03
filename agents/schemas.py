"""JSON schemas for OpenAI structured outputs (strict mode — no $ref)."""

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
