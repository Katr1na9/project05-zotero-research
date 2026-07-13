import hashlib
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = (
    ROOT / "09-experiments" / "scripts" / "build_claim_source_excerpts.py"
)
SPEC = importlib.util.spec_from_file_location("claim_source_excerpts", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

PACKET_DIR = ROOT / "09-experiments" / "annotation" / "c07_c11_v0.2"
PACKAGE_DIR = (
    ROOT
    / "09-experiments"
    / "annotation"
    / "source_excerpts"
    / "c07_c11_v0.1"
)
MANIFEST_PATH = PACKAGE_DIR / "source_excerpt_manifest.json"
LOCAL_EXCERPT_PATH = PACKAGE_DIR / "local" / "claim_source_excerpts.jsonl"
CLAIM_ITEMS_PATH = PACKET_DIR / "public" / "claim_items.jsonl"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class ClaimSourceExcerptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.claim_items = load_jsonl(CLAIM_ITEMS_PATH)

    def test_manifest_closes_all_27_source_pointers_locally(self):
        self.assertEqual(27, self.manifest["excerpt_count"])
        self.assertEqual(
            "ready_local_canonical_excerpts",
            self.manifest["source_gate_status"],
        )
        self.assertFalse(self.manifest["human_labels_present"])
        self.assertEqual(
            {
                "darpa_e5_R04_pidsmaker_event_table": 5,
                "darpa_e5_R05_pidsmaker_event_table": 4,
                "darpa_optc_R06_sysclient0201_ecar_window": 5,
                "darpa_optc_R07_sysclient0351_ecar_window": 5,
                "otrf_apt29_day1_host_events": 8,
            },
            self.manifest["artifact_counts"],
        )

    def test_manifest_is_bound_to_the_blind_claim_packet(self):
        self.assertEqual(
            sha256_file(CLAIM_ITEMS_PATH),
            self.manifest["claim_items_sha256"],
        )
        expected_blind_ids = {item["blind_id"] for item in self.claim_items}
        self.assertEqual(
            expected_blind_ids,
            set(self.manifest["excerpt_sha256_by_blind_id"]),
        )

    def test_distribution_boundary_is_local_admin_only(self):
        self.assertEqual(
            "local_admin_bundle_not_committed",
            self.manifest["local_excerpt_file"]["distribution"],
        )

    def test_local_payload_matches_manifest_when_available(self):
        if not LOCAL_EXCERPT_PATH.is_file():
            self.skipTest("local-only source excerpt payload is unavailable")
        self.assertEqual(
            sha256_file(LOCAL_EXCERPT_PATH),
            self.manifest["local_excerpt_file"]["sha256"],
        )
        rows = load_jsonl(LOCAL_EXCERPT_PATH)
        self.assertEqual(27, len(rows))
        by_blind = {row["blind_id"]: row for row in rows}
        self.assertEqual(27, len(by_blind))
        public_by_blind = {item["blind_id"]: item for item in self.claim_items}
        for blind_id, row in by_blind.items():
            with self.subTest(blind_id=blind_id):
                self.assertEqual(
                    public_by_blind[blind_id]["source_pointer"],
                    row["source_pointer"],
                )
                self.assertEqual(
                    MODULE.sha256_bytes(
                        MODULE.canonical_json(
                            MODULE.decode_source_payload(row["source_excerpt"])
                        )
                    ),
                    row["excerpt_sha256"],
                )
                self.assertEqual(
                    "recursive_utf8_hex_v1",
                    row["source_excerpt_encoding"],
                )
                self.assertEqual(
                    self.manifest["excerpt_sha256_by_blind_id"][blind_id],
                    row["excerpt_sha256"],
                )


if __name__ == "__main__":
    unittest.main()
