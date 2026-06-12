"""
Hero composition agent — compose the can + glass + garnish, then review the
result with a vision model, in a loop until it looks good.

Two ChatGPT roles (separate API calls):
  1. Composer  (HERO_COMPOSE_MODEL) — proposes layer positions as JSON.
  2. Critic    (HERO_REVIEW_MODEL, vision) — looks at the rendered preview and
     either approves it or returns a revision brief.

The loop: compose -> render PNG -> review -> (revise) -> ... until the critic
says "pass" (and clears the score bar) or max iterations is reached. The best
scoring layout is then applied to the live site via css/hero-generated.css.

Usage:
  python -m agents.hero_run
  python -m agents.hero_run --max-iterations 5 --pass-score 85
  python -m agents.hero_run --no-apply        # experiment only, don't touch the site
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agents.llm.env import (
    get_anthropic_api_key,
    get_openai_api_key,
    load_project_env,
)
from agents.schemas import HERO_LAYOUT_SCHEMA, HERO_REVIEW_SCHEMA
from scripts.compose_hero import build_manifest, layout_to_css, render_layout

# Per-provider default models (override with --compose-model / --review-model or env).
PROVIDER_DEFAULTS = {
    "openai": {"compose": "gpt-4.1", "review": "gpt-4o"},
    "anthropic": {"compose": "claude-sonnet-4-6", "review": "claude-sonnet-4-6"},
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMPOSER_PROMPT = PROJECT_ROOT / "agents" / "prompts" / "hero_composer.md"
CRITIC_PROMPT = PROJECT_ROOT / "agents" / "prompts" / "hero_critic.md"
RUNS_DIR = PROJECT_ROOT / "experiments" / "runs"
HERO_DIR = PROJECT_ROOT / "experiments" / "hero"
GENERATED_CSS = PROJECT_ROOT / "css" / "hero-generated.css"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _compose_message(
    manifest: list[dict[str, Any]],
    *,
    iteration: int,
    previous_layout: dict[str, Any] | None,
    previous_review: dict[str, Any] | None,
) -> str:
    parts = [
        "Arrange the PEP hero composition (can + glass + garnish).",
        "",
        "## Available assets (allow-listed — use these roles and aspect ratios)",
        "```json",
        json.dumps(manifest, indent=2),
        "```",
        "",
        "Canvas: aspect ratio 4:5 (portrait), origin bottom-left. Background: calm cream (#faf6f0).",
    ]
    if iteration == 0 or not previous_layout:
        parts += [
            "",
            "This is the first attempt. Produce a balanced, premium serving "
            "arrangement following the rules in your system prompt.",
        ]
    else:
        parts += [
            "",
            f"## Previous attempt (iteration {iteration})",
            "```json",
            json.dumps(previous_layout, indent=2),
            "```",
            "",
            "## Critic feedback on that attempt",
            "```json",
            json.dumps(
                {
                    "overallScore": (previous_review or {}).get("overallScore"),
                    "scores": (previous_review or {}).get("scores"),
                    "issues": (previous_review or {}).get("issues"),
                    "revisionBrief": (previous_review or {}).get("revisionBrief"),
                },
                indent=2,
            ),
            "```",
            "",
            "Apply the revision brief with concrete numeric changes. Keep what "
            "the critic praised; fix what it flagged.",
        ]
    return "\n".join(parts)


def _review_message(layout: dict[str, Any], manifest: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            "Review the attached hero composition preview.",
            "",
            "The composition was built from this layout spec:",
            "```json",
            json.dumps(layout, indent=2),
            "```",
            "",
            "Asset real aspect ratios (for scale sanity checks):",
            "```json",
            json.dumps(
                [
                    {"key": m["key"], "aspectRatio": m["aspectRatio"]}
                    for m in manifest
                ],
                indent=2,
            ),
            "```",
            "",
            "Judge the actual rendered image, not just the numbers. Score every "
            "dimension and give a clear verdict.",
        ]
    )


def _provider_backend(provider: str):
    """Return (client, chat_json_fn, vision_json_fn) for the chosen provider."""
    if provider == "anthropic":
        from agents.llm.anthropic_client import chat_json, make_client, vision_json

        get_anthropic_api_key()
        return make_client(), chat_json, vision_json
    if provider == "openai":
        from agents.llm.openai_client import chat_json, make_client, vision_json

        get_openai_api_key()
        return make_client(), chat_json, vision_json
    raise SystemExit(f"Unknown provider: {provider!r} (use openai or anthropic)")


def run_hero(
    *,
    max_iterations: int,
    pass_score: int,
    compose_model: str,
    review_model: str,
    apply: bool,
    provider: str = "openai",
) -> dict[str, Any]:
    load_project_env()
    client, chat_json, vision_json = _provider_backend(provider)

    manifest = build_manifest()
    composer_system = _read_text(COMPOSER_PROMPT)
    critic_system = _read_text(CRITIC_PROMPT)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / f"hero-{stamp}"
    (run_dir / "previews").mkdir(parents=True, exist_ok=True)

    history: list[dict[str, Any]] = []
    previous_layout: dict[str, Any] | None = None
    previous_review: dict[str, Any] | None = None
    best: dict[str, Any] | None = None
    approved = False

    for iteration in range(max_iterations):
        print(f"\n=== Iteration {iteration + 1}/{max_iterations} ===")
        print(f"Composing layout with {compose_model}...")
        layout = chat_json(
            client,
            model=compose_model,
            system=composer_system,
            user=_compose_message(
                manifest,
                iteration=iteration,
                previous_layout=previous_layout,
                previous_review=previous_review,
            ),
            schema_name="pep_hero_layout",
            schema=HERO_LAYOUT_SCHEMA,
        )

        preview_path = run_dir / "previews" / f"iter-{iteration + 1}.png"
        render_layout(layout, out_path=preview_path)
        (run_dir / f"layout-{iteration + 1}.json").write_text(
            json.dumps(layout, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"Rendered {preview_path.relative_to(PROJECT_ROOT)}")

        print(f"Reviewing preview with {review_model} (vision)...")
        review = vision_json(
            client,
            model=review_model,
            system=critic_system,
            user=_review_message(layout, manifest),
            image_paths=[preview_path],
            schema_name="pep_hero_review",
            schema=HERO_REVIEW_SCHEMA,
        )
        (run_dir / f"review-{iteration + 1}.json").write_text(
            json.dumps(review, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

        score = int(review.get("overallScore", 0))
        verdict = review.get("verdict", "revise")
        print(f"Verdict: {verdict} | overallScore: {score}")
        for issue in review.get("issues", []):
            print(f"  - [{issue.get('severity')}] {issue.get('finding')}")

        entry = {
            "iteration": iteration + 1,
            "preview": preview_path.relative_to(PROJECT_ROOT).as_posix(),
            "overallScore": score,
            "verdict": verdict,
        }
        history.append(entry)

        if best is None or score > best["score"]:
            best = {"layout": layout, "review": review, "score": score, "iteration": iteration + 1}

        if verdict == "pass" and score >= pass_score:
            approved = True
            print(f"Approved on iteration {iteration + 1}.")
            break

        previous_layout = layout
        previous_review = review

    assert best is not None
    best_layout = best["layout"]

    HERO_DIR.mkdir(parents=True, exist_ok=True)
    final_preview = HERO_DIR / "hero-preview.png"
    render_layout(best_layout, out_path=final_preview)
    (HERO_DIR / "hero-layout.json").write_text(
        json.dumps(best_layout, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (HERO_DIR / "hero-review.json").write_text(
        json.dumps(best["review"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    report = {
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "approved": approved,
        "passScore": pass_score,
        "provider": provider,
        "composeModel": compose_model,
        "reviewModel": review_model,
        "bestIteration": best["iteration"],
        "bestScore": best["score"],
        "applied": apply,
        "history": history,
    }
    (run_dir / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    if apply:
        GENERATED_CSS.write_text(layout_to_css(best_layout), encoding="utf-8")
        print(f"\nApplied best layout to {GENERATED_CSS.relative_to(PROJECT_ROOT)}")
    else:
        print("\n--no-apply: site CSS left unchanged.")

    return {"run_dir": run_dir, "report": report, "best": best, "approved": approved}


def main() -> None:
    load_project_env()
    parser = argparse.ArgumentParser(
        description="PEP hero composition agent (compose + vision review loop)"
    )
    parser.add_argument(
        "--provider",
        default=os.environ.get("HERO_PROVIDER", "openai"),
        choices=["openai", "anthropic"],
        help="Which LLM provider to use for both agents",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=int(os.environ.get("HERO_MAX_ITERATIONS", "4")),
        help="Max compose -> render -> review cycles",
    )
    parser.add_argument(
        "--pass-score",
        type=int,
        default=int(os.environ.get("HERO_PASS_SCORE", "82")),
        help="Minimum overallScore (with verdict=pass) to auto-approve",
    )
    parser.add_argument(
        "--compose-model",
        default=None,
        help="Composer model (defaults per provider)",
    )
    parser.add_argument(
        "--review-model",
        default=None,
        help="Vision critic model (defaults per provider)",
    )
    parser.add_argument(
        "--no-apply",
        action="store_true",
        help="Run the loop but do not write css/hero-generated.css",
    )
    args = parser.parse_args()

    defaults = PROVIDER_DEFAULTS[args.provider]
    compose_model = (
        args.compose_model or os.environ.get("HERO_COMPOSE_MODEL") or defaults["compose"]
    )
    review_model = (
        args.review_model or os.environ.get("HERO_REVIEW_MODEL") or defaults["review"]
    )
    print(f"Provider: {args.provider} | compose: {compose_model} | review: {review_model}")

    result = run_hero(
        max_iterations=args.max_iterations,
        pass_score=args.pass_score,
        compose_model=compose_model,
        review_model=review_model,
        apply=not args.no_apply,
        provider=args.provider,
    )

    report = result["report"]
    print("\nDone.")
    print(f"  Run artifacts: {result['run_dir']}")
    print(f"  Best iteration: {report['bestIteration']} (score {report['bestScore']})")
    print(f"  Approved by critic: {report['approved']}")
    print("  Approved layout: experiments/hero/hero-layout.json")
    print("  Preview: experiments/hero/hero-preview.png")
    if report["applied"]:
        print("  Live site updated: css/hero-generated.css")


if __name__ == "__main__":
    main()
