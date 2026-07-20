import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPO_ROOT
    / "04-progress"
    / "m3star-final-blind-data-intake-v0.1-20260719"
    / "otrf-anchor-audit-curator-run-contract-v0.3.json"
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_otrf_anchor_audit_contract_is_frozen_and_script_bound():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["status"] == "frozen_before_record_anchor_audit"
    assert contract["frozen_case_scope"]["eligible_case_count"] == 7
    assert len(contract["frozen_case_scope"]["eligible_case_ids"]) == 7
    assert contract["frozen_case_scope"]["comparison_scenario_count"] == 2
    assert not contract["frozen_case_scope"][
        "comparison_scenarios_receive_case_credit"
    ]
    assert contract["frozen_anchor_policy"]["maximum_records_per_anchor"] == 5
    assert contract["frozen_anchor_policy"][
        "cross_scenario_uniqueness_required"
    ]
    assert contract["frozen_anchor_policy"][
        "explicit_tool_to_attack_mapping_linkage_required_for_automatic_case_bundle"
    ]
    for item in contract["pinned_scripts"]:
        assert sha256(REPO_ROOT / item["path"]) == item["sha256"]
    assert not contract["one_shot_evaluation_consumed"]
    assert not contract["one_shot_execution_authorized"]
    serialized = json.dumps(contract).casefold()
    for forbidden_name in (
        "goldensamladfsmailaccess",
        "log4shell",
        "lsass_campaign",
    ):
        assert forbidden_name not in serialized
