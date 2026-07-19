import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXP = Path(__file__).resolve().parents[1]
ROOT = EXP.parent
SCRIPT = EXP / "scripts" / "build_replay_resource_benchmark.py"
COHORT = EXP / "governance" / "cohorts" / "real-case-cohort-v0.3.json"
ONTOLOGY = EXP / "governance" / "profiles" / "action-ontology-v0.3-real-only-draft.json"
SOURCE_CASES = EXP / "real_cases"


def load_script(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ReplayResourceBenchmarkTests(unittest.TestCase):
    def test_builds_real_only_executable_views_and_scan_equivalent_profile(self):
        self.assertTrue(SCRIPT.is_file())
        builder = load_script(SCRIPT, "build_replay_resource_benchmark")
        runtime = load_script(EXP / "scripts" / "cost_profile_runtime.py", "cost_runtime")
        run_mvp = load_script(EXP / "scripts" / "run_mvp.py", "run_mvp_for_replay_benchmark")
        source_hashes = {
            path.relative_to(SOURCE_CASES).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in SOURCE_CASES.rglob("*.json")
        }

        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "benchmark"
            profile_path = Path(temp) / "cost-profile.json"
            manifest = builder.build_benchmark(
                COHORT,
                ONTOLOGY,
                SOURCE_CASES,
                output,
                profile_path,
                created_utc="2026-07-18T12:00:00Z",
            )

            self.assertEqual(9, manifest["case_count"])
            self.assertEqual(42, manifest["executable_action_count"])
            self.assertEqual(
                {
                    "extend_log_window",
                    "query_host_subgraph",
                    "recover_network_summary",
                    "ttp_local_probe",
                },
                set(manifest["executable_action_types"]),
            )
            self.assertEqual(
                source_hashes,
                {
                    path.relative_to(SOURCE_CASES).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in SOURCE_CASES.rglob("*.json")
                },
            )

            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual("frozen", profile["status"])
            self.assertEqual("measured", profile["regime"])
            self.assertEqual("case_replay_full_scan_equivalent", profile["scoring"]["unit"])
            self.assertEqual(42, len(profile["actions"]))
            indexed = {
                (row["case_id"], row["action_id"]): row for row in profile["actions"]
            }
            cohort = json.loads(COHORT.read_text(encoding="utf-8"))
            c02 = next(row for row in cohort["cases"] if row["canonical_case_id"] == "C02")
            events = next(row["size_bytes"] for row in c02["replay_artifacts"] if row["path"].endswith("events.jsonl"))
            nodes = next(row["size_bytes"] for row in c02["replay_artifacts"] if row["path"].endswith("nodes.jsonl"))
            total = events + nodes
            self.assertAlmostEqual(
                (2 * events + nodes) / total,
                indexed[("C05-darpa-e3-cadets", "C05-AA-002")]["measured_cost"],
            )
            self.assertAlmostEqual(
                nodes / total,
                indexed[("C05-darpa-e3-cadets", "C05-AA-003")]["measured_cost"],
            )
            self.assertNotIn(
                ("C05-darpa-e3-cadets", "C05-AA-005"),
                indexed,
            )

            profile_bundle = runtime.load_cost_profile(profile_path)
            development_prefixes = ("C07-", "C08-", "C09-", "C10-", "C11-", "C12-")
            for case_dir in sorted((output / "cases").iterdir()):
                config = json.loads((case_dir / "case_config.json").read_text(encoding="utf-8"))
                claims = json.loads((case_dir / "evidence_claims.json").read_text(encoding="utf-8"))
                actions = json.loads((case_dir / "acquisition_actions.json").read_text(encoding="utf-8"))
                self.assertTrue(
                    all(action["action_type"] in manifest["executable_action_types"] for action in actions)
                )
                measured_actions, _ = runtime.apply_cost_regime(
                    actions,
                    config["case_id"],
                    "measured",
                    profile_bundle,
                )
                if not case_dir.name.startswith(development_prefixes):
                    continue
                successes = 0
                for condition in run_mvp.experiment_conditions(config):
                    row, _ = run_mvp.run_episode(
                        config,
                        claims,
                        measured_actions,
                        *condition,
                        "oracle_optimal",
                    )
                    successes += int(row["reached_target"])
                self.assertEqual(45, successes, config["case_id"])


if __name__ == "__main__":
    unittest.main()
