"""Format-specific parsers for transaction input files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import xmltodict


LIST_FIELDS = {
    "input_addresses",
    "output_addresses",
    "input_amounts",
    "output_amounts",
}


def _read_json_records(value: Any) -> list[dict[str, Any]]:
    """Extract transaction dictionaries from common JSON container shapes."""
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in ("transactions", "transaction", "records", "data"):
            if key in value:
                nested = value[key]
                if isinstance(nested, dict):
                    return [nested]
                if isinstance(nested, list):
                    return [item for item in nested if isinstance(item, dict)]
        return [value]
    return []


def parse_csv(path: str | Path) -> pd.DataFrame:
    """Read a CSV file and split pipe-delimited list fields into Python lists."""
    frame = pd.read_csv(path, on_bad_lines="skip")
    for column in LIST_FIELDS:
        if column in frame.columns:
            frame[column] = frame[column].map(
                lambda value: []
                if pd.isna(value)
                else [item.strip() for item in str(value).split("|") if item.strip()]
            )
    return frame


def parse_json(path: str | Path) -> pd.DataFrame:
    """Read JSON transaction records while preserving native list fields."""
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return pd.DataFrame(_read_json_records(payload))


def _as_list(value: Any, nested_key: str | None = None) -> list[Any]:
    """Turn xmltodict's scalar, list, or nested value into a list."""
    if value is None:
        return []
    if isinstance(value, list):
        values = value
    elif isinstance(value, dict) and nested_key:
        values = value.get(nested_key, [])
        if not isinstance(values, list):
            values = [values]
    else:
        values = [value]
    return [item for item in values if item is not None]


def _xml_transaction_records(payload: Any) -> list[dict[str, Any]]:
    """Extract transaction dictionaries from an xmltodict result."""
    if not isinstance(payload, dict) or not payload:
        return []
    root = next(iter(payload.values()))
    if isinstance(root, dict):
        if "txid" in root:
            return [root]
        records = root.get("transaction", root.get("transactions"))
        if isinstance(records, dict):
            records = records.get("transaction", records)
        if isinstance(records, list):
            return [record for record in records if isinstance(record, dict)]
        if isinstance(records, dict):
            return [records]
        if all(not isinstance(value, (dict, list)) for value in root.values()):
            return [root]
    if isinstance(root, list):
        return [record for record in root if isinstance(record, dict)]
    return []


def parse_xml(path: str | Path) -> pd.DataFrame:
    """Read XML transactions and normalize repeated or singleton XML elements."""
    with open(path, "rb") as handle:
        payload = xmltodict.parse(handle.read())

    records = _xml_transaction_records(payload)
    normalized: list[dict[str, Any]] = []
    for record in records:
        item = dict(record)
        for field in LIST_FIELDS:
            value = item.get(field)
            if isinstance(value, dict):
                # Supports <input_addresses><address>...</address></input_addresses>.
                child_key = "address" if "address" in field else "amount"
                item[field] = _as_list(value, child_key)
            else:
                item[field] = _as_list(value)
        normalized.append(item)
    return pd.DataFrame(normalized)
