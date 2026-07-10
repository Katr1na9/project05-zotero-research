import importlib.util
import tempfile
import unittest
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = EXPERIMENT_DIR / "scripts" / "resolve_pgdump_nodes.py"
SPEC = importlib.util.spec_from_file_location(
    "resolve_pgdump_nodes",
    MODULE_PATH,
)
resolver = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(resolver)


class PgdumpNodeResolverHelpersTests(unittest.TestCase):
    def test_event_hashes_are_collected_from_both_endpoints(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.tsv"
            path.write_text(
                "src-a\t1\tEVENT_WRITE\tdst-a\t2\tevent-a\t100\t1\n"
                "src-b\t3\tEVENT_READ\tdst-a\t4\tevent-b\t101\t2\n",
                encoding="utf-8",
            )
            self.assertEqual(
                {"src-a", "dst-a", "src-b"},
                resolver.read_event_node_hashes(path),
            )

    def test_node_row_keeps_the_hash_id_join_key(self):
        record = resolver.node_record_from_copy_row(
            "subject_node_table",
            b"UUID-1\thash-1\t/usr/sbin/sshd\tsshd: root@pts/0\t42",
        )
        self.assertEqual("hash-1", record["hash_id"])
        self.assertEqual("/usr/sbin/sshd", record["path"])
        self.assertEqual("subject", record["node_type"])

    def test_node_row_with_wrong_column_count_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected 5 COPY columns"):
            resolver.node_record_from_copy_row("subject_node_table", b"only\ttwo")


if __name__ == "__main__":
    unittest.main()
