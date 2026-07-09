import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = EXPERIMENT_DIR / "scripts" / "download_pidsmaker_dumps.py"


def load_downloader():
    if not MODULE_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location(
        "download_pidsmaker_dumps",
        MODULE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


downloader = load_downloader()


class PidsmakerDownloadTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            downloader,
            "download_pidsmaker_dumps.py has not been implemented",
        )

    def test_uses_ids_published_by_official_pidsmaker_script(self):
        self.assertEqual(
            "1DGcGBhpavNmXTnCDd_s4NWBNh2n4-6nd",
            downloader.DATASETS["cadets_e3"],
        )
        self.assertEqual(
            "17YHqUMbuNwP05iaOaifxvcQc2oC9pJbZ",
            downloader.DATASETS["fivedirections_e3"],
        )

    def test_builds_authorized_request_with_resume_offset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "cadets_e3.dump"
            target.write_bytes(b"partial")

            request = downloader.build_request(
                "cadets_e3",
                target,
                "secret-token",
            )

        self.assertEqual(
            "Bearer secret-token",
            request.get_header("Authorization"),
        )
        self.assertEqual("bytes=7-", request.get_header("Range"))
        self.assertIn(
            downloader.DATASETS["cadets_e3"],
            request.full_url,
        )

    def test_reads_token_from_environment_without_cli_argument(self):
        with patch.dict(
            os.environ,
            {"PIDSMaker_GOOGLE_ACCESS_TOKEN": "secret-token"},
            clear=True,
        ):
            self.assertEqual(
                "secret-token",
                downloader.resolve_access_token(),
            )

    def test_rejects_unknown_dataset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, "Unsupported dataset"):
                downloader.download_dataset(
                    "unknown",
                    Path(temp_dir),
                    "secret-token",
                )


if __name__ == "__main__":
    unittest.main()
