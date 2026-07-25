import hashlib
import importlib.util
import io
import json
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = EXPERIMENT_ROOT.parent
CONTRACT_ROOT = EXPERIMENT_ROOT / "llm_evidence_compiler_mainline" / "contracts"
AUTHORITY_PATH = CONTRACT_ROOT / "authority-lock-v0.7.json"
TRANSPORT_AUTHORITY_PATH = CONTRACT_ROOT / "authority-lock-v0.8.json"
POST_ACQUISITION_AUTHORITY_PATH = CONTRACT_ROOT / "authority-lock-v0.9.json"
SCRIPT_PATH = EXPERIMENT_ROOT / "scripts" / "audit_beth_source_gate.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_script():
    spec = importlib.util.spec_from_file_location("beth_source_gate", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BethSourceGateAuthorityTests(unittest.TestCase):
    def test_v07_authority_exists_and_is_exactly_bounded(self):
        self.assertTrue(AUTHORITY_PATH.is_file(), "v0.7 authority lock is missing")
        authority = load_json(AUTHORITY_PATH)
        gate = authority["beth_single_file_source_gate"]
        self.assertTrue(gate["authority_granted"])
        self.assertEqual("katehighnam/beth-dataset", gate["dataset_ref"])
        self.assertEqual(3, gate["dataset_version_number"])
        self.assertEqual(
            "labelled_2021may-ip-10-100-1-105.csv",
            gate["allowlisted_file"],
        )
        self.assertEqual(512 * 1024 * 1024, gate["maximum_downloaded_bytes"])
        self.assertEqual(1, gate["maximum_source_files"])
        self.assertTrue(gate["license_notice_schema_exclusion_audit_allowed"])
        self.assertTrue(gate["read_only_g0_count_audit_allowed"])
        self.assertFalse(gate["normalized_record_output_allowed"])
        self.assertFalse(gate["formal_candidate_pair_construction_allowed"])
        self.assertFalse(gate["tokenizer_model_training_or_inference_allowed"])
        self.assertFalse(gate["m3_runtime_integration_allowed"])
        self.assertTrue(
            {
                "dependency_install_or_change",
                "whole_beth_dataset_download",
                "second_beth_file_download",
                "normalized_record_output",
                "formal_candidate_pair_construction",
                "tokenizer_download",
                "model_download",
                "smoke_training",
                "formal_training",
                "formal_inference",
                "m3_runtime_integration",
            }
            <= set(authority["not_authorized"])
        )

    def test_v07_hashes_parent_document_and_contract(self):
        self.assertTrue(AUTHORITY_PATH.is_file(), "v0.7 authority lock is missing")
        authority = load_json(AUTHORITY_PATH)
        parent = authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        for group in ("authoritative_documents", "authoritative_contracts"):
            for relative, expected in authority[group].items():
                with self.subTest(path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))

    def test_v08_allows_only_an_exact_single_member_transport_zip(self):
        self.assertTrue(
            TRANSPORT_AUTHORITY_PATH.is_file(), "v0.8 transport authority is missing"
        )
        authority = load_json(TRANSPORT_AUTHORITY_PATH)
        wrapper = authority["kaggle_single_file_transport_wrapper"]
        self.assertTrue(wrapper["authority_granted"])
        self.assertEqual(
            "labelled_2021may-ip-10-100-1-105.csv.zip",
            wrapper["allowlisted_transport_name"],
        )
        self.assertEqual(1, wrapper["required_member_count"])
        self.assertEqual(
            "labelled_2021may-ip-10-100-1-105.csv",
            wrapper["required_member_name"],
        )
        self.assertFalse(wrapper["second_member_allowed"])
        self.assertFalse(wrapper["encrypted_member_allowed"])
        self.assertFalse(wrapper["whole_dataset_archive_allowed"])
        parent = authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        for group in ("authoritative_documents", "authoritative_contracts"):
            for relative, expected in authority[group].items():
                with self.subTest(path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))

    def test_v09_locks_exact_observed_schema_and_composite_license_evidence(self):
        self.assertTrue(
            POST_ACQUISITION_AUTHORITY_PATH.is_file(),
            "v0.9 post-acquisition authority is missing",
        )
        authority = load_json(POST_ACQUISITION_AUTHORITY_PATH)
        correction = authority["beth_post_acquisition_correction"]
        self.assertTrue(correction["authority_granted"])
        self.assertEqual(13, correction["required_csv_field_count"])
        self.assertEqual(
            ["threadId", "mountNamespace", "stackAddresses"],
            correction["published_but_absent_fields"],
        )
        self.assertFalse(correction["missing_field_imputation_allowed"])
        self.assertFalse(correction["label_supervision_allowed"])
        parent = authority["parent_authority"]
        self.assertEqual(parent["sha256"], sha256(REPO_ROOT / parent["path"]))
        for group in ("authoritative_documents", "authoritative_contracts"):
            for relative, expected in authority[group].items():
                with self.subTest(path=relative):
                    self.assertEqual(expected, sha256(REPO_ROOT / relative))


class BethSourceGateScriptTests(unittest.TestCase):
    def test_source_gate_script_exists(self):
        self.assertTrue(SCRIPT_PATH.is_file(), "BETH source-gate script is missing")


class BethSourceGateBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_script()
        cls.contract = load_json(CONTRACT_ROOT / "beth-source-gate-contract-v0.2.json")

    def make_csv(self, path: Path, *, label_value: int = 0, protected=None):
        header = self.contract["required_schema_fields"]
        lines = [",".join(header)]
        for index in range(160):
            process_name = protected if protected and index == 0 else f"proc{index}"
            values = {
                "timestamp": str(1000.0 + index),
                "processId": str(2000 + index),
                "threadId": str(3000 + index),
                "parentProcessId": str(1000 + index),
                "userId": "1000",
                "mountNamespace": "4026531840",
                "processName": process_name,
                "hostName": "ip-10-100-1-105",
                "eventId": "59",
                "eventName": "execve",
                "argsNum": "1",
                "returnValue": "0",
                "stackAddresses": "[]",
                "args": "[]",
                "sus": str(label_value),
                "evil": str(label_value),
            }
            lines.append(",".join(values[name] for name in header))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    def acquisition(self, path: Path) -> dict:
        return {
            "dataset_ref": "katehighnam/beth-dataset",
            "dataset_version_number": 3,
            "file_name": "labelled_2021may-ip-10-100-1-105.csv",
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "response_content_type": "text/csv",
            "license_status": "passed_cc0_v3_no_conflicting_notice",
            "nested_notice_conflicts": [],
        }

    def fixture_contract(self, path: Path) -> dict:
        contract = json.loads(json.dumps(self.contract))
        dataset = contract["dataset"]
        dataset["expected_csv_bytes"] = path.stat().st_size
        dataset["expected_csv_sha256"] = sha256(path)
        dataset.pop("expected_transport_zip_bytes", None)
        dataset.pop("expected_transport_zip_sha256", None)
        return contract

    def metadata_bundle(self) -> dict:
        expected_names = self.contract["license_evidence"]["expected_file_inventory"]
        return {
            "dataset_view": {
                "ref": "katehighnam/beth-dataset",
                "currentVersionNumber": 3,
                "licenseName": "CC0: Public Domain",
            },
            "file_inventory": {
                "datasetFiles": [{"name": name} for name in expected_names],
            },
            "request": {
                "dataset_version_number": 3,
                "page_extract_sha256": self.contract["license_evidence"][
                    "page_extract_sha256"
                ],
            },
        }

    def small_lock(self, protected_text: str) -> dict:
        normalized = self.module.normalized_text(protected_text)
        grams = self.module.hashed_character_ngrams(normalized, 5)
        return {
            "character_ngram_n": 5,
            "contains_raw_private_gold": False,
            "contains_raw_test_payload": False,
            "minimum_protected_text_chars": 16,
            "near_duplicate_threshold": 0.85,
            "normalized_text_hashes": [
                self.module.sha256_bytes(normalized.encode("utf-8"))
            ],
            "ngram_signatures": [
                {
                    "normalized_text_sha256": self.module.sha256_bytes(
                        normalized.encode("utf-8")
                    ),
                    "ngram_count": len(grams),
                    "ngram_hashes": sorted(grams),
                }
            ],
        }

    def test_request_is_version_file_and_size_exact(self):
        url = self.module.build_download_url(
            "katehighnam/beth-dataset",
            3,
            "labelled_2021may-ip-10-100-1-105.csv",
            512 * 1024 * 1024,
        )
        self.assertIn("datasetVersionNumber=3", url)
        self.assertIn("fileName=labelled_2021may-ip-10-100-1-105.csv", url)
        self.assertNotIn("versions/latest", url)
        for field, value in (
            ("dataset_ref", "other/dataset"),
            ("version", 2),
            ("file_name", "labelled_training_data.csv"),
            ("max_bytes", 928188305),
        ):
            kwargs = {
                "dataset_ref": "katehighnam/beth-dataset",
                "version": 3,
                "file_name": "labelled_2021may-ip-10-100-1-105.csv",
                "max_bytes": 512 * 1024 * 1024,
            }
            kwargs[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.module.build_download_url(**kwargs)

    def test_bounded_copy_is_atomic_caps_bytes_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "source.csv"
            report = self.module.copy_bounded_stream(
                io.BytesIO(b"header\nrow\n"), output, max_bytes=64
            )
            self.assertEqual(11, report["bytes"])
            self.assertEqual(sha256(output), report["sha256"])
            with self.assertRaises(FileExistsError):
                self.module.copy_bounded_stream(io.BytesIO(b"x"), output, 64)
            capped = root / "capped.csv"
            with self.assertRaises(ValueError):
                self.module.copy_bounded_stream(io.BytesIO(b"x" * 65), capped, 64)
            self.assertFalse(capped.exists())
            self.assertFalse((root / "capped.csv.part").exists())

    def test_retrieval_wrapper_checks_response_identity_and_declared_size(self):
        class FakeResponse(io.BytesIO):
            status = 200

            def __init__(self, payload, *, final_url, length=None, disposition=None):
                super().__init__(payload)
                self._final_url = final_url
                self.headers = {
                    "Content-Type": "text/csv",
                    "Content-Length": str(length if length is not None else len(payload)),
                }
                if disposition is not None:
                    self.headers["Content-Disposition"] = disposition

            def geturl(self):
                return self._final_url

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def clean_open(request, timeout):
                self.assertIn("datasetVersionNumber=3", request.full_url)
                self.assertIn("fileName=labelled_2021may-ip-10-100-1-105.csv", request.full_url)
                self.assertTrue(request.get_header("Authorization").startswith("Basic "))
                return FakeResponse(
                    b"timestamp,processId\n1,2\n",
                    final_url=(
                        "https://storage.example/"
                        "labelled_2021may-ip-10-100-1-105.csv?signature=x"
                    ),
                )

            output = root / "labelled_2021may-ip-10-100-1-105.csv"
            report = self.module.retrieve_single_file(
                output, opener=clean_open, authorization="Basic Zml4dHVyZQ=="
            )
            self.assertEqual(sha256(output), report["sha256"])
            self.assertEqual(3, report["dataset_version_number"])
            self.assertEqual(
                "labelled_2021may-ip-10-100-1-105.csv", report["file_name"]
            )
            self.assertNotIn("authorization", json.dumps(report).casefold())

            def oversized_open(request, timeout):
                return FakeResponse(
                    b"unused",
                    final_url="https://storage.example/labelled_2021may-ip-10-100-1-105.csv",
                    length=512 * 1024 * 1024 + 1,
                )

            with self.assertRaises(ValueError):
                self.module.retrieve_single_file(
                    root / "oversized.csv",
                    opener=oversized_open,
                    authorization="Basic Zml4dHVyZQ==",
                )
            self.assertFalse((root / "oversized.csv").exists())

            def wrong_file_open(request, timeout):
                return FakeResponse(
                    b"unused",
                    final_url="https://storage.example/beth-dataset.zip",
                    disposition='attachment; filename="beth-dataset.zip"',
                )

            with self.assertRaises(ValueError):
                self.module.retrieve_single_file(
                    root / "wrong.csv",
                    opener=wrong_file_open,
                    authorization="Basic Zml4dHVyZQ==",
                )
            self.assertFalse((root / "wrong.csv").exists())

    def test_official_single_member_zip_wrapper_is_accepted_and_extra_member_rejected(self):
        class FakeResponse(io.BytesIO):
            status = 200

            def __init__(self, payload):
                super().__init__(payload)
                self.headers = {
                    "Content-Type": "application/zip",
                    "Content-Length": str(len(payload)),
                }

            def geturl(self):
                return (
                    "https://storage.example/"
                    "labelled_2021may-ip-10-100-1-105.csv.zip?signature=redacted"
                )

        def archive(extra=False):
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                bundle.writestr(
                    "labelled_2021may-ip-10-100-1-105.csv",
                    "timestamp,processId\n1,2\n",
                )
                if extra:
                    bundle.writestr("README.txt", "unexpected second member")
            return buffer.getvalue()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def clean_open(request, timeout):
                return FakeResponse(archive())

            destination = root / "labelled_2021may-ip-10-100-1-105.csv"
            report = self.module.retrieve_single_file(
                destination,
                opener=clean_open,
                authorization="Basic Zml4dHVyZQ==",
            )
            self.assertTrue(destination.is_file())
            self.assertEqual(sha256(destination), report["sha256"])
            self.assertEqual("single_member_zip", report["transport"]["kind"])
            self.assertEqual(1, report["transport"]["member_count"])
            self.assertTrue(Path(report["transport"]["archive_path"]).is_file())

            def extra_open(request, timeout):
                return FakeResponse(archive(extra=True))

            rejected = root / "rejected.csv"
            with self.assertRaises(ValueError):
                self.module.retrieve_single_file(
                    rejected,
                    opener=extra_open,
                    authorization="Basic Zml4dHVyZQ==",
                )
            self.assertFalse(rejected.exists())
            self.assertFalse((root / "rejected.csv.zip").exists())

    def test_zip_wrapper_rejects_traversal_symlink_ratio_bomb_and_bad_crc(self):
        class FakeResponse(io.BytesIO):
            status = 200

            def __init__(self, payload):
                super().__init__(payload)
                self.headers = {
                    "Content-Type": "application/zip",
                    "Content-Length": str(len(payload)),
                }

            def geturl(self):
                return (
                    "https://storage.example/"
                    "labelled_2021may-ip-10-100-1-105.csv.zip"
                )

        def make_archive(kind):
            buffer = io.BytesIO()
            compression = zipfile.ZIP_STORED if kind == "bad_crc" else zipfile.ZIP_DEFLATED
            with zipfile.ZipFile(buffer, "w", compression=compression) as bundle:
                if kind == "traversal":
                    bundle.writestr("../labelled_2021may-ip-10-100-1-105.csv", "x")
                elif kind == "symlink":
                    member = zipfile.ZipInfo(
                        "labelled_2021may-ip-10-100-1-105.csv"
                    )
                    member.create_system = 3
                    member.external_attr = (stat.S_IFLNK | 0o777) << 16
                    bundle.writestr(member, "target.csv")
                elif kind == "ratio_bomb":
                    bundle.writestr(
                        "labelled_2021may-ip-10-100-1-105.csv", b"A" * 200000
                    )
                else:
                    bundle.writestr(
                        "labelled_2021may-ip-10-100-1-105.csv",
                        b"timestamp,processId\n1,2\n",
                    )
            payload = buffer.getvalue()
            if kind == "bad_crc":
                payload = payload.replace(b"timestamp", b"Timestamp", 1)
            return payload

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for kind in ("traversal", "symlink", "ratio_bomb", "bad_crc"):
                destination = root / f"{kind}.csv"

                def rejected_open(request, timeout, payload=make_archive(kind)):
                    return FakeResponse(payload)

                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    self.module.retrieve_single_file(
                        destination,
                        opener=rejected_open,
                        authorization="Basic Zml4dHVyZQ==",
                    )
                self.assertFalse(destination.exists())
                self.assertFalse((root / f"{kind}.csv.zip").exists())
                self.assertFalse((root / f"{kind}.csv.part").exists())

    def test_kaggle_credentials_load_only_from_external_config_or_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".kaggle" / "kaggle.json"
            config.parent.mkdir()
            config.write_text(
                json.dumps({"username": "fixture-user", "key": "fixture-key"}),
                encoding="utf-8",
            )
            authorization = self.module.load_kaggle_authorization(
                home=home, environ={}
            )
            self.assertTrue(authorization.startswith("Basic "))
            self.assertNotIn("fixture-user", authorization)
            env_authorization = self.module.load_kaggle_authorization(
                home=home / "absent",
                environ={
                    "KAGGLE_USERNAME": "env-user",
                    "KAGGLE_KEY": "env-key",
                },
            )
            self.assertTrue(env_authorization.startswith("Basic "))
            with self.assertRaises(PermissionError):
                self.module.load_kaggle_authorization(
                    home=home / "absent", environ={}
                )

    def test_payload_type_rejects_archive_html_and_json_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, payload in (
                ("archive.csv", b"PK\x03\x04archive"),
                ("html.csv", b"<html>login</html>"),
                ("json.csv", b'{"error":"not authorized"}'),
            ):
                path = root / name
                path.write_bytes(payload)
                with self.subTest(name=name), self.assertRaises(ValueError):
                    self.module.validate_csv_payload_kind(path)

    def test_license_finalizer_requires_v3_cc0_file_inventory_and_legalcode(self):
        legalcode = b"fixture official CC0 legalcode"
        expected_legalcode_hash = self.module.sha256_bytes(legalcode)
        metadata = self.metadata_bundle()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "labelled_2021may-ip-10-100-1-105.csv"
            self.make_csv(path)
            retrieval = self.acquisition(path)
            retrieval.pop("license_status")
            retrieval.pop("nested_notice_conflicts")
            finalized = self.module.finalize_license_audit(
                path,
                retrieval,
                metadata,
                legalcode,
                self.fixture_contract(path),
                expected_legalcode_sha256=expected_legalcode_hash,
            )
            self.assertEqual(
                "passed_cc0_v3_no_conflicting_notice", finalized["license_status"]
            )
            self.assertEqual([], finalized["nested_notice_conflicts"])
            self.assertEqual(expected_legalcode_hash, finalized["license_evidence"]["legalcode_sha256"])
            conflicting = json.loads(json.dumps(metadata))
            conflicting["dataset_view"]["licenseName"] = "CC-BY-NC-4.0"
            with self.assertRaises(ValueError):
                self.module.finalize_license_audit(
                    path,
                    retrieval,
                    conflicting,
                    legalcode,
                    self.fixture_contract(path),
                    expected_legalcode_sha256=expected_legalcode_hash,
                )
            with self.assertRaises(ValueError):
                self.module.finalize_license_audit(
                    path,
                    retrieval,
                    metadata,
                    b"wrong legalcode",
                    self.fixture_contract(path),
                    expected_legalcode_sha256=expected_legalcode_hash,
                )

    def test_composite_metadata_keeps_view_and_inventory_evidence_separate(self):
        legalcode = b"fixture official CC0 legalcode"
        expected_legalcode_hash = self.module.sha256_bytes(legalcode)
        bundle = self.metadata_bundle()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "labelled_2021may-ip-10-100-1-105.csv"
            self.make_csv(path)
            retrieval = self.acquisition(path)
            retrieval.pop("license_status")
            retrieval.pop("nested_notice_conflicts")
            finalized = self.module.finalize_license_audit(
                path,
                retrieval,
                bundle,
                legalcode,
                self.fixture_contract(path),
                expected_legalcode_sha256=expected_legalcode_hash,
            )
            evidence = finalized["license_evidence"]
            self.assertEqual(15, evidence["metadata_file_count"])
            self.assertIn("dataset_view_canonical_sha256", evidence)
            self.assertIn("file_inventory_canonical_sha256", evidence)
            broken = json.loads(json.dumps(bundle))
            broken["file_inventory"]["datasetFiles"].pop()
            with self.assertRaises(ValueError):
                self.module.finalize_license_audit(
                    path,
                    retrieval,
                    broken,
                    legalcode,
                    self.fixture_contract(path),
                    expected_legalcode_sha256=expected_legalcode_hash,
                )

    def test_read_only_audit_is_label_invariant_and_emits_counts_only(self):
        clean_lock = self.small_lock("protected sentence absent from every source row")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            zero = root / "zero.csv"
            one = root / "one.csv"
            self.make_csv(zero, label_value=0)
            self.make_csv(one, label_value=1)
            first = self.module.audit_beth_csv(
                zero, self.fixture_contract(zero), clean_lock, self.acquisition(zero)
            )
            second = self.module.audit_beth_csv(
                one, self.fixture_contract(one), clean_lock, self.acquisition(one)
            )
            self.assertEqual("passed_candidate_fourth_family_source_gate", first["status"])
            self.assertEqual(160, first["g0_audit"]["eligible_candidates"])
            self.assertEqual(
                first["g0_audit"]["eligible_candidates"],
                second["g0_audit"]["eligible_candidates"],
            )
            self.assertEqual(
                first["g0_audit"]["candidate_digest"],
                second["g0_audit"]["candidate_digest"],
            )
            self.assertEqual([], first["prohibited_supervision"]["fields_used"])
            self.assertNotIn("records", first)
            self.assertNotIn("candidates", first)
            self.assertFalse(first["execution_claims"]["candidate_pairs_constructed"])
            self.assertFalse(first["execution_claims"]["normalized_records_written"])

    def test_exact_and_near_protected_matches_fail_closed(self):
        protected = "this protected process sentence must never enter training"
        near = "this protected process sentence must never enter traininx"
        lock = self.small_lock(protected)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            exact_path = root / "exact.csv"
            near_path = root / "near.csv"
            self.make_csv(exact_path, protected=protected)
            self.make_csv(near_path, protected=near)
            exact = self.module.audit_beth_csv(
                exact_path,
                self.fixture_contract(exact_path),
                lock,
                self.acquisition(exact_path),
            )
            near_report = self.module.audit_beth_csv(
                near_path,
                self.fixture_contract(near_path),
                lock,
                self.acquisition(near_path),
            )
            self.assertEqual("failed_closed", exact["status"])
            self.assertGreater(exact["protected_scan"]["exact_matches"], 0)
            self.assertEqual("failed_closed", near_report["status"])
            self.assertGreater(near_report["protected_scan"]["near_matches"], 0)
            self.assertEqual([], exact["protected_scan"]["raw_matches"])

    def test_schema_or_identity_mismatch_fails_before_candidate_credit(self):
        lock = self.small_lock("protected sentence absent from every source row")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "bad.csv"
            path.write_text("timestamp,processId,sus,evil\n1,2,0,0\n", encoding="utf-8")
            report = self.module.audit_beth_csv(
                path, self.fixture_contract(path), lock, self.acquisition(path)
            )
            self.assertEqual("failed_closed", report["status"])
            self.assertIn("csv_schema_mismatch", report["errors"])
            acquisition = self.acquisition(path)
            acquisition["dataset_version_number"] = 2
            report = self.module.audit_beth_csv(
                path, self.fixture_contract(path), lock, acquisition
            )
            self.assertIn("acquisition_identity_mismatch", report["errors"])

    def test_cli_freezes_request_url_and_writes_waiting_status_once(self):
        request = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "request-url"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("datasetVersionNumber=3", request.stdout)
        self.assertIn("fileName=labelled_2021may-ip-10-100-1-105.csv", request.stdout)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "status.json"
            command = [
                sys.executable,
                str(SCRIPT_PATH),
                "waiting-report",
                "--output",
                str(output),
            ]
            subprocess.run(command, check=True, capture_output=True, text=True)
            status = load_json(output)
            self.assertEqual("awaiting_kaggle_authentication", status["status"])
            self.assertEqual(
                "kaggle_authentication_required_or_single_file_endpoint_not_public",
                status["blocking_condition"]["code"],
            )
            self.assertFalse(status["blocking_condition"]["local_credentials_present"])
            self.assertFalse(status["execution_claims"]["corpus_downloaded"])
            self.assertFalse(status["execution_claims"]["candidate_pairs_constructed"])
            repeated = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(0, repeated.returncode)


if __name__ == "__main__":
    unittest.main()
