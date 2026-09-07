"""Configurable heuristic geography risk flags."""

from __future__ import annotations

import pandas as pd

# Illustrative placeholder only. A real deployment should source this from
# current FATF grey/black lists or another reviewed policy source.
DEFAULT_HIGH_RISK_COUNTRIES = ["ZZ"]


def flag_high_risk_geo(
    df: pd.DataFrame,
    high_risk_countries: list[str] | None = None,
) -> pd.DataFrame:
    """Flag rows whose country name or ISO code matches a configured list.

    These flags are heuristic features for later ML analysis, not a
    determination that a transaction or person is guilty of wrongdoing.
    """
    result = df.copy()
    configured = {
        str(country).strip().casefold()
        for country in (high_risk_countries or DEFAULT_HIGH_RISK_COUNTRIES)
    }

    def is_high_risk(row: pd.Series, prefix: str) -> bool:
        """Check both the country name and country code for one endpoint."""
        values = (row.get(f"{prefix}_country"), row.get(f"{prefix}_country_code"))
        return any(
            value is not None and not pd.isna(value) and str(value).strip().casefold() in configured
            for value in values
        )

    result["src_high_risk_geo"] = result.apply(lambda row: is_high_risk(row, "src"), axis=1).astype(bool)
    result["dst_high_risk_geo"] = result.apply(lambda row: is_high_risk(row, "dst"), axis=1).astype(bool)
    return result
