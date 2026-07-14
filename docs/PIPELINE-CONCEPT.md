# Brand pipeline — at a glance

The one-screen visual overview. Step-by-step commands are in
**[docs/WORKFLOW.md](WORKFLOW.md)**; repo layout in **[docs/ASSETS.md](ASSETS.md)**.

```mermaid
flowchart TB
    classDef in fill:#fff4d6,stroke:#e86a1a,color:#1f4d3a;
    classDef agent fill:#1f4d3a,stroke:#1f4d3a,color:#fff;
    classDef out fill:#e86a1a,stroke:#e86a1a,color:#fff;
    classDef step fill:#3b6ea5,stroke:#2b5580,color:#fff;
    classDef temp fill:#f0f0f0,stroke:#cccccc,color:#999999,stroke-dasharray:4 3;

    subgraph INPUTS["brand/inputs/"]
        PP[product-profile.json]:::in
        PO[positioning-options.json<br/>functional / lifestyle / social]:::in
        COMP[competition/<br/>characteristics.csv + images/]:::in
        EXT[external-designs/&lt;slug&gt;]:::in
    end

    subgraph PREP["inputs prep (scripts/)"]
        parse[brand:parse]
        pdf[brand:extract-pdf]
        enrich[brand:enrich]
        imgs[brand:competitor-images]
        merge[brand:merge → research-bundle.md]
    end

    RUN["brand_run<br/>(strategist)"]:::agent
    PKG["brand_package"]:::agent
    IMG["brand_images<br/>(brand board)"]:::agent
    ID["brand_identity<br/>(design themes)"]:::agent

    STRAT["directions/&lt;slug&gt;/strategy/<br/>positioning.json + brand-guidelines.md"]:::out
    THEMES["directions/&lt;slug&gt;/identity/<br/>design-themes.json"]:::out
    BOARD["identity/images/brand-board.png<br/>★ main deliverable"]:::out
    PKGOUT["brand-package/ + brandings.json<br/>(activeSlug)"]:::out
    SITE["site/public/<br/>(temporary hand-off)"]:::temp

    PP --> RUN
    PO --> parse --> RUN
    COMP --> pdf --> enrich --> merge --> RUN

    RUN --> STRAT
    STRAT --> PKG
    STRAT --> IMG
    STRAT --> ID

    COMP --> imgs --> ID
    EXT -.->|from-design| ID
    ID --> THEMES

    THEMES -->|theme| IMG
    IMG --> BOARD

    PKG --> PKGOUT
    PKGOUT -->|site sync| SITE
```

Read it as: **inputs → strategist → `positioning.json` (+ guidelines)**, which then feeds
**identity → `design-themes.json`** and, together with a chosen theme, **the board →
`brand-board.png`** (the main deliverable). `brand_package` rolls the direction up into
`brandings.json`, and `site:sync` publishes approved assets to `site/public/`.

## Stages

| # | Stage | Command | Output |
|---|-------|---------|--------|
| 1 | Strategy (the strategist) | `npm run brand` | `directions/<slug>/strategy/positioning.json` + `brand-guidelines.md` |
| 2 | Design themes | `npm run brand:identity` | `directions/<slug>/identity/design-themes.json` |
| 3 | Brand board (from a theme) | `npm run brand:images` | `directions/<slug>/identity/images/brand-board.png` |
| 4 | Package | `npm run brand:package` | `directions/<slug>/brand-package/` + `brandings.json` |
| — | Publish to site | `npm run site:sync` | `site/public/` |

The **brand board is the main visual deliverable** — generated directly from the strategy + one
design theme (the image model invents the palette/type onto the board; you read them off it).

Positioning IDs: **1** `functional-protein` · **2** `lifestyle` · **3** `social`.

The strategy is **format-agnostic**: brands are grouped by *positioning fit* first
(`inLineBrands` / `positioningFitTypeMismatch` / `peerBrandsOtherPositionings`), with drink
category as secondary context — so a mocktail can be a valid **social** peer even though its
format differs from PEP.
