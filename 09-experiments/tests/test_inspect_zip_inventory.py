import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = EXPERIMENT_DIR / "scripts" / "inspect_zip_inventory.py"
SPEC = importlib.util.spec_from_file_location("inspect_zip_inventory", MODULE_PATH)
inventory = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(inventory)


class InspectZipInventoryTests(unittest.TestCase):
    def test_safe_archive_inventory_is_content_agnostic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "safe.zip"
            with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("events/part-01.json", '{"event": 1}\n')
                archive.writestr("events/part-02.json", '{"event": 2}\n')

            result = inventory.inspect_archive(archive_path)

        self.assertTrue(result["path_safety_pass"])
        self.assertIsNone(result["first_bad_crc_member"])
        self.assertEqual(2, result["file_member_count"])
        self.assertEqual([], result["duplicate_names"])
        self.assertNotIn("content", result["entries"][0])

    def test_parent_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "unsafe.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("../escape.json", "{}")

            result = inventory.inspect_archive(archive_path, check_crc=False)

        self.assertFalse(result["path_safety_pass"])
        self.assertEqual("parent_traversal", result["unsafe_members"][0]["reason"])

    def test_windows_drive_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "unsafe-drive.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("C:/outside.json", "{}")

            result = inventory.inspect_archive(archive_path, check_crc=False)

        self.assertFalse(result["path_safety_pass"])
        self.assertEqual(
            "windows_drive_path",
            result["unsafe_members"][0]["reason"],
        )


if __name__ == "__main__":
    unittest.main()
