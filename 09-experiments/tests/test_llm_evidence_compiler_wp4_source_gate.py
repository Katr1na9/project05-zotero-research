import copy
import importlib.util
import json
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
CATALOG_PATH = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "wp4"
    / "cti-text-source-catalog-v0.1.json"
)


def load_script(name):
    path = EXPERIMENT_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gate = load_script("validate_compiler_cti_source_gate")


def load_catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def activate(catalog, *source_ids):
    selected = set(source_ids)
    for item in catalog["candidates"]:
        if item["source_id"] in selected:
            item["user_decision"] = "conditional_approve"
            item["retrieval_authorized"] = True


class CTITextSourceGateTests(unittest.TestCase):
    def test_authoritative_catalog_authorizes_only_bounded_retrieval(self):
        catalog = load_catalog()
        report = gate.validate_catalog(catalog, repo_root=REPO_ROOT)
        self.assertEqual(
            "ready_for_bounded_retrieval_and_payload_scan", report["status"]
        )
        self.assertEqual([], report["errors"])
        self.assertEqual(7, report["counts"]["candidate_sources"])
        self.assertEqual(3, report["counts"]["eligible_sources"])
        self.assertEqual(0, report["counts"]["pending_user_decisions"])
        self.assertEqual(3, report["counts"]["activated_sources"])
        self.assertFalse(catalog["raw_cti_text_present"])
        self.assertFalse(catalog["corpus_downloaded"])
        self.assertTrue(report["authorization"]["bounded_retrieval"])
        self.assertFalse(report["authorization"]["component_runtime"])
        self.assertFalse(report["authorization"]["controller_integration"])

    def test_three_publisher_blocked_roles_can_authorize_only_bounded_retrieval(self):
        catalog = load_catalog()
        activate(
            catalog,
            "ctid_blueprints_intrusion_sample",
            "mitre_attack_software_procedure_text",
            "tram_cisa_first_party_advisory_subset",
        )
        report = gate.validate_catalog(catalog, repo_root=REPO_ROOT)
        self.assertEqual(
            "ready_for_bounded_retrieval_and_payload_scan", report["status"]
        )
        self.assertEqual([], report["errors"])
        self.assertTrue(report["authorization"]["bounded_retrieval"])
        self.assertFalse(report["authorization"]["payload_normalization"])
        self.assertFalse(report["authorization"]["component_runtime"])
        self.assertFalse(report["authorization"]["C07_C12_execution"])
        self.assertEqual(
            {
                "unit": ["ctid_blueprints"],
                "development": ["mitre_attack"],
                "component_validation": ["cisa_first_party_advisories"],
            },
            report["role_to_publisher_families"],
        )

    def test_missing_role_or_family_fails_closed_after_decisions(self):
        catalog = load_catalog()
        catalog["candidates"][2]["user_decision"] = "reject"
        catalog["candidates"][2]["retrieval_authorized"] = False
        report = gate.validate_catalog(catalog, repo_root=None)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("missing_required_roles:component_validation", report["errors"])
        self.assertIn("insufficient_distinct_publisher_families", report["errors"])

    def test_publisher_family_cannot_cross_roles(self):
        catalog = load_catalog()
        activate(
            catalog,
            "ctid_blueprints_intrusion_sample",
            "mitre_attack_software_procedure_text",
            "tram_cisa_first_party_advisory_subset",
        )
        catalog["candidates"][2]["publisher_family"] = "mitre_attack"
        report = gate.validate_catalog(catalog, repo_root=None)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("publisher_family_crosses_roles:mitre_attack", report["errors"])

    def test_rejected_mixed_corpus_cannot_be_activated(self):
        catalog = load_catalog()
        catalog["candidates"][0]["user_decision"] = "reject"
        catalog["candidates"][1]["user_decision"] = "reject"
        catalog["candidates"][2]["user_decision"] = "reject"
        catalog["candidates"][0]["retrieval_authorized"] = False
        catalog["candidates"][1]["retrieval_authorized"] = False
        catalog["candidates"][2]["retrieval_authorized"] = False
        activate(catalog, "tram_full_mjson_corpus")
        report = gate.validate_catalog(catalog, repo_root=None)
        self.assertEqual("failed_closed", report["status"])
        self.assertIn("ineligible_source_activated:tram_full_mjson_corpus", report["errors"])

    def test_unapproved_retrieval_or_legacy_mutation_fails_closed(self):
        catalog = load_catalog()
        catalog["candidates"][0]["user_decision"] = "pending"
        catalog["candidates"][0]["retrieval_authorized"] = True
        report = gate.validate_catalog(catalog, repo_root=None)
        self.assertIn(
            "retrieval_authorized_without_approval:ctid_blueprints_intrusion_sample",
            report["errors"],
        )

        clean = load_catalog()
        clean["legacy_inheritance_lock"]["09-experiments/scripts/run_mvp.py"] = "0" * 64
        report = gate.validate_catalog(clean, repo_root=REPO_ROOT)
        self.assertIn(
            "legacy_lock_hash_mismatch:09-experiments/scripts/run_mvp.py",
            report["errors"],
        )

    def test_concurrent_m3_boundary_keeps_sidecars_ineligible(self):
        catalog = load_catalog()
        boundary = catalog["concurrency_boundary"]
        self.assertTrue(boundary["parallel_work_allowed"])
        self.assertIn("09-experiments/scripts/run_m3star.py", boundary["llm_forbidden_write_roots"])
        self.assertIn("09-experiments/results/m3star_*", boundary["llm_forbidden_write_roots"])
        self.assertTrue(
            all(item["controller_eligible"] is False for item in catalog["candidates"])
        )


if __name__ == "__main__":
    unittest.main()
