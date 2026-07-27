import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from compiler.llm import m1_audit_log_projection_adapter as adapter  # noqa: E402


FIXTURE_PATH = REPO_ROOT / adapter.RED_FIXTURE_PATH


def load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authority_for(projection: dict) -> dict:
    return {
        "status": adapter.TEST_AUTHORITY_STATUS,
        "scope": copy.deepcopy(adapter._EXPECTED_AUTHORITY_SCOPE),
        "pinned_hashes": {
            "a3_red_acceptance_sha256": adapter.A3_RED_ACCEPTANCE_SHA256,
            "projection_contract_sha256": adapter.PROJECTION_CONTRACT_SHA256,
            "mapping_contract_sha256": adapter.MAPPING_CONTRACT_SHA256,
            "external_evidence_v0_2_sha256": (
                adapter.EXTERNAL_EVIDENCE_V0_2_SHA256
            ),
            "kernel_additive_v0_2_sha256": (
                adapter.KERNEL_ADDITIVE_V0_2_SHA256
            ),
            "consumer_v0_3_sha256": adapter.CONSUMER_V0_3_SHA256,
            "adapter_implementation_sha256": file_sha256(
                REPO_ROOT / adapter.ADAPTER_IMPLEMENTATION_PATH
            ),
        },
        "pinned_input": {
            "source_class": adapter.SOURCE_CLASS,
            "projection_contract_sha256": adapter.PROJECTION_CONTRACT_SHA256,
            "projection_content_sha256": adapter.canonical_json_sha256(
                projection
            ),
        },
        "output_policy": copy.deepcopy(adapter._EXPECTED_OUTPUT_POLICY),
        "still_blocked": copy.deepcopy(adapter._EXPECTED_STILL_BLOCKED),
    }


class M1AuditLogProjectionAdapterTests(unittest.TestCase):
    def test_red_protected_and_new_identity_pins_are_exact(self):
        adapter.verify_adapter_pins(REPO_ROOT)
        review = json.loads(
            (REPO_ROOT / adapter.RED_REVIEW_PACKET_PATH).read_text(
                encoding="utf-8"
            )
        )
        inherited = {
            item["path"]: item["sha256"]
            for item in review["mandatory_pin_table"]
        }
        self.assertEqual(21, len(inherited))
        direct = {
            adapter.A3_RED_ACCEPTANCE_PATH: adapter.A3_RED_ACCEPTANCE_SHA256,
            adapter.RED_DESIGN_PATH: adapter.RED_DESIGN_SHA256,
            adapter.PROJECTION_CONTRACT_PATH: (
                adapter.PROJECTION_CONTRACT_SHA256
            ),
            adapter.MAPPING_CONTRACT_PATH: adapter.MAPPING_CONTRACT_SHA256,
            adapter.RED_FIXTURE_PATH: adapter.RED_FIXTURE_SHA256,
            adapter.RED_REVIEW_PACKET_PATH: adapter.RED_REVIEW_PACKET_SHA256,
            adapter.EXTERNAL_EVIDENCE_V0_2_PATH: (
                adapter.EXTERNAL_EVIDENCE_V0_2_SHA256
            ),
            adapter.KERNEL_ADDITIVE_V0_2_PATH: (
                adapter.KERNEL_ADDITIVE_V0_2_SHA256
            ),
            adapter.CONSUMER_V0_3_PATH: adapter.CONSUMER_V0_3_SHA256,
        }
        expected = {**inherited, **direct}
        actual = {
            path: file_sha256(REPO_ROOT / path) for path in expected
        }
        self.assertEqual(expected, actual)

    def test_missing_or_mutated_authority_fails_closed(self):
        projection = load_fixture()
        with self.assertRaises(
            adapter.M1AuditLogProjectionAdapterError
        ) as context:
            adapter.adapt_audit_log_public_projection(
                projection,
                repo_root=REPO_ROOT,
            )
        self.assertEqual("MISSING_TEST_ONLY_AUTHORITY", context.exception.code)

        authority = authority_for(projection)
        authority["output_policy"]["raw_source_read"] = True
        with self.assertRaises(
            adapter.M1AuditLogProjectionAdapterError
        ) as context:
            adapter.adapt_audit_log_public_projection(
                projection,
                repo_root=REPO_ROOT,
                authority=authority,
            )
        self.assertEqual(
            "DENY_CONSTANT_OR_PIN_MISMATCH",
            context.exception.code,
        )

    def test_reported_declaration_is_deterministic_and_not_elevated(self):
        projection = load_fixture()
        before = copy.deepcopy(projection)
        authority = authority_for(projection)
        first = adapter.adapt_audit_log_public_projection(
            projection,
            repo_root=REPO_ROOT,
            authority=authority,
        )
        second = adapter.adapt_audit_log_public_projection(
            copy.deepcopy(projection),
            repo_root=REPO_ROOT,
            authority=copy.deepcopy(authority),
        )
        self.assertEqual(first, second)
        self.assertEqual(before, projection)
        self.assertEqual("reported", first["source_metadata"]["epistemic_modality"])
        self.assertTrue(first["audit_entry"]["recorded_marker"])
        self.assertEqual("succeeded", first["audit_entry"]["reported_outcome"])
        text = json.dumps(first, sort_keys=True)
        for forbidden in (
            "truth_label",
            "authorization_proof",
            "source_field",
            "afs_slot",
            "CERTIFIED_STOP",
        ):
            self.assertNotIn(forbidden, text)

    def test_unknown_modality_abstains_without_package(self):
        projection = load_fixture()
        projection["source_metadata"].update(
            {
                "epistemic_modality": "unknown",
                "modality_basis_code": "UNRESOLVED_AUDIT_BASIS",
            }
        )
        before = copy.deepcopy(projection)
        with self.assertRaises(
            adapter.M1AuditLogProjectionAdapterError
        ) as context:
            adapter.adapt_audit_log_public_projection(
                projection,
                repo_root=REPO_ROOT,
                authority=authority_for(projection),
            )
        self.assertEqual("ABSTAIN_NO_PACKAGE", context.exception.code)
        self.assertEqual(before, projection)

    def test_observed_and_derived_are_modality_laundering(self):
        for modality in ("observed", "derived"):
            projection = load_fixture()
            projection["source_metadata"]["epistemic_modality"] = modality
            with self.subTest(modality=modality):
                with self.assertRaises(
                    adapter.M1AuditLogProjectionAdapterError
                ) as context:
                    adapter.adapt_audit_log_public_projection(
                        projection,
                        repo_root=REPO_ROOT,
                        authority=authority_for(projection),
                    )
                self.assertEqual(
                    "DENY_MODALITY_LAUNDERING",
                    context.exception.code,
                )

    def test_raw_text_bytes_path_uri_diff_body_token_and_oracle_are_denied(self):
        cases = []
        for field, value in (
            ("full_text", "raw audit line"),
            ("raw_bytes", b"raw"),
            ("filesystem_path", "C:\\private\\audit.log"),
            ("uri", "https://example.invalid/audit"),
            ("diff", "before -> after"),
            ("request_body", "{}"),
            ("authorization_token", "token"),
            ("oracle", True),
        ):
            projection = load_fixture()
            projection["audit_entry"][field] = value
            cases.append((field, projection))
        for field, projection in cases:
            with self.subTest(field=field):
                with self.assertRaises(
                    adapter.M1AuditLogProjectionAdapterError
                ) as context:
                    adapter.adapt_audit_log_public_projection(
                        projection,
                        repo_root=REPO_ROOT,
                        authority=authority_for(load_fixture()),
                    )
                self.assertIn(
                    context.exception.code,
                    {"DENY_RAW_AUDIT_MATERIAL", "DENY_PATH_OR_URI"},
                )

    def test_missing_unknown_marker_and_basis_mismatch_fail_closed(self):
        missing = load_fixture()
        del missing["audit_entry"]["entry_id"]
        unknown = load_fixture()
        unknown["audit_entry"]["unexpected"] = "x"
        marker = load_fixture()
        marker["audit_entry"]["recorded_marker"] = False
        basis = load_fixture()
        basis["source_metadata"]["modality_basis_code"] = (
            "UNRESOLVED_AUDIT_BASIS"
        )
        for name, projection, expected in (
            ("missing", missing, "DENY_UNKNOWN_OR_MISSING_FIELD"),
            ("unknown", unknown, "DENY_UNKNOWN_OR_MISSING_FIELD"),
            ("marker", marker, "DENY_RECORDED_MARKER"),
            ("basis", basis, "DENY_CONSTANT_OR_PIN_MISMATCH"),
        ):
            with self.subTest(case=name):
                with self.assertRaises(
                    adapter.M1AuditLogProjectionAdapterError
                ) as context:
                    adapter.adapt_audit_log_public_projection(
                        projection,
                        repo_root=REPO_ROOT,
                        authority=authority_for(projection),
                    )
                self.assertEqual(expected, context.exception.code)

    def test_system_log_alias_cross_modality_and_planner_namespace_are_denied(self):
        alias = load_fixture()
        alias["audit_entry"]["public_change_ref"] = (
            "evidence.system_log.event.event_id"
        )
        merged = load_fixture()
        merged["event"] = {"event_id": "smuggled"}
        planner = load_fixture()
        planner["audit_entry"]["source_field"] = "config.case_id"
        for name, projection, expected in (
            ("alias", alias, "DENY_NAMESPACE_ALIAS"),
            ("merged", merged, "DENY_CROSS_MODALITY_MERGE"),
            ("planner", planner, "DENY_PLANNER_NAMESPACE"),
        ):
            with self.subTest(case=name):
                with self.assertRaises(
                    adapter.M1AuditLogProjectionAdapterError
                ) as context:
                    adapter.adapt_audit_log_public_projection(
                        projection,
                        repo_root=REPO_ROOT,
                        authority=authority_for(projection),
                    )
                self.assertEqual(expected, context.exception.code)


if __name__ == "__main__":
    unittest.main()
