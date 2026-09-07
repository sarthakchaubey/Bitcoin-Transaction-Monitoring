"""Schema normalization and row validation for transaction records."""

from __future__ import annotations

import ipaddress
from datetime import datetime
from typing import Any

import pandas as pd


SCHEMA = [
    "timestamp",
    "src_ip",
    "dst_ip",
    "src_port",
    "dst_port",
    "txid",
    "input_addresses",
    "output_addresses",
    "input_amounts",
    "output_amounts",
    "fee",
    "script_type",
]
LIST_FIELDS = {"input_addresses", "output_addresses", "input_amounts", "output_amounts"}
ADDRESS_FIELDS = {"input_addresses", "output_addresses"}
AMOUNT_FIELDS = {"input_amounts", "output_amounts"}
REQUIRED_FIELDS = set(SCHEMA)


def _list_value(value: Any) -> list[Any]:
    """Convert a scalar, delimited string, or sequence to a list."""
    if value is None:
        return []
    if not isinstance(value, (list, tuple, dict, str)) and pd.isna(value):
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        return [part.strip() for part in value.split("|") if part.strip()]
    return [value]


def normalize_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Return records with the canonical columns and normalized pandas dtypes."""
    result = df.copy()
    for column in SCHEMA:
        if column not in result.columns:
            result[column] = pd.NA
    result = result[SCHEMA]

    result["timestamp"] = pd.to_datetime(result["timestamp"], errors="coerce", utc=True)
    for column in ("src_port", "dst_port"):
        result[column] = pd.to_numeric(result[column], errors="coerce").astype("Int64")
    result["fee"] = pd.to_numeric(result["fee"], errors="coerce")

    for column in ADDRESS_FIELDS:
        result[column] = result[column].map(
            lambda value: [str(item).strip() for item in _list_value(value) if str(item).strip()]
        )
    for column in AMOUNT_FIELDS:
        result[column] = result[column].map(
            lambda value: pd.to_numeric(_list_value(value), errors="coerce").tolist()
        )
    for column in ("src_ip", "dst_ip", "txid", "script_type"):
        result[column] = result[column].astype("string")
    return result.reset_index(drop=True)


def validate_row(row: pd.Series) -> tuple[bool, list[str]]:
    """Validate one normalized transaction row and return status plus reasons."""
    reasons: list[str] = []
    for field in REQUIRED_FIELDS:
        value = row.get(field)
        missing = value is None
        if not missing and not isinstance(value, (list, tuple)):
            missing = bool(pd.isna(value))
        if missing or (field in LIST_FIELDS and not value):
            reasons.append(f"missing required field: {field}")

    for field in ("src_ip", "dst_ip"):
        value = row.get(field)
        if value is not None and not pd.isna(value):
            try:
                ipaddress.ip_address(str(value))
            except ValueError:
                reasons.append(f"malformed {field}: {value}")

    for field in ("src_port", "dst_port"):
        value = row.get(field)
        if value is not None and not pd.isna(value) and not 0 <= int(value) <= 65535:
            reasons.append(f"invalid {field}: {value}")

    timestamp = row.get("timestamp")
    if timestamp is None or pd.isna(timestamp):
        reasons.append("invalid timestamp")
    elif not isinstance(timestamp, (pd.Timestamp, datetime)):
        reasons.append("invalid timestamp")

    for addresses, amounts, label in (
        ("input_addresses", "input_amounts", "input"),
        ("output_addresses", "output_amounts", "output"),
    ):
        address_values = row.get(addresses, [])
        amount_values = row.get(amounts, [])
        if len(address_values) != len(amount_values):
            reasons.append(f"{label}_amounts length mismatch with {label}_addresses")
        if any(pd.isna(value) or float(value) < 0 for value in amount_values):
            reasons.append(f"negative or invalid {label}_amounts")

    fee = row.get("fee")
    if fee is None or pd.isna(fee) or float(fee) < 0:
        reasons.append("negative or invalid fee")
    return not reasons, reasons
