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
    / "audit_cam_lds_command_record_linkage_v03.py"
)
SPEC = importlib.util.spec_from_file_location("cam_linkage_audit_v03", SCRIPT_PATH)
AUDITOR = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = AUDITOR
SPEC.loader.exec_module(AUDITOR)
KEY = b"private-test-key-material-at-least-32-bytes"


def command_document(command_pairs):
    return {
        "commands": [
            {
                "type": "action",
                "cmd": command,
                "metadata": {
                    "tactics": f"secret-tactic-{index}",
                    "techniques": f"secret-technique-{index}",
                    "technique_name": f"secret-name-{index}",
                },
            }
            for index, command in enumerate(command_pairs, start=1)
        ]
    }


def write_archive(
    path,
    command_pairs,
    json_records=(),
    log_lines=(),
    include_mapping=True,
):
    document = command_document(command_pairs)
    if not include_mapping:
        for item in document["commands"]:
            item.pop("metadata")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "config/actions.yaml",
            yaml.safe_dump(document, sort_keys=False),
        )
        if json_records:
            archive.writestr(
                "telemetry/events.json",
                "".join(json.dumps(record) + "\n" for record in json_records),
            )
        if log_lines:
            archive.writestr(
                "telemetry/audit.log",
                "".join(line + "\n" for line in log_lines),
            )


class CamLdsCommandRecordLinkageTests(unittest.TestCase):
    def run_audit(self, cases, max_records=5):
        return AUDITOR.audit_cam_archives(
            cases,
            commitment_key=KEY,
            maximum_records_per_anchor=max_records,
            minimum_distinct_mapping_commitments=2,
        )

    def test_two_source_mapped_commands_anchor_a_chain_without_value_return(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = "UniqueCollectorOne.exe --mode 71"
            second = "UniqueCollectorTwo.exe --mode 92"
            archive = root / "case.zip"
            write_archive(
                archive,
                [first, second],
                json_records=[
                    {"cmd": first, "host": "private-host-one"},
                    {"command": second, "label": "private-label"},
                ],
            )
            report = self.run_audit(
                [AUDITOR.CaseArchive("C021-final-blind", archive)]
            )

        case = report["case_reports"][0]
        self.assertTrue(case["source_native_mapping_gate_passed"])
        self.assertTrue(case["command_record_anchor_gate_passed"])
        self.assertTrue(case["minimum_chain_mapping_gate_passed"])
        self.assertTrue(case["automatic_case_bundle_ready"])
        self.assertGreaterEqual(case["distinct_anchored_mapping_count"], 2)
        serialized = json.dumps(report)
        for forbidden in (
            "UniqueCollector",
            "private-host",
            "private-label",
            "secret-tactic",
            "secret-technique",
            "secret-name",
            "actions.yaml",
            "events.json",
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertFalse(report["command_values_disclosed"])
        self.assertFalse(report["telemetry_values_disclosed"])
        self.assertFalse(report["one_shot_evaluation_consumed"])

    def test_cross_case_common_command_is_not_unique(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            common = "SharedMappedCollector.exe --mode 33"
            eligible = root / "eligible.zip"
            comparison = root / "comparison.zip"
            write_archive(eligible, [common], json_records=[{"cmd": common}])
            write_archive(comparison, [], json_records=[{"cmd": common}])
            report = self.run_audit(
                [
                    AUDITOR.CaseArchive("C021-final-blind", eligible),
                    AUDITOR.CaseArchive("X-comparison", comparison, True),
                ]
            )

        case = report["case_reports"][0]
        self.assertEqual(0, case["rare_unambiguous_anchor_count"])
        self.assertIn(
            "no_cross_case_unique_low_frequency_mapped_command_record_anchor",
            case["source_specific_blockers"],
        )

    def test_one_anchored_mapping_is_not_a_chain(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command = "SingleMappedCollector.exe --mode 44"
            archive = root / "single.zip"
            write_archive(archive, [command], json_records=[{"cmd": command}])
            report = self.run_audit(
                [AUDITOR.CaseArchive("C021-final-blind", archive)]
            )

        case = report["case_reports"][0]
        self.assertTrue(case["command_record_anchor_gate_passed"])
        self.assertFalse(case["minimum_chain_mapping_gate_passed"])
        self.assertFalse(case["automatic_case_bundle_ready"])
        self.assertIn(
            "insufficient_distinct_record_anchored_attack_mappings",
            case["source_specific_blockers"],
        )

    def test_unmapped_command_document_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command = "UnmappedCollectorTool.exe --mode 55"
            archive = root / "unmapped.zip"
            write_archive(
                archive,
                [command],
                json_records=[{"cmd": command}],
                include_mapping=False,
            )
            report = self.run_audit(
                [AUDITOR.CaseArchive("C027-final-blind", archive)]
            )

        case = report["case_reports"][0]
        self.assertFalse(case["source_native_mapping_gate_passed"])
        self.assertFalse(case["automatic_case_bundle_ready"])
        self.assertIn(
            "no_source_native_attack_mapping",
            case["source_specific_blockers"],
        )

    def test_structured_log_command_field_is_scanned_but_generic_path_is_not(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = "LogMappedCollectorOne.exe --mode 61"
            second = "LogMappedCollectorTwo.exe --mode 62"
            archive = root / "logs.zip"
            write_archive(
                archive,
                [first, second],
                log_lines=[
                    f'COMMAND="{first}" path="{second}"',
                    f'cmd="{second}"',
                ],
            )
            report = self.run_audit(
                [AUDITOR.CaseArchive("C021-final-blind", archive)]
            )

        case = report["case_reports"][0]
        self.assertTrue(case["automatic_case_bundle_ready"])
        matched_fields = {
            field
            for anchor in case["rare_anchors"]
            for record in anchor["records"]
            for field in record["matched_field_names"]
        }
        self.assertIn("COMMAND", matched_fields)
        self.assertIn("cmd", matched_fields)
        self.assertNotIn("path", matched_fields)

    def test_high_frequency_command_fails_rarity_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command = "FrequentMappedCollector.exe --mode 81"
            archive = root / "frequent.zip"
            write_archive(
                archive,
                [command],
                json_records=[{"cmd": command} for _ in range(4)],
            )
            report = self.run_audit(
                [AUDITOR.CaseArchive("C021-final-blind", archive)],
                max_records=3,
            )

        case = report["case_reports"][0]
        self.assertFalse(case["command_record_anchor_gate_passed"])

    def test_same_token_bound_to_multiple_mappings_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            command = "AmbiguousMappedCollector.exe --mode 72"
            archive = root / "ambiguous.zip"
            write_archive(
                archive,
                [command, command],
                json_records=[{"cmd": command}],
            )
            report = self.run_audit(
                [AUDITOR.CaseArchive("C021-final-blind", archive)]
            )

        case = report["case_reports"][0]
        self.assertEqual(0, case["rare_unambiguous_anchor_count"])
        self.assertFalse(case["automatic_case_bundle_ready"])

    def test_json_command_document_cannot_match_itself_as_telemetry(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = "SelfMatchGuardOne.exe --mode 73"
            second = "SelfMatchGuardTwo.exe --mode 74"
            archive_path = root / "json-command-doc.zip"
            with zipfile.ZipFile(
                archive_path,
                "w",
                zipfile.ZIP_DEFLATED,
            ) as archive:
                archive.writestr(
                    "config/actions.json",
                    json.dumps(command_document([first, second])),
                )
            report = self.run_audit(
                [AUDITOR.CaseArchive("C021-final-blind", archive_path)]
            )

        case = report["case_reports"][0]
        self.assertEqual(0, case["parsed_record_count"])
        self.assertEqual(0, case["rare_unambiguous_anchor_count"])
        self.assertFalse(case["command_record_anchor_gate_passed"])


if __name__ == "__main__":
    unittest.main()
