"""
Knowledge base service — loads and queries AI model and cloud provider data.
"""

import json
from pathlib import Path
from typing import Optional

# Load JSON data at module level for performance
_KB_DIR = Path(__file__).resolve().parent.parent / "knowledge_base"

with open(_KB_DIR / "models.json", "r", encoding="utf-8") as f:
    _MODELS: list[dict] = json.load(f)

with open(_KB_DIR / "cloud_providers.json", "r", encoding="utf-8") as f:
    _CLOUD_PROVIDERS: list[dict] = json.load(f)


def get_all_models() -> list[dict]:
    """Return all AI models from the knowledge base."""
    return _MODELS


def get_models_by_tier(tier: str) -> list[dict]:
    """Return models filtered by tier (Small, Medium, Large)."""
    return [m for m in _MODELS if m["tier"].lower() == tier.lower()]


def get_all_cloud_providers() -> list[dict]:
    """Return all cloud providers from the knowledge base."""
    return _CLOUD_PROVIDERS


def get_compliant_clouds(
    required_certs: list[str],
    required_region: Optional[str] = None,
) -> list[dict]:
    """
    Return cloud providers filtered by compliance certifications and region.

    For each provider, only regions matching the required certifications
    (and optional region keyword) are included.
    """
    results = []

    for provider in _CLOUD_PROVIDERS:
        matching_regions = []

        for region in provider["regions"]:
            # Check that region has all required certifications
            region_certs = {c.upper() for c in region.get("compliance", [])}
            has_certs = all(
                cert.upper() in region_certs for cert in required_certs
            )

            if not has_certs:
                continue

            # Optional: filter by region keyword (e.g., "EU", "India", "USA")
            if required_region:
                location = region.get("location", "").lower()
                region_id = region.get("id", "").lower()
                region_kw = required_region.lower()

                # Map common keywords to location substrings
                region_matches = False
                if region_kw in ("eu", "europe"):
                    region_matches = any(
                        kw in location
                        for kw in ("eu", "europe", "ireland", "netherlands", "germany", "belgium", "frankfurt")
                    )
                elif region_kw in ("india", "in"):
                    region_matches = any(
                        kw in location for kw in ("india", "mumbai", "pune")
                    )
                elif region_kw in ("us", "usa", "united states"):
                    region_matches = any(
                        kw in location for kw in ("usa", "virginia", "iowa")
                    )
                else:
                    # Generic substring match
                    region_matches = (
                        region_kw in location or region_kw in region_id
                    )

                if not region_matches:
                    continue

            matching_regions.append(region)

        if matching_regions:
            results.append(
                {
                    **provider,
                    "regions": matching_regions,
                }
            )

    return results


def format_models_for_llm(models: list[dict]) -> str:
    """Format model data as a readable string for LLM context."""
    if not models:
        return "No models available."

    lines = ["=== Available AI Models ===\n"]
    for m in models:
        lines.append(f"Model: {m['name']}")
        lines.append(f"  Provider: {m['provider']}")
        lines.append(f"  Tier: {m['tier']}")
        lines.append(
            f"  Pricing: ${m['cost_per_1k_input_tokens']}/1K input tokens, "
            f"${m['cost_per_1k_output_tokens']}/1K output tokens"
        )
        lines.append(f"  Max Context: {m['max_context']:,} tokens")
        lines.append(f"  Strengths: {', '.join(m['strengths'])}")
        lines.append(f"  Limitations: {', '.join(m['limitations'])}")
        lines.append(f"  Best For: {', '.join(m['best_for'])}")
        lines.append("")

    return "\n".join(lines)


def format_clouds_for_llm(clouds: list[dict]) -> str:
    """Format cloud provider data as a readable string for LLM context."""
    if not clouds:
        return "No cloud providers available."

    lines = ["=== Available Cloud Providers ===\n"]
    for c in clouds:
        lines.append(f"Provider: {c['name']}")
        if "market_share" in c:
            lines.append(f"  Market Share: {c['market_share']}")
        if "description" in c:
            lines.append(f"  Description: {c['description']}")
        lines.append(f"  Strengths: {', '.join(c['strengths'])}")
        lines.append(f"  Pricing: {c['pricing_notes']}")
        lines.append(f"  Supported Models: {', '.join(c['supported_models'])}")
        lines.append("  Regions:")
        for r in c["regions"]:
            lines.append(
                f"    - {r['id']} ({r['location']}): "
                f"Compliance: {', '.join(r['compliance'])}"
            )
        lines.append("")

    return "\n".join(lines)
