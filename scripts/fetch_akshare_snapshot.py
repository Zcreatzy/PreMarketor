#!/usr/bin/env python3
"""Fetch compact A/H market evidence for the daily brief through AKShare only."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import akshare as ak
import pandas as pd


def json_records(frame):
    return frame.astype(object).where(frame.notna(), None).to_dict("records")


def representative_indices(frame, selectors):
    code_col = "代码"
    name_col = "名称"
    selected = []
    used = set()
    codes = frame[code_col].astype(str).str.lower()
    names = frame[name_col].astype(str)
    for wanted_codes, wanted_names in selectors:
        mask = codes.isin({item.lower() for item in wanted_codes})
        for name in wanted_names:
            mask |= names.str.contains(name, regex=False, na=False)
        matches = frame.loc[mask]
        if not matches.empty:
            row = matches.iloc[[0]]
            code = str(row.iloc[0][code_col])
            if code not in used:
                selected.append(row)
                used.add(code)
    if not selected:
        return json_records(frame.head(8))
    return json_records(pd.concat(selected, ignore_index=True))


def index_summary(selectors):
    def summarize(frame):
        rows = representative_indices(frame, selectors)
        return {"representative": rows, "sample": rows}

    return summarize


def stock_summary(frame):
    code_col = "代码"
    name_col = "名称" if "名称" in frame.columns else "中文名称"
    pct_col = "涨跌幅"
    price_col = "最新价"
    required = {code_col, name_col, pct_col, price_col}
    missing = required.difference(frame.columns)
    if missing:
        raise RuntimeError(f"missing columns: {sorted(missing)}")

    usable = frame.copy()
    usable["_pct"] = pd.to_numeric(usable[pct_col], errors="coerce")
    usable["_price"] = pd.to_numeric(usable[price_col], errors="coerce")
    usable = usable.dropna(subset=["_pct", "_price"])
    usable = usable[usable["_price"] > 0]
    if usable.empty:
        raise RuntimeError("no usable stock quotes")

    def movers(rows):
        columns = [code_col, name_col, price_col, pct_col]
        if "成交额" in rows.columns:
            columns.append("成交额")
        return json_records(rows[columns].head(8))

    timestamp_col = next(
        (name for name in ("日期时间", "时间戳", "时点") if name in usable.columns),
        None,
    )
    return {
        "breadth": {
            "advancers": int((usable["_pct"] > 0).sum()),
            "decliners": int((usable["_pct"] < 0).sum()),
            "unchanged": int((usable["_pct"] == 0).sum()),
            "medianChangePct": round(float(usable["_pct"].median()), 4),
        },
        "leaders": movers(usable.sort_values("_pct", ascending=False)),
        "laggards": movers(usable.sort_values("_pct", ascending=True)),
        "dataTimestamp": str(usable[timestamp_col].max()) if timestamp_col else None,
    }


def fetch_with_fallback(label, sources, summarize, attempts=3):
    errors = []
    for source_name, fetch in sources:
        for attempt in range(1, attempts + 1):
            try:
                frame = fetch()
                if frame.empty:
                    raise RuntimeError("empty response")
                result = {
                    "status": "ok",
                    "source": source_name,
                    "rowCount": len(frame),
                }
                result.update(summarize(frame))
                return result
            except Exception as exc:  # Upstream sites fail in several different ways.
                errors.append(f"{source_name} attempt {attempt}: {type(exc).__name__}: {exc}")
                if attempt < attempts:
                    time.sleep(attempt)
    return {"status": "error", "errors": errors, "market": label}


def market_phase(now, close_hour):
    minutes = now.hour * 60 + now.minute
    if minutes < 9 * 60 + 30:
        return "previous_close_baseline"
    if minutes < close_hour * 60:
        return "intraday_snapshot"
    return "latest_close"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/akshare-latest.json"),
        help="JSON snapshot path",
    )
    args = parser.parse_args()

    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    a_index = fetch_with_fallback(
        "A",
        [
            (
                "stock_zh_index_spot_em",
                lambda: ak.stock_zh_index_spot_em(symbol="沪深重要指数"),
            ),
            ("stock_zh_index_spot_sina", ak.stock_zh_index_spot_sina),
        ],
        index_summary(
            [
                ({"sh000001"}, {"上证指数"}),
                ({"sh000300", "sz399300"}, {"沪深300"}),
                ({"sz399001"}, {"深证成指"}),
                ({"sz399006"}, {"创业板指"}),
                ({"sh000688"}, {"科创50"}),
            ]
        ),
    )
    a_stocks = fetch_with_fallback(
        "A stocks",
        [
            ("stock_zh_a_spot_em", ak.stock_zh_a_spot_em),
            ("stock_zh_a_spot", ak.stock_zh_a_spot),
        ],
        stock_summary,
    )
    hk_index = fetch_with_fallback(
        "HK",
        [
            ("stock_hk_index_spot_em", ak.stock_hk_index_spot_em),
            ("stock_hk_index_spot_sina", ak.stock_hk_index_spot_sina),
        ],
        index_summary(
            [
                (set(), {"恒生指数"}),
                (set(), {"恒生中国企业指数", "国企指数"}),
                (set(), {"恒生科技指数"}),
                (set(), {"恒生综合指数"}),
            ]
        ),
    )
    hk_stocks = fetch_with_fallback(
        "HK stocks",
        [
            ("stock_hk_spot_em", ak.stock_hk_spot_em),
            ("stock_hk_spot", ak.stock_hk_spot),
        ],
        stock_summary,
    )
    markets = {
        "A": {**a_index, "marketPhase": market_phase(now, 15), "stocks": a_stocks},
        "HK": {**hk_index, "marketPhase": market_phase(now, 16), "stocks": hk_stocks},
    }
    index_ok = all(item["status"] == "ok" for item in (a_index, hk_index))
    analysis_ready = all(item["status"] == "ok" for item in (a_stocks, hk_stocks))
    status = "ok" if index_ok and analysis_ready else ("partial" if index_ok else "error")
    snapshot = {
        "schemaVersion": 2,
        "provider": "AKShare",
        "akshareVersion": ak.__version__,
        "fetchedAt": now.isoformat(timespec="seconds"),
        "status": status,
        "analysisReady": analysis_ready,
        "markets": markets,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    print(f"AKShare snapshot: {status} -> {args.output}")
    if status == "error":
        for market, result in (("A", a_index), ("HK", hk_index)):
            if result["status"] == "error":
                print(f"{market}: {result['errors'][-1]}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
