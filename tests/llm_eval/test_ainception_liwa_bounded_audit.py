from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "datasets"
    / "llm"
    / "audit_ainception_liwa_bounded.py"
)
SPEC = importlib.util.spec_from_file_location("bounded_audit", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BoundedAuditContractTest(unittest.TestCase):
    def test_member_path_normalization_rejects_traversal(self) -> None:
        self.assertIsNone(MODULE._normalized_member_path("../secret.csv"))
        self.assertEqual(
            MODULE._normalized_member_path("folder\\events.csv"),
            "folder/events.csv",
        )

    def test_policy_token_matches_tokenized_path(self) -> None:
        self.assertTrue(
            MODULE._has_policy_token(
                "scenario/ground-truth/events.csv", ["ground_truth"]
            )
        )
        self.assertFalse(
            MODULE._has_policy_token("scenario/raw/events.csv", ["ground_truth"])
        )

    def test_liwa_view_tokens_collapse_paired_names(self) -> None:
        view_tokens = {
            "native",
            "sysmon",
            "wazuh",
            "enhanced",
            "windows",
            "security",
            "events",
            "csv",
        }
        native = MODULE._derive_liwa_run_token(
            "Kerberoasting_native_run_03.csv", view_tokens
        )
        enhanced = MODULE._derive_liwa_run_token(
            "Kerberoasting_sysmon_wazuh_run_03.csv", view_tokens
        )
        self.assertEqual(native, enhanced)
        self.assertIsNotNone(native)

    def test_liwa_run_token_requires_numeric_identity(self) -> None:
        self.assertIsNone(
            MODULE._derive_liwa_run_token(
                "Kerberoasting_native.csv", {"native", "csv"}
            )
        )

    def test_contract_local_root_must_remain_in_worktree(self) -> None:
        contract = {
            "status": "frozen_before_payload_acquisition",
            "scope": {
                "label_value_read_authorized": False,
                "ground_truth_read_authorized": False,
                "supervision_generation_authorized": False,
                "normalization_generation_authorized": False,
                "family_role_change_authorized": False,
                "quota_status_change_authorized": False,
                "train_admission_authorized": False,
                "baseline_authorized": False,
                "fine_tuning_authorized": False,
                "l2_gate_passed": False,
                "git_push_authorized": False,
            },
            "acquisition": {
                "local_root": "../outside",
                "maximum_total_download_bytes": 5,
                "files": [
                    {
                        "source_family_id": "ainception_zenodo_2025",
                        "local_relative_path": f"a/{index}.zip",
                        "download_url": "https://zenodo.org/api/records/1/files/x/content",
                        "expected_bytes": 1,
                    }
                    for index in range(4)
                ]
                + [
                    {
                        "source_family_id": "liwa_ad_endpoint_telemetry_30run_2026",
                        "local_relative_path": "b/0.zip",
                        "download_url": "https://zenodo.org/api/records/2/files/x/content",
                        "expected_bytes": 1,
                    }
                ],
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(MODULE.AuditBlocked):
                MODULE._validate_contract(contract, Path(directory))


if __name__ == "__main__":
    unittest.main()
