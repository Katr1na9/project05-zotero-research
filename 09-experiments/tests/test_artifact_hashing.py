import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


EXP = Path(__file__).resolve().parents[1]
HASHING_PATH = EXP / "scripts" / "artifact_hashing.py"


def load_hashing():
    spec = importlib.util.spec_from_file_location("artifact_hashing", HASHING_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArtifactHashingTests(unittest.TestCase):
    def test_repository_text_hash_is_newline_portable_while_raw_hash_is_exact(self):
        self.assertTrue(
            HASHING_PATH.is_file(),
            "artifact_hashing.py must define explicit raw and repository-text schemes",
        )
        hashing = load_hashing()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            lf = root / "lf.txt"
            crlf = root / "crlf.txt"
            lf.write_bytes(b"alpha\nbeta\n")
            crlf.write_bytes(b"alpha\r\nbeta\r\n")

            self.assertNotEqual(
                hashing.file_sha256(lf, hashing.RAW_BYTES_SHA256),
                hashing.file_sha256(crlf, hashing.RAW_BYTES_SHA256),
            )
            self.assertEqual(
                hashing.file_sha256(lf, hashing.UTF8_LF_NORMALIZED_SHA256),
                hashing.file_sha256(crlf, hashing.UTF8_LF_NORMALIZED_SHA256),
            )
            self.assertEqual(
                hashlib.sha256(b"alpha\nbeta\n").hexdigest(),
                hashing.file_sha256(crlf, hashing.UTF8_LF_NORMALIZED_SHA256),
            )

    def test_repository_text_hash_rejects_invalid_utf8_and_unknown_schemes(self):
        self.assertTrue(HASHING_PATH.is_file())
        hashing = load_hashing()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "invalid.bin"
            path.write_bytes(b"\xff\xfe")

            with self.assertRaises(UnicodeDecodeError):
                hashing.file_sha256(path, hashing.UTF8_LF_NORMALIZED_SHA256)
            with self.assertRaisesRegex(ValueError, "unsupported artifact hash scheme"):
                hashing.file_sha256(path, "invented_scheme")


if __name__ == "__main__":
    unittest.main()
