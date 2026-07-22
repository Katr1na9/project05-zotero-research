import copy
import json
import unittest
from pathlib import Path

import yaml

from jsonschema import Draft202012Validator, FormatChecker

from src.ir.canonical_hash import canonical_document_hash


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas"
SCHEMA_NAMES = (
    "claim-ir-kernel.schema.json",
    "gamma-kernel.schema.json",
    "action-kernel.schema.json",
    "certificate.schema.json",
    "counterexample.schema.json",
    "admission-policy.schema.json",
    "policy-approval.schema.json",
    "formal-ceiling.schema.json",
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validator_for_definition(schema, definition):
    wrapper = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": schema["$defs"],
        "$ref": f"#/$defs/{definition}",
    }
    return Draft202012Validator(wrapper, format_checker=FormatChecker())


def candidate_response():
    return {
        "schema_version": "0.8.0",
        "request_id": "REQ-TWIN-001",
        "candidates": [
            {
                "candidate_id": "CAND-001",
                "subject": {"entity_id": "H3", "entity_type": "host"},
                "predicate": "authenticated_account",
                "object": {
                    "entity_id": "ACCOUNT-A",
                    "literal": None,
                    "entity_type": "account",
                },
                "time": {
                    "start": "2026-01-01T10:04:00Z",
                    "end": "2026-01-01T10:04:00Z",
                    "precision": "exact",
                },
                "location": {"host": "H3", "tenant": "T1", "zone": None},
                "polarity": "positive",
                "binding_proposals": [
                    {"field": "subject.entity_id", "entity_id": "H3"}
                ],
                "abstention": None,
            }
        ],
    }


def kernel_claim():
    return {
        "schema_version": "0.8.0",
        "claim_id": "TWIN-EC-001",
        "subject": {"entity_id": "H3", "entity_type": "host"},
        "predicate": "authenticated_account",
        "object": {
            "entity_id": "ACCOUNT-A",
            "literal": None,
            "entity_type": "account",
        },
        "time": {
            "start": "2026-01-01T10:04:00Z",
            "end": "2026-01-01T10:04:00Z",
            "precision": "exact",
        },
        "location": {"host": "H3", "tenant": "T1", "zone": None},
        "polarity": "positive",
        "modality": "observed",
        "truth_status": "supported",
        "epistemic_role": "case_evidence",
        "certification_authority": {
            "allowed": True,
            "levels": ["compromised_host"],
            "basis_rule_id": "A001",
            "policy_hash": "sha256:8f34a5e99c2cba3d79304667acd5bb010492af74b8b99425352375a796825671",
        },
        "source_family": "identity",
        "source_schema": "twin.auth.v0.8",
        "pointer": {
            "source_id": "auth.jsonl",
            "record_id": "AUTH-001",
            "byte_or_row_range": [1, 1],
            "content_hash": "sha256:" + "2" * 64,
        },
        "compiler": {
            "parser_id": "fixture-parser",
            "parser_version": "0.8.0",
            "model_id": None,
            "prompt_or_rule_hash": "sha256:" + "3" * 64,
        },
        "binding_status": "bound",
        "admission_status": "admitted",
        "promotion_status": "none",
        "promotion_event_id": None,
        "admissible_levels": ["compromised_host"],
        "support_claim_ids": [],
        "contradict_claim_ids": [],
        "rule_trace": ["A001"],
        "confidence": {"extraction": 1.0, "source": 1.0, "model": None},
        "lifecycle_state": "admitted",
    }


def deterministic_action_catalog():
    return {
        "schema_version": "0.8.0",
        "catalog_id": "test-catalog",
        "catalog_version": "0.8.0",
        "actions": [
            {
                "action_id": "query_auth_h1",
                "actor": "automated_tool",
                "authority": {
                    "required_permissions": ["read:auth"],
                    "current_status": "executable",
                },
                "target": {"entity_ids": ["H1"], "entity_type": "host"},
                "scope": {
                    "time_window": {
                        "start": "2026-01-01T10:00:00Z",
                        "end": "2026-01-01T10:15:00Z",
                    },
                    "spatial_scope": "tenant:T1/host:H1",
                    "resolution": "event",
                },
                "preconditions": ["sensor_up(auth-H1)"],
                "invocation": {
                    "executor_id": "auth-query-v0.8",
                    "query_template_id": "auth-by-host-window",
                    "parameters": {"host": "H1"},
                },
                "termination": {
                    "timeout_seconds": 30,
                    "success_conditions": ["valid_output_schema"],
                    "failure_conditions": ["timeout", "permission_denied"],
                },
                "observation_model": {
                    "observable_id": "kerberos_auth",
                    "output_schema": "kernel.auth-presence.v0.8",
                    "projection_rule_id": "auth-presence-by-origin-v1",
                    "noise_model": "deterministic",
                    "output_domain": ["present", "absent"],
                    "absence_semantics_ref": "auth-H1",
                    "world_dependencies": ["credential_activity(H1)"],
                },
                "formal_analysis_eligibility": "formal",
                "state_effect": {
                    "claim_template_ids": ["auth-observation-v1"],
                    "world_elimination_rule_ids": ["zero-hit-auth-v1"],
                },
                "feasibility": {"status": "executable", "reason_codes": []},
                "resource_instrumentation": {
                    "wall_seconds": True,
                    "cpu_seconds": False,
                    "bytes_scanned": True,
                    "records_scanned": True,
                    "analyst_seconds": False,
                },
            }
        ],
        "hash": "sha256:" + "4" * 64,
    }


def valid_certificate():
    return {
        "schema_version": "0.8.0",
        "certificate_id": "CERT-001",
        "case_id": "TWIN-CERT-001",
        "issued_by": "kernel_checker",
        "gamma_hash": "sha256:" + "1" * 64,
        "evidence_hash": "sha256:" + "2" * 64,
        "admission_policy_hash": "sha256:8f34a5e99c2cba3d79304667acd5bb010492af74b8b99425352375a796825671",
        "admission_policy_approval_hash": "sha256:2eda84dd347d1a0acdf8802edb01e7ba1cd00c6b8e767d02d78170e3d0fd1f8b",
        "formal_ceiling_hash": "sha256:9a91a99b1dfdf2c00d4a81761d1952e8f9113ce0cc841fbcaa19c2f0ae685cde",
        "level": "initial_foothold",
        "conclusion": {"entity_id": "H1", "entity_type": "host"},
        "certification_scope": "level_complete",
        "candidate_coverage": {
            "level": "initial_foothold",
            "mode": "exhaustive",
            "declared_domain_size": 2,
            "checked_count": 2,
            "result_candidates": ["H1", "H3"],
            "legal_world_count": 2,
            "legal_worlds_hash": "sha256:6d4bbedd4bf705be0e6a0dce9cc5440948be163e496cf96c55ba2d33fd0a080c",
            "cartesian_assignment_bound": 4,
            "omitted_known_candidates": [],
            "solver_seed_used": True,
        },
        "core_query_results": {
            "base": "SAT",
            "support": "SAT",
            "alternative": "UNSAT",
        },
        "level_certification": {
            "all_legal_results_covered": True,
            "exactly_one_feasible_result": True,
            "all_critical_queries_known": True,
        },
        "positive_witness": ["TWIN-EC-001"],
        "proof_artifact": {
            "proof_level": "reproducible_run",
            "solver": "finite_domain_enumerator",
            "solver_version": "0.8.0",
            "query_hashes": ["sha256:" + "3" * 64],
            "artifact_uri": None,
        },
        "critical_scope_assumptions": ["auth-H1 bounded completeness holds"],
        "promotion_dependencies": [],
        "created_at": "2026-01-01T10:20:00Z",
        "status": "valid",
    }


def counterexample_with_timeout_mindiff():
    return {
        "schema_version": "0.8.0",
        "counterexample_id": "CEX-001",
        "case_id": "TWIN-COUNTEREXAMPLE-001",
        "gamma_hash": "sha256:" + "1" * 64,
        "evidence_hash": "sha256:" + "2" * 64,
        "target_level": "initial_foothold",
        "candidate_q": {"entity_id": "H1", "entity_type": "host"},
        "checker_status": "COUNTEREXAMPLE_FOUND",
        "core_query_results": {"base": "SAT", "support": "SAT", "alternative": "SAT"},
        "support_world": {
            "world_id": "W-SUPPORT",
            "target_result": {"entity_id": "H1", "entity_type": "host"},
            "predicates": ["credential_activity(H1)"],
        },
        "alternative_world": {
            "world_id": "W-ALT",
            "target_result": {"entity_id": "H3", "entity_type": "host"},
            "predicates": ["external_auth_origin(H3)"],
        },
        "shared_predicates": ["suspicious_account_activity(H3)"],
        "support_only_predicates": ["credential_activity(H1)"],
        "alternative_only_predicates": ["external_auth_origin(H3)"],
        "distinguishing_predicates": ["auth_origin(H3)"],
        "critical_absence_semantics": ["auth-H1:bounded_completeness"],
        "minimization_status": "TIMEOUT",
        "generation_basis": "kernel_checker",
    }


class KernelSchemaTests(unittest.TestCase):
    def test_all_kernel_schemas_exist_and_are_valid_draft_2020_12(self):
        self.assertEqual(SCHEMA_NAMES, tuple(path.name for path in map(SCHEMA_DIR.__truediv__, SCHEMA_NAMES)))
        for name in SCHEMA_NAMES:
            path = SCHEMA_DIR / name
            self.assertTrue(path.is_file(), name)
            schema = load_json(path)
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
            Draft202012Validator.check_schema(schema)

    def test_policy_and_approved_manifest_are_schema_valid_and_hashed(self):
        vectors = (
            (
                "admission-policy.schema.json",
                "admission-policy-kernel-v0.8.yaml",
            ),
            (
                "policy-approval.schema.json",
                "admission-policy-approval-kernel-v0.8.yaml",
            ),
        )
        for schema_name, config_name in vectors:
            with self.subTest(config=config_name):
                schema = load_json(SCHEMA_DIR / schema_name)
                document = yaml.safe_load(
                    (ROOT / "configs" / config_name).read_text(encoding="utf-8")
                )
                validator = Draft202012Validator(
                    schema, format_checker=FormatChecker()
                )
                self.assertEqual([], list(validator.iter_errors(document)))
                self.assertEqual(document["hash"], canonical_document_hash(document))

        manifest = yaml.safe_load(
            (
                ROOT
                / "configs"
                / "admission-policy-approval-kernel-v0.8.yaml"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual("APPROVED", manifest["decision"])
        self.assertEqual("Project05 repository owner", manifest["approved_by"])

    def test_candidate_compiler_profile_accepts_candidate_only_output(self):
        schema = load_json(SCHEMA_DIR / "claim-ir-kernel.schema.json")
        validator = validator_for_definition(schema, "candidateCompilerResponse")
        self.assertEqual([], list(validator.iter_errors(candidate_response())))

        leaked = candidate_response()
        leaked["candidates"][0]["certification_authority"] = {"allowed": True}
        self.assertTrue(list(validator.iter_errors(leaked)))

    def test_full_claim_keeps_modality_truth_role_and_authority_separate(self):
        schema = load_json(SCHEMA_DIR / "claim-ir-kernel.schema.json")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual([], list(validator.iter_errors(kernel_claim())))

        promoted = kernel_claim()
        promoted.update(
            {
                "modality": "reported",
                "promotion_status": "promoted",
                "promotion_event_id": "PROM-001",
            }
        )
        promoted["pointer"].update({"record_id": None, "content_hash": None})
        self.assertTrue(list(validator.iter_errors(promoted)))

    def test_action_catalog_rejects_stochastic_models_and_ground_truth_fields(self):
        schema = load_json(SCHEMA_DIR / "action-kernel.schema.json")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        catalog = deterministic_action_catalog()
        self.assertEqual([], list(validator.iter_errors(catalog)))

        stochastic = copy.deepcopy(catalog)
        stochastic["actions"][0]["observation_model"]["noise_model"] = "stochastic"
        self.assertTrue(list(validator.iter_errors(stochastic)))

        leaked = copy.deepcopy(catalog)
        leaked["actions"][0]["recoverable_claim_ids"] = ["SECRET"]
        self.assertTrue(list(validator.iter_errors(leaked)))

    def test_level_complete_certificate_rejects_heuristic_coverage_and_non_checker_issuer(self):
        schema = load_json(SCHEMA_DIR / "certificate.schema.json")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        certificate = valid_certificate()
        self.assertEqual([], list(validator.iter_errors(certificate)))

        heuristic = copy.deepcopy(certificate)
        heuristic["candidate_coverage"]["mode"] = "heuristic"
        self.assertTrue(list(validator.iter_errors(heuristic)))

        non_checker = copy.deepcopy(certificate)
        non_checker["issued_by"] = "m3star"
        self.assertTrue(list(validator.iter_errors(non_checker)))

    def test_mindiff_timeout_does_not_change_counterexample_found(self):
        schema = load_json(SCHEMA_DIR / "counterexample.schema.json")
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        counterexample = counterexample_with_timeout_mindiff()
        self.assertEqual([], list(validator.iter_errors(counterexample)))
        self.assertEqual("COUNTEREXAMPLE_FOUND", counterexample["checker_status"])


if __name__ == "__main__":
    unittest.main()
