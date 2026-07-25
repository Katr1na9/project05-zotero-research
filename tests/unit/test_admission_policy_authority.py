import copy
import unittest

from src.firewall.policy import AdmissionPolicyAuthority, AdmissionPolicyRejected
from src.ir.canonical_hash import canonical_document_hash
from tests.unit.policy_test_helpers import approved_policy_parts, policy_documents


class AdmissionPolicyAuthorityTests(unittest.TestCase):
    def assert_rejected(self, reason_code, callback):
        with self.assertRaises(AdmissionPolicyRejected) as caught:
            callback()
        self.assertEqual(reason_code, caught.exception.reason_code)

    def test_exact_approved_policy_manifest_and_gamma_binding_verify(self):
        policy, manifest, gamma_ref = approved_policy_parts()
        authority = AdmissionPolicyAuthority.from_documents(
            policy, manifest, gamma_ref
        )

        self.assertEqual(policy["hash"], authority.policy_hash)
        self.assertEqual(manifest["hash"], authority.approval_manifest_hash)
        self.assertTrue(
            authority.authorizes(
                rule_id="A001",
                source_family="identity",
                levels=("initial_foothold",),
            )
        )
        self.assertFalse(
            authority.authorizes(
                rule_id="A003",
                source_family="software_supply_chain",
                levels=("package_origin",),
            )
        )

    def test_repository_manifest_is_exact_hash_approved_authority(self):
        policy, manifest, gamma = policy_documents()
        self.assertEqual("APPROVED", manifest["decision"])
        self.assertEqual("Project05 repository owner", manifest["approved_by"])
        authority = AdmissionPolicyAuthority.from_documents(
            policy, manifest, gamma["admission_policy"]
        )
        self.assertEqual(manifest["hash"], authority.approval_manifest_hash)

        pending = copy.deepcopy(manifest)
        pending.update(
            {
                "decision": "PENDING",
                "approved_by": None,
                "approved_at": None,
                "authority_source": None,
            }
        )
        pending["hash"] = canonical_document_hash(pending)
        self.assert_rejected(
            "AP-003_POLICY_NOT_APPROVED",
            lambda: AdmissionPolicyAuthority.from_documents(
                policy, pending, gamma["admission_policy"]
            ),
        )

    def test_wrong_missing_and_tampered_policy_hashes_fail_closed(self):
        policy, manifest, gamma_ref = approved_policy_parts()
        cases = []

        wrong = copy.deepcopy(policy)
        wrong["hash"] = "sha256:" + "1" * 64
        cases.append(wrong)

        missing = copy.deepcopy(policy)
        del missing["hash"]
        cases.append(missing)

        tampered = copy.deepcopy(policy)
        tampered["rules"][0]["source_families"].append("external_intel")
        cases.append(tampered)

        for invalid in cases:
            with self.subTest(policy=invalid.get("hash")):
                self.assert_rejected(
                    "AP-001_POLICY_HASH_MISMATCH",
                    lambda invalid=invalid: AdmissionPolicyAuthority.from_documents(
                        invalid, manifest, gamma_ref
                    ),
                )

    def test_manifest_and_gamma_mismatches_fail_closed(self):
        policy, manifest, gamma_ref = approved_policy_parts()

        tampered_manifest = copy.deepcopy(manifest)
        tampered_manifest["approved_by"] = "different-authority"
        self.assert_rejected(
            "AP-002_APPROVAL_HASH_MISMATCH",
            lambda: AdmissionPolicyAuthority.from_documents(
                policy, tampered_manifest, gamma_ref
            ),
        )

        wrong_policy_manifest = copy.deepcopy(manifest)
        wrong_policy_manifest["policy_hash"] = "sha256:" + "2" * 64
        wrong_policy_manifest["hash"] = canonical_document_hash(
            wrong_policy_manifest
        )
        self.assert_rejected(
            "AP-004_APPROVAL_POLICY_MISMATCH",
            lambda: AdmissionPolicyAuthority.from_documents(
                policy, wrong_policy_manifest, gamma_ref
            ),
        )

        wrong_gamma = copy.deepcopy(gamma_ref)
        wrong_gamma["policy_hash"] = "sha256:" + "3" * 64
        self.assert_rejected(
            "AP-005_GAMMA_BINDING_MISMATCH",
            lambda: AdmissionPolicyAuthority.from_documents(
                policy, manifest, wrong_gamma
            ),
        )


if __name__ == "__main__":
    unittest.main()
