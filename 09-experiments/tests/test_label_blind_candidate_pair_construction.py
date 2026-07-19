import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
SCRIPT_PATH = EXPERIMENT_ROOT / "scripts" / "construct_label_blind_candidate_pairs.py"
CEDGE_PATH = EXPERIMENT_ROOT / "scripts" / "build_candidate_edge_training.py"
CONTRACT_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "contracts"
FIELD_MAP_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "field_maps" / "v0.3"
AUTHORITY_PATH = CONTRACT_ROOT / "authority-lock-v0.12.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class LabelBlindAuthorityTests(unittest.TestCase):
    def test_v012_authority_hash_chain_and_model_hard_stops(self):
        self.assertTrue(AUTHORITY_PATH.is_file(), "v0.12 authority lock is missing")
        authority = load_json(AUTHORITY_PATH)
        gate = authority["non_token_data_gate"]
        self.assertTrue(gate["passed"])
        self.assertEqual(1500, gate["examples"])
        self.assertFalse(authority["next_gate"]["formal_data_gate_passed"])
        self.assertEqual(
            "pending_not_authorized", authority["next_gate"]["token_gate_status"]
        )
        prohibited = set(authority["not_authorized"])
        self.assertIn("tokenizer_download_or_use", prohibited)
        self.assertIn("model_download_or_use", prohibited)
        self.assertIn("formal_training", prohibited)
        self.assertIn("m3_runtime_integration", prohibited)
        parent = authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        for group in (
            "authoritative_documents",
            "authoritative_contracts",
            "authoritative_evidence",
        ):
            for relative, expected in authority[group].items():
                with self.subTest(path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))

    def test_v03_field_map_adds_only_beth_as_seventh_family(self):
        maps = load_json(FIELD_MAP_ROOT / "source-field-maps.json")
        lock = load_json(FIELD_MAP_ROOT / "field-map-lock.json")
        self.assertEqual("0.3.0", maps["map_version"])
        self.assertEqual(7, len(maps["families"]))
        self.assertEqual(7, lock["source_family_count"])
        self.assertEqual(lock["map_sha256"], sha256(FIELD_MAP_ROOT / lock["map_path"]))
        beth = maps["families"]["beth_process_events"]
        self.assertEqual("train", beth["split_role"])
        self.assertEqual(
            "beth_record_local_parent_process_v1",
            beth["templates"][0]["candidate_parser"],
        )

    def test_contract_freezes_exact_1500_balanced_examples(self):
        contract = load_json(
            CONTRACT_ROOT / "label-blind-pair-construction-contract-v0.2.json"
        )
        train_positive = sum(contract["positive_quotas"]["train"].values())
        validation_positive = sum(
            contract["positive_quotas"]["training-validation"].values()
        )
        self.assertEqual(600, train_positive)
        self.assertEqual(150, validation_positive)
        self.assertEqual(1200, contract["data_gate"]["exact_train_candidate_pairs"])
        self.assertEqual(
            300,
            contract["data_gate"]["exact_training_validation_candidate_pairs"],
        )
        self.assertEqual(4, len(contract["positive_quotas"]["train"]))
        self.assertEqual(
            2, len(contract["positive_quotas"]["training-validation"])
        )
        self.assertEqual(
            {"N1": 36, "N2": 4, "N3": 35, "N4": 0},
            contract["negative_generator_quotas"]["training-validation"]
            ["zeek_non_pcap_test_logs"],
        )
        for split, families in contract["positive_quotas"].items():
            for family, positive_quota in families.items():
                self.assertEqual(
                    positive_quota,
                    sum(
                        contract["negative_generator_quotas"][split][family].values()
                    ),
                )


class LabelBlindConstructionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module(SCRIPT_PATH, "label_blind_pairs")
        cls.cedge = load_module(CEDGE_PATH, "candidate_edge_builder_for_pairs")
        cls.maps = cls.cedge.load_field_maps(
            FIELD_MAP_ROOT / "source-field-maps.json",
            FIELD_MAP_ROOT / "field-map-lock.json",
        )

    def row(self, index: int, label: str = "0"):
        return {
            "timestamp": f"{1000 + index}.25",
            "processId": str(2000 + index),
            "parentProcessId": str(1000 + index),
            "userId": "1000",
            "processName": f"proc{index}",
            "hostName": "host-a",
            "eventId": "59",
            "eventName": "execve",
            "argsNum": "1",
            "returnValue": "0",
            "args": "[]",
            "sus": label,
            "evil": label,
        }

    def beth_record(self, index: int, label: str = "0"):
        record = self.module.normalize_beth_row(
            self.row(index, label),
            row_number=index + 2,
            source_sha256="A" * 64,
            license_sha256="B" * 64,
            source_url="https://www.kaggle.com/datasets/example/source?filename=hidden.csv",
        )
        self.assertIsNotNone(record)
        enriched = self.module.enrich_record(record, self.maps)
        self.assertIsNotNone(enriched)
        return enriched

    def test_beth_normalization_is_label_invariant_and_emits_no_label_keys(self):
        zero = self.beth_record(1, "0")
        one = self.beth_record(1, "1")
        self.assertEqual(zero, one)
        encoded = json.dumps(zero, sort_keys=True).casefold()
        self.assertNotIn('"sus"', encoded)
        self.assertNotIn('"evil"', encoded)
        self.assertEqual("https://www.kaggle.com", zero["provenance"]["source_url"])
        candidate = zero["observation_candidates"][0]
        self.assertEqual("parent_of", candidate["predicate"])
        self.assertTrue(
            self.cedge.validate_g0_candidate(zero, candidate, self.maps)["eligible"]
        )

    def test_family_constructor_meets_n1_n2_n3_quotas_with_valid_proofs(self):
        records = [self.beth_record(index) for index in range(12)]
        examples, record_index = self.module.construct_family_pairs(
            records,
            positive_quota=6,
            generator_quotas={"N1": 2, "N2": 2, "N3": 2, "N4": 0},
            field_maps=self.maps,
        )
        self.assertEqual(12, len(examples))
        supported = [
            row for row in examples if row["support_decision"] == "supported"
        ]
        negatives = [
            row
            for row in examples
            if row["support_decision"] == "unsupported_by_bound_pointer"
        ]
        self.assertEqual(6, len(supported))
        self.assertEqual(
            {"N1": 2, "N2": 2, "N3": 2},
            {
                name: sum(
                    row["negative_proof"]["generator"] == name for row in negatives
                )
                for name in ("N1", "N2", "N3")
            },
        )
        for negative in negatives:
            self.assertTrue(
                self.cedge.validate_negative_example(
                    negative, record_index, self.maps
                )["valid"]
            )

    def test_only_exact_full_record_duplicates_are_removed(self):
        first = self.beth_record(1)
        second_pointer = self.beth_record(2)
        unique, removed = self.module.deduplicate_exact_records(
            [first, json.loads(json.dumps(first)), second_pointer]
        )
        self.assertEqual(2, len(unique))
        self.assertEqual(1, removed)

    def test_pointer_swap_selection_skips_a_duplicate_negative_id(self):
        records = [self.beth_record(index) for index in range(4)]
        positive = self.cedge.build_supported_example(
            records[0], records[0]["observation_candidates"][0], self.maps
        )
        first = self.module._try_negative(
            "N2", positive, records[0], records, self.maps, set()
        )
        self.assertIsNotNone(first)
        second = self.module._try_negative(
            "N2", positive, records[0], records, self.maps, {first["example_id"]}
        )
        self.assertIsNotNone(second)
        self.assertNotEqual(first["example_id"], second["example_id"])
        self.assertNotEqual(
            first["negative_proof"]["bound_record_sha256"],
            second["negative_proof"]["bound_record_sha256"],
        )

    def test_deterministic_gzip_is_byte_identical_and_refuses_overwrite(self):
        records = [self.beth_record(index) for index in range(6)]
        examples, _ = self.module.construct_family_pairs(
            records,
            positive_quota=3,
            generator_quotas={"N1": 1, "N2": 1, "N3": 1, "N4": 0},
            field_maps=self.maps,
        )
        examples = sorted(examples, key=lambda row: row["example_id"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.jsonl.gz"
            second = root / "second.jsonl.gz"
            self.module.write_deterministic_gzip_jsonl(first, examples)
            self.module.write_deterministic_gzip_jsonl(second, examples)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with self.assertRaises(FileExistsError):
                self.module.write_deterministic_gzip_jsonl(first, examples)


if __name__ == "__main__":
    unittest.main()
