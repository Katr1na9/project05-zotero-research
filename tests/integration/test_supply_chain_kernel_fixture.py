import hashlib
import json
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from src.checker.finite_domain import FiniteDomainChecker
from src.cli.kernel_e2e import DeterministicKernelE2EDriver, KernelE2ERunRequest
from src.counterexample.artifact import CounterexampleArtifactMetadata
from src.executor.deterministic import FrozenExecutionTables
from src.ir.canonical_hash import canonical_document_hash
from tests.integration.supply_chain_kernel_inputs import (
    FIXTURE,
    ROOT,
    load_json,
    load_supply_chain_kernel_inputs,
    supply_chain_admission_config,
)


def canonical_record_hash(value):
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def supply_chain_request(*, feedback_observation_ids=()):
    inputs = load_supply_chain_kernel_inputs()
    frozen = inputs.expected_counterexample
    metadata = CounterexampleArtifactMetadata(
        counterexample_id=frozen["counterexample_id"],
        case_id=frozen["case_id"],
        gamma_hash=frozen["gamma_hash"],
        evidence_hash=frozen["evidence_hash"],
        target_level=frozen["target_level"],
        result_entity_type=frozen["candidate_q"]["entity_type"],
        support_world_id=frozen["support_world"]["world_id"],
        alternative_world_id=frozen["alternative_world"]["world_id"],
        support_world_predicates=tuple(frozen["support_world"]["predicates"]),
        alternative_world_predicates=tuple(
            frozen["alternative_world"]["predicates"]
        ),
        shared_predicates=tuple(frozen["shared_predicates"]),
        critical_absence_semantics=tuple(frozen["critical_absence_semantics"]),
    )
    return KernelE2ERunRequest(
        gamma_contract=inputs.gamma,
        problem=inputs.compiled.problem,
        target_variable=inputs.compiled.target_variable,
        candidate=inputs.expected["candidate_q"],
        predicate_projections=inputs.predicate_projections,
        artifact_metadata=metadata,
        action_catalog=inputs.catalog,
        execution_tables=FrozenExecutionTables(
            observation_rows=inputs.observation_rows,
            resource_rows=inputs.resource_rows,
        ),
        feedback_observation_ids=feedback_observation_ids,
        observation_admission=supply_chain_admission_config(),
        compiled_problem=inputs.compiled,
    )


class SupplyChainKernelFixtureIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.inputs = load_supply_chain_kernel_inputs()

    def test_second_gamma_catalog_claims_and_real_pointers_validate(self):
        gamma_schema = load_json(ROOT / "schemas" / "gamma-kernel.schema.json")
        action_schema = load_json(ROOT / "schemas" / "action-kernel.schema.json")
        claim_schema = load_json(ROOT / "schemas" / "claim-ir-kernel.schema.json")
        for schema, document in (
            (gamma_schema, self.inputs.gamma),
            (action_schema, self.inputs.catalog),
        ):
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            self.assertEqual([], list(validator.iter_errors(document)))
            self.assertEqual(document["hash"], canonical_document_hash(document))

        validator = Draft202012Validator(
            claim_schema, format_checker=FormatChecker()
        )
        raw_by_source = {
            "package_install.jsonl": json.loads(
                (FIXTURE / "raw" / "package_install.jsonl")
                .read_text(encoding="utf-8")
                .strip()
            ),
            "build_provenance.jsonl": json.loads(
                (FIXTURE / "raw" / "build_provenance.jsonl")
                .read_text(encoding="utf-8")
                .strip()
            ),
        }
        for claim in self.inputs.case_evidence:
            self.assertEqual([], list(validator.iter_errors(claim)))
            source = claim["pointer"]["source_id"]
            self.assertEqual(
                canonical_record_hash(raw_by_source[source]),
                claim["pointer"]["content_hash"],
            )

    def test_declarative_three_world_checker_is_not_twin_h1_h3_logic(self):
        compiled = self.inputs.compiled
        self.assertEqual(
            ("REGISTRY-A", "MIRROR-B", "BUILDER-C"),
            tuple(compiled.problem.domains["package_origin"]),
        )
        self.assertEqual(3, len(compiled.legal_worlds))
        self.assertTrue(
            compiled.compilation_profile.startswith("explicit_legal_worlds_v0.8")
        )
        run = FiniteDomainChecker().check_candidate(
            compiled.problem,
            target_variable="package_origin",
            candidate="REGISTRY-A",
        )
        self.assertEqual("COUNTEREXAMPLE_FOUND", run.checker_status.value)
        self.assertEqual("REGISTRY-A", run.support.witness["package_origin"])
        self.assertEqual("MIRROR-B", run.alternative.witness["package_origin"])

    def test_supply_chain_runs_p1_to_p9_with_a003_a004_admission_and_no_stop(self):
        result = DeterministicKernelE2EDriver().run(supply_chain_request())

        self.assertEqual(
            self.inputs.expected_counterexample,
            dict(result.counterexample_artifact),
        )
        self.assertEqual(
            tuple(self.inputs.expected["allowed_actions"]),
            result.action_selection.allowed_actions,
        )
        self.assertEqual(
            ("SC-OBS-001", "SC-OBS-002", "SC-OBS-003"),
            tuple(row["observation_id"] for row in result.execution_result.observations),
        )
        self.assertTrue(all(item.allowed for item in result.firewall_decisions))
        self.assertEqual(3, len(result.admission_transitions))
        self.assertEqual(
            ("A003", "A003", "A004"),
            tuple(item.audit_event.rule_id for item in result.admission_transitions),
        )
        self.assertEqual("CONTINUE", result.system_state.system_status.value)
        self.assertIsNone(result.system_state.certificate_id)
        self.assertNotIn("CERTIFIED_STOP", json.dumps(result.to_outcome_fields()))

    def test_recertification_keeps_unseen_third_world_after_one_alternative_is_removed(self):
        result = DeterministicKernelE2EDriver().run(
            supply_chain_request(feedback_observation_ids=("SC-OBS-002",))
        )

        self.assertIsNotNone(result.recertification_result)
        recertification = result.recertification_result
        self.assertEqual(("W-MIRROR",), recertification.eliminated_world_ids)
        self.assertEqual(
            ("W-REGISTRY", "W-BUILDER"),
            recertification.surviving_world_ids,
        )
        self.assertEqual(
            "COUNTEREXAMPLE_FOUND",
            recertification.checker_run.checker_status.value,
        )
        self.assertEqual("BUILDER-C", recertification.checker_run.alternative.witness["package_origin"])
        self.assertEqual("CONTINUE", result.system_state.system_status.value)
        self.assertIsNone(result.system_state.certificate_id)


if __name__ == "__main__":
    unittest.main()
