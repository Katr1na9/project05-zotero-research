import importlib.util
import json
import tempfile
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


retrieval = load_script("retrieve_compiler_cti_sources")


def load_catalog():
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def fake_meta(url, payload):
    return {
        "requested_url": url,
        "final_url": url,
        "http_status": 200,
        "content_type": "application/json",
        "bytes": len(payload),
        "sha256": retrieval.sha256_bytes(payload),
    }


def small_lock(protected_text="this protected sentence must never be admitted"):
    hashes = retrieval.hashed_character_ngrams(protected_text, 5)
    return {
        "blocked_family_ids": sorted(retrieval.EXPECTED_BLOCKED_FAMILIES),
        "character_ngram_n": 5,
        "contains_raw_private_gold": False,
        "contains_raw_test_payload": False,
        "minimum_protected_text_chars": 16,
        "near_duplicate_threshold": 0.85,
        "normalized_text_hashes": [retrieval.normalized_text_hash(protected_text)],
        "ngram_signatures": [
            {
                "normalized_text_sha256": retrieval.normalized_text_hash(protected_text),
                "ngram_count": len(hashes),
                "ngram_hashes": sorted(hashes),
            }
        ],
        "lock_sha256": "fixture",
    }


class WP4RetrievalTests(unittest.TestCase):
    def test_authoritative_catalog_allows_only_bounded_retrieval(self):
        sources = retrieval.verified_catalog(load_catalog())
        self.assertEqual(retrieval.EXPECTED_SOURCE_IDS, {x["source_id"] for x in sources})
        self.assertTrue(all(x["controller_eligible"] is False for x in sources))

    def test_git_blob_sha_verifies_license_bytes(self):
        payload = b"license bytes\n"
        source = {
            "source_id": "fixture",
            "license": {
                "id": "fixture",
                "evidence_url": "https://github.com/o/r/blob/deadbeef/LICENSE",
                "evidence_blob_sha": retrieval.git_blob_sha1(payload),
            },
        }

        def fetch(url, **kwargs):
            return payload, fake_meta(url, payload)

        audit = retrieval.verify_license(source, fetch)
        self.assertEqual("verified", audit["status"])

    def test_mitre_normalizer_keeps_only_software_procedure_text(self):
        bundle = {
            "objects": [
                {"type": "malware", "id": "malware--1", "name": "SafeWare"},
                {"type": "intrusion-set", "id": "intrusion-set--1", "name": "Actor"},
                {"type": "attack-pattern", "id": "attack-pattern--1", "name": "Pattern"},
                {
                    "type": "relationship",
                    "id": "relationship--keep",
                    "relationship_type": "uses",
                    "source_ref": "malware--1",
                    "target_ref": "attack-pattern--1",
                    "description": "SafeWare creates /tmp/example. [Citation: Example Report]",
                },
                {
                    "type": "relationship",
                    "id": "relationship--drop-actor",
                    "relationship_type": "uses",
                    "source_ref": "intrusion-set--1",
                    "target_ref": "attack-pattern--1",
                    "description": "Actor does something.",
                },
                {
                    "type": "relationship",
                    "id": "relationship--drop-apt29",
                    "relationship_type": "uses",
                    "source_ref": "malware--1",
                    "target_ref": "attack-pattern--1",
                    "description": "APT29 uses SafeWare.",
                },
            ]
        }
        source = next(
            x for x in load_catalog()["candidates"]
            if x["source_id"] == "mitre_attack_software_procedure_text"
        )
        raw = json.dumps(bundle).encode()
        records = retrieval.normalize_mitre_attack(
            source, raw, fake_meta("https://example.test/attack.json", raw)
        )
        self.assertEqual(1, len(records))
        self.assertEqual(["Example Report"], records[0]["payload"]["citation_labels"])
        self.assertNotIn("attack_pattern", records[0]["payload"])

    def test_tram_parser_requires_original_url_and_strips_headers(self):
        value = {
            "signal": (
                "title: Test CISA Advisory\n"
                "url: https://www.cisa.gov/example\n\n"
                "CISA describes an observable process execution."
            )
        }
        title, url, body = retrieval.parse_tram_signal(value)
        self.assertEqual("Test CISA Advisory", title)
        self.assertEqual("https://www.cisa.gov/example", url)
        self.assertNotIn("title:", body)

    def test_exclusion_scan_rejects_exact_near_and_forbidden_literal(self):
        protected = "this protected sentence must never be admitted"
        records = [
            {
                "source_family_id": "fixture",
                "record_id": "exact",
                "payload": {"text": protected},
            },
            {
                "source_family_id": "fixture",
                "record_id": "literal",
                "payload": {"text": "This record explicitly discusses APT29 operations."},
            },
            {
                "source_family_id": "fixture",
                "record_id": "clean",
                "payload": {"text": "A process opened a local configuration file."},
            },
        ]
        admitted, audit = retrieval.audit_records(records, small_lock(protected))
        self.assertEqual(["clean"], [x["record_id"] for x in admitted])
        self.assertEqual(2, audit["excluded_record_count"])
        self.assertGreaterEqual(audit["normalized_exact_match_count"], 1)
        self.assertGreaterEqual(audit["forbidden_literal_match_count"], 1)

    def test_exclusion_lock_cannot_contain_raw_test_payload(self):
        lock = small_lock()
        lock["contains_raw_test_payload"] = True
        with self.assertRaisesRegex(ValueError, "raw test payload"):
            retrieval.validate_exclusion_lock(lock)

    def test_output_is_atomic_and_no_overwrite(self):
        result = {
            "manifest": {"status": "passed"},
            "records": [],
            "origin_audit": [],
            "exclusion_audit": {"status": "passed_clean"},
        }
        lock = small_lock()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lock_path = root / "lock.json"
            lock_path.write_text(json.dumps(lock), encoding="utf-8")
            output = root / "output"
            retrieval.write_retrieval_output(output, result, lock_path, lock)
            self.assertTrue((output / "retrieval-manifest.json").is_file())
            with self.assertRaises(FileExistsError):
                retrieval.write_retrieval_output(output, result, lock_path, lock)


if __name__ == "__main__":
    unittest.main()
