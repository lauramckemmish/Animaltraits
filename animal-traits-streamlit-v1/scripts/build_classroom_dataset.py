"""Build the checked-in classroom extract from pinned AnimalTraits v1.0.7 data.

The application never downloads this source at runtime. Obtain the archived
``observations.csv`` separately, then run this script with its local path.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_PATH = ROOT / "data" / "animal_traits.csv"
PINNED_RELEASE = "v1.0.7"
PINNED_RELEASE_COMMIT = "278ddf4e899cb74989e99c6595c1db18a78d13ec"
PINNED_SOURCE_SHA256 = "151a77e6e9d6c27878e7c94321b3d686b81088d4845c0a510fcdb0d3a45fb44d"

# Ordered to make the generated CSV schema stable. Values are copied verbatim
# from the pinned upstream CSV; no scientific filtering, aggregation, or
# rounding is applied.
CLASSROOM_FIELD_MAP = (
    ("phylum", "phylum"),
    ("class", "class"),
    ("order", "order"),
    ("family", "family"),
    ("genus", "genus"),
    ("species", "species"),
    ("sex", "study sample sex"),
    ("sampleSizeValue", "study sample size"),
    ("body mass", "body mass (kg)"),
    ("metabolic rate", "metabolic rate (W)"),
    ("mass-specific metabolic rate", "mass-specific metabolic rate (W/kg)"),
    ("brain size", "brain size (kg)"),
    ("brain size - method", "brain size - method"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source_file:
        for block in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_classroom_dataset(
    source_path: Path,
    output_path: Path,
    *,
    expected_sha256: str = PINNED_SOURCE_SHA256,
) -> int:
    """Verify a pinned source CSV and write the deterministic classroom extract."""
    actual_sha256 = sha256_file(source_path)
    if actual_sha256 != expected_sha256:
        raise ValueError(
            "Source checksum does not match AnimalTraits "
            f"{PINNED_RELEASE} ({PINNED_RELEASE_COMMIT}). Expected "
            f"{expected_sha256}, got {actual_sha256}."
        )

    source_fields = [source for source, _ in CLASSROOM_FIELD_MAP]
    output_fields = [target for _, target in CLASSROOM_FIELD_MAP]
    with source_path.open(newline="", encoding="utf-8-sig") as source_file:
        reader = csv.DictReader(source_file)
        missing_fields = set(source_fields).difference(reader.fieldnames or [])
        if missing_fields:
            raise ValueError(f"Pinned source is missing fields: {', '.join(sorted(missing_fields))}.")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as output_file:
            writer = csv.DictWriter(
                output_file, fieldnames=output_fields, lineterminator="\n"
            )
            writer.writeheader()
            count = 0
            for row in reader:
                writer.writerow({target: row[source] for source, target in CLASSROOM_FIELD_MAP})
                count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="Local AnimalTraits v1.0.7 observations.csv")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH, help="Generated classroom CSV path")
    args = parser.parse_args()

    count = build_classroom_dataset(args.source, args.output)
    print(f"Wrote {count:,} observations to {args.output}.")


if __name__ == "__main__":
    main()
