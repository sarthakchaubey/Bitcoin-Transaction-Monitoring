"""Tests for offline GeoIP enrichment and geography flags."""

from __future__ import annotations

import pandas as pd

from geoip.enrich import enrich_dataframe
from geoip.risk import flag_high_risk_geo


class FakeGeoIPLookup:
    """Small lookup double that records calls without requiring an MMDB file."""

    def __init__(self):
        self.calls: list[str] = []
        self.values = {
            "8.8.8.8": {
                "country": "United States",
                "country_code": "US",
                "asn": 15169,
                "asn_org": "Google LLC",
                "latitude": 37.751,
                "longitude": -97.822,
            },
            "1.1.1.1": {
                "country": "Australia",
                "country_code": "AU",
                "asn": 13335,
                "asn_org": "Cloudflare",
                "latitude": -33.494,
                "longitude": 143.210,
            },
        }

    def lookup_ip(self, ip: str) -> dict:
        self.calls.append(ip)
        return self.values.get(
            ip,
            {
                "country": None,
                "country_code": None,
                "asn": None,
                "asn_org": None,
                "latitude": None,
                "longitude": None,
            },
        )


def test_enrich_dataframe_adds_all_geo_columns():
    lookup = FakeGeoIPLookup()
    frame = pd.DataFrame({"src_ip": ["8.8.8.8"], "dst_ip": ["1.1.1.1"]})

    result = enrich_dataframe(frame, lookup)

    expected = {
        "src_country", "src_country_code", "src_asn", "src_asn_org",
        "dst_country", "dst_country_code", "dst_asn", "dst_asn_org",
    }
    assert expected.issubset(result.columns)
    assert result.loc[0, "src_country_code"] == "US"
    assert result.loc[0, "dst_asn"] == 13335


def test_private_and_invalid_ips_return_none_values():
    lookup = FakeGeoIPLookup()
    frame = pd.DataFrame({"src_ip": ["10.0.0.1", "not-an-ip"], "dst_ip": ["8.8.8.8", "10.0.0.2"]})

    result = enrich_dataframe(frame, lookup)

    assert pd.isna(result.loc[0, "src_country"])
    assert pd.isna(result.loc[1, "src_country_code"])
    assert pd.isna(result.loc[1, "dst_asn"])


def test_duplicate_ips_are_looked_up_once():
    lookup = FakeGeoIPLookup()
    frame = pd.DataFrame({"src_ip": ["8.8.8.8", "8.8.8.8"], "dst_ip": ["1.1.1.1", "8.8.8.8"]})

    enrich_dataframe(frame, lookup)

    assert lookup.calls == ["1.1.1.1", "8.8.8.8"]


def test_flag_high_risk_geo_uses_configured_country_names_and_codes():
    frame = pd.DataFrame(
        {
            "src_country": ["Exampleland", "United States"],
            "src_country_code": ["EX", "US"],
            "dst_country": ["Australia", None],
            "dst_country_code": ["AU", None],
        }
    )

    result = flag_high_risk_geo(frame, ["EX", "Australia"])

    assert result["src_high_risk_geo"].tolist() == [True, False]
    assert result["dst_high_risk_geo"].tolist() == [True, False]
