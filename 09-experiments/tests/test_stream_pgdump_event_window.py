import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace


EXPERIMENT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = EXPERIMENT_DIR / "scripts" / "stream_pgdump_event_window.py"
SPEC = importlib.util.spec_from_file_location(
    "stream_pgdump_event_window",
    MODULE_PATH,
)
streamer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(streamer)


def event_row(timestamp_ns: int, row_id: int = 1) -> bytes:
    return (
        "src-hash\t10\tEVENT_WRITE\tdst-hash\t20\t"
        f"event-{row_id}\t{timestamp_ns}\t{row_id}"
    ).encode("utf-8")


class EventWindowHelpersTests(unittest.TestCase):
    def test_utc_time_bounds_are_nanosecond_precise(self):
        self.assertEqual(
            1557946080000000000,
            streamer.utc_to_epoch_ns("2019-05-15T18:48:00Z"),
        )
        self.assertEqual(
            1557947220000000000,
            streamer.utc_to_epoch_ns("2019-05-15T19:07:00Z"),
        )

    def test_window_is_start_inclusive_and_end_exclusive(self):
        start = 100
        end = 200
        self.assertTrue(streamer.event_in_window(event_row(start), start, end))
        self.assertTrue(streamer.event_in_window(event_row(end - 1), start, end))
        self.assertFalse(streamer.event_in_window(event_row(end), start, end))

    def test_event_timestamp_uses_the_seventh_copy_column(self):
        row = event_row(123456789, row_id=9)
        self.assertEqual(123456789, streamer.event_timestamp_ns(row))

    def test_malformed_event_rows_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "8 COPY columns"):
            streamer.event_timestamp_ns(b"too\tfew\tcolumns")

    def test_non_utc_input_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "UTC offset"):
            streamer.utc_to_epoch_ns("2019-05-15T18:48:00")

    def test_table_entry_selection_is_not_limited_to_event_table(self):
        dump = SimpleNamespace(
            entries=[
                SimpleNamespace(
                    desc="TABLE DATA",
                    namespace="public",
                    tag="event_table",
                ),
                SimpleNamespace(
                    desc="TABLE DATA",
                    namespace="public",
                    tag="subject_node_table",
                ),
            ]
        )
        entry = streamer.find_table_data_entry(dump, "subject_node_table")
        self.assertEqual("subject_node_table", entry.tag)


if __name__ == "__main__":
    unittest.main()
