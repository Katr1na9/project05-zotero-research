"""Test-only, authority-gated adapter for a CTI-report public projection."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from compiler.llm.m1_system_log_projection_adapter import (
    CONSUMER_CONTRACT_PATH,
    CONSUMER_CONTRACT_SHA256,
    EXTERNAL_SCHEMA_PATH,
    EXTERNAL_SCHEMA_SHA256,
    FRAMEWORK_PATH,
    FRAMEWORK_SHA256,
    KERNEL_SCHEMA_PATH,
    KERNEL_SCHEMA_SHA256,
    M0_PROJECTION_PATH,
    M0_PROJECTION_SHA256,
    M1EvidenceModalityAdapterError,
    PLANNER_IMPLEMENTATION_PATH,
    PLANNER_IMPLEMENTATION_SHA256,
    RED_ACCEPTANCE_PATH,
    RED_ACCEPTANCE_SHA256,
    SURFACE_ID,
    VALID_FIXTURE_IMPLEMENTATION_PATH,
    VALID_FIXTURE_IMPLEMENTATION_SHA256,
    _require_constant,
    _require_exact_keys,
    _require_exact_mapping,
    _require_safe_opaque,
    _require_sha,
    adapt_projection_with_spec,
    canonical_json_sha256,
    verify_projection_adapter_pins,
)


SOURCE_CLASS = "cti_report_public_projection"
ADAPTER_ID = "m1a_cti_report_projection_v0_1"
ADAPTER_VERSION = "0.1.0"
TEST_AUTHORITY_STATUS = (
    "activated_test_only_in_memory_cti_report_projection_authority"
)
PROJECTION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-cti-report-public-field-projection-"
    "v0.1-20260726.json"
)
PROJECTION_SHA256 = (
    "7ec2fc8a04bdb2bd8119edee6b97151ffa9a2faff68cf997b38dd059919b7afb"
)
PROJECTION_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-m1-cti-report-public-field-projection-"
    "v0.1-20260726"
)
CONTRACT_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-cti-report-projection-adapter-contract-"
    "v0.1-20260726.json"
)
CONTRACT_SHA256 = (
    "5461906b9ef9cc0b300840c9ff29780efa949c4637cea08fdd4683e11373c087"
)
SUPPORT_IMPLEMENTATION_PATH = (
    "src/compiler/llm/m1_system_log_projection_adapter.py"
)
SUPPORT_IMPLEMENTATION_SHA256 = (
    "b7cc4710a2db30eedb353b44671d0f4993a50442c3f5bd2afe06ed5ee33f0116"
)
ADAPTER_IMPLEMENTATION_PATH = (
    "src/compiler/llm/m1_cti_report_projection_adapter.py"
)

M1CTIReportProjectionAdapterError = M1EvidenceModalityAdapterError

CTI_REPORT_SPEC: dict[str, Any] = {
    "surface_id": SURFACE_ID,
    "source_class": SOURCE_CLASS,
    "adapter_id": ADAPTER_ID,
    "adapter_version": ADAPTER_VERSION,
    "authority_status": TEST_AUTHORITY_STATUS,
    "red_acceptance_path": RED_ACCEPTANCE_PATH,
    "red_acceptance_sha256": RED_ACCEPTANCE_SHA256,
    "framework_path": FRAMEWORK_PATH,
    "framework_sha256": FRAMEWORK_SHA256,
    "projection_path": PROJECTION_PATH,
    "projection_sha256": PROJECTION_SHA256,
    "projection_artifact_id": PROJECTION_ARTIFACT_ID,
    "contract_path": CONTRACT_PATH,
    "contract_sha256": CONTRACT_SHA256,
    "external_schema_path": EXTERNAL_SCHEMA_PATH,
    "external_schema_sha256": EXTERNAL_SCHEMA_SHA256,
    "kernel_schema_path": KERNEL_SCHEMA_PATH,
    "kernel_schema_sha256": KERNEL_SCHEMA_SHA256,
    "consumer_contract_path": CONSUMER_CONTRACT_PATH,
    "consumer_contract_sha256": CONSUMER_CONTRACT_SHA256,
    "m0_projection_path": M0_PROJECTION_PATH,
    "m0_projection_sha256": M0_PROJECTION_SHA256,
    "implementation_path": ADAPTER_IMPLEMENTATION_PATH,
    "support_implementation_path": SUPPORT_IMPLEMENTATION_PATH,
    "support_implementation_sha256": SUPPORT_IMPLEMENTATION_SHA256,
    "acceptance_artifact_key": "cti_report_adapter_contract",
    "acceptance_projection_key": "cti_report_public_field_projection",
    "extra_pins": (
        (SUPPORT_IMPLEMENTATION_PATH, SUPPORT_IMPLEMENTATION_SHA256),
    ),
}


def verify_adapter_pins(repo_root: Path) -> None:
    """Verify all CTI-report adapter pins and accepted RED boundaries."""

    verify_projection_adapter_pins(repo_root, CTI_REPORT_SPEC)


def adapt_cti_report_projection(
    descriptor: Mapping[str, Any],
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None = None,
    fixture_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate one declared CTI projection and return an M0 envelope."""

    return adapt_projection_with_spec(
        descriptor,
        repo_root=repo_root,
        authority=authority,
        fixture_registry=fixture_registry,
        spec=CTI_REPORT_SPEC,
        fixture_validator=_validate_cti_report_fixture,
    )


def _validate_cti_report_fixture(
    fixture: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> None:
    _require_exact_keys(
        fixture,
        {"descriptor", "report", "source_metadata"},
        "fixture",
    )
    descriptor = fixture["descriptor"]
    _require_exact_keys(
        descriptor,
        {
            "surface_id",
            "source_class",
            "opaque_record_reference",
            "projection_pin_declaration",
        },
        "fixture.descriptor",
    )
    _require_constant(
        descriptor["surface_id"],
        spec["surface_id"],
        "fixture.descriptor.surface_id",
    )
    _require_constant(
        descriptor["source_class"],
        spec["source_class"],
        "fixture.descriptor.source_class",
    )
    _require_safe_opaque(
        descriptor["opaque_record_reference"],
        "fixture.descriptor.opaque_record_reference",
    )
    _require_exact_mapping(
        descriptor["projection_pin_declaration"],
        {
            "artifact_id": spec["projection_artifact_id"],
            "version": "0.1",
            "sha256": spec["projection_sha256"],
        },
        "fixture.descriptor.projection_pin_declaration",
        "fixture_projection_pin",
    )

    report = fixture["report"]
    _require_exact_keys(
        report,
        {
            "report_id",
            "publisher_ref",
            "publication_window",
            "reported_marker",
            "public_objects",
            "public_techniques",
            "public_relations",
        },
        "fixture.report",
    )
    _require_safe_opaque(report["report_id"], "fixture.report.report_id")
    _require_safe_opaque(
        report["publisher_ref"],
        "fixture.report.publisher_ref",
    )
    _require_constant(
        report["reported_marker"],
        True,
        "fixture.report.reported_marker",
    )
    window = report["publication_window"]
    _require_exact_keys(
        window,
        {"start", "end"},
        "fixture.report.publication_window",
    )
    if (
        not isinstance(window["start"], str)
        or not isinstance(window["end"], str)
        or len(window["start"]) < 10
        or len(window["end"]) < 10
    ):
        raise M1EvidenceModalityAdapterError(
            "publication_window",
            "CTI publication window must contain public date declarations",
        )

    objects = report["public_objects"]
    techniques = report["public_techniques"]
    relations = report["public_relations"]
    if (
        not isinstance(objects, list)
        or not isinstance(techniques, list)
        or not isinstance(relations, list)
    ):
        raise M1EvidenceModalityAdapterError(
            "report_arrays",
            "CTI objects, techniques, and relations must be arrays",
        )
    object_keys: list[tuple[str, str]] = []
    object_refs: set[str] = set()
    for index, item in enumerate(objects):
        _require_exact_keys(
            item,
            {"object_ref", "object_type"},
            f"fixture.report.public_objects[{index}]",
        )
        _require_safe_opaque(
            item["object_ref"],
            f"fixture.report.public_objects[{index}].object_ref",
        )
        _require_safe_opaque(
            item["object_type"],
            f"fixture.report.public_objects[{index}].object_type",
        )
        object_keys.append((item["object_ref"], item["object_type"]))
        object_refs.add(item["object_ref"])
    if object_keys != sorted(object_keys) or len(object_refs) != len(objects):
        raise M1EvidenceModalityAdapterError(
            "cti_object_order",
            "CTI object declarations must be unique and canonically sorted",
        )
    technique_refs: list[str] = []
    for index, item in enumerate(techniques):
        _require_exact_keys(
            item,
            {"technique_ref"},
            f"fixture.report.public_techniques[{index}]",
        )
        _require_safe_opaque(
            item["technique_ref"],
            f"fixture.report.public_techniques[{index}].technique_ref",
        )
        technique_refs.append(item["technique_ref"])
    if technique_refs != sorted(technique_refs) or len(technique_refs) != len(
        set(technique_refs)
    ):
        raise M1EvidenceModalityAdapterError(
            "cti_technique_order",
            "CTI technique declarations must be unique and canonically sorted",
        )
    allowed_refs = object_refs | set(technique_refs)
    relation_keys: list[tuple[str, str, str]] = []
    for index, item in enumerate(relations):
        _require_exact_keys(
            item,
            {"subject_ref", "relation_type", "object_ref"},
            f"fixture.report.public_relations[{index}]",
        )
        for field in ("subject_ref", "relation_type", "object_ref"):
            _require_safe_opaque(
                item[field],
                f"fixture.report.public_relations[{index}].{field}",
            )
        if item["subject_ref"] not in allowed_refs or item["object_ref"] not in allowed_refs:
            raise M1EvidenceModalityAdapterError(
                "dangling_cti_relation",
                "CTI relation references an undeclared object or technique",
            )
        relation_keys.append(
            (item["subject_ref"], item["relation_type"], item["object_ref"])
        )
    if relation_keys != sorted(relation_keys) or len(relation_keys) != len(
        set(relation_keys)
    ):
        raise M1EvidenceModalityAdapterError(
            "cti_relation_order",
            "CTI relation declarations must be unique and canonically sorted",
        )

    metadata = fixture["source_metadata"]
    _require_exact_keys(
        metadata,
        {
            "source_family",
            "epistemic_modality",
            "modality_basis_code",
            "trusted_ingestion_metadata_sha256",
        },
        "fixture.source_metadata",
    )
    _require_constant(
        metadata["source_family"],
        "external_intel",
        "fixture.source_metadata.source_family",
    )
    if metadata["epistemic_modality"] in {"observed", "derived"}:
        raise M1EvidenceModalityAdapterError(
            "modality_laundering",
            "CTI reported material cannot be normalized to observed or derived",
        )
    expected = {
        "PUBLIC_CTI_REPORT_DECLARATION": "reported",
        "UNRESOLVED_REPORTING_BASIS": "unknown",
    }
    modality = expected.get(metadata["modality_basis_code"])
    if modality != metadata["epistemic_modality"]:
        raise M1EvidenceModalityAdapterError(
            "modality_mapping",
            "CTI modality and trusted basis do not match",
        )
    _require_sha(
        metadata["trusted_ingestion_metadata_sha256"],
        "fixture.source_metadata.trusted_ingestion_metadata_sha256",
    )
