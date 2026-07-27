"""Test-only, authority-gated adapter for a provenance-graph projection."""

from __future__ import annotations

from collections import Counter
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


SOURCE_CLASS = "provenance_graph_public_projection"
ADAPTER_ID = "m1a_provenance_graph_projection_v0_1"
ADAPTER_VERSION = "0.1.0"
TEST_AUTHORITY_STATUS = (
    "activated_test_only_in_memory_provenance_graph_projection_authority"
)
PROJECTION_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-provenance-graph-public-field-projection-"
    "v0.1-20260726.json"
)
PROJECTION_SHA256 = (
    "8a210a4eb2d9f48ac35c65f78fb29e2801c6a991b5b28798beaf5980f0c90ad5"
)
PROJECTION_ARTIFACT_ID = (
    "llm-editor-v0.8-l2-m1-provenance-graph-public-field-projection-"
    "v0.1-20260726"
)
CONTRACT_PATH = (
    "docs/llm-editor/"
    "llm-editor-v0.8-l2-m1-provenance-graph-projection-adapter-contract-"
    "v0.1-20260726.json"
)
CONTRACT_SHA256 = (
    "49f9b69d186bbd698ab37d3e375bd5adc2d30b4e93f92eb66782773644e7228f"
)
SUPPORT_IMPLEMENTATION_PATH = (
    "src/compiler/llm/m1_system_log_projection_adapter.py"
)
SUPPORT_IMPLEMENTATION_SHA256 = (
    "b7cc4710a2db30eedb353b44671d0f4993a50442c3f5bd2afe06ed5ee33f0116"
)
ADAPTER_IMPLEMENTATION_PATH = (
    "src/compiler/llm/m1_provenance_graph_projection_adapter.py"
)

M1ProvenanceGraphProjectionAdapterError = M1EvidenceModalityAdapterError

PROVENANCE_GRAPH_SPEC: dict[str, Any] = {
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
    "acceptance_artifact_key": "provenance_graph_adapter_contract",
    "acceptance_projection_key": "provenance_graph_public_field_projection",
    "extra_pins": (
        (SUPPORT_IMPLEMENTATION_PATH, SUPPORT_IMPLEMENTATION_SHA256),
    ),
}


def verify_adapter_pins(repo_root: Path) -> None:
    """Verify all provenance-graph adapter pins and accepted RED boundaries."""

    verify_projection_adapter_pins(repo_root, PROVENANCE_GRAPH_SPEC)


def adapt_provenance_graph_projection(
    descriptor: Mapping[str, Any],
    *,
    repo_root: Path,
    authority: Mapping[str, Any] | None = None,
    fixture_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Validate one declared provenance projection and return an M0 envelope."""

    return adapt_projection_with_spec(
        descriptor,
        repo_root=repo_root,
        authority=authority,
        fixture_registry=fixture_registry,
        spec=PROVENANCE_GRAPH_SPEC,
        fixture_validator=_validate_provenance_graph_fixture,
    )


def _validate_provenance_graph_fixture(
    fixture: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> None:
    _require_exact_keys(
        fixture,
        {"descriptor", "graph", "source_metadata"},
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

    graph = fixture["graph"]
    _require_exact_keys(
        graph,
        {"graph_id", "nodes", "edges", "time_window", "summary"},
        "fixture.graph",
    )
    _require_safe_opaque(graph["graph_id"], "fixture.graph.graph_id")
    nodes = graph["nodes"]
    edges = graph["edges"]
    if not isinstance(nodes, list) or not nodes:
        raise M1EvidenceModalityAdapterError(
            "graph_nodes",
            "provenance projection requires declared public nodes",
        )
    if not isinstance(edges, list):
        raise M1EvidenceModalityAdapterError(
            "graph_edges",
            "provenance edges must be an array",
        )
    node_ids: list[str] = []
    for index, node in enumerate(nodes):
        _require_exact_keys(
            node,
            {"node_id", "node_type"},
            f"fixture.graph.nodes[{index}]",
        )
        _require_safe_opaque(
            node["node_id"],
            f"fixture.graph.nodes[{index}].node_id",
        )
        _require_safe_opaque(
            node["node_type"],
            f"fixture.graph.nodes[{index}].node_type",
        )
        node_ids.append(node["node_id"])
    if node_ids != sorted(node_ids) or len(node_ids) != len(set(node_ids)):
        raise M1EvidenceModalityAdapterError(
            "graph_node_order",
            "node_id values must be unique and canonically sorted",
        )
    edge_ids: list[str] = []
    relation_types: list[str] = []
    for index, edge in enumerate(edges):
        _require_exact_keys(
            edge,
            {"edge_id", "from_node_id", "to_node_id", "relationship_type"},
            f"fixture.graph.edges[{index}]",
        )
        for field in (
            "edge_id",
            "from_node_id",
            "to_node_id",
            "relationship_type",
        ):
            _require_safe_opaque(
                edge[field],
                f"fixture.graph.edges[{index}].{field}",
            )
        if (
            edge["from_node_id"] not in node_ids
            or edge["to_node_id"] not in node_ids
        ):
            raise M1EvidenceModalityAdapterError(
                "dangling_edge",
                "edge references an undeclared node",
            )
        edge_ids.append(edge["edge_id"])
        relation_types.append(edge["relationship_type"])
    if edge_ids != sorted(edge_ids) or len(edge_ids) != len(set(edge_ids)):
        raise M1EvidenceModalityAdapterError(
            "graph_edge_order",
            "edge_id values must be unique and canonically sorted",
        )

    window = graph["time_window"]
    _require_exact_keys(
        window,
        {"start", "end", "precision"},
        "fixture.graph.time_window",
    )
    if (
        not isinstance(window["start"], (str, type(None)))
        or not isinstance(window["end"], (str, type(None)))
        or window["precision"] not in {"exact", "bounded", "coarse", "unknown"}
    ):
        raise M1EvidenceModalityAdapterError(
            "graph_time_window",
            "time-window declaration is malformed",
        )
    if (
        (window["start"] is None or window["end"] is None)
        and window["precision"] != "unknown"
    ):
        raise M1EvidenceModalityAdapterError(
            "graph_time_window",
            "null time bounds require unknown precision",
        )

    summary = graph["summary"]
    _require_exact_keys(
        summary,
        {"node_count", "edge_count", "relationship_counts"},
        "fixture.graph.summary",
    )
    _require_constant(
        summary["node_count"],
        len(nodes),
        "fixture.graph.summary.node_count",
    )
    _require_constant(
        summary["edge_count"],
        len(edges),
        "fixture.graph.summary.edge_count",
    )
    counts = summary["relationship_counts"]
    if not isinstance(counts, list):
        raise M1EvidenceModalityAdapterError(
            "relationship_counts",
            "relationship counts must be an array",
        )
    declared_counts: dict[str, int] = {}
    for index, item in enumerate(counts):
        _require_exact_keys(
            item,
            {"relationship_type", "count"},
            f"fixture.graph.summary.relationship_counts[{index}]",
        )
        _require_safe_opaque(
            item["relationship_type"],
            f"fixture.graph.summary.relationship_counts[{index}].relationship_type",
        )
        if (
            not isinstance(item["count"], int)
            or isinstance(item["count"], bool)
            or item["count"] < 0
            or item["relationship_type"] in declared_counts
        ):
            raise M1EvidenceModalityAdapterError(
                "relationship_counts",
                "relationship counts are malformed or duplicated",
            )
        declared_counts[item["relationship_type"]] = item["count"]
    if list(declared_counts) != sorted(declared_counts):
        raise M1EvidenceModalityAdapterError(
            "relationship_count_order",
            "relationship counts must be canonically sorted",
        )
    if declared_counts != dict(Counter(relation_types)):
        raise M1EvidenceModalityAdapterError(
            "relationship_count_mismatch",
            "relationship summary does not match declared edges",
        )

    metadata = fixture["source_metadata"]
    _require_exact_keys(
        metadata,
        {
            "source_family",
            "epistemic_modality",
            "materialization_class",
            "modality_basis_code",
            "trusted_ingestion_metadata_sha256",
        },
        "fixture.source_metadata",
    )
    _require_constant(
        metadata["source_family"],
        "system_provenance",
        "fixture.source_metadata.source_family",
    )
    expected = {
        (
            "DIRECT_SOURCE_ATTESTED_GRAPH",
            "ALL_NODES_AND_EDGES_DIRECTLY_ATTESTED",
        ): "observed",
        (
            "TRANSFORMED_OR_INFERRED_GRAPH",
            "ONE_OR_MORE_ELEMENTS_TRANSFORMED_OR_INFERRED",
        ): "derived",
        (
            "MIXED_OR_UNRESOLVED_GRAPH",
            "MIXED_UNSPLIT_OR_UNRESOLVED_BASIS",
        ): "unknown",
    }
    modality = expected.get(
        (
            metadata["materialization_class"],
            metadata["modality_basis_code"],
        )
    )
    if modality != metadata["epistemic_modality"]:
        raise M1EvidenceModalityAdapterError(
            "modality_mapping",
            "provenance modality and trusted basis do not match",
        )
    _require_sha(
        metadata["trusted_ingestion_metadata_sha256"],
        "fixture.source_metadata.trusted_ingestion_metadata_sha256",
    )
