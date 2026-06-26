"""
Compliance service — rule-based compliance checks for model/cloud/region combinations.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Regions considered EU for GDPR purposes
_EU_LOCATIONS = {"eu", "europe", "ireland", "netherlands", "germany", "belgium", "frankfurt"}

# Regions considered India
_INDIA_LOCATIONS = {"india", "mumbai", "pune"}


def _location_is_eu(region: dict) -> bool:
    """Check if a region is in the EU based on its location string."""
    location = region.get("location", "").lower()
    return any(kw in location for kw in _EU_LOCATIONS)


def _location_is_india(region: dict) -> bool:
    """Check if a region is in India based on its location string."""
    location = region.get("location", "").lower()
    return any(kw in location for kw in _INDIA_LOCATIONS)


def _region_has_cert(region: dict, cert: str) -> bool:
    """Check if a region has a specific compliance certification."""
    certs = {c.upper() for c in region.get("compliance", [])}
    return cert.upper() in certs


def check_compliance(
    extracted_fields: dict,
    model: dict,
    cloud: dict,
    region: dict,
) -> list[dict[str, Any]]:
    """
    Run rule-based compliance checks for a model + cloud + region combination.

    Returns a list of compliance flags, each with:
      - flag: name of the check
      - status: "pass", "fail", or "warning"
      - detail: explanation
    """
    flags: list[dict[str, Any]] = []

    data_sensitivity = extracted_fields.get("data_sensitivity", "none").lower()
    compliance_region = extracted_fields.get("compliance_region", "unknown").lower()

    # ── 1. High / Critical Data Sensitivity Checks ───────────────────────

    if data_sensitivity in ("high", "critical"):
        # Need HIPAA or GDPR capable region
        has_hipaa = _region_has_cert(region, "HIPAA")
        has_gdpr = _region_has_cert(region, "GDPR")

        if has_hipaa or has_gdpr:
            flags.append({
                "flag": "Sensitive Data Protection",
                "status": "pass",
                "detail": (
                    f"Region {region['id']} supports "
                    f"{'HIPAA' if has_hipaa else ''}"
                    f"{' and ' if has_hipaa and has_gdpr else ''}"
                    f"{'GDPR' if has_gdpr else ''} "
                    f"for {data_sensitivity}-sensitivity data."
                ),
            })
        else:
            flags.append({
                "flag": "Sensitive Data Protection",
                "status": "fail",
                "detail": (
                    f"Region {region['id']} lacks HIPAA/GDPR certification "
                    f"required for {data_sensitivity}-sensitivity data."
                ),
            })

    # ── 2. EU / Europe Region Compliance ─────────────────────────────────

    if compliance_region in ("eu", "europe"):
        if _location_is_eu(region):
            flags.append({
                "flag": "EU Data Residency",
                "status": "pass",
                "detail": f"Region {region['id']} ({region['location']}) is in the EU.",
            })
        else:
            flags.append({
                "flag": "EU Data Residency",
                "status": "fail",
                "detail": (
                    f"Region {region['id']} ({region['location']}) is NOT in the EU. "
                    "EU compliance requires data to reside in EU regions."
                ),
            })

        # GDPR check for EU
        if _region_has_cert(region, "GDPR"):
            flags.append({
                "flag": "GDPR Compliance",
                "status": "pass",
                "detail": f"Region {region['id']} is GDPR certified.",
            })
        else:
            flags.append({
                "flag": "GDPR Compliance",
                "status": "fail",
                "detail": f"Region {region['id']} does NOT have GDPR certification.",
            })

    # ── 3. India Region Compliance ───────────────────────────────────────

    if compliance_region in ("india", "in"):
        if _location_is_india(region):
            flags.append({
                "flag": "India Data Residency",
                "status": "pass",
                "detail": f"Region {region['id']} ({region['location']}) is in India.",
            })
        else:
            flags.append({
                "flag": "India Data Residency",
                "status": "fail",
                "detail": (
                    f"Region {region['id']} ({region['location']}) is NOT in India. "
                    "India data residency requirements not met."
                ),
            })

    # ── 4. PII Handling (needs GDPR-capable region) ──────────────────────

    description_lower = extracted_fields.get("task_type", "").lower()
    if "pii" in data_sensitivity or data_sensitivity in ("medium", "high"):
        if _region_has_cert(region, "GDPR"):
            flags.append({
                "flag": "PII Protection (GDPR)",
                "status": "pass",
                "detail": f"Region {region['id']} has GDPR certification for PII handling.",
            })
        else:
            flags.append({
                "flag": "PII Protection (GDPR)",
                "status": "warning",
                "detail": (
                    f"Region {region['id']} lacks GDPR certification. "
                    "Consider a GDPR-certified region for PII workloads."
                ),
            })

    # ── 5. PHI Handling (needs HIPAA) ────────────────────────────────────

    if data_sensitivity == "critical" or "phi" in data_sensitivity:
        if _region_has_cert(region, "HIPAA"):
            flags.append({
                "flag": "PHI Protection (HIPAA)",
                "status": "pass",
                "detail": f"Region {region['id']} has HIPAA certification for PHI handling.",
            })
        else:
            flags.append({
                "flag": "PHI Protection (HIPAA)",
                "status": "fail",
                "detail": (
                    f"Region {region['id']} lacks HIPAA certification. "
                    "HIPAA is required for PHI/health data workloads."
                ),
            })

    # ── 6. General SOC2 / ISO 27001 Checks ───────────────────────────────

    if _region_has_cert(region, "SOC2"):
        flags.append({
            "flag": "SOC 2 Compliance",
            "status": "pass",
            "detail": f"Region {region['id']} has SOC 2 certification.",
        })
    else:
        flags.append({
            "flag": "SOC 2 Compliance",
            "status": "warning",
            "detail": f"Region {region['id']} does not have SOC 2 certification.",
        })

    if _region_has_cert(region, "ISO 27001"):
        flags.append({
            "flag": "ISO 27001 Compliance",
            "status": "pass",
            "detail": f"Region {region['id']} has ISO 27001 certification.",
        })
    else:
        flags.append({
            "flag": "ISO 27001 Compliance",
            "status": "warning",
            "detail": f"Region {region['id']} does not have ISO 27001 certification.",
        })

    # ── 7. Self-hosted model privacy advantage ───────────────────────────

    if model.get("provider") == "Meta (self-hosted)" and data_sensitivity in ("high", "critical"):
        flags.append({
            "flag": "Self-Hosted Privacy Advantage",
            "status": "pass",
            "detail": (
                f"{model['name']} can be self-hosted, keeping {data_sensitivity}-"
                "sensitivity data entirely on-premise."
            ),
        })

    return flags
