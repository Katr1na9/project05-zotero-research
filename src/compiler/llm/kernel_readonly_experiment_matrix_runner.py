"""Fail-closed GREEN runner for the Kernel read-only A/B/C matrix.

The runner verifies the exact Owner acceptance, intake pin table, and stable
RED review inputs before it evaluates one deterministic local fixture. Arm B
uses only the committed durable-replay load/validate path. This module never
calls a write executor, replays an activation, or writes an output fixture.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from src.compiler.llm import claim_id_durable_replay_attacher as durable
from src.compiler.llm import claim_id_mainline_handoff as handoff_module


INTAKE_PATH = (
    "docs/kernel/kernel-v0.8-claim-id-certificate-track-handoff-intake-"
    "and-experiment-plan-v0.1-20260725.json"
)
INTAKE_SHA256 = "5da2ceedb63ccdb3ca8d409d3dfd23aec0a274da4c01ee3747276d42f8c232cf"
DESIGN_PATH = (
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-readonly-experiment-"
    "matrix-design-v0.1-20260725.json"
)
DESIGN_SHA256 = "78b31c84c812316840f8cafe9286f35eb99894104e9f7793ed3815bf0fd879ca"
OWNER_ACCEPTANCE_PATH = (
    "docs/kernel/kernel-v0.8-readonly-experiment-matrix-red-owner-"
    "acceptance-v0.1-20260725.json"
)
OWNER_ACCEPTANCE_SHA256 = (
    "a95a07cb302c8231cbe66336422af0998e15d869c687a42ba6cbac9a06d3263a"
)
RED_REVIEW_PACKET_PATH = (
    "docs/llm-editor/llm-editor-v0.8-l2-kernel-owner-readonly-experiment-"
    "matrix-review-packet-v0.1-20260725.json"
)
RED_REVIEW_PACKET_SHA256 = (
    "71a91e468c71a75a913f09e302eea97b7fd879319d4d1ebb41a8035aa4e68caa"
)
RED_REVIEW_PACKET_CANONICAL_SELF_SHA256 = (
    "eade44fb9319998da34ff65cb76fbe58e9f97f43b044a07e77dc64b511107203"
)
RED_RUNNER_SHA256 = (
    "9758a35338e52066cc634f168941920d37f230a6ce2c24fb7469240546b668b8"
)
RED_TESTS_SHA256 = (
    "9849ea6e3c1d4b4a0c9db8b55031f565f10b7ee699b6ce1cc2155b5613e7f3d6"
)
RED_RESULT_SHA256 = (
    "a4b72b48995c7f2186895a2fdaf197375beac616f6eeb0b7cc2ddc0aa3545cc3"
)
RED_RECEIPT_SHA256 = (
    "f70fa6b0a744eb2c15620c682202e031e3c7e584ef92de82e118a5a6ac96be90"
)
REVIEWED_TIP = "14999363ce1ff1cadadf1a54d995503ae582c5ae"
MATRIX_STATUS = "PASS_READ_ONLY"

_PROTECTED_PIN_NAMES = frozenset(
    {
        "intake_store",
        "store_receipt",
        "e_case_record",
        "e_case_receipt",
        "certificate_record",
        "certificate_receipt",
        "certified_stop_record",
        "certified_stop_receipt",
        "control_loop_reference",
        "durable_replay_receipt",
        "controller_import_receipt",
        "planner_import_receipt",
    }
)


class KernelReadonlyExperimentMatrixError(ValueError):
    """Raised when any accepted read-only matrix boundary fails closed."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def verify_intake_and_pins(repo_root: Path) -> dict[str, dict[str, str]]:
    """Rehash the intake and all verified pins without mutating state."""

    root = repo_root.resolve()
    intake_bytes = _read_bytes(root / INTAKE_PATH, "handoff_intake")
    _require_sha256(intake_bytes, INTAKE_SHA256, "handoff_intake_pin")
    intake = _decode_json_bytes(intake_bytes, "handoff_intake")
    verification = _require_mapping(
        intake.get("verification"), "verification", "intake_shape"
    )
    verified_pins = _require_mapping(
        verification.get("verified_pins"),
        "verification.verified_pins",
        "intake_shape",
    )
    observed = {
        "handoff_intake": {"path": INTAKE_PATH, "sha256": INTAKE_SHA256}
    }
    for name, raw_item in verified_pins.items():
        if not isinstance(name, str) or not name:
            raise KernelReadonlyExperimentMatrixError(
                "intake_shape", "verified pin name must be non-empty text"
            )
        item = _require_mapping(
            raw_item, f"verification.verified_pins.{name}", "intake_shape"
        )
        if set(item) != {"path", "content_sha256", "verified_at_tip"}:
            raise KernelReadonlyExperimentMatrixError(
                "intake_shape", f"verified pin {name} fields are not canonical"
            )
        path = item.get("path")
        expected_sha256 = item.get("content_sha256")
        if not isinstance(path, str) or not path:
            raise KernelReadonlyExperimentMatrixError(
                "intake_shape", f"verified pin {name} path is invalid"
            )
        pinned_bytes = _read_bytes(root / path, f"verified_pin.{name}")
        _require_sha256(pinned_bytes, expected_sha256, f"verified_pin.{name}")
        observed[name] = {"path": path, "sha256": expected_sha256}
    return observed


def verify_owner_acceptance(repo_root: Path) -> dict[str, Any]:
    """Verify the exact Owner transition record and immutable RED inputs."""

    root = repo_root.resolve()
    acceptance_bytes = _read_bytes(
        root / OWNER_ACCEPTANCE_PATH, "owner_acceptance"
    )
    _require_sha256(
        acceptance_bytes, OWNER_ACCEPTANCE_SHA256, "owner_acceptance_pin"
    )
    acceptance = _decode_json_bytes(acceptance_bytes, "owner_acceptance")
    for field, expected in (
        ("artifact_type", "kernel_m3_readonly_experiment_matrix_red_owner_acceptance"),
        ("owner", "Kernel/M3*"),
        ("decision", "accept"),
        (
            "status",
            "red_accepted_green_readonly_implementation_and_local_run_authorized_only",
        ),
        ("authority_base_commit", REVIEWED_TIP),
        ("reviewed_tip", REVIEWED_TIP),
    ):
        _require_constant(
            acceptance.get(field), expected, f"owner_acceptance.{field}"
        )

    review_pin = _require_mapping(
        acceptance.get("pinned_review_packet"),
        "owner_acceptance.pinned_review_packet",
        "owner_acceptance_shape",
    )
    if dict(review_pin) != {
        "path": RED_REVIEW_PACKET_PATH,
        "content_sha256": RED_REVIEW_PACKET_SHA256,
        "canonical_self_hash": RED_REVIEW_PACKET_CANONICAL_SELF_SHA256,
    }:
        raise KernelReadonlyExperimentMatrixError(
            "owner_acceptance_pin",
            "Owner acceptance does not pin the accepted RED review packet",
        )
    review_bytes = _read_bytes(
        root / RED_REVIEW_PACKET_PATH, "red_review_packet"
    )
    _require_sha256(
        review_bytes, RED_REVIEW_PACKET_SHA256, "red_review_packet_pin"
    )
    review = _decode_json_bytes(review_bytes, "red_review_packet")
    reported_self = review["packet_identity"][
        "self_reported_canonical_sha256"
    ]
    review["packet_identity"]["self_reported_canonical_sha256"] = None
    if (
        reported_self != RED_REVIEW_PACKET_CANONICAL_SELF_SHA256
        or _canonical_json_sha256(review)
        != RED_REVIEW_PACKET_CANONICAL_SELF_SHA256
    ):
        raise KernelReadonlyExperimentMatrixError(
            "red_review_packet_pin",
            "accepted RED review packet canonical self-hash changed",
        )

    red_pins = _require_mapping(
        acceptance.get("pinned_red_artifacts"),
        "owner_acceptance.pinned_red_artifacts",
        "owner_acceptance_shape",
    )
    expected_red_pins = {
        "design": (DESIGN_PATH, DESIGN_SHA256),
        "runner_red_skeleton": (
            "src/compiler/llm/kernel_readonly_experiment_matrix_runner.py",
            RED_RUNNER_SHA256,
        ),
        "tests": (
            "tests/compiler_contract/test_kernel_readonly_experiment_matrix.py",
            RED_TESTS_SHA256,
        ),
        "matrix_result_red_not_run": (
            "docs/llm-editor/fixtures/kernel-readonly-experiment-matrix/"
            "project05-depth2-public-v0.1/matrix-result.json",
            RED_RESULT_SHA256,
        ),
        "sanitized_receipt_revised": (
            "docs/llm-editor/fixtures/kernel-readonly-experiment-matrix/"
            "project05-depth2-public-v0.1/sanitized-receipt.json",
            RED_RECEIPT_SHA256,
        ),
    }
    if set(red_pins) != set(expected_red_pins):
        raise KernelReadonlyExperimentMatrixError(
            "owner_acceptance_pin",
            "Owner acceptance RED artifact names are not canonical",
        )
    for name, (path, expected_sha256) in expected_red_pins.items():
        item = _require_mapping(
            red_pins.get(name),
            f"owner_acceptance.pinned_red_artifacts.{name}",
            "owner_acceptance_shape",
        )
        if dict(item) != {
            "path": path,
            "content_sha256": expected_sha256,
        }:
            raise KernelReadonlyExperimentMatrixError(
                "owner_acceptance_pin",
                f"Owner acceptance predecessor pin {name} changed",
            )
    _require_sha256(
        _read_bytes(root / DESIGN_PATH, "accepted_design"),
        DESIGN_SHA256,
        "accepted_design_pin",
    )

    answers = _require_mapping(
        acceptance.get("answers_to_owner_questions"),
        "owner_acceptance.answers_to_owner_questions",
        "owner_acceptance_shape",
    )
    if dict(answers) != {
        "arm_ab_comparison_sufficient_for_v0_1": True,
        "arm_b_entry_path_accepted": (
            "load_claim_id_durable_replay_attachment + "
            "validate_durable_replay_attachment"
        ),
        "arm_c_three_cases_complete_for_v0_1": True,
        "protected_byte_snapshot_set_sufficient": True,
        "green_may_proceed_without_new_activation": True,
    }:
        raise KernelReadonlyExperimentMatrixError(
            "owner_acceptance_semantics",
            "Owner answers do not authorize the GREEN boundary",
        )
    authorized = _require_mapping(
        acceptance.get("authorized_now"),
        "owner_acceptance.authorized_now",
        "owner_acceptance_shape",
    )
    if not authorized or any(value is not True for value in authorized.values()):
        raise KernelReadonlyExperimentMatrixError(
            "owner_acceptance_semantics",
            "every GREEN authorization flag must be true",
        )
    not_authorized = _require_mapping(
        acceptance.get("not_authorized"),
        "owner_acceptance.not_authorized",
        "owner_acceptance_shape",
    )
    if not not_authorized or any(
        value is not False for value in not_authorized.values()
    ):
        raise KernelReadonlyExperimentMatrixError(
            "owner_acceptance_semantics",
            "every explicit non-authorization must remain false",
        )
    _require_constant(
        acceptance.get("hard_stop_after_green_local_run_until_rereview"),
        True,
        "owner_acceptance.hard_stop",
    )
    return acceptance


def snapshot_protected_state(repo_root: Path) -> dict[str, str]:
    """Hash protected records, receipts, and historical activation files."""

    root = repo_root.resolve()
    pins = verify_intake_and_pins(root)
    protected_paths = {
        item["path"]
        for name, item in pins.items()
        if name in _PROTECTED_PIN_NAMES
    }
    llm_docs = root / "docs/llm-editor"
    if llm_docs.exists():
        for path in llm_docs.rglob("*.json"):
            relative = path.relative_to(root).as_posix()
            if "activation" in path.name.lower():
                protected_paths.add(relative)
    return {
        path: _sha256(_read_bytes(root / path, f"protected_state.{path}"))
        for path in sorted(protected_paths)
    }


def run_matrix(repo_root: Path) -> dict[str, Any]:
    """Evaluate the accepted local A/B/C matrix without write-side effects."""

    root = repo_root.resolve()
    verify_owner_acceptance(root)
    pins = verify_intake_and_pins(root)
    if handoff_module.PRODUCTION_REGISTRATION_ENABLED is not False:
        raise KernelReadonlyExperimentMatrixError(
            "registration_switch",
            "PRODUCTION_REGISTRATION_ENABLED must remain False",
        )
    protected_before = snapshot_protected_state(root)

    planner_adapter = _load_script(
        root / durable.PLANNER_ADAPTER_PATH,
        "kernel_readonly_matrix_planner_adapter",
    )
    run_mvp = _load_script(
        root / durable.CONTROLLER_ENTRYPOINT_PATH,
        "kernel_readonly_matrix_run_mvp",
    )
    config, state, actions = _planner_fixture()
    arm_a_view = planner_adapter.build_runtime_view(config, state, actions)

    capability_receipt_path = root / durable.CAPABILITY_RECEIPT_PATH
    capability_receipt_sha256 = _sha256(
        _read_bytes(capability_receipt_path, "durable_receipt")
    )
    attachment = durable.load_claim_id_durable_replay_attachment(
        root / durable.REFERENCE_PATH,
        capability_receipt_path,
        capability_receipt_sha256,
        repo_root=root,
    )
    provenance = durable.validate_durable_replay_attachment(attachment)
    arm_b_view = planner_adapter.build_runtime_view(
        config,
        state,
        actions,
        claim_id_durable_replay_attachment=attachment,
    )
    arm_b_core = {key: arm_b_view[key] for key in arm_a_view}
    if arm_a_view != arm_b_core:
        raise KernelReadonlyExperimentMatrixError(
            "algorithm_changed",
            "Arm B changed the planner core runtime view",
        )
    if arm_b_view.get("claim_id_mainline_reference") != provenance:
        raise KernelReadonlyExperimentMatrixError(
            "durable_replay_projection",
            "Arm B sidecar does not match the validated attachment",
        )

    arm_a_action = _select_action(run_mvp, arm_a_view)
    arm_b_action = _select_action(run_mvp, arm_b_view)
    if arm_a_action != arm_b_action:
        raise KernelReadonlyExperimentMatrixError(
            "algorithm_changed", "Arm A and Arm B selected different actions"
        )

    core_bytes = _canonical_json_bytes(arm_a_view)
    if b"clm_" in core_bytes:
        raise KernelReadonlyExperimentMatrixError(
            "claim_id_scoring_leak",
            "opaque Claim-ID entered the planner core runtime view",
        )
    case_local_visible = list(state["visible_claim_ids"])
    if any(
        isinstance(value, str) and value.startswith("clm_")
        for value in case_local_visible
    ):
        raise KernelReadonlyExperimentMatrixError(
            "claim_id_case_leak",
            "opaque Claim-ID entered case-local visible evidence",
        )

    arm_c = _evaluate_mixlayer_cases(root)
    protected_after = snapshot_protected_state(root)
    if protected_before != protected_after:
        raise KernelReadonlyExperimentMatrixError(
            "write_side_effect",
            "protected store/E_case/certificate/STOP or activation bytes changed",
        )
    protected_sha256 = _canonical_json_sha256(protected_before)
    core_sha256 = _sha256(core_bytes)

    return {
        "matrix_status": MATRIX_STATUS,
        "authority_base_commit": REVIEWED_TIP,
        "owner_acceptance": {
            "path": OWNER_ACCEPTANCE_PATH,
            "sha256": OWNER_ACCEPTANCE_SHA256,
            "decision": "accept",
        },
        "pin_reverify": "OK",
        "pin_count_including_intake": len(pins),
        "arms": [
            {
                "arm_id": "A_baseline_no_claim_id_provenance",
                "status": "PASS",
                "claim_id_provenance_attached": False,
                "action_id": arm_a_action,
                "algorithm_changed": False,
                "case_local_visible_evidence": case_local_visible,
                "scoring_claim_id_hits": [],
                "core_runtime_view_sha256": core_sha256,
            },
            {
                "arm_id": "B_claim_id_provenance_attached_read_only",
                "status": "PASS",
                "claim_id_provenance_attached": True,
                "action_id": arm_b_action,
                "algorithm_changed": False,
                "case_local_visible_evidence": case_local_visible,
                "scoring_claim_id_hits": [],
                "core_runtime_view_sha256": core_sha256,
                "provenance_sha256": durable.canonical_json_sha256(provenance),
                "reference_sha256": durable.REFERENCE_SHA256,
                "capability_receipt_sha256": capability_receipt_sha256,
                "per_attach_ledger_consumed": False,
            },
            arm_c,
        ],
        "production_registration_enabled": False,
        "algorithm_changed": False,
        "checker_decision": None,
        "evidence_sufficiency": None,
        "write_side_effects": "none",
        "protected_path_count": len(protected_before),
        "protected_before_sha256": protected_sha256,
        "protected_after_sha256": protected_sha256,
        "protected_bytes_identical": True,
        "activation_ledger_replayed": False,
        "certified_stop_executed": False,
        "l2_authorized": False,
        "part_b_elevated": False,
        "m2_fit_authorized": False,
        "four_family_ingestion_authorized": False,
    }


def _planner_fixture() -> tuple[
    dict[str, Any], dict[str, Any], list[dict[str, Any]]
]:
    """Return the deterministic E1-only public fixture accepted for v0.1."""

    case_id = "project05-depth2-public-v0.1"
    config = {
        "case_id": case_id,
        "budget_total": 3,
        "cti_nodes": [
            {
                "node_id": "N1",
                "stage": "execution",
                "critical": True,
                "required_claim_ids": ["E1"],
            }
        ],
        "channel_reliability": {"host": 0.8},
    }
    state = {
        "case_id": case_id,
        "step_index": 0,
        "matched_cti_node_ids": [],
        "unmatched_cti_node_ids": ["N1"],
        "matched_cti_edge_ids": [],
        "unmatched_cti_edge_ids": [],
        "coverage": {
            "cti_node_coverage": 0.0,
            "cti_edge_coverage": 0.0,
            "critical_gap_count": 1,
        },
        "budget": {
            "budget_total": 3,
            "budget_used": 0,
            "budget_remaining": 3,
        },
        "actions_taken": [],
        "action_feedback": [],
        "remaining_action_ids": ["A-low", "A-high"],
        "visible_claim_ids": ["E1"],
    }

    def action(action_id: str, gain: float) -> dict[str, Any]:
        return {
            "action_id": action_id,
            "case_id": case_id,
            "action_type": "query",
            "acquisition_channel": "host",
            "target": {"target_type": "node", "target_value": "N1"},
            "cost": 1.0,
            "intended_cti_node_ids": ["N1"],
            "expected_evidence_types": ["host"],
            "expected_stages": ["execution"],
            "expected_effects": {"expected_granularity_gain": gain},
            "recoverable_claim_ids": ["E1"],
        }

    return config, state, [action("A-low", 0.1), action("A-high", 0.2)]


def _select_action(run_mvp: ModuleType, view: Mapping[str, Any]) -> str:
    selected = run_mvp.select_action(
        "project05_m1",
        view["config"],
        [],
        view["actions"],
        view["state"],
        {"E1"},
        set(),
        [],
        0,
    )
    if not isinstance(selected, dict):
        raise KernelReadonlyExperimentMatrixError(
            "planner_selection", "frozen planner returned no action"
        )
    action_id = selected.get("action_id")
    if not isinstance(action_id, str) or not action_id:
        raise KernelReadonlyExperimentMatrixError(
            "planner_selection", "frozen planner action id is invalid"
        )
    return action_id


def _evaluate_mixlayer_cases(repo_root: Path) -> dict[str, Any]:
    cases = (
        (
            "store_as_e_case",
            "docs/llm-editor/fixtures/kernel-claim-ir-intake-store/"
            "project05-depth2-public-v0.1/store-record.json",
            {"is_kernel_store_record": True, "is_e_case": False},
            "kernel_claim_ir_intake_store",
            "e_case",
        ),
        (
            "certificate_as_certified_stop",
            "docs/llm-editor/fixtures/certificate/"
            "project05-depth2-public-v0.1/certificate-record.json",
            {"is_certificate": True, "is_e_case": False},
            "certificate",
            "certified_stop",
        ),
        (
            "certified_stop_as_run_mvp_stop",
            "docs/llm-editor/fixtures/certified-stop/"
            "project05-depth2-public-v0.1/certified-stop-record.json",
            {
                "is_certified_stop": True,
                "is_ordinary_run_mvp_stop": False,
            },
            "certified_stop",
            "run_mvp_ordinary_stop",
        ),
    )
    rejections = []
    for case_id, path, flags, source_class, requested_class in cases:
        source_bytes = _read_bytes(repo_root / path, f"arm_c.{case_id}")
        source = _decode_json_bytes(source_bytes, f"arm_c.{case_id}")
        for field, expected in flags.items():
            _require_constant(
                source.get(field), expected, f"arm_c.{case_id}.{field}"
            )
        rejections.append(
            {
                "case_id": case_id,
                "source_record_class": source_class,
                "requested_record_class": requested_class,
                "source_sha256": _sha256(source_bytes),
                "decision": "FAIL_CLOSED_DENY",
                "write_path_invoked": False,
            }
        )
    return {
        "arm_id": "C_negative_mixlayer_rejected",
        "status": "PASS",
        "rejections": rejections,
        "ordinary_run_mvp_stop_emitted": False,
        "certificate_issued": False,
        "certified_stop_issued": False,
    }


def _load_script(path: Path, module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise KernelReadonlyExperimentMatrixError(
            "runtime_module", f"could not load {path}"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _canonical_json_sha256(value: Any) -> str:
    return _sha256(_canonical_json_bytes(value))


def _read_bytes(path: Path, field: str) -> bytes:
    try:
        if not path.is_file():
            raise KernelReadonlyExperimentMatrixError(
                "missing_approved_artifact", f"{field} is missing"
            )
        return path.read_bytes()
    except OSError as exc:
        raise KernelReadonlyExperimentMatrixError(
            "artifact_read", f"{field} could not be read"
        ) from exc


def _decode_json_bytes(value: bytes, field: str) -> dict[str, Any]:
    try:
        decoded = value.decode("utf-8")
        result = json.loads(decoded, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError, _DuplicateJSONKey) as exc:
        raise KernelReadonlyExperimentMatrixError(
            "artifact_json", f"{field} is not canonical JSON"
        ) from exc
    if not isinstance(result, dict):
        raise KernelReadonlyExperimentMatrixError(
            "artifact_json", f"{field} must be a JSON object"
        )
    return result


def _require_mapping(value: Any, field: str, code: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise KernelReadonlyExperimentMatrixError(
            code, f"{field} must be an object"
        )
    return value


def _require_constant(value: Any, expected: Any, field: str) -> None:
    if value != expected or type(value) is not type(expected):
        raise KernelReadonlyExperimentMatrixError(
            "accepted_semantics", f"{field} must remain {expected!r}"
        )


def _require_sha256(value: bytes, expected_sha256: Any, code: str) -> None:
    if not isinstance(expected_sha256, str) or len(expected_sha256) != 64:
        raise KernelReadonlyExperimentMatrixError(
            "pin_shape", f"{code} has an invalid expected SHA-256"
        )
    observed = _sha256(value)
    if observed != expected_sha256:
        raise KernelReadonlyExperimentMatrixError(
            code,
            f"SHA-256 mismatch: expected {expected_sha256}, observed {observed}",
        )


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class _DuplicateJSONKey(ValueError):
    pass


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateJSONKey(key)
        value[key] = item
    return value
