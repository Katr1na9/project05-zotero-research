import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWLIST = (
    REPO_ROOT
    / "04-progress"
    / "m3star-final-blind-data-intake-v0.1-20260719"
    / "final-blind-missing-reacquisition-allowlist-v0.3.json"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


ACQUIRE = load_module(
    "acquire_m3star_final_blind_missing_v03_test",
    REPO_ROOT
    / "09-experiments"
    / "scripts"
    / "acquire_m3star_final_blind_missing_v03.py",
)


class MissingBlindArtifactAcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(ALLOWLIST.read_text(encoding="utf-8"))

    def test_frozen_allowlist_has_exact_15_files_and_byte_total(self):
        result = ACQUIRE.validate_plan(self.plan)
        self.assertEqual(5, result["record_count"])
        self.assertEqual(15, result["file_count"])
        self.assertEqual(18_308_224_167, result["download_bytes"])
        self.assertEqual(
            ACQUIRE.EXPECTED_FILES,
            {
                (
                    str(record["record_id"]),
                    item["key"],
                    item["size"],
                    item["publisher_md5"],
                    item["access_class"],
                )
                for record in self.plan["records"]
                for item in record["files"]
            },
        )

    def test_nonselected_ainception_variant_cannot_replace_frozen_file(self):
        changed = copy.deepcopy(self.plan)
        record = next(
            item
            for item in changed["records"]
            if item["record_id"] == "17659656"
        )
        record["files"][0]["key"] = "SL300_variant_7.zip"
        record["files"][0][
            "download_url"
        ] = "https://zenodo.org/api/records/17659656/files/SL300_variant_7.zip/content"
        with self.assertRaisesRegex(ValueError, "identity set differs"):
            ACQUIRE.validate_plan(changed)

    def test_external_download_host_is_rejected(self):
        changed = copy.deepcopy(self.plan)
        changed["records"][0]["files"][0][
            "download_url"
        ] = "https://example.invalid/file"
        with self.assertRaisesRegex(ValueError, "outside the exact endpoint"):
            ACQUIRE.validate_plan(changed)

    def test_existing_verified_file_is_reused_without_network_access(self):
        content = b"sealed-fixture"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            record = {
                "record_id": "fixture",
                "source_id": "fixture",
                "destination_subdir": "sealed",
            }
            item = {
                "key": "payload.bin",
                "size": len(content),
                "publisher_md5": hashlib.md5(
                    content, usedforsecurity=False
                ).hexdigest(),
                "download_url": "https://example.invalid/not-used",
                "access_class": "sealed_telemetry_payload",
            }
            path = root / "sealed" / "payload.bin"
            path.parent.mkdir(parents=True)
            path.write_bytes(content)
            result = ACQUIRE.download_one(record, item, root)
        self.assertTrue(result["download_reused"])
        self.assertTrue(result["publisher_md5_verified"])
        self.assertEqual(hashlib.sha256(content).hexdigest(), result["sha256"])

    def test_parallel_range_assembly_preserves_existing_prefix(self):
        content = bytes(range(251)) * 100
        prefix_size = 1234
        with tempfile.TemporaryDirectory() as temporary:
            partial = Path(temporary) / "payload.bin.part"
            partial.write_bytes(content[:prefix_size])
            item = {
                "key": "payload.bin",
                "size": len(content),
                "download_url": "https://example.invalid/not-used",
            }
            record = {"record_id": "fixture"}
            original = ACQUIRE.download_range

            def fake_download_range(
                *,
                url,
                item,
                range_start,
                range_end,
                segment_path,
                on_chunk,
            ):
                chunk = content[range_start : range_end + 1]
                segment_path.write_bytes(chunk)
                on_chunk(len(chunk))

            ACQUIRE.download_range = fake_download_range
            try:
                ACQUIRE.download_parallel_ranges(
                    partial=partial,
                    current=prefix_size,
                    item=item,
                    record=record,
                    connections=4,
                )
            finally:
                ACQUIRE.download_range = original
            observed = partial.read_bytes()
        self.assertEqual(content, observed)

    def test_split_ranges_are_contiguous_and_exhaustive(self):
        ranges = ACQUIRE.split_ranges(100, 999, 4)
        self.assertEqual(100, ranges[0][0])
        self.assertEqual(999, ranges[-1][1])
        self.assertEqual(
            900,
            sum(end - start + 1 for start, end in ranges),
        )
        for left, right in zip(ranges, ranges[1:]):
            self.assertEqual(left[1] + 1, right[0])

    def test_short_range_response_retries_from_preserved_segment_length(self):
        content = b"abcdefghij"
        calls = []

        class FakeResponse:
            status = 206

            def __init__(self, start, chunk):
                self.headers = {"Content-Range": f"bytes {start}-9/10"}
                self.chunk = chunk

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def getcode(self):
                return self.status

            def read(self, size):
                if self.chunk is None:
                    return b""
                chunk, self.chunk = self.chunk, None
                return chunk

        def fake_urlopen(request, timeout):
            range_header = request.get_header("Range")
            calls.append(range_header)
            start = int(range_header.split("=")[1].split("-")[0])
            end = 5 if len(calls) == 1 else 10
            return FakeResponse(start, content[start:end])

        original_urlopen = ACQUIRE.urllib.request.urlopen
        original_sleep = ACQUIRE.time.sleep
        ACQUIRE.urllib.request.urlopen = fake_urlopen
        ACQUIRE.time.sleep = lambda seconds: None
        try:
            with tempfile.TemporaryDirectory() as temporary:
                segment = Path(temporary) / "segment.part"
                ACQUIRE.download_range(
                    url="https://example.invalid/not-used",
                    item={
                        "key": "payload.bin",
                        "size": len(content),
                        "download_url": "https://example.invalid/not-used",
                    },
                    range_start=0,
                    range_end=9,
                    segment_path=segment,
                    on_chunk=lambda length: None,
                )
                observed = segment.read_bytes()
        finally:
            ACQUIRE.urllib.request.urlopen = original_urlopen
            ACQUIRE.time.sleep = original_sleep
        self.assertEqual(content, observed)
        self.assertEqual(["bytes=0-9", "bytes=5-9"], calls)


if __name__ == "__main__":
    unittest.main()
