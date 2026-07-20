import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = (
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "audit_otrf_high_precision_record_anchors_v03.py"
)
SPEC = importlib.util.spec_from_file_location("otrf_anchor_audit_v03", SCRIPT_PATH)
AUDITOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = AUDITOR
SPEC.loader.exec_module(AUDITOR)


def write_scenario(root, name, metadata, records):
    metadata_dir = root / "_metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / f"{name}.yaml").write_text(
        yaml.safe_dump(metadata, sort_keys=False),
        encoding="utf-8",
    )
    scenario_dir = root / name
    scenario_dir.mkdir()
    with zipfile.ZipFile(scenario_dir / "events.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "events.json",
            "".join(json.dumps(record) + "\n" for record in records),
        )


def metadata(tool_name, script, *, linked=False, description="narrative-secret"):
    tool = {"name": tool_name, "script": script, "type": "utility"}
    mapping = {"technique": "label-secret", "tactics": ["tactic-secret"]}
    if linked:
        tool["technique_id"] = "mapping-secret"
    return {
        "description": description,
        "simulation": {"tools": [tool]},
        "attack_mappings": [mapping],
    }


class OtrfHighPrecisionAnchorAuditTests(unittest.TestCase):
    def run_audit(self, root, specs, max_records=5):
        return AUDITOR.audit_compound_scenarios(
            root,
            specs,
            commitment_key=b"private-test-commitment-key",
            max_records_per_anchor=max_records,
        )

    def test_report_retains_only_commitments_fields_ordinals_and_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_scenario(
                root,
                "scenario-one",
                metadata(
                    "HighlyUniqueDumpTool.exe",
                    "Invoke-HighlyUniqueDumpTool HighlyUniqueDumpTool.exe",
                    linked=True,
                ),
                [
                    {"Message": "ran HighlyUniqueDumpTool.exe", "Host": "host-secret"},
                    {"Message": "unrelated payload-secret", "Host": "other-secret"},
                ],
            )
            report = self.run_audit(
                root,
                [AUDITOR.ScenarioSpec("C013-final-blind", "scenario-one")],
            )

        case = report["case_reports"][0]
        self.assertTrue(case["record_anchor_gate_passed"])
        self.assertTrue(case["explicit_mapping_linkage_present"])
        self.assertTrue(case["automatic_case_bundle_ready"])
        self.assertEqual(1, case["rare_anchors"][0]["record_hit_count"])
        record = case["rare_anchors"][0]["records"][0]
        self.assertEqual(["Message"], record["matched_field_names"])
        self.assertEqual(1, record["line_number"])
        self.assertEqual("raw_jsonl_line", record["record_hash_basis"])
        self.assertRegex(record["record_sha256"], r"^[0-9a-f]{64}$")
        serialized = json.dumps(report)
        for secret in (
            "HighlyUniqueDumpTool",
            "payload-secret",
            "host-secret",
            "narrative-secret",
            "label-secret",
            "mapping-secret",
            "scenario-one",
        ):
            self.assertNotIn(secret, serialized)
        self.assertFalse(report["payload_values_disclosed"])
        self.assertFalse(report["attack_label_values_disclosed"])
        self.assertFalse(report["one_shot_evaluation_consumed"])

    def test_cross_scenario_common_anchor_is_not_rare(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            common = "SharedSpecificCollector.exe"
            write_scenario(
                root,
                "eligible",
                metadata(common, common, linked=True),
                [{"Message": common}],
            )
            write_scenario(
                root,
                "comparison",
                metadata(common, common, linked=True),
                [{"Message": common}],
            )
            report = self.run_audit(
                root,
                [
                    AUDITOR.ScenarioSpec("C013-final-blind", "eligible"),
                    AUDITOR.ScenarioSpec("X-comparison", "comparison", True),
                ],
            )

        case = report["case_reports"][0]
        self.assertEqual(0, case["rare_anchor_count"])
        self.assertIn(
            "no_cross_scenario_unique_low_frequency_record_anchor",
            case["source_specific_blockers"],
        )

    def test_event_anchor_does_not_substitute_for_mapping_linkage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tool = "SemanticallyUnboundTool.exe"
            write_scenario(
                root,
                "unbound",
                metadata(tool, tool, linked=False),
                [{"Message": tool}],
            )
            report = self.run_audit(
                root,
                [AUDITOR.ScenarioSpec("C013-final-blind", "unbound")],
            )

        case = report["case_reports"][0]
        self.assertTrue(case["record_anchor_gate_passed"])
        self.assertFalse(case["explicit_mapping_linkage_present"])
        self.assertFalse(case["automatic_case_bundle_ready"])
        self.assertIn(
            "no_explicit_tool_to_attack_mapping_linkage",
            case["source_specific_blockers"],
        )

    def test_description_text_is_never_an_anchor_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            description_only = "DescriptionOnlySecretTool.exe"
            write_scenario(
                root,
                "description-only",
                metadata(
                    "powershell",
                    "powershell",
                    linked=True,
                    description=description_only,
                ),
                [{"Message": description_only}],
            )
            report = self.run_audit(
                root,
                [AUDITOR.ScenarioSpec("C013-final-blind", "description-only")],
            )

        case = report["case_reports"][0]
        self.assertEqual(0, case["candidate_anchor_count"])
        self.assertEqual(0, case["rare_anchor_count"])

    def test_high_frequency_anchor_fails_rarity_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tool = "FrequentSpecificTool.exe"
            write_scenario(
                root,
                "frequent",
                metadata(tool, tool, linked=True),
                [{"Message": tool} for _ in range(4)],
            )
            report = self.run_audit(
                root,
                [AUDITOR.ScenarioSpec("C013-final-blind", "frequent")],
                max_records=3,
            )

        case = report["case_reports"][0]
        self.assertEqual(0, case["rare_anchor_count"])
        self.assertFalse(case["record_anchor_gate_passed"])

    def test_nested_multiline_document_yields_record_ordinals_without_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tool = "NestedDocumentTool.exe"
            metadata_dir = root / "_metadata"
            metadata_dir.mkdir()
            (metadata_dir / "nested.yaml").write_text(
                yaml.safe_dump(metadata(tool, tool, linked=True), sort_keys=False),
                encoding="utf-8",
            )
            scenario_dir = root / "nested"
            scenario_dir.mkdir()
            document = {"wrapper": {"events": [{"Message": tool}, {"Message": "secret"}]}}
            with zipfile.ZipFile(
                scenario_dir / "events.zip", "w", zipfile.ZIP_DEFLATED
            ) as archive:
                archive.writestr("events.json", json.dumps(document, indent=2))
            report = self.run_audit(
                root,
                [AUDITOR.ScenarioSpec("C013-final-blind", "nested")],
            )

        record = report["case_reports"][0]["rare_anchors"][0]["records"][0]
        self.assertEqual(1, record["record_ordinal"])
        self.assertIsNone(record["line_number"])
        self.assertEqual("canonical_json", record["record_hash_basis"])
        self.assertNotIn("NestedDocumentTool", json.dumps(report))

    def test_jsonl_line_number_counts_blank_lines(self):
        payload = (
            b"\n"
            + json.dumps({"Message": "FirstSpecificTool.exe"}).encode()
            + b"\n\n"
            + json.dumps({"Message": "SecondSpecificTool.exe"}).encode()
            + b"\n"
        )
        import io

        records = list(
            AUDITOR.records_from_json_stream(
                io.BytesIO(payload),
                artifact_id="artifact",
                member_id="member",
            )
        )
        self.assertEqual([2, 4], [record.line_number for record in records])

    def test_cli_scenario_parser_rejects_path_escape(self):
        with self.assertRaises(Exception):
            AUDITOR.parse_scenario("C013-final-blind=../outside", False)

    def test_duplicate_comparison_identifiers_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tool = "DuplicateGuardTool.exe"
            for name in ("eligible", "comparison-one", "comparison-two"):
                write_scenario(
                    root,
                    name,
                    metadata(tool, tool, linked=True),
                    [{"Message": tool}],
                )
            with self.assertRaisesRegex(ValueError, "identifiers must be unique"):
                self.run_audit(
                    root,
                    [
                        AUDITOR.ScenarioSpec("C013-final-blind", "eligible"),
                        AUDITOR.ScenarioSpec("comparison", "comparison-one", True),
                        AUDITOR.ScenarioSpec("comparison", "comparison-two", True),
                    ],
                )


if __name__ == "__main__":
    unittest.main()
