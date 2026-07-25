import hashlib
import importlib.util
import json
import zipfile
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "datasets"
    / "llm"
    / "audit_bounded_lineage.py"
)
SPEC = importlib.util.spec_from_file_location("audit_bounded_lineage", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


GLOBAL_POLICY = {
    "payload_scalar_fields_allowed": [
        "@timestamp",
        "timestamp",
        "ts",
        "host.name",
        "hostname",
        "host",
    ],
    "forbidden_path_tokens": ["label", "labels", "answer", "ground_truth"],
    "forbidden_field_tokens": ["label", "class", "target", "gold"],
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_zip(path: Path, members: dict[str, str]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in members.items():
            archive.writestr(name, value)


def test_forbidden_field_suppresses_lineage_scalars() -> None:
    line = json.dumps(
        {
            "@timestamp": "2026-01-01T00:00:00Z",
            "host": {"name": "host-a"},
            "label": "abnormal",
        }
    ).encode("utf-8")
    timestamps, hosts = AUDIT._extract_allowed_scalars(
        line,
        allowed_fields=GLOBAL_POLICY["payload_scalar_fields_allowed"],
        forbidden_fields=GLOBAL_POLICY["forbidden_field_tokens"],
        family="test",
    )
    assert timestamps == []
    assert hosts == set()


def test_cam_steps_are_repeated_views_of_collection(tmp_path: Path) -> None:
    archive_path = tmp_path / "manifestations_filtered.zip"
    _write_zip(
        archive_path,
        {
            "root/run-a/steps/step-1/logs/host-a/a.jsonl": (
                '{"@timestamp":"2026-01-01T00:00:00Z","host":{"name":"a"}}\n'
            ),
            "root/run-a/steps/step-2/logs/host-b/b.jsonl": (
                '{"@timestamp":"2026-01-01T00:01:00Z","host":{"name":"b"}}\n'
            ),
            "root/run-b/steps/step-1/logs/host-c/c.jsonl": (
                '{"@timestamp":"2026-01-02T00:00:00Z","host":{"name":"c"}}\n'
            ),
            "root/run-a/sequences/forbidden.json": '{"label":"attack"}\n',
        },
    )
    policy = {
        "source_family_id": "ait_cam_lds_manifestations_filtered",
        "archive": {
            "path_suffix": "manifestations_filtered.zip",
            "sha256": _sha256(archive_path),
            "maximum_archive_bytes": archive_path.stat().st_size,
            "maximum_member_uncompressed_bytes": 1024 * 1024,
            "maximum_payload_members_read": 10,
            "maximum_payload_bytes_read": 1024 * 1024,
        },
        "member_allowlist": {
            "required_path_markers": ["steps", "logs"],
            "allowed_suffixes": [".log", ".json", ".jsonl", ".txt"],
            "forbidden_path_markers": [
                "techniques",
                "sequences",
                "configs",
                "attacker",
                "facts.json",
                "eve.json",
            ],
        },
        "deterministic_sampling": {"maximum_lines_per_member": 256},
    }
    result = AUDIT._audit_cam(archive_path, policy, GLOBAL_POLICY)
    assert result["central_directory"]["eligible_member_count"] == 3
    assert result["grouping"]["collection_candidate_count"] == 2
    assert result["grouping"]["step_group_count"] == 3
    assert result["grouping"]["independence_demonstrated"] is False
    assert result["grouping"]["counts_toward_independent_lineage_quota"] is False


def test_socbed_suffix_clusters_views_into_runs(tmp_path: Path) -> None:
    archive_path = tmp_path / "dataset.zip"
    members = {}
    for run, day in ((1, "01"), (2, "02")):
        for view in ("host-a", "host-b"):
            members[f"dataset/{view}/winlogbeat_{run}.jsonl"] = json.dumps(
                {
                    "@timestamp": f"2026-01-{day}T00:00:0{run}Z",
                    "host": {"name": view},
                    "observer": run,
                }
            ) + "\n"
    _write_zip(archive_path, members)
    policy = {
        "source_family_id": "fkie_socbed_acsac2021_winlogbeat",
        "archive": {
            "path_suffix": "dataset.zip",
            "sha256": _sha256(archive_path),
            "maximum_archive_bytes": archive_path.stat().st_size,
            "maximum_member_uncompressed_bytes": 1024 * 1024,
            "maximum_payload_members_read": 4,
            "maximum_payload_bytes_read": 1024 * 1024,
        },
        "member_allowlist": {
            "path_regex": r"(?i)(?:^|/)winlogbeat_([0-9]+)\.jsonl$"
        },
        "deterministic_sampling": {"maximum_lines_per_member": 512},
    }
    result = AUDIT._audit_socbed(archive_path, policy, GLOBAL_POLICY)
    assert result["central_directory"]["eligible_member_count"] == 4
    assert result["grouping"]["parent_view_count"] == 2
    assert result["grouping"]["run_suffix_count"] == 2
    assert result["grouping"]["bounded_run_group_count"] == 2
    assert result["grouping"]["all_run_groups_passed"] is True
    assert result["grouping"]["statistical_independence_demonstrated"] is False
    assert result["grouping"]["counts_toward_independent_lineage_quota"] is False
