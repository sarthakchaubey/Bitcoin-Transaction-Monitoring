"""Offline MaxMind GeoLite2 lookup with an in-memory IP cache."""

from __future__ import annotations

import ipaddress
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


def _empty_result() -> dict[str, Any]:
    """Return the stable result shape for unresolved IP addresses."""
    return {
        "country": None,
        "country_code": None,
        "asn": None,
        "asn_org": None,
        "latitude": None,
        "longitude": None,
    }


class GeoIPLookup:
    """Perform offline country, coordinate, and ASN lookups against MMDB files."""

    def __init__(
        self,
        city_db_path: str | Path | None = None,
        asn_db_path: str | Path | None = None,
    ) -> None:
        """Load the City database and, when available, the separate ASN database."""
        self.city_db_path = Path(city_db_path or Path(__file__).with_name("GeoLite2-City.mmdb"))
        self.asn_db_path = Path(asn_db_path or Path(__file__).with_name("GeoLite2-ASN.mmdb"))
        if not self.city_db_path.is_file():
            raise FileNotFoundError(
                "GeoLite2-City.mmdb was not found at "
                f"{self.city_db_path}. Create a free MaxMind account at "
                "https://www.maxmind.com/en/geolite2/signup, download the "
                "GeoLite2-City database, and place it at geoip/GeoLite2-City.mmdb."
            )

        try:
            from geoip2.database import Reader
        except ImportError as exc:
            raise ImportError(
                "The geoip2 package is required for GeoIP enrichment. "
                "Install dependencies with: python -m pip install -r requirements.txt"
            ) from exc

        self._city_reader = Reader(str(self.city_db_path))
        self._asn_reader = Reader(str(self.asn_db_path)) if self.asn_db_path.is_file() else None
        if self._asn_reader is None:
            LOGGER.info("ASN database not found at %s; using City traits when available", self.asn_db_path)

    @staticmethod
    def _is_public_ip(ip: str) -> bool:
        """Return whether a value is a valid globally routable IP address."""
        try:
            address = ipaddress.ip_address(str(ip).strip())
        except (ValueError, TypeError):
            return False
        return address.is_global

    @lru_cache(maxsize=10000)
    def lookup_ip(self, ip: str) -> dict[str, Any]:
        """Look up one IP without network access, returning null fields when unresolved."""
        result = _empty_result()
        if not self._is_public_ip(ip):
            return result

        normalized_ip = str(ip).strip()
        try:
            city = self._city_reader.city(normalized_ip)
            result["country"] = city.country.name
            result["country_code"] = city.country.iso_code
            result["latitude"] = city.location.latitude
            result["longitude"] = city.location.longitude

            if self._asn_reader is not None:
                asn_response = self._asn_reader.asn(normalized_ip)
                result["asn"] = asn_response.autonomous_system_number
                result["asn_org"] = asn_response.autonomous_system_organization
            else:
                traits = city.traits
                result["asn"] = getattr(traits, "autonomous_system_number", None)
                result["asn_org"] = getattr(traits, "autonomous_system_organization", None)
                if result["asn"] is None and result["asn_org"] is None:
                    LOGGER.warning("ASN data unavailable for IP lookup %s", normalized_ip)
        except Exception as exc:  # geoip2 raises AddressNotFoundError and reader-specific errors
            LOGGER.info("GeoIP lookup failed for %s: %s", normalized_ip, exc)
            return _empty_result()
        return result

    def close(self) -> None:
        """Close the underlying MMDB readers."""
        self._city_reader.close()
        if self._asn_reader is not None:
            self._asn_reader.close()
