import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "hk_coverage_ledger.py"
SPEC = importlib.util.spec_from_file_location("hk_coverage_ledger", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


class HkCoverageLedgerTests(unittest.TestCase):
    def setUp(self):
        self.row = {
            "NEWS_ID": "308046402",
            "STOCK_CODE": "02048",
            "STOCK_NAME": "E-HOUSE ENT",
            "DATE_TIME": "31/08/2026 19:19",
            "TITLE": "INTERIM RESULTS ANNOUNCEMENT FOR THE SIX MONTHS ENDED 30 JUNE 2026",
            "LONG_TEXT": "Announcements and Notices - [Interim Results / Modified Report by Auditors]",
            "FILE_LINK": "/listedco/listconews/sehk/2026/0831/2026083101697.pdf",
        }
        self.calendar = {
            "02048": {
                "security": "HK.02048",
                "name": "易居企业控股",
                "eps_actual": "N/A",
                "eps_predict": "N/A",
                "revenue_actual": "N/A",
                "revenue_predict": "N/A",
                "ebit_actual": "N/A",
                "ebit_predict": "N/A",
                "market_cap": 143422881.46,
            }
        }
        self.text = """
        Profit/(loss) for the period attributable to Owners of the Company
        was RMB45,245,000, compared to loss of RMB298,172,000 in 2025.
        Revenue decreased by 35.5%. Positive cash flow from operating activities
        was RMB14.5 million, largely due to gains from termination of VIE arrangements.
        A material uncertainty may cast significant doubt on the Group's ability
        to continue as a going concern.
        """

    def test_ehouse_low_cap_na_metrics_is_never_silently_filtered(self):
        entry = MODULE.make_entry(self.row, self.calendar, self.text)
        self.assertEqual(entry["canonical_ticker"], "HK.02048")
        self.assertEqual(entry["review_status"], "must_review")
        self.assertEqual(entry["publication_decision"], "pending")
        self.assertIn("turnaround", entry["hard_triggers"])
        self.assertIn("absolute_yoy_change_ge_30pct", entry["hard_triggers"])
        self.assertIn("positive_operating_cash_flow", entry["hard_triggers"])
        self.assertIn("going_concern", entry["hard_triggers"])
        self.assertIn("vie_termination", entry["quality_flags"])
        self.assertEqual(len(entry["calendar_missing_metrics"]), 6)

    def test_validator_rejects_market_cap_only_exclusion(self):
        entry = MODULE.make_entry(self.row, self.calendar, self.text)
        entry["publication_decision"] = "exclude"
        entry["publication_reason"] = "low market cap and N/A consensus"
        errors = MODULE.validate_ledger({"entries": [entry]})
        self.assertTrue(any("forbidden" in error for error in errors))

    def test_validator_accepts_inclusion_and_no_pending(self):
        entry = MODULE.make_entry(self.row, self.calendar, self.text)
        entry["publication_decision"] = "include"
        entry["publication_reason"] = "turnaround and cash-flow inflection can affect the property-services sector at the open"
        errors = MODULE.validate_ledger({"entries": [entry]})
        self.assertEqual(errors, [])

    def test_every_entry_needs_a_disposition(self):
        entry = MODULE.make_entry(self.row, self.calendar, self.text)
        errors = MODULE.validate_ledger({"entries": [entry]})
        self.assertTrue(any("pending" in error for error in errors))

    def test_futu_console_logs_do_not_break_json_parsing(self):
        output = '2026-09-01 INFO connected\n{"market":"HK","data":[{"security":"HK.02048"}]}\nINFO closed'
        payload = MODULE.parse_json_from_mixed_output(output)
        self.assertEqual(payload["data"][0]["security"], "HK.02048")

    def test_na_metrics_require_parse_but_not_permanent_inclusion(self):
        neutral_text = "Revenue was broadly stable. Profit remained positive and no material event was reported."
        neutral_row = dict(self.row)
        neutral_row["LONG_TEXT"] = "Announcements and Notices - [Interim Results]"
        entry = MODULE.make_entry(neutral_row, self.calendar, neutral_text)
        self.assertEqual(entry["review_status"], "screened_out")
        self.assertIn("document parsed", entry["screening_reason"])


if __name__ == "__main__":
    unittest.main()
