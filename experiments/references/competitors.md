# References for the site concept agent

You only need to maintain **anchored URLs** below. The agent **discovers** additional similar sites itself (web search at concept time)—you do not have to build a long competitor list.

---

## Your two anchored sites (always include in Pass 1)

### [Revized](https://www.revized-seltzer.com/) — primary layout inspiration

**Product:** Hard seltzer (sparkling water + fruit + alcohol) — not protein, but close to PEP’s *feel*: light, refreshing, flavour-led.

**Steal patterns (not pixels):**

- Hero: one clear line + product proof (calories, natural, no sugar)
- **Flavour grid** — each SKU with short sensory copy
- **“Drinking ritual”** — step-by-step serve (glass, ice, garnish) → PEP can mirror “how to enjoy” / occasions
- About + founder story as its own beat
- Clean DTC nav: Flavours, Serving, About, Contact

**PEP should differ:** Protein + out-of-home venues pilot; Lou & Shannon story; no alcohol; your `brand.json` palette (greens/creams, not seltzer neon).

---

### [drinkpep.com](https://drinkpep.com/) — same name, different brand (read carefully)

**Product:** US “Platinum Energy Probiotics” — gut-friendly **energy** drink (Beasley brothers, Austin). **Not** your PEP (premium **protein**, Lou & Shannon, **pep-drink.com**).

**Useful for website IA only:**

- Benefit blocks (probiotics, B vitamins, electrolytes) → PEP equivalent: protein, calories, no added sugar, gluten-free
- Shop / flavour product cards
- Testimonials carousel
- Email / “stay connected” band
- Lifestyle photography + product on location

**Do not confuse:** Copy, ingredients, founders, or positioning with your brand. The agent must label this reference as **“name collision — layout reference only”** in `site-concept.json`.

---

## Agent-led discovery (automatic)

When `concept_run` runs, it should **search the web** for 5–8 more sites in these lanes (examples of search intent, not a fixed list):

| Lane | Example search intent |
|------|------------------------|
| **Protein RTD / clear protein** | Premium ready-to-drink protein, light protein water, café-friendly protein beverage |
| **Functional refreshment** | Low-calorie premium drink DTC, “social wellness” beverage brand |
| **Flavour-forward DTC** | Multi-flavour drink brand website, scrollable flavour lineup |
| **Occasion / out-of-home** | Beverage brand positioning for bars, terraces, brunch (if findable) |

**Rules for discovered sites:**

- Record each in `experiments/concepts/<run>/discovered-references.json` with URL, why it’s relevant, and what pattern to adapt
- Adapt **layout and narrative patterns** only — never logos, names, or proprietary copy
- Prefer brands closer to **light + premium + flavour** than gym-shake or extreme energy aesthetics

**Optional env flag (when CLI exists):**

```bash
CONCEPT_AGENT_WEB_SEARCH=1   # default on for concept_run
```

---

## PEP assets the agent must respect (local, not scraped)

- `brand/brand.json` — colors & fonts
- `brand/research/directions/provided/assets/marketing/originals/design-reference-full.png`
- `brand/research/directions/provided/assets/product/flavours/flavours.json` — flavours and colours
- Founder story & SKU truth on the current site — do not invent products or availability
