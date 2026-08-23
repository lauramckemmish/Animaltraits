"""Build the local, auditable common-name mapping used by AnimalTraits.

The Streamlit app never calls GBIF. Run this script when the source dataset changes:

    python scripts/build_common_name_mapping.py --resolve-gbif

GBIF results are accepted only for exact species matches with an English vernacular
name. All other taxa deliberately fall back to their scientific names in the app.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "data" / "animal_traits.csv"
OUTPUT_PATH = ROOT / "data" / "common_name_mapping.csv"
GBIF_API = "https://api.gbif.org/v1/species"
INVALID_NAMES = {"", "0", "none", "nan", "n/a", "na", "unknown"}
CLASS_LABELS = {
    "Amphibia": "Amphibian",
    "Arachnida": "Arachnid",
    "Aves": "Bird",
    "Chilopoda": "Centipede",
    "Clitellata": "Segmented worm",
    "Gastropoda": "Snail / slug",
    "Insecta": "Insect",
    "Malacostraca": "Crustacean",
    "Mammalia": "Mammal",
    "Reptilia": "Reptile",
}


def cleaned_name(value: str | None) -> str:
    value = (value or "").strip()
    return "" if value.lower() in INVALID_NAMES else value


def usable_english_common_name(value: str | None) -> str:
    """Reject compact all-caps bird codes that GBIF sometimes lists as vernaculars."""
    value = cleaned_name(value)
    compact = value.replace(" ", "")
    return "" if value.isupper() and compact.isalpha() and len(compact) <= 6 else value


def get_json(url: str) -> dict:
    request = Request(url, headers={"User-Agent": "AnimalTraits-common-name-mapping/1.0"})
    with urlopen(request, timeout=20) as response:  # noqa: S310 - fixed public API URL
        return json.loads(response.read().decode("utf-8"))


def resolve_gbif(scientific_name: str) -> dict[str, str]:
    """Return a high-confidence English GBIF vernacular name, if available."""
    try:
        match = get_json(f"{GBIF_API}/match?{urlencode({'name': scientific_name, 'rank': 'SPECIES'})}")
        usage_key = match.get("usageKey")
        exact_species = match.get("matchType") == "EXACT" and match.get("rank") == "SPECIES"
        if not usage_key or not exact_species:
            return {
                "external_taxon_id": str(usage_key or ""),
                "match_status": "requires_review" if usage_key else "unresolved",
                "common_name": "",
                "common_name_source": "",
            }

        names = get_json(f"{GBIF_API}/{usage_key}/vernacularNames").get("results", [])
        english = [
            usable_english_common_name(item.get("vernacularName"))
            for item in names
            if str(item.get("language", "")).lower() in {"eng", "en", "english"}
        ]
        common_name = next((name for name in english if name), "")
        return {
            "external_taxon_id": str(usage_key),
            "match_status": "confident" if common_name else "unresolved",
            "common_name": common_name,
            "common_name_source": "GBIF Backbone Taxonomy" if common_name else "",
        }
    except Exception:  # Network failures leave a clearly auditable unresolved row.
        return {"external_taxon_id": "", "match_status": "unresolved", "common_name": "", "common_name_source": ""}


def source_taxa() -> list[dict[str, str]]:
    by_species: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"classes": set(), "candidates": set()})
    with SOURCE_PATH.open(newline="", encoding="utf-8-sig") as source_file:
        for row in csv.DictReader(source_file):
            scientific_name = (row.get("species") or "").strip()
            if not scientific_name:
                continue
            by_species[scientific_name]["classes"].add((row.get("class") or "").strip())
            candidate = cleaned_name(row.get("common name"))
            if candidate:
                by_species[scientific_name]["candidates"].add(candidate)

    taxa = []
    for scientific_name, values in sorted(by_species.items()):
        source_classes = sorted(values["classes"])
        candidates = sorted(values["candidates"])
        taxa.append(
            {
                "scientific_name": scientific_name,
                "animal_class": CLASS_LABELS.get(source_classes[0], source_classes[0]) if len(source_classes) == 1 else "",
                "source_candidate_name": " | ".join(candidates),
                "candidate_status": "ambiguous_source_name" if len(candidates) > 1 else "",
            }
        )
    return taxa


def build_mapping(resolve: bool) -> list[dict[str, str]]:
    taxa = source_taxa()
    resolved: dict[str, dict[str, str]] = {}
    if resolve:
        with ThreadPoolExecutor(max_workers=32) as executor:
            futures = {executor.submit(resolve_gbif, row["scientific_name"]): row["scientific_name"] for row in taxa}
            for future in as_completed(futures):
                resolved[futures[future]] = future.result()

    mapping = []
    for row in taxa:
        result = resolved.get(row["scientific_name"])
        if result is None:
            result = {
                "external_taxon_id": "",
                "match_status": "unresolved",
                "common_name": "",
                "common_name_source": "",
            }
        if row["candidate_status"]:
            result["match_status"] = "requires_review"
            result["common_name"] = ""
            result["common_name_source"] = ""
        mapping.append({**row, **result})
    return mapping


def write_mapping(mapping: list[dict[str, str]]) -> None:
    fields = [
        "scientific_name",
        "common_name",
        "animal_class",
        "external_taxon_id",
        "match_status",
        "common_name_source",
        "source_candidate_name",
        "candidate_status",
    ]
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(mapping)


def audit_existing_mapping() -> list[dict[str, str]]:
    with OUTPUT_PATH.open(newline="", encoding="utf-8") as mapping_file:
        mapping = list(csv.DictReader(mapping_file))
    for row in mapping:
        if row["match_status"] == "confident" and not usable_english_common_name(row["common_name"]):
            row["common_name"] = ""
            row["common_name_source"] = ""
            row["match_status"] = "requires_review"
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resolve-gbif", action="store_true", help="Query GBIF now; the app never does this at runtime.")
    parser.add_argument("--audit-existing", action="store_true", help="Re-audit the existing local mapping without a network lookup.")
    args = parser.parse_args()
    mapping = audit_existing_mapping() if args.audit_existing else build_mapping(args.resolve_gbif)
    write_mapping(mapping)
    counts = Counter(row["match_status"] for row in mapping)
    print(f"Unique scientific names: {len(mapping)}")
    print(f"Confident English common names: {counts['confident']}")
    print(f"Unresolved: {counts['unresolved']}")
    print(f"Ambiguous / review: {counts['requires_review']}")


if __name__ == "__main__":
    main()
