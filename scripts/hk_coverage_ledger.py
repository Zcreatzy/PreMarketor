#!/usr/bin/env python3
"""Build and validate a complete HKEX announcement coverage ledger.

The collector deliberately separates recall from ranking:

* Every HKEX "Announcements and Notices" item in the requested date window is
  enumerated from HKEX's title-search servlet, one day at a time.
* Results documents are parsed when ``pypdf`` is available. Missing Futu
  calendar metrics are a reason to parse the notice, never a rejection reason.
* Every material candidate must receive an explicit publication decision.
  Validation fails on pending decisions, silent drops, market-cap-only
  exclusions, or a hard-trigger candidate excluded without a substantive
  market-impact comparison.

The output is an internal audit artifact; it is not written to the website.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import html
import io
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable


HKEX_ENDPOINT = "https://www1.hkexnews.hk/search/titleSearchServlet.do"
HKEX_ORIGIN = "https://www1.hkexnews.hk"
DEFAULT_FUTU_CALENDAR = Path(
    "/Users/chenzhang/Documents/Trading/newsQuant/futuskills/futuapi/"
    "scripts/quote/get_earnings_calendar.py"
)
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

HSTECH_CODES = {
    "00020", "00241", "00268", "00285", "00303", "00522", "00700",
    "00772", "00909", "00981", "00992", "01024", "01347", "01810",
    "02015", "02382", "02518", "03690", "03888", "06060", "06618",
    "06690", "09618", "09626", "09866", "09868", "09888", "09988",
    "09999",
}

RESULT_MARKERS = (
    "RESULT", "EARNINGS", "PROFIT ALERT", "PROFIT WARNING", "LOSS ALERT",
    "盈喜", "盈警", "業績", "业绩",
)
MATERIAL_TITLE_MARKERS = RESULT_MARKERS + (
    "INSIDE INFORMATION", "SUSPENSION", "RESUMPTION", "TAKEOVER",
    "ACQUISITION", "DISPOSAL", "PRIVATISATION", "RESTRUCTURING",
    "RIGHTS ISSUE", "PLACING", "SHARE BUYBACK", "MODIFIED REPORT",
    "AUDITOR", "DEFAULT", "WINDING UP", "重大", "停牌", "復牌", "复牌",
    "收購", "收购", "出售", "配售", "供股", "回購", "回购",
)

HARD_TRIGGER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("turnaround", re.compile(
        r"turn(?:ed|ing)?\s+(?:around|from\s+(?:a\s+)?loss\s+to\s+(?:a\s+)?profit)"
        r"|profit.{0,180}(?:compared|as\s+compared)\s+(?:to|with).{0,80}loss"
        r"|扭亏为盈|轉虧為盈|转亏为盈", re.I | re.S)),
    ("profit_to_loss", re.compile(
        r"loss.{0,180}(?:compared|as\s+compared)\s+(?:to|with).{0,80}profit"
        r"|盈转亏|盈轉虧", re.I | re.S)),
    ("going_concern", re.compile(
        r"material\s+uncertaint(?:y|ies).{0,160}going\s+concern"
        r"|重大不確定性.{0,80}持續經營|重大不确定性.{0,80}持续经营", re.I | re.S)),
    ("modified_audit", re.compile(
        r"modified\s+(?:report|opinion)|qualified\s+opinion|disclaimer\s+of\s+opinion"
        r"|保留意見|保留意见|無法表示意見|无法表示意见", re.I)),
    ("positive_operating_cash_flow", re.compile(
        r"positive\s+cash\s+flow\s+from\s+operating\s+activities"
        r"|operating\s+cash\s+flow.{0,80}turn(?:ed)?\s+positive"
        r"|经营现金流.{0,40}转正|經營現金流.{0,40}轉正", re.I | re.S)),
    ("profit_alert", re.compile(
        r"positive\s+profit\s+alert|profit\s+warning|loss\s+alert|盈喜|盈警", re.I)),
    ("trading_suspension", re.compile(r"suspension\s+of\s+trading|停牌", re.I)),
)

ONE_OFF_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("one_off", re.compile(r"one[- ]off|non[- ]recurring|一次性|非經常性|非经常性", re.I)),
    ("vie_termination", re.compile(r"termination\s+of.{0,100}VIE\s+arrangements|终止.{0,80}VIE|終止.{0,80}VIE", re.I | re.S)),
    ("fair_value", re.compile(r"fair\s+value\s+gain|公允价值收益|公平值收益", re.I)),
)

FORBIDDEN_EXCLUSION_REASONS = re.compile(
    r"(?:low|small).{0,20}market\s*cap|market\s*cap.{0,20}(?:low|small)"
    r"|市值(?:小|低)|小市值|N/?A|no\s+consensus|无一致预期|沒有一致預期",
    re.I,
)


def request_json(url: str, *, timeout: int = 30) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def date_range(start: dt.date, end: dt.date) -> Iterable[dt.date]:
    current = start
    while current <= end:
        yield current
        current += dt.timedelta(days=1)


def normalize_hk_code(value: Any) -> str:
    raw = str(value or "").upper().strip()
    raw = raw.removeprefix("HK.").removesuffix(".HK")
    digits = re.sub(r"\D", "", raw)
    return digits.zfill(5)[-5:] if digits else ""


def clean_markup(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_hkex_day(day: dt.date) -> list[dict[str, Any]]:
    compact = day.strftime("%Y%m%d")
    params = {
        "sortDir": "0",
        "sortByOptions": "DateTime",
        "category": "0",
        "market": "SEHK",
        "stockId": "-1",
        "documentType": "-1",
        "fromDate": compact,
        "toDate": compact,
        "title": "",
        "searchType": "1",
        "t1code": "10000",
        "t2Gcode": "-2",
        "t2code": "-2",
        "rowRange": "1000",
        "lang": "E",
    }
    payload = request_json(f"{HKEX_ENDPOINT}?{urllib.parse.urlencode(params)}")
    rows = json.loads(payload.get("result") or "[]")
    total = int(payload.get("recordCnt") or (rows[0].get("TOTAL_COUNT") if rows else 0) or 0)
    if total > 1000 or len(rows) != total:
        raise RuntimeError(
            f"HKEX enumeration incomplete for {day}: fetched {len(rows)} of {total}; "
            "narrow the query before publication"
        )
    return rows


def fetch_calendar(start: dt.date, end: dt.date, script: Path) -> list[dict[str, Any]]:
    if not script.exists():
        raise FileNotFoundError(f"Futu calendar script not found: {script}")
    command = [
        sys.executable if "futu" in sys.modules else "python3",
        str(script), "--market", "HK",
        "--begin-date", start.isoformat(), "--end-date", end.isoformat(), "--json",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=120, check=False)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Futu calendar failed")
    payload = parse_json_from_mixed_output(completed.stdout)
    if payload.get("error"):
        raise RuntimeError(str(payload["error"]))
    return list(payload.get("data") or [])


def parse_json_from_mixed_output(value: str) -> dict[str, Any]:
    """Extract the first JSON object from SDK output that may contain console logs."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", value):
        try:
            payload, _ = decoder.raw_decode(value[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise ValueError("no JSON object found in command output")


def load_calendar(path: Path | None, start: dt.date, end: dt.date, script: Path) -> tuple[list[dict[str, Any]], str | None]:
    try:
        if path:
            payload = json.loads(path.read_text(encoding="utf-8"))
            return list(payload.get("data", payload) if isinstance(payload, dict) else payload), None
        return fetch_calendar(start, end, script), None
    except Exception as exc:  # Futu is a discovery/enrichment source, not the official enumeration source.
        return [], str(exc)


def is_missing_metric(value: Any) -> bool:
    return value is None or str(value).strip().upper() in {"", "N/A", "NA", "NONE", "NAN", "--"}


def calendar_by_code(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        code = normalize_hk_code(row.get("security") or row.get("code"))
        if code:
            result[code] = row
    return result


def download_pdf_text(url: str, max_pages: int = 80) -> tuple[str, str | None]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return "", "pypdf unavailable; run with bundled Codex Python"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=30) as response:
            pdf = response.read()
        reader = PdfReader(io.BytesIO(pdf))
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:max_pages])
        return text, None
    except Exception as exc:
        return "", str(exc)


def extract_percent_moves(text: str, threshold: float = 30.0) -> list[str]:
    moves: list[str] = []
    pattern = re.compile(
        r"\b(revenue|turnover|profit(?: attributable to (?:owners|shareholders))?|net profit|net loss|loss for the period)\b"
        r".{0,120}?\b(increase[ds]?|decrease[ds]?|rose|fell|grew|declined)\s+(?:by\s+)?"
        r"([0-9]+(?:\.[0-9]+)?)\s*%",
        re.I | re.S,
    )
    for subject, direction, value in pattern.findall(text):
        number = float(value)
        if number >= threshold:
            normalized_subject = re.sub(r"\s+", "_", subject.lower())
            moves.append(f"{normalized_subject}:{direction.lower()}_{number:g}%")
    return sorted(set(moves))


def detect_signals(title: str, category: str, document_text: str) -> tuple[list[str], list[str], list[str]]:
    combined = "\n".join((title, category, document_text))
    hard = [name for name, pattern in HARD_TRIGGER_PATTERNS if pattern.search(combined)]
    percent_moves = extract_percent_moves(document_text)
    if percent_moves:
        hard.append("absolute_yoy_change_ge_30pct")
    one_off = [name for name, pattern in ONE_OFF_PATTERNS if pattern.search(combined)]
    return sorted(set(hard)), percent_moves, sorted(set(one_off))


def is_result_item(title: str, category: str) -> bool:
    upper = f"{title} {category}".upper()
    return any(marker.upper() in upper for marker in RESULT_MARKERS)


def is_material_title(title: str, category: str) -> bool:
    upper = f"{title} {category}".upper()
    return any(marker.upper() in upper for marker in MATERIAL_TITLE_MARKERS)


def make_entry(row: dict[str, Any], calendar: dict[str, dict[str, Any]], document_text: str = "", extraction_error: str | None = None) -> dict[str, Any]:
    code = normalize_hk_code(row.get("STOCK_CODE"))
    title = clean_markup(row.get("TITLE"))
    category = clean_markup(row.get("LONG_TEXT") or row.get("SHORT_TEXT"))
    calendar_row = calendar.get(code, {})
    metric_fields = ("eps_actual", "eps_predict", "revenue_actual", "revenue_predict", "ebit_actual", "ebit_predict")
    missing_metrics = [field for field in metric_fields if is_missing_metric(calendar_row.get(field))] if calendar_row else []
    hard, percent_moves, one_off = detect_signals(title, category, document_text)
    result_item = is_result_item(title, category)
    material = is_material_title(title, category)

    if hard:
        review_status = "must_review"
        screening_reason = "hard trigger detected; market cap and consensus availability cannot suppress review"
    elif result_item and extraction_error:
        review_status = "must_review"
        screening_reason = "results document extraction failed; manual review required"
    elif result_item and not document_text:
        review_status = "must_review"
        screening_reason = "original results document has not been parsed"
    elif result_item and (code in HSTECH_CODES or float(calendar_row.get("market_cap") or 0) >= 10_000_000_000):
        review_status = "must_review"
        screening_reason = "results document parsed; index membership or market impact requires review"
    elif result_item:
        review_status = "screened_out"
        screening_reason = "original results document parsed; no hard trigger or broad market-impact flag detected"
    elif material:
        review_status = "must_review"
        screening_reason = "material HKEX headline category"
    else:
        review_status = "screened_out"
        screening_reason = "no material headline or document trigger"

    return {
        "event_id": str(row.get("NEWS_ID") or row.get("FILE_LINK") or ""),
        "market": "HK",
        "code": code,
        "canonical_ticker": f"HK.{code}" if code else "",
        "name": clean_markup(row.get("STOCK_NAME")),
        "release_time": clean_markup(row.get("DATE_TIME")),
        "title": title,
        "category": category,
        "source": "HKEX",
        "url": urllib.parse.urljoin(HKEX_ORIGIN, str(row.get("FILE_LINK") or "")),
        "is_hstech": code in HSTECH_CODES,
        "is_results": result_item,
        "calendar_present": bool(calendar_row),
        "calendar_missing_metrics": missing_metrics,
        "market_cap": calendar_row.get("market_cap"),
        "hard_triggers": hard,
        "large_percent_moves": percent_moves,
        "quality_flags": one_off,
        "document_text_extracted": bool(document_text),
        "document_extraction_error": extraction_error,
        "review_status": review_status,
        "screening_reason": screening_reason,
        "publication_decision": "pending" if review_status == "must_review" else "not_applicable",
        "publication_reason": "",
    }


def collect(start: dt.date, end: dt.date, calendar_rows: list[dict[str, Any]], parse_pdfs: bool, workers: int) -> list[dict[str, Any]]:
    raw_rows: list[dict[str, Any]] = []
    for day in date_range(start, end):
        raw_rows.extend(fetch_hkex_day(day))
    by_code = calendar_by_code(calendar_rows)

    pdf_targets: dict[str, tuple[str, str]] = {}
    if parse_pdfs:
        for row in raw_rows:
            title = clean_markup(row.get("TITLE"))
            category = clean_markup(row.get("LONG_TEXT") or row.get("SHORT_TEXT"))
            if is_result_item(title, category):
                event_id = str(row.get("NEWS_ID") or row.get("FILE_LINK") or "")
                pdf_targets[event_id] = (urllib.parse.urljoin(HKEX_ORIGIN, str(row.get("FILE_LINK") or "")), title)

    extracted: dict[str, tuple[str, str | None]] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        future_map = {executor.submit(download_pdf_text, url): event_id for event_id, (url, _) in pdf_targets.items()}
        for future in concurrent.futures.as_completed(future_map):
            event_id = future_map[future]
            try:
                extracted[event_id] = future.result()
            except Exception as exc:
                extracted[event_id] = ("", str(exc))

    entries: list[dict[str, Any]] = []
    for row in raw_rows:
        event_id = str(row.get("NEWS_ID") or row.get("FILE_LINK") or "")
        text, error = extracted.get(event_id, ("", None if not parse_pdfs else "not a results document"))
        if not is_result_item(clean_markup(row.get("TITLE")), clean_markup(row.get("LONG_TEXT") or row.get("SHORT_TEXT"))):
            error = None
        entries.append(make_entry(row, by_code, text, error))

    # A calendar row may be absent from the HKEX result set because of source timing or
    # identifier drift. Keep it visible as a synthetic must-review candidate.
    seen_codes = {entry["code"] for entry in entries if entry["is_results"]}
    for code, row in by_code.items():
        if code in seen_codes:
            continue
        missing = [
            field for field in ("eps_actual", "eps_predict", "revenue_actual", "revenue_predict", "ebit_actual", "ebit_predict")
            if is_missing_metric(row.get(field))
        ]
        entries.append({
            "event_id": f"calendar:{code}:{row.get('earnings_date', '')}",
            "market": "HK",
            "code": code,
            "canonical_ticker": f"HK.{code}",
            "name": str(row.get("name") or ""),
            "release_time": str(row.get("earnings_date") or ""),
            "title": "Futu earnings-calendar entry without matched HKEX results notice",
            "category": "earnings_calendar_unmatched",
            "source": "Futu earnings calendar",
            "url": "",
            "is_hstech": code in HSTECH_CODES,
            "is_results": True,
            "calendar_present": True,
            "calendar_missing_metrics": missing,
            "market_cap": row.get("market_cap"),
            "hard_triggers": [],
            "large_percent_moves": [],
            "quality_flags": ["identifier_or_timing_gap"],
            "document_text_extracted": False,
            "document_extraction_error": "HKEX results notice not matched",
            "review_status": "must_review",
            "screening_reason": "calendar/HKEX reconciliation gap; original notice lookup required",
            "publication_decision": "pending",
            "publication_reason": "",
        })
    return entries


def validate_ledger(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        return ["ledger has no entries"]
    ids: set[str] = set()
    for entry in entries:
        event_id = str(entry.get("event_id") or "")
        if not event_id:
            errors.append("entry missing event_id")
        elif event_id in ids:
            errors.append(f"duplicate event_id: {event_id}")
        ids.add(event_id)
        if not entry.get("review_status") or not entry.get("screening_reason"):
            errors.append(f"{event_id}: missing screening disposition/reason")
        if entry.get("review_status") == "must_review":
            decision = entry.get("publication_decision")
            reason = str(entry.get("publication_reason") or "").strip()
            if decision not in {"include", "exclude"}:
                errors.append(f"{event_id}: material candidate still pending")
            if not reason:
                errors.append(f"{event_id}: publication decision lacks reason")
            if decision == "exclude" and FORBIDDEN_EXCLUSION_REASONS.search(reason):
                errors.append(f"{event_id}: forbidden market-cap/N/A/consensus exclusion rationale")
            if decision == "exclude" and entry.get("hard_triggers"):
                comparison_terms = re.compile(r"impact|market|opening|sector|liquidity|already priced|影响|开盘|板块|流动性|已计价", re.I)
                if not comparison_terms.search(reason):
                    errors.append(f"{event_id}: hard-trigger exclusion lacks substantive market-impact comparison")

    included = [entry for entry in entries if entry.get("publication_decision") == "include"]
    material = [entry for entry in entries if entry.get("review_status") == "must_review"]
    if len(material) >= 2 and len(included) < 2:
        errors.append("HK publication floor failed: at least two material HK events must be included")
    outside_hstech = [entry for entry in material if not entry.get("is_hstech")]
    if outside_hstech and not any(not entry.get("is_hstech") for entry in included):
        errors.append("HK breadth floor failed: include at least one material non-HSTECH event")
    return errors


def build_payload(start: dt.date, end: dt.date, entries: list[dict[str, Any]], calendar_error: str | None) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "window": {"from": start.isoformat(), "to": end.isoformat(), "timezone": "Asia/Shanghai"},
        "sources": {
            "hkex": {"status": "ok", "endpoint": HKEX_ENDPOINT},
            "futu_earnings_calendar": {"status": "degraded" if calendar_error else "ok", "error": calendar_error},
        },
        "counts": {
            "all_announcements": len(entries),
            "must_review": sum(entry["review_status"] == "must_review" for entry in entries),
            "screened_out": sum(entry["review_status"] == "screened_out" for entry in entries),
            "hard_triggered": sum(bool(entry["hard_triggers"]) for entry in entries),
            "pending_publication_decision": sum(entry["publication_decision"] == "pending" for entry in entries),
        },
        "entries": entries,
    }


def parse_date(value: str) -> dt.date:
    return dt.date.fromisoformat(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-date", type=parse_date)
    parser.add_argument("--to-date", type=parse_date)
    parser.add_argument("--calendar-json", type=Path)
    parser.add_argument("--futu-calendar-script", type=Path, default=DEFAULT_FUTU_CALENDAR)
    parser.add_argument("--skip-pdf", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--validate", type=Path, help="validate a reviewed ledger instead of collecting")
    args = parser.parse_args()

    if args.validate:
        payload = json.loads(args.validate.read_text(encoding="utf-8"))
        errors = validate_ledger(payload)
        print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        return 1 if errors else 0

    if not args.from_date or not args.to_date or not args.output:
        parser.error("collection requires --from-date, --to-date, and --output")
    if args.from_date > args.to_date:
        parser.error("--from-date cannot be after --to-date")

    calendar_rows, calendar_error = load_calendar(
        args.calendar_json, args.from_date, args.to_date, args.futu_calendar_script
    )
    entries = collect(args.from_date, args.to_date, calendar_rows, not args.skip_pdf, args.workers)
    payload = build_payload(args.from_date, args.to_date, entries, calendar_error)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
