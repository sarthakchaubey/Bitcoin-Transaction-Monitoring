"""Tests for the format-agnostic transaction ingestion layer."""

from __future__ import annotations

import json

import pandas as pd
from pandas.testing import assert_frame_equal

from ingestion import loader
from ingestion.loader import load_transactions


ROWS = [
    {
        "timestamp": "2024-01-01T00:00:00Z",
        "src_ip": "192.0.2.1",
        "dst_ip": "198.51.100.1",
        "src_port": 1000,
        "dst_port": 8333,
        "txid": "tx-1",
        "input_addresses": ["in-1", "in-2"],
        "output_addresses": ["out-1"],
        "input_amounts": [1.0, 2.0],
        "output_amounts": [2.9],
        "fee": 0.1,
        "script_type": "p2pkh",
    },
    {
        "timestamp": "2024-01-02T00:00:00Z",
        "src_ip": "192.0.2.2",
        "dst_ip": "198.51.100.2",
        "src_port": 1001,
        "dst_port": 8333,
        "txid": "tx-2",
        "input_addresses": ["in-3"],
        "output_addresses": ["out-2", "out-3"],
        "input_amounts": [3.0],
        "output_amounts": [2.0, 0.9],
        "fee": 0.1,
        "script_type": "p2sh",
    },
    {
        "timestamp": "2024-01-03T00:00:00Z",
        "src_ip": "192.0.2.3",
        "dst_ip": "198.51.100.3",
        "src_port": 1002,
        "dst_port": 8333,
        "txid": "tx-3",
        "input_addresses": ["in-4"],
        "output_addresses": ["out-4"],
        "input_amounts": [4.0],
        "output_amounts": [3.9],
        "fee": 0.1,
        "script_type": "p2wpkh",
    },
]


def _write_fixtures(tmp_path):
    columns = list(ROWS[0])
    csv_rows = []
    for row in ROWS:
        csv_row = row.copy()
        for field in ("input_addresses", "output_addresses", "input_amounts", "output_amounts"):
            csv_row[field] = "|".join(str(value) for value in row[field])
        csv_rows.append(csv_row)
    pd.DataFrame(csv_rows, columns=columns).to_csv(tmp_path / "transactions.csv", index=False)
    (tmp_path / "transactions.json").write_text(json.dumps(ROWS), encoding="utf-8")

    def xml_record(row):
        def tags(name, values, child):
            return f"<{name}>" + "".join(f"<{child}>{value}</{child}>" for value in values) + f"</{name}>"

        scalar = "".join(f"<{field}>{row[field]}</{field}>" for field in (
            "timestamp", "src_ip", "dst_ip", "src_port", "dst_port", "txid", "fee", "script_type"
        ))
        return (
            f"<transaction>{scalar}"
            f"{tags('input_addresses', row['input_addresses'], 'address')}"
            f"{tags('output_addresses', row['output_addresses'], 'address')}"
            f"{tags('input_amounts', row['input_amounts'], 'amount')}"
            f"{tags('output_amounts', row['output_amounts'], 'amount')}"
            "</transaction>"
        )

    xml = "<transactions>" + "".join(xml_record(row) for row in ROWS) + "</transactions>"
    (tmp_path / "transactions.xml").write_text(xml, encoding="utf-8")
    return tmp_path / "transactions.csv", tmp_path / "transactions.json", tmp_path / "transactions.xml"


def test_csv_json_xml_produce_identical_frames(tmp_path):
    paths = _write_fixtures(tmp_path)
    frames = [load_transactions(str(path)) for path in paths]

    for frame in frames[1:]:
        assert_frame_equal(frames[0], frame, check_dtype=True)


def test_malformed_row_is_rejected_and_logged(tmp_path, monkeypatch):
    path = tmp_path / "bad.csv"
    row = ROWS[0].copy()
    row["input_amounts"] = [1.0]
    csv_row = row.copy()
    for field in ("input_addresses", "output_addresses", "input_amounts", "output_amounts"):
        csv_row[field] = "|".join(str(value) for value in row[field])
    pd.DataFrame([csv_row]).to_csv(path, index=False)
    log_path = tmp_path / "rejected_rows.log"
    monkeypatch.setattr(loader, "REJECTION_LOG", log_path)

    result = load_transactions(str(path))

    assert result.empty
    assert "length mismatch" in log_path.read_text(encoding="utf-8")


def test_missing_required_field_is_rejected_gracefully(tmp_path, monkeypatch):
    path = tmp_path / "missing.json"
    row = ROWS[0].copy()
    del row["txid"]
    path.write_text(json.dumps([row]), encoding="utf-8")
    log_path = tmp_path / "rejected_rows.log"
    monkeypatch.setattr(loader, "REJECTION_LOG", log_path)

    result = load_transactions(str(path))

    assert result.empty
    assert "missing required field: txid" in log_path.read_text(encoding="utf-8")


def test_duplicate_txid_keeps_first_occurrence(tmp_path, caplog):
    path = tmp_path / "duplicates.json"
    duplicate = ROWS[0].copy()
    duplicate["fee"] = 99.0
    path.write_text(json.dumps([ROWS[0], duplicate]), encoding="utf-8")

    with caplog.at_level("WARNING"):
        result = load_transactions(str(path))

    assert len(result) == 1
    assert result.iloc[0]["fee"] == 0.1
    assert "duplicate txid" in caplog.text
