import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(name: str, relative_path: str):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


AUDIT = load_module(
    "external_afa_audit_test",
    "09-experiments/scripts/audit_external_afa_baselines.py",
)
SCREEN = load_module(
    "c12_witfoo_screen_test",
    "09-experiments/scripts/screen_witfoo_c12_candidates.py",
)
EVENT_AUDIT = load_module(
    "c12_witfoo_event_audit_test",
    "09-experiments/scripts/audit_witfoo_c12_event_sources.py",
)
LOCK = (
    ROOT
    / "09-experiments"
    / "external_baselines"
    / "external_baseline_lock_v0.1.json"
)
C12_LOCK_PATH = (
    ROOT
    / "09-experiments"
    / "real_data"
    / "witfoo_precinct6"
    / "c12_intake_lock_v0.1.json"
)
C12_LOCK = json.loads(C12_LOCK_PATH.read_text(encoding="utf-8"))


class ExternalAFAAndC12ScreenTests(unittest.TestCase):
    def test_external_lock_rejects_direct_same_task_claim(self):
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertFalse(lock["decision"]["direct_same_task_claim_allowed"])
        self.assertEqual("afabench-kdd2026", lock["decision"]["external_framework"])
        self.assertEqual(4, len(lock["baselines"]))

    def test_all_current_action_types_have_a_winregrl_family(self):
        result = AUDIT.audit(LOCK, clone_root=None)
        self.assertTrue(result["action_family_gate"]["pass"])
        self.assertFalse(result["action_family_gate"]["unmapped_action_types"])
        self.assertGreater(result["action_family_gate"]["total_action_type_count"], 0)

    def test_c12_screen_keeps_only_human_confirmed_multisource_incidents(self):
        records = [
            {
                "incident_id": "a-good",
                "disposition": "Disrupted",
                "disposition_category": "confirmed-malicious",
                "products_observed": ["ASA Firewall", "Windows Active Directory"],
                "attack_tactics": ["TA0001", "TA0011"],
                "attack_techniques": ["T1071"],
                "lifecycle_stage": "complete-mission",
                "lead_count": 4,
                "node_count": 6,
                "edge_count": 5,
            },
            {
                "incident_id": "b-auto",
                "disposition": "Unprocessed",
                "disposition_category": "automated",
                "products_observed": ["ASA Firewall", "Windows Active Directory"],
                "attack_tactics": ["TA0001", "TA0011"],
                "node_count": 6,
                "edge_count": 5,
            },
            {
                "incident_id": "c-one-channel",
                "disposition": "Resolved",
                "disposition_category": "confirmed-malicious",
                "products_observed": ["Cisco Meraki Firewall", "Meraki"],
                "attack_tactics": ["TA0001", "TA0011"],
                "node_count": 6,
                "edge_count": 5,
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "reports.jsonl"
            source.write_text(
                "".join(json.dumps(row) + "\n" for row in records),
                encoding="utf-8",
            )
            result = SCREEN.screen(
                str(source),
                C12_LOCK,
                "fixture-lock-sha256",
                max_records=None,
            )
        self.assertEqual(3, result["counts"]["records_scanned"])
        self.assertEqual(1, result["counts"]["selected"])
        self.assertEqual("a-good", result["candidates"][0]["incident_id"])
        self.assertEqual(
            "graph/incidents_graphml/a/a-good.graphml",
            result["candidates"][0]["graph_path"],
        )

    def test_c12_screen_ranking_is_deterministic(self):
        base = {
            "disposition": "Resolved",
            "disposition_category": "confirmed-malicious",
            "products_observed": ["Meraki", "Umbrella"],
            "attack_tactics": ["TA0001", "TA0011"],
            "node_count": 6,
            "edge_count": 5,
        }
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "reports.jsonl"
            source.write_text(
                json.dumps({**base, "incident_id": "z", "lead_count": 1})
                + "\n"
                + json.dumps(
                    {
                        **base,
                        "incident_id": "a",
                        "lead_count": 1,
                        "lifecycle_stage": "move-laterally",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            result = SCREEN.screen(
                str(source), C12_LOCK, "fixture-lock-sha256", None
            )
        self.assertEqual(["a", "z"], [row["incident_id"] for row in result["candidates"]])

    def test_c12_aliases_do_not_create_false_multisource_candidate(self):
        profile = SCREEN.product_profile(
            ["Cisco Meraki Firewall", "Meraki"],
            C12_LOCK["product_taxonomy"],
        )
        self.assertEqual(["cisco_meraki_firewall"], profile["families"])
        self.assertEqual(["network_perimeter"], profile["sensor_channels"])

    def test_graphml_incident_links_are_not_counted_as_raw_telemetry(self):
        graphml = b'''<?xml version="1.0" encoding="UTF-8"?>
        <graphml xmlns="http://graphml.graphdrawing.org/xmlns">
          <key id="n_type" for="node" attr.name="type" attr.type="string"/>
          <key id="e_type" for="edge" attr.name="type" attr.type="string"/>
          <graph id="G" edgedefault="directed">
            <node id="n1"><data key="n_type">HOST</data></node>
            <node id="n2"><data key="n_type">CRED</data></node>
            <edge id="e1" source="n1" target="n2">
              <data key="e_type">INCIDENT_LINK</data>
            </edge>
          </graph>
        </graphml>'''
        result = EVENT_AUDIT.parse_graphml(graphml)
        self.assertTrue(result["projection_only"])
        self.assertEqual(0, result["telemetry_edge_count"])

    def test_embedded_leads_can_pass_multichannel_recoverability_gate(self):
        expected = {"lead_count": 2}
        record = {
            "id": "fixture",
            "status_name": "Disrupted",
            "lead_count": 2,
            "leads": {
                "a": {
                    "artifact": {
                        "streamname": "cisco_asa",
                        "messagetype": "firewall_action",
                        "action": "deny",
                    },
                    "details": "firewall event",
                    "observed_at": 1,
                    "node_id": "host-1",
                    "description": "ASA Deny",
                    "product": {"name": "ASA Firewall", "vendor_name": "Cisco"},
                },
                "b": {
                    "artifact": {
                        "streamname": "microsoft-windows-security-auditing",
                        "messagetype": "security_audit_event",
                        "action": "Logon",
                    },
                    "details": "identity event",
                    "observed_at": 2,
                    "node_id": "cred-1",
                    "description": "Special privileges assigned",
                    "product": {
                        "name": "Windows Active Directory",
                        "vendor_name": "Microsoft",
                    },
                },
            },
        }
        result = EVENT_AUDIT.summarize_incident(
            record,
            expected,
            C12_LOCK["product_taxonomy"],
            C12_LOCK["stream_taxonomy"],
            "fixture-sha256",
        )
        self.assertTrue(result["recoverability_gate"]["pass"])
        self.assertEqual(2, len(result["verified_sensor_channels"]))

    def test_product_labels_cannot_fake_two_independent_stream_channels(self):
        expected = {"lead_count": 2}
        record = {
            "id": "fixture",
            "lead_count": 2,
            "leads": {
                "a": {
                    "artifact": {"streamname": "meraki"},
                    "details": "one",
                    "observed_at": 1,
                    "node_id": "host-1",
                    "product": {"name": "Meraki"},
                },
                "b": {
                    "artifact": {"streamname": "meraki"},
                    "details": "two",
                    "observed_at": 2,
                    "node_id": "host-2",
                    "product": {"name": "Umbrella"},
                },
            },
        }
        result = EVENT_AUDIT.summarize_incident(
            record,
            expected,
            C12_LOCK["product_taxonomy"],
            C12_LOCK["stream_taxonomy"],
            "fixture-sha256",
        )
        self.assertFalse(result["recoverability_gate"]["pass"])
        self.assertEqual(1, len(result["lead_stream_channels"]))


if __name__ == "__main__":
    unittest.main()
