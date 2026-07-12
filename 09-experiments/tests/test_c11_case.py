import hashlib
import importlib.util
import json
import unittest
import zipfile
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
ROOT = EXPERIMENT_DIR.parent
DATA_DIR = EXPERIMENT_DIR / "real_data" / "otrf_apt29"
CASE_DIR = (
    EXPERIMENT_DIR
    / "real_cases"
    / "C11-otrf-apt29-day1-scranton-nashua"
)
MVP_PATH = EXPERIMENT_DIR / "scripts" / "run_mvp.py"
MVP_SPEC = importlib.util.spec_from_file_location("run_mvp_c11", MVP_PATH)
MVP = importlib.util.module_from_spec(MVP_SPEC)
assert MVP_SPEC.loader is not None
MVP_SPEC.loader.exec_module(MVP)


class C11CaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(
            (CASE_DIR / "case_config.json").read_text(encoding="utf-8")
        )
        cls.claims = json.loads(
            (CASE_DIR / "evidence_claims.json").read_text(encoding="utf-8")
        )
        cls.actions = json.loads(
            (CASE_DIR / "acquisition_actions.json").read_text(encoding="utf-8")
        )
        cls.report = json.loads(
            (CASE_DIR / "motif_report.json").read_text(encoding="utf-8")
        )
        cls.selection = json.loads(
            (DATA_DIR / "derived" / "R08_claim_selection.json").read_text(
                encoding="utf-8"
            )
        )

    def test_frozen_motif_spec_hash_is_unchanged(self):
        record = json.loads(
            (
                DATA_DIR
                / "derived"
                / "R08_motif_preregistration_record.json"
            ).read_text(encoding="utf-8")
        )
        path = ROOT / record["frozen_file"]["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        self.assertEqual(record["frozen_file"]["sha256"], digest)

    def test_d3_passes_without_replacing_the_failed_node(self):
        probe = json.loads(
            (DATA_DIR / "derived" / "R08_motif_probe.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("PASS", probe["d3_multiclaim_gate"])
        self.assertEqual(4, probe["passing_critical_node_count"])
        failed = next(
            node
            for node in probe["nodes"]
            if node["node_id"] == "N01_initial_breach_c2"
        )
        self.assertFalse(failed["multiclaim_node_pass"])
        self.assertEqual(0, failed["matched_record_count"])
        self.assertEqual(
            ["N01_initial_breach_c2"],
            [item["node_id"] for item in self.selection["missing_nodes"]],
        )

    def test_compiled_case_uses_and_and_is_downgraded_to_g2(self):
        self.assertEqual("AND", self.config["node_coverage_semantics"])
        self.assertEqual("G2_tactic_intent", self.config["target_granularity"])
        self.assertEqual("G2_tactic_intent", self.config["support_ceiling"])
        visible = {claim["claim_id"] for claim in self.claims}
        self.assertEqual(
            "G2_tactic_intent",
            MVP.supportable_granularity(self.config, visible),
        )
        self.assertEqual(
            "G2_tactic_intent",
            self.report["support_decision"]["compiled_ceiling"],
        )

    def test_each_compiled_node_has_two_provider_families(self):
        claims = {claim["claim_id"]: claim for claim in self.claims}
        for node in self.config["cti_nodes"]:
            if node["node_id"] == "N01_initial_breach_c2":
                self.assertEqual([], node["required_claim_ids"])
                continue
            families = {
                tag.split(":", 1)[1]
                for claim_id in node["required_claim_ids"]
                for tag in claims[claim_id]["tags"]
                if tag.startswith("provider:")
            }
            with self.subTest(node=node["node_id"]):
                self.assertEqual(2, len(node["required_claim_ids"]))
                self.assertEqual(2, len(families))

    def test_claims_pass_schema_and_exclude_zeek(self):
        schema = json.loads(
            (
                EXPERIMENT_DIR
                / "data_schema"
                / "evidence_claim.schema.json"
            ).read_text(encoding="utf-8")
        )
        validator = Draft202012Validator(
            schema,
            format_checker=FormatChecker(),
        )
        for claim in self.claims:
            with self.subTest(claim=claim["claim_id"]):
                validator.validate(claim)
                self.assertEqual(
                    "otrf_apt29_day1_host_events",
                    claim["source_pointer"]["artifact_id"],
                )

    def test_actions_are_cross_referenced_and_do_not_expose_exact_outcomes(self):
        claim_ids = {claim["claim_id"] for claim in self.claims}
        node_ids = {node["node_id"] for node in self.config["cti_nodes"]}
        for action in self.actions:
            with self.subTest(action=action["action_id"]):
                self.assertTrue(set(action["recoverable_claim_ids"]) <= claim_ids)
                self.assertTrue(set(action["intended_cti_node_ids"]) <= node_ids)
                self.assertFalse(
                    MVP.intended_equals_recoverable_or(self.config, action)
                )
                self.assertNotIn(
                    "recoverable_claim_ids",
                    MVP.planner_action_view(action),
                )

    def test_selected_source_records_match_frozen_anchors_when_raw_is_local(self):
        archive_path = DATA_DIR / "raw" / "apt29_evals_day1_manual.zip"
        if not archive_path.is_file():
            self.skipTest("local-only OTRF host archive is unavailable")
        selected = {
            item["line_number"]: item for item in self.selection["claims"]
        }
        seen = set()
        with zipfile.ZipFile(archive_path) as archive:
            with archive.open(archive.infolist()[0]) as handle:
                for line_number, raw_line in enumerate(handle, start=1):
                    item = selected.get(line_number)
                    if item is None:
                        continue
                    event = json.loads(raw_line)
                    searchable = " ".join(
                        str(value)
                        for value in event.values()
                        if isinstance(value, (str, int, float))
                    ).casefold()
                    self.assertIn(item["term"].casefold(), searchable)
                    self.assertIn(
                        str(event.get("RecordNumber")),
                        item["record_locator"],
                    )
                    seen.add(line_number)
        self.assertEqual(set(selected), seen)


if __name__ == "__main__":
    unittest.main()
