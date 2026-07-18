import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = EXPERIMENT_ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


builder = load_script("build_compiler_public_request")


def fixture_public_inputs():
    record = builder.build_record(
        "REC-0000000000000001",
        {
            "operation": "EVENT_WRITE",
            "process": "powershell.exe",
            "path": "C:\\Temp\\A.zip",
        },
        scope={"host_id": "host-a"},
        time_window={
            "start": "2026-01-01T00:00:00Z",
            "end": "2026-01-01T00:00:01Z",
        },
    )
    artifact = builder.build_artifact(
        "ART-0000000000000001",
        "local_log",
        [record],
        scope={"host_id": "host-a"},
    )
    target = builder.build_target_node(
        "NODE-0000000000000001",
        "A process writes an archive file",
        allowed_claim_types=["file_activity"],
        allowed_predicates=["wrote"],
    )
    return {
        "case_id": "C04-compiler-development",
        "split": "development",
        "step_index": 0,
        "visible_artifacts": [artifact],
        "target_nodes": [target],
        "predicate_allowlist": {"local_log": ["wrote"]},
    }


class PublicRequestBoundaryTests(unittest.TestCase):
    def test_private_mutation_does_not_change_public_request_or_hash(self):
        inputs = fixture_public_inputs()
        private_a = {"canonical_claim_id": "C04-EC-001", "gold": "alpha"}
        request_a = builder.build_public_request(**inputs)
        hash_a = builder.sha256_value(request_a)

        private_a["gold"] = "changed-private-answer"
        private_a["canonical_claim_id"] = "C04-EC-999"
        request_b = builder.build_public_request(**inputs)

        self.assertEqual(request_a, request_b)
        self.assertEqual(hash_a, builder.sha256_value(request_b))
        self.assertNotIn("changed-private-answer", builder.canonical_json_text(request_b))

    def test_recursive_forbidden_key_is_rejected(self):
        inputs = fixture_public_inputs()
        inputs["visible_artifacts"][0]["records"][0]["payload"][
            "recoverable_claim_ids"
        ] = ["C04-EC-001"]

        with self.assertRaisesRegex(ValueError, "recoverable_claim_ids"):
            builder.build_public_request(**inputs)

    def test_canonical_claim_identifier_is_rejected_even_under_safe_key(self):
        inputs = fixture_public_inputs()
        inputs["visible_artifacts"][0]["records"][0]["payload"]["note"] = (
            "answer C04-EC-001"
        )

        with self.assertRaisesRegex(ValueError, "canonical claim identifier"):
            builder.build_public_request(**inputs)

    def test_public_path_guard_rejects_private_tree_and_escape(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            public = root / "public"
            private = root / "private"
            public.mkdir()
            private.mkdir()
            okay = public / "request.json"
            okay.write_text("{}", encoding="utf-8")
            secret = private / "gold.json"
            secret.write_text("{}", encoding="utf-8")

            self.assertEqual(okay.resolve(), builder.ensure_public_path(okay, public))
            with self.assertRaisesRegex(ValueError, "public root"):
                builder.ensure_public_path(secret, public)

    def test_request_id_and_hash_are_reproducible_and_request_scoped(self):
        first = builder.build_public_request(**fixture_public_inputs())
        second = builder.build_public_request(**fixture_public_inputs())

        self.assertEqual(first["request_id"], second["request_id"])
        self.assertEqual(first["request_content_sha256"], second["request_content_sha256"])
        self.assertRegex(first["request_id"], r"^REQ-[A-F0-9]{24}$")
        self.assertNotIn("EC-", first["request_id"])


if __name__ == "__main__":
    unittest.main()

