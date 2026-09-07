"""DataFrame enrichment using offline GeoIP lookups."""

from __future__ import annotations

import logging

import pandas as pd

from .lookup import GeoIPLookup

LOGGER = logging.getLogger(__name__)
ENRICHMENT_FIELDS = (
    "country",
    "country_code",
    "asn",
    "asn_org",
)


def enrich_dataframe(df: pd.DataFrame, lookup: GeoIPLookup) -> pd.DataFrame:
    """Add source and destination country/ASN fields using one lookup per unique IP."""
    result = df.copy()
    ip_values: set[str] = set()
    for column in ("src_ip", "dst_ip"):
        if column in result.columns:
            ip_values.update(
                str(value).strip()
                for value in result[column].dropna().unique()
                if str(value).strip()
            )

    resolved = {ip: lookup.lookup_ip(ip) for ip in sorted(ip_values)}
    successful = sum(any(value is not None for value in details.values()) for details in resolved.values())
    failed = len(resolved) - successful

    for prefix, ip_column in (("src", "src_ip"), ("dst", "dst_ip")):
        for field in ENRICHMENT_FIELDS:
            output_column = f"{prefix}_{field}"
            if ip_column in result.columns:
                result[output_column] = result[ip_column].map(
                    lambda value, field=field: resolved.get(str(value).strip(), {}).get(field)
                    if pd.notna(value)
                    else None
                )
            else:
                result[output_column] = None

    result.attrs["geoip_summary"] = {
        "unique_ips": len(resolved),
        "resolved_ips": successful,
        "failed_or_private_ips": failed,
        "resolution_rate": successful / len(resolved) if resolved else 0.0,
    }
    LOGGER.info(
        "GeoIP enrichment: unique IPs looked up=%d, resolved=%d, failed/private/invalid=%d",
        len(resolved), successful, failed,
    )
    return result
