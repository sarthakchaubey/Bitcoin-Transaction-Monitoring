"""Construction of a unified wallet, transaction, and IP graph."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

import networkx as nx
import pandas as pd

LOGGER = logging.getLogger(__name__)
INPUT_TO = "INPUT_TO"
OUTPUT_TO = "OUTPUT_TO"
BROADCAST_FROM = "BROADCAST_FROM"
BROADCAST_TO = "BROADCAST_TO"


def _as_list(value: Any) -> list[Any]:
    """Return list-like transaction fields as a safe Python list."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, str):
        return [item.strip() for item in value.split("|") if item.strip()]
    try:
        if pd.isna(value):
            return []
    except (TypeError, ValueError):
        pass
    return [value]


def _indexed_pairs(addresses: Any, amounts: Any, label: str, txid: str) -> Iterable[tuple[str, Any]]:
    """Yield aligned address/amount pairs and warn about malformed entries."""
    address_list = _as_list(addresses)
    amount_list = _as_list(amounts)
    if len(address_list) != len(amount_list):
        LOGGER.warning(
            "Skipping malformed %s edge(s) for txid %s: %d addresses, %d amounts",
            label, txid, len(address_list), len(amount_list),
        )
    for index, address in enumerate(address_list):
        if index >= len(amount_list):
            break
        if address is None or pd.isna(address):
            LOGGER.warning("Skipping %s edge with missing address for txid %s", label, txid)
            continue
        amount = amount_list[index]
        try:
            if pd.isna(amount):
                LOGGER.warning("Skipping %s edge with missing amount for txid %s", label, txid)
                continue
        except (TypeError, ValueError):
            pass
        yield str(address), amount


def _transaction_id(row: pd.Series, row_number: int) -> str:
    """Create a stable transaction node ID, including a fallback for malformed rows."""
    txid = row.get("txid")
    if txid is None or pd.isna(txid):
        return f"row-{row_number}"
    return str(txid)


def build_graph(df: pd.DataFrame) -> nx.MultiDiGraph:
    """Build a directed multi-graph linking wallets, transactions, and IPs."""
    graph = nx.MultiDiGraph()
    for row_number, (_, row) in enumerate(df.iterrows()):
        txid = _transaction_id(row, row_number)
        tx_node = f"tx:{txid}"
        graph.add_node(
            tx_node,
            type="transaction",
            txid=txid,
            timestamp=row.get("timestamp"),
            fee=row.get("fee"),
            script_type=row.get("script_type"),
        )

        for address, amount in _indexed_pairs(
            row.get("input_addresses"), row.get("input_amounts"), "input", txid
        ):
            graph.add_node(address, type="wallet", address=address)
            graph.add_edge(address, tx_node, type=INPUT_TO, amount=amount)

        for address, amount in _indexed_pairs(
            row.get("output_addresses"), row.get("output_amounts"), "output", txid
        ):
            graph.add_node(address, type="wallet", address=address)
            graph.add_edge(tx_node, address, type=OUTPUT_TO, amount=amount)

        for endpoint, edge_type, prefix in (
            ("src_ip", BROADCAST_FROM, "src"),
            ("dst_ip", BROADCAST_TO, "dst"),
        ):
            ip = row.get(endpoint)
            if ip is None or pd.isna(ip):
                LOGGER.warning("Skipping %s edge with missing IP for txid %s", edge_type, txid)
                continue
            ip_value = str(ip)
            ip_node = f"ip:{ip_value}"
            graph.add_node(ip_node, type="ip", ip=ip_value)
            graph.add_edge(
                tx_node,
                ip_node,
                type=edge_type,
                timestamp=row.get("timestamp"),
                port=row.get(f"{prefix}_port"),
                country=row.get(f"{prefix}_country"),
                country_code=row.get(f"{prefix}_country_code"),
                asn=row.get(f"{prefix}_asn"),
                asn_org=row.get(f"{prefix}_asn_org"),
            )
    return graph
