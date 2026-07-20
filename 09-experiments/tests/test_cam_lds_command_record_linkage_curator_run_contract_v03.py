import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPO_ROOT
    / "04-progress"
    / "m3star-final-blind-data-intake-v0.1-20260719"
    / "cam-lds-command-record-linkage-curator-run-contract-v0.3.json"
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_cam_linkage_contract_is_frozen_and_script_bound():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["status"] == (
        "frozen_before_private_command_record_linkage_audit"
    )
    scope = contract["frozen_case_scope"]
    assert scope["eligible_case_count"] == 7
    assert scope["eligible_case_ids"] == [
        f"C0{case_id}-final-blind" for case_id in range(21, 28)
    ]
    assert scope["comparison_case_count"] == 0
    policy = contract["frozen_command_anchor_policy"]
    assert policy["maximum_records_per_anchor"] == 5
    assert policy["minimum_distinct_record_anchored_mapping_commitments"] == 2
    assert policy["single_mapped_node_is_not_a_chain"]
    fields = set(
        contract["frozen_telemetry_policy"][
            "allowed_structured_field_names_case_insensitive"
        ]
    )
    assert "name" not in fields
    assert "path" not in fields
    assert contract["frozen_telemetry_policy"][
        "generic_name_or_path_fields_forbidden"
    ]
    for item in contract["pinned_scripts"]:
        assert sha256(REPO_ROOT / item["path"]) == item["sha256"]
    assert not contract["one_shot_evaluation_consumed"]
    assert not contract["one_shot_execution_authorized"]
