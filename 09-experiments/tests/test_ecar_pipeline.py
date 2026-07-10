import importlib.util
import gzip
import json
import tempfile
import unittest
import zipfile
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
LOCAL_OPTC_PASSWORD_ZIP = (
    EXPERIMENT_DIR
    / "real_data"
    / "darpa_optc"
    / "raw"
    / "errata_av_bypass"
    / "AIA-351-375.ecar-last.json.zip.passwdOPTC2019.zip"
)


def load_module(name: str, relative: str):
    path = EXPERIMENT_DIR / "scripts" / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


streamer = load_module("stream_ecar_event_window", "stream_ecar_event_window.py")
compiler = load_module("compile_ecar_motifs", "compile_ecar_motifs.py")


class EcarStreamWindowTests(unittest.TestCase):
    def test_filters_by_hostname_and_utc_window(self):
        events = [
            {
                "id": "in-window",
                "hostname": "SysClient0201.systemia.com",
                "object": "PROCESS",
                "action": "CREATE",
                "timestamp": "2019-09-23T11:30:00.000-04:00",
                "properties": {"image_path": "C:\\Windows\\Temp\\runme.bat"},
            },
            {
                "id": "wrong-host",
                "hostname": "SysClient0999.systemia.com",
                "object": "PROCESS",
                "action": "CREATE",
                "timestamp": "2019-09-23T11:30:00.000-04:00",
                "properties": {},
            },
            {
                "id": "out-of-window",
                "hostname": "SysClient0201.systemia.com",
                "object": "PROCESS",
                "action": "CREATE",
                "timestamp": "2019-09-23T10:00:00.000-04:00",
                "properties": {},
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "events.jsonl"
            output = root / "window.jsonl"
            summary = root / "summary.json"
            source.write_text(
                "\n".join(json.dumps(event) for event in events) + "\n",
                encoding="utf-8",
            )
            result = streamer.stream_window(
                inputs=[source],
                output_path=output,
                summary_path=summary,
                hostnames=["SysClient0201"],
                start_utc="2019-09-23T15:23:00Z",
                end_utc="2019-09-23T19:30:00Z",
            )
            rows = [
                json.loads(line)
                for line in output.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(1, result["rows_selected"])
            self.assertEqual(["in-window"], [row["id"] for row in rows])

    def test_exact_host_filter_ignores_prefix_hostnames(self):
        events = [
            {
                "id": "target",
                "hostname": "SysClient0201.systemia.com",
                "object": "PROCESS",
                "action": "CREATE",
                "timestamp": "2019-09-23T11:30:00.000-04:00",
                "properties": {},
            },
            {
                "id": "prefix-collision",
                "hostname": "SysClient02010.systemia.com",
                "object": "PROCESS",
                "action": "CREATE",
                "timestamp": "2019-09-23T11:30:00.000-04:00",
                "properties": {},
            },
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "events.jsonl"
            output = root / "window.jsonl"
            summary = root / "summary.json"
            source.write_text(
                "\n".join(json.dumps(event) for event in events) + "\n",
                encoding="utf-8",
            )
            result = streamer.stream_window(
                inputs=[source],
                output_path=output,
                summary_path=summary,
                hostnames=[],
                exact_hostnames=["SysClient0201.systemia.com"],
                start_utc="2019-09-23T15:23:00Z",
                end_utc="2019-09-23T19:30:00Z",
            )

            rows = [
                json.loads(line)
                for line in output.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(1, result["rows_selected"])
            self.assertEqual(["target"], [row["id"] for row in rows])
            self.assertEqual("exact", result["hostname_match_mode"])

    def test_late_input_error_preserves_existing_outputs(self):
        event = {
            "id": "in-window",
            "hostname": "SysClient0201.systemia.com",
            "object": "PROCESS",
            "action": "CREATE",
            "timestamp": "2019-09-23T11:30:00.000-04:00",
            "properties": {},
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "events.jsonl"
            missing = root / "missing.jsonl"
            output = root / "window.jsonl"
            summary = root / "summary.json"
            source.write_text(json.dumps(event) + "\n", encoding="utf-8")
            output.write_text("previous output\n", encoding="utf-8")
            summary.write_text("previous summary\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing input"):
                streamer.stream_window(
                    inputs=[source, missing],
                    output_path=output,
                    summary_path=summary,
                    hostnames=["SysClient0201"],
                    start_utc="2019-09-23T15:23:00Z",
                    end_utc="2019-09-23T19:30:00Z",
                )

            self.assertEqual("previous output\n", output.read_text(encoding="utf-8"))
            self.assertEqual("previous summary\n", summary.read_text(encoding="utf-8"))

    def test_rejects_unsupported_crypt_optc_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            crypt = Path(tmp) / "payload.json.gz.cryptOPTC2019"
            crypt.write_bytes(b"not a supported archive")

            with self.assertRaisesRegex(ValueError, "cryptOPTC2019"):
                list(streamer.open_ecar_lines(crypt, b"OPTC2019"))

    def test_reads_gzip_jsonl(self):
        event = {
            "id": "gzip-event",
            "hostname": "SysClient0201.systemia.com",
            "object": "FILE",
            "action": "CREATE",
            "timestamp": "2019-09-23T11:24:00.000-04:00",
            "properties": {"file_path": "C:\\runme.bat"},
        }
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "events.json.gz"
            with gzip.open(source, "wt", encoding="utf-8") as handle:
                handle.write(json.dumps(event) + "\n")

            lines = list(streamer.open_ecar_lines(source, b"OPTC2019"))
            self.assertEqual(1, len(lines))
            self.assertIn(b"gzip-event", lines[0])

    def test_summary_uses_chronological_bounds_for_out_of_order_events(self):
        late_event = {
            "id": "late",
            "hostname": "SysClient0201.systemia.com",
            "object": "FILE",
            "action": "CREATE",
            "timestamp": "2019-09-23T12:00:00.000-04:00",
            "properties": {},
        }
        early_event = dict(late_event, id="early", timestamp="2019-09-23T11:00:00.000-04:00")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "events.jsonl"
            output = root / "window.jsonl"
            summary = root / "summary.json"
            source.write_text(
                "\n".join(json.dumps(event) for event in [late_event, early_event])
                + "\n",
                encoding="utf-8",
            )

            result = streamer.stream_window(
                inputs=[source],
                output_path=output,
                summary_path=summary,
                hostnames=["SysClient0201"],
                start_utc="2019-09-23T15:00:00Z",
                end_utc="2019-09-23T17:00:00Z",
            )

            self.assertEqual("2019-09-23T15:00:00Z", result["first_selected_timestamp_utc"])
            self.assertEqual("2019-09-23T16:00:00Z", result["last_selected_timestamp_utc"])


class EcarMotifCompilerTests(unittest.TestCase):
    def test_rejects_unknown_match_operator(self):
        event = {
            "id": "flow-1",
            "hostname": "SysClient0201.systemia.com",
            "object": "FLOW",
            "action": "START",
            "timestamp": "2019-09-23T11:30:00.000-04:00",
            "properties": {"dest_ip": "132.197.158.98"},
        }
        spec = {
            "case_id": "C09-test",
            "artifact_id": "test-ecar",
            "motifs": [
                {
                    "motif_id": "C09-EC-001",
                    "match": {"remote_ips_in": ["132.197.158.98"]},
                    "claim": {"source_type": "network_summary"},
                }
            ],
        }

        with self.assertRaisesRegex(ValueError, "unknown match operator"):
            compiler.compile_motifs([event], spec)

        context = compiler.event_context(event)
        with self.assertRaisesRegex(ValueError, "unknown match operator"):
            compiler.matches_rule(context, {"remote_ips_in": ["132.197.158.98"]})

    def test_rejects_empty_match_rule(self):
        spec = {
            "case_id": "C09-test",
            "artifact_id": "test-ecar",
            "motifs": [
                {
                    "motif_id": "C09-EC-001",
                    "match": {},
                    "claim": {"source_type": "network_summary"},
                }
            ],
        }

        with self.assertRaisesRegex(ValueError, "at least one operator"):
            compiler.compile_motifs([], spec)

    def test_rejects_duplicate_motif_ids(self):
        motif = {
            "motif_id": "C09-EC-001",
            "match": {"object_in": ["FLOW"]},
            "claim": {"source_type": "network_summary"},
        }
        spec = {
            "case_id": "C09-test",
            "artifact_id": "test-ecar",
            "motifs": [motif, dict(motif)],
        }

        with self.assertRaisesRegex(ValueError, "duplicate motif_id"):
            compiler.compile_motifs([], spec)

    def test_flow_motif_matches_remote_ip_and_process(self):
        event = {
            "id": "flow-1",
            "hostname": "SysClient0201.systemia.com",
            "object": "FLOW",
            "action": "START",
            "timestamp": "2019-09-23T11:30:00.000-04:00",
            "properties": {
                "image_path": "\\Device\\HarddiskVolume1\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
                "dest_ip": "132.197.158.98",
                "dest_port": "80",
            },
        }
        spec = {
            "case_id": "C09-test",
            "artifact_id": "test-ecar",
            "motifs": [
                {
                    "motif_id": "C09-EC-001",
                    "match": {
                        "event_type_in": ["FLOW:START"],
                        "process_contains_any": ["powershell.exe"],
                        "remote_ip_in": ["132.197.158.98"],
                    },
                    "claim": {"source_type": "network_summary"},
                }
            ],
        }
        claims, report = compiler.compile_motifs([event], spec)
        self.assertEqual(1, len(claims))
        self.assertEqual("flow-1", claims[0]["source_pointer"]["record_id"])
        self.assertEqual(1, report["motifs"]["C09-EC-001"]["matched_event_count"])

    def test_registry_motif_uses_path_contains(self):
        event = {
            "id": "reg-1",
            "hostname": "SysClient0201.systemia.com",
            "object": "REGISTRY",
            "action": "EDIT",
            "timestamp": "2019-09-23T11:26:00.000-04:00",
            "properties": {
                "image_path": "powershell.exe",
                "key": "\\REGISTRY\\USER\\S-1-5-21\\Environment\\windir",
            },
        }
        context = compiler.event_context(event)
        self.assertTrue(
            compiler.matches_rule(
                context,
                {
                    "object_in": ["REGISTRY"],
                    "action_in": ["EDIT"],
                    "path_contains_any": ["windir"],
                },
            )
        )

    def test_report_uses_chronological_bounds_for_out_of_order_events(self):
        late_event = {
            "id": "late",
            "hostname": "SysClient0201.systemia.com",
            "object": "FILE",
            "action": "CREATE",
            "timestamp": "2019-09-23T12:00:00.000-04:00",
            "properties": {"file_path": "C:\\runme.bat"},
        }
        early_event = dict(late_event, id="early", timestamp="2019-09-23T11:00:00.000-04:00")
        spec = {
            "case_id": "C09-test",
            "artifact_id": "test-ecar",
            "motifs": [
                {
                    "motif_id": "C09-EC-001",
                    "match": {"object_in": ["FILE"]},
                    "claim": {"source_type": "file_observation"},
                }
            ],
        }

        _, report = compiler.compile_motifs([late_event, early_event], spec)
        state = report["motifs"]["C09-EC-001"]
        self.assertEqual("2019-09-23T15:00:00Z", state["first_timestamp_utc"])
        self.assertEqual("2019-09-23T16:00:00Z", state["last_timestamp_utc"])


class EcarPasswordZipSmokeTests(unittest.TestCase):
    def test_reads_zip_member_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zipped = root / "payload.zip"
            with zipfile.ZipFile(zipped, "w") as archive:
                archive.writestr(
                    "payload.json",
                    json.dumps(
                        {
                            "id": "z1",
                            "hostname": "SysClient0201.systemia.com",
                            "object": "FILE",
                            "action": "CREATE",
                            "timestamp": "2019-09-23T11:24:00.000-04:00",
                            "properties": {
                                "file_path": "C:\\Users\\Public\\runme.bat"
                            },
                        }
                    )
                    + "\n",
                )
            lines = list(streamer.open_ecar_lines(zipped, b"OPTC2019"))
            self.assertEqual(1, len(lines))
            self.assertIn(b"runme.bat", lines[0])

    @unittest.skipUnless(
        LOCAL_OPTC_PASSWORD_ZIP.is_file(),
        "requires locally ignored OpTC password ZIP",
    )
    def test_reads_local_password_protected_optc_archive(self):
        line = next(streamer.open_ecar_lines(LOCAL_OPTC_PASSWORD_ZIP, b"OPTC2019"))
        event = json.loads(line)
        self.assertIsInstance(event["timestamp"], str)
        self.assertIn("hostname", event)


if __name__ == "__main__":
    unittest.main()
