"""Public transaction loading entry point."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .normalize import SCHEMA, normalize_schema, validate_row
from .parsers import parse_csv, parse_json, parse_xml

LOGGER = logging.getLogger(__name__)
REJECTION_LOG = Path(__file__).resolve().parents[1] / "data" / "raw" / "rejected_rows.log"


def _log_rejection(row: pd.Series, reasons: list[str]) -> None:
    """Append a rejected row and its validation reasons to the rejection log."""
    REJECTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with REJECTION_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"reasons={'; '.join(reasons)} row={row.to_dict()}\n")


def load_transactions(path: str) -> pd.DataFrame:
    """Parse, normalize, validate, deduplicate, and return clean transactions."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Transaction file not found: {source}")
    if source.stat().st_size == 0:
        LOGGER.info("Loaded empty transaction file: %s", source)
        return normalize_schema(pd.DataFrame(columns=SCHEMA))

    parsers = {".csv": parse_csv, ".json": parse_json, ".xml": parse_xml}
    parser = parsers.get(source.suffix.lower())
    if parser is None:
        raise ValueError("Unsupported transaction format; expected .csv, .json, or .xml")

    try:
        raw = parser(source)
    except (OSError, ValueError, TypeError) as exc:
        raise ValueError(f"Could not parse transaction file {source}: {exc}") from exc

    normalized = normalize_schema(raw)
    valid_rows: list[pd.Series] = []
    rejected = 0
    for _, row in normalized.iterrows():
        valid, reasons = validate_row(row)
        if valid:
            valid_rows.append(row)
        else:
            rejected += 1
            _log_rejection(row, reasons)

    clean = pd.DataFrame(valid_rows, columns=SCHEMA) if valid_rows else normalized.iloc[0:0].copy()
    duplicate_count = int(clean["txid"].duplicated(keep="first").sum())
    if duplicate_count:
        LOGGER.warning("Found %d duplicate txid(s); keeping first occurrence", duplicate_count)
        clean = clean.drop_duplicates(subset="txid", keep="first")
    clean = clean.reset_index(drop=True)
    LOGGER.info(
        "Loaded %d rows: total rows read=%d, rows rejected=%d, rows kept=%d, duplicate txids found=%d",
        len(clean), len(normalized), rejected, len(clean), duplicate_count,
    )
    return clean
