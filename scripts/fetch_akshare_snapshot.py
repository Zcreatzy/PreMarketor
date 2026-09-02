#!/usr/bin/env python3
"""Fetch a small A/H index snapshot through AKShare only."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import akshare as ak


def fetch_with_fallback(label, sources, attempts=3):
    errors = []
    for source_name, fetch in sources:
        for attempt in range(1, attempts + 1):
            try:
                frame = fetch()
                if frame.empty:
                    raise RuntimeError("empty response")
                return {
                    "status": "ok",
                    "source": source_name,
                    "rowCount": len(frame),
                    "sample": (
                        frame.head(8).astype(object).where(frame.notna(), None).to_dict("records")
                    ),
                }
            except Exception as exc:  # Upstream sites fail in several different ways.
                errors.append(f"{source_name} attempt {attempt}: {type(exc).__name__}: {exc}")
                if attempt < attempts:
                    time.sleep(attempt)
    return {"status": "error", "errors": errors, "market": label}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/akshare-latest.json"),
        help="JSON snapshot path",
    )
    args = parser.parse_args()

    markets = {
        "A": fetch_with_fallback(
            "A",
            [
                (
                    "stock_zh_index_spot_em",
                    lambda: ak.stock_zh_index_spot_em(symbol="沪深重要指数"),
                ),
                ("stock_zh_index_spot_sina", ak.stock_zh_index_spot_sina),
            ],
        ),
        "HK": fetch_with_fallback(
            "HK",
            [
                ("stock_hk_index_spot_em", ak.stock_hk_index_spot_em),
                ("stock_hk_index_spot_sina", ak.stock_hk_index_spot_sina),
            ],
        ),
    }
    status = "ok" if all(item["status"] == "ok" for item in markets.values()) else "error"
    snapshot = {
        "schemaVersion": 1,
        "provider": "AKShare",
        "akshareVersion": ak.__version__,
        "fetchedAt": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds"),
        "status": status,
        "markets": markets,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"AKShare snapshot: {status} -> {args.output}")
    if status != "ok":
        for market, result in markets.items():
            if result["status"] == "error":
                print(f"{market}: {result['errors'][-1]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
