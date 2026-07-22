import hashlib
import importlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from src.checker.finite_domain import (
    CheckerRun,
    CheckerStatus,
    QueryResult,
    QueryStatus,
)


try:
    certificate_api = importlib.import_module("src.checker.level_certificate")
except (ImportError, ModuleNotFoundError):
    certificate_api = None


ROOT = Path(__file__).resolve().parents[2]


def sha256(label):
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def candidate_certified_run():
    return CheckerRun(
        base=QueryResult(
            QueryStatus.SAT,
            assignments_examined=1,
            witness={"initial_foothold": "H1"},
        ),
        support=QueryResult(
            QueryStatus.SAT,
            assignments_examined=1,
            witness={"initial_foothold": "H1"},
        ),
        alternative=QueryResult(QueryStatus.UNSAT, assignments_examined=2),
        checker_status=CheckerStatus.CANDIDATE_CERTIFIED,
    )


def counterexample_run():
    return CheckerRun(
        base=QueryResult(QueryStatus.SAT, witness={"initial_foothold": "H1"}),
        support=QueryResult(QueryStatus.SAT, witness={"initial_foothold": "H1"}),
        alternative=QueryResult(
            QueryStatus.SAT, witness={"initial_foothold": "H3"}
        ),
        checker_status=CheckerStatus.COUNTEREXAMPLE_FOUND,
    )


def valid_issue_kwargs():
    return {
        "certificate_id": "CERT-LEVEL-001",
        "case_id": "CASE-LEVEL-001",
        "gamma_hash": sha256("approved-gamma"),
        "evidence_hash": sha256("admitted-evidence"),
        "level": "initial_foothold",
        "conclusion": {"entity_id": "H1", "entity_type": "host"},
        "candidate_coverage": {
            "level": "initial_foothold",
            "mode": "exhaustive",
            "declared_domain_size": 2,
            "checked_count": 2,
            "omitted_known_candidates": [],
            "solver_seed_used": True,
        },
        "level_certification": {
            "all_legal_results_covered": True,
            "exactly_one_feasible_result": True,
            "all_critical_queries_known": True,
        },
        "positive_witness": ("CLAIM-OBS-001",),
        "proof_artifact": {
            "proof_level": "reproducible_run",
            "solver": "finite_domain_enumerator",
            "solver_version": "0.8.0",
            "query_hashes": [sha256("base-support-alternative")],
            "artifact_uri": None,
        },
        "critical_scope_assumptions": ("bounded finite domain is frozen",),
        "promotion_dependencies": (),
        "created_at": "2026-01-01T10:20:00Z",
        "requested_issuer": "kernel_checker",
        "formal_artifacts_verified": True,
    }


def issue_valid_certificate():
    return certificate_api.LevelCertificateIssuer().issue(
        candidate_certified_run(), **valid_issue_kwargs()
    )


class LevelCertificateIssuerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(certificate_api, "P9 level certificate API is missing")

    def assert_rejected(self, reason_code, callback):
        with self.assertRaises(certificate_api.LevelCertificateRejected) as caught:
            callback()
        self.assertEqual(reason_code, caught.exception.reason_code)

    def test_exhaustive_checker_proof_issues_schema_valid_level_certificate(self):
        issued = issue_valid_certificate()
        certificate = issued.to_dict()

        schema = json.loads(
            (ROOT / "schemas" / "certificate.schema.json").read_text(
                encoding="utf-8"
            )
        )
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        self.assertEqual([], list(validator.iter_errors(certificate)))
        self.assertEqual("kernel_checker", certificate["issued_by"])
        self.assertEqual("level_complete", certificate["certification_scope"])
        self.assertEqual("exhaustive", certificate["candidate_coverage"]["mode"])
        self.assertTrue(issued.binds_checker_run(candidate_certified_run()))
        self.assertNotIn("system_status", certificate)

    def test_candidate_only_checker_result_cannot_issue_without_level_proof(self):
        kwargs = valid_issue_kwargs()
        kwargs["level_certification"] = {
            "all_legal_results_covered": False,
            "exactly_one_feasible_result": True,
            "all_critical_queries_known": True,
        }

        self.assert_rejected(
            "P9-CERT-004_LEVEL_PROOF_INCOMPLETE",
            lambda: certificate_api.LevelCertificateIssuer().issue(
                candidate_certified_run(), **kwargs
            ),
        )

    def test_counterexample_and_non_checker_issuer_are_rejected(self):
        self.assert_rejected(
            "P9-CERT-001_CHECKER_CONDITIONS_NOT_MET",
            lambda: certificate_api.LevelCertificateIssuer().issue(
                counterexample_run(), **valid_issue_kwargs()
            ),
        )

        kwargs = valid_issue_kwargs()
        kwargs["requested_issuer"] = "m3star"
        self.assert_rejected(
            "P9-CERT-002_NON_CHECKER_ISSUER",
            lambda: certificate_api.LevelCertificateIssuer().issue(
                candidate_certified_run(), **kwargs
            ),
        )

    def test_heuristic_and_solver_complete_coverage_are_not_signed(self):
        for mode in ("heuristic", "solver_complete"):
            with self.subTest(mode=mode):
                kwargs = valid_issue_kwargs()
                kwargs["candidate_coverage"] = dict(kwargs["candidate_coverage"])
                kwargs["candidate_coverage"]["mode"] = mode
                self.assert_rejected(
                    "P9-CERT-003_NON_EXHAUSTIVE_COVERAGE",
                    lambda: certificate_api.LevelCertificateIssuer().issue(
                        candidate_certified_run(), **kwargs
                    ),
                )

    def test_incomplete_counts_omissions_and_unknown_queries_are_rejected(self):
        variants = []
        checked_short = valid_issue_kwargs()
        checked_short["candidate_coverage"] = dict(
            checked_short["candidate_coverage"]
        )
        checked_short["candidate_coverage"]["checked_count"] = 1
        variants.append(checked_short)
        omitted = valid_issue_kwargs()
        omitted["candidate_coverage"] = dict(omitted["candidate_coverage"])
        omitted["candidate_coverage"]["omitted_known_candidates"] = ["H3"]
        variants.append(omitted)

        for kwargs in variants:
            self.assert_rejected(
                "P9-CERT-003_NON_EXHAUSTIVE_COVERAGE",
                lambda kwargs=kwargs: certificate_api.LevelCertificateIssuer().issue(
                    candidate_certified_run(), **kwargs
                ),
            )

    def test_unverified_or_placeholder_hashes_cannot_support_certificate(self):
        unverified = valid_issue_kwargs()
        unverified["formal_artifacts_verified"] = False
        self.assert_rejected(
            "P9-CERT-005_FORMAL_HASHES_NOT_VERIFIED",
            lambda: certificate_api.LevelCertificateIssuer().issue(
                candidate_certified_run(), **unverified
            ),
        )

        placeholder = valid_issue_kwargs()
        placeholder["gamma_hash"] = "sha256:" + "1" * 64
        self.assert_rejected(
            "P9-CERT-005_FORMAL_HASHES_NOT_VERIFIED",
            lambda: certificate_api.LevelCertificateIssuer().issue(
                candidate_certified_run(), **placeholder
            ),
        )


if __name__ == "__main__":
    unittest.main()
