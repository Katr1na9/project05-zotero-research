import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


EXP = Path(__file__).resolve().parents[1]
SCRIPTS = EXP / "scripts"
ONTOLOGY = (
    EXP
    / "governance"
    / "profiles"
    / "action-ontology-v0.3-real-only-draft.json"
)


def load_script(name):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_script("build_action_executor_registry")
VALIDATOR = load_script("validate_action_executor_registry")


class ActionExecutorRegistryTests(unittest.TestCase):
    def write_registry(self, path):
        registry = BUILDER.build_registry(ONTOLOGY)
        path.write_text(json.dumps(registry), encoding="utf-8")
        return registry

    def test_registry_covers_all_seven_real_action_types_without_claiming_implementation(self):
        registry = BUILDER.build_registry(ONTOLOGY)

        self.assertEqual(7, len(registry["adapters"]))
        self.assertEqual(
            {
                "cti_report_lookup",
                "extend_log_window",
                "human_review",
                "ioc_enrichment",
                "query_host_subgraph",
                "recover_network_summary",
                "ttp_local_probe",
            },
            {row["action_type"] for row in registry["adapters"]},
        )
        self.assertTrue(
            all(row["status"] == "unimplemented" for row in registry["adapters"])
        )
        self.assertTrue(
            all(
                row["operational_cost_measurement_eligible"] is False
                for row in registry["adapters"]
            )
        )
        self.assertEqual(
            {
                "canonical_C01_C09": "real_cases_in_scope",
                "canonical_C10_plus": "unassigned_and_sealed",
                "source_C13_plus": "sealed",
            },
            registry["data_boundary"],
        )

    def test_draft_is_schema_valid_and_complete_but_not_formally_ready(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "registry.json"
            self.write_registry(path)

            report = VALIDATOR.validate_registry(path)

            self.assertTrue(report["schema_valid"])
            self.assertTrue(report["ontology_integrity_valid"])
            self.assertTrue(report["action_type_coverage_valid"])
            self.assertEqual(7, report["adapter_count"])
            self.assertEqual(0, report["implemented_adapter_count"])
            self.assertEqual(0, report["eligible_adapter_count"])
            self.assertFalse(report["formal_ready"])
            self.assertEqual([], report["errors"])

    def test_unimplemented_adapters_block_registry_freeze(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "registry.json"
            registry = self.write_registry(path)
            registry["status"] = "frozen"
            path.write_text(json.dumps(registry), encoding="utf-8")

            report = VALIDATOR.validate_registry(path)

            self.assertFalse(report["formal_ready"])
            self.assertIn(
                "frozen registry contains unimplemented adapters", report["errors"]
            )

    def test_oracle_input_prohibition_cannot_be_silently_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "registry.json"
            registry = self.write_registry(path)
            registry["adapters"][0]["oracle_input_fields_forbidden"].pop()
            path.write_text(json.dumps(registry), encoding="utf-8")

            report = VALIDATOR.validate_registry(path)

            self.assertFalse(report["schema_valid"])
            self.assertTrue(
                any(
                    "oracle input prohibition is incomplete" in error
                    for error in report["errors"]
                )
            )


if __name__ == "__main__":
    unittest.main()
