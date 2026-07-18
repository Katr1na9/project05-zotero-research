#!/usr/bin/env python3
"""Adapt a frozen external triplet profile into a source-grounded sidecar.

This is a clean-room, dependency-free boundary adapter.  It does not import,
install, execute, or copy CTINexus, OntoLogX, Matryoshka, TACTIC-KG, or any
model runtime.  External triples remain controller-ineligible until a public
source sentence containing both endpoint surfaces is mechanically recovered.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Iterator


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
DEFAULT_CATALOG = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "wp3"
    / "component-catalog-v0.1.json"
)
ADAPTER_ID = "project05-clean-room-component-graph-adapter"
ADAPTER_VERSION = "0.1.0"
SUPPORT_METHOD = "minimal_same_record_sentence_casefold_v0.1"

PROHIBITED_CONCLUSION_ENTITY_TYPES = frozenset(
    {
        "actor",
        "attack_campaign",
        "campaign",
        "intrusion_set",
        "threat_actor",
    }
)
PROHIBITED_CONCLUSION_RELATIONS = frozenset(
    {
        "acted_for",
        "associated_with_actor",
        "attributed_to",
        "attribution",
        "campaign_attribution",
        "conducted_by",
        "operated_by",
        "performed_by",
    }
)
PRIVATE_PATH_PARTS = frozenset({"gold", "private", "reference"})


def load_sibling(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


BUILDER = load_sibling(
    "project05_public_builder_for_wp3_component_adapter",
    "build_compiler_public_request.py",
)


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json_no_overwrite(path: Path, value: Any) -> None:
    output = Path(path)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite component output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def ensure_not_private_path(path: Path) -> Path:
    resolved = Path(path).resolve()
    lowered = {part.casefold() for part in resolved.parts}
    hits = sorted(lowered.intersection(PRIVATE_PATH_PARTS))
    if hits:
        raise ValueError(f"component adapter input path crosses private state: {hits}")
    return resolved


def normalize_surface(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value)).casefold()
    return " ".join(text.split())


def normalize_token(value: Any) -> str:
    normalized = normalize_surface(value)
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")


def iter_text_leaves(value: Any, path: str = "payload") -> Iterator[tuple[str, str]]:
    """Yield public string leaves with deterministic field paths."""

    if isinstance(value, str):
        if value.strip():
            yield path, value
        return
    if isinstance(value, dict):
        for key in sorted(value, key=lambda item: str(item)):
            yield from iter_text_leaves(value[key], f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_text_leaves(item, f"{path}[{index}]")


def sentence_candidates(text: str) -> list[str]:
    return [
        item.strip()
        for item in re.split(r"(?<=[.!?])\s+|[\r\n]+", text)
        if item.strip()
    ]


def recover_minimal_support(
    payload: Any,
    subject_surface: str,
    object_surface: str,
) -> tuple[str, str] | None:
    """Return the shortest same-record sentence containing both endpoints."""

    subject = normalize_surface(subject_surface)
    object_ = normalize_surface(object_surface)
    if not subject or not object_:
        return None
    matches: list[tuple[int, str, str]] = []
    for field_path, text in iter_text_leaves(payload):
        for sentence in sentence_candidates(text):
            normalized_sentence = normalize_surface(sentence)
            if subject in normalized_sentence and object_ in normalized_sentence:
                matches.append((len(sentence), field_path, sentence))
    if not matches:
        return None
    _, field_path, sentence = min(matches, key=lambda row: (row[0], row[1], row[2]))
    return field_path, sentence


def request_record_indexes(
    request: dict[str, Any],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[tuple[str, str], tuple[dict[str, Any], dict[str, Any]]],
]:
    artifacts: dict[str, dict[str, Any]] = {}
    records: dict[
        tuple[str, str], tuple[dict[str, Any], dict[str, Any]]
    ] = {}
    for artifact in request.get("visible_artifacts", []) or []:
        artifact_id = artifact.get("artifact_id")
        if not isinstance(artifact_id, str):
            continue
        artifacts[artifact_id] = artifact
        for record in artifact.get("records", []) or []:
            record_id = record.get("record_id")
            if isinstance(record_id, str):
                records[(artifact_id, record_id)] = (artifact, record)
    return artifacts, records


def catalog_component(
    catalog: dict[str, Any], component_id: Any
) -> dict[str, Any] | None:
    for component in catalog.get("components", []) or []:
        if component.get("component_id") == component_id:
            return component
    return None


def component_gate_reasons(
    bundle: dict[str, Any], catalog: dict[str, Any]
) -> list[str]:
    reasons: list[str] = []
    component = catalog_component(catalog, bundle.get("component_id"))
    if component is None:
        return ["component_not_catalogued"]
    if component.get("revision") != bundle.get("component_revision"):
        reasons.append("component_revision_mismatch")
    if component.get("license") != bundle.get("component_license"):
        reasons.append("component_license_mismatch")
    if component.get("output_profile") != bundle.get("output_profile"):
        reasons.append("component_output_profile_mismatch")
    if bundle.get("component_runtime_executed") is True and not component.get(
        "runtime_authorized", False
    ):
        reasons.append("component_runtime_not_authorized")
    if bundle.get("schema_version") != "0.1.0":
        reasons.append("component_bundle_schema_version_mismatch")
    return sorted(set(reasons))


def source_pointer(
    artifact: dict[str, Any],
    record: dict[str, Any],
    field_path: str,
) -> dict[str, Any]:
    pointer: dict[str, Any] = {
        "artifact_id": artifact["artifact_id"],
        "record_id": record["record_id"],
        "record_sha256": record["record_sha256"],
        "field_path": field_path,
    }
    for key in ("location", "line_start", "line_end"):
        if key in record:
            pointer[key] = copy.deepcopy(record[key])
    return pointer


def triplet_shape_reasons(triplet: Any) -> list[str]:
    if not isinstance(triplet, dict):
        return ["malformed_triplet"]
    required = {"triplet_id", "subject", "relation", "object", "source_pointer"}
    if required.difference(triplet):
        return ["malformed_triplet"]
    if not isinstance(triplet.get("triplet_id"), str) or not triplet["triplet_id"]:
        return ["malformed_triplet"]
    if not isinstance(triplet.get("relation"), str) or not triplet["relation"].strip():
        return ["malformed_triplet"]
    for endpoint in ("subject", "object"):
        entity = triplet.get(endpoint)
        if not isinstance(entity, dict):
            return ["malformed_triplet"]
        if not isinstance(entity.get("entity_type"), str) or not entity[
            "entity_type"
        ].strip():
            return ["malformed_triplet"]
        if not isinstance(entity.get("value"), str) or not entity["value"].strip():
            return ["malformed_triplet"]
    pointer = triplet.get("source_pointer")
    if not isinstance(pointer, dict) or not isinstance(
        pointer.get("artifact_id"), str
    ) or not isinstance(pointer.get("record_id"), str):
        return ["malformed_triplet"]
    return []


def triplet_signature(triplet: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalize_token(triplet["subject"]["entity_type"]),
        normalize_surface(triplet["subject"]["value"]),
        normalize_token(triplet["relation"]),
        normalize_token(triplet["object"]["entity_type"]),
        normalize_surface(triplet["object"]["value"]),
        triplet["source_pointer"]["artifact_id"],
        triplet["source_pointer"]["record_id"],
    )


def triplet_policy_reasons(triplet: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    endpoint_types = {
        normalize_token(triplet[endpoint]["entity_type"])
        for endpoint in ("subject", "object")
    }
    if endpoint_types.intersection(PROHIBITED_CONCLUSION_ENTITY_TYPES):
        reasons.append("unsupported_conclusion_entity")
    if normalize_token(triplet["relation"]) in PROHIBITED_CONCLUSION_RELATIONS:
        reasons.append("unsupported_conclusion_relation")
    return reasons


def build_empty_output(
    request_id: str,
    bundle: dict[str, Any],
    *,
    status: str = "abstained",
) -> dict[str, Any]:
    return {
        "schema_version": "0.1.0",
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "request_id": request_id,
        "component_id": str(bundle.get("component_id") or "missing"),
        "component_revision": str(bundle.get("component_revision") or "missing"),
        "component_license": str(bundle.get("component_license") or "missing"),
        "upstream_component_runtime_executed": bool(
            bundle.get("component_runtime_executed", False)
        ),
        "third_party_code_copied": False,
        "status": status,
        "nodes": [],
        "edges": [],
        "rejections": [],
        "abstention_reasons": [],
        "counts": {
            "input_triplets": len(bundle.get("triplets", []) or [])
            if isinstance(bundle.get("triplets", []), list)
            else 0,
            "accepted_edges": 0,
            "rejected_triplets": 0,
            "output_nodes": 0,
        },
    }


def reject_all_for_bundle_gate(
    output: dict[str, Any], bundle: dict[str, Any], reasons: Iterable[str]
) -> dict[str, Any]:
    reason_codes = sorted(set(reasons))
    triplets = bundle.get("triplets", []) or []
    if isinstance(triplets, list):
        for index, triplet in enumerate(triplets):
            triplet_id = (
                triplet.get("triplet_id", f"malformed-{index}")
                if isinstance(triplet, dict)
                else f"malformed-{index}"
            )
            output["rejections"].append(
                {"triplet_id": str(triplet_id), "reason_codes": reason_codes}
            )
    output["abstention_reasons"] = reason_codes
    output["counts"]["rejected_triplets"] = len(output["rejections"])
    BUILDER.assert_public_boundary(output)
    return output


def adapt_bundle(
    request: dict[str, Any],
    bundle: dict[str, Any],
    catalog: dict[str, Any],
) -> dict[str, Any]:
    """Fail closed from a public request and normalized triplets to a sidecar."""

    integrity_errors = BUILDER.validate_public_request_integrity(request)
    if integrity_errors:
        raise ValueError(
            "invalid public request: " + ",".join(sorted(integrity_errors))
        )
    BUILDER.assert_public_boundary(bundle)
    request_id = request["request_id"]
    output = build_empty_output(request_id, bundle)

    artifacts, records = request_record_indexes(request)
    cti_artifact_ids = {
        artifact_id
        for artifact_id, artifact in artifacts.items()
        if artifact.get("source_type") == "cti_text"
    }
    if not cti_artifact_ids:
        output["abstention_reasons"] = ["no_visible_cti_text_artifact"]
        BUILDER.assert_public_boundary(output)
        return output

    bundle_reasons = component_gate_reasons(bundle, catalog)
    if bundle.get("request_id") != request_id:
        bundle_reasons.append("request_id_mismatch")
    if bundle_reasons:
        return reject_all_for_bundle_gate(output, bundle, bundle_reasons)

    triplets = bundle.get("triplets")
    if not isinstance(triplets, list):
        return reject_all_for_bundle_gate(
            output, bundle, ["component_bundle_triplets_not_array"]
        )
    if not triplets:
        output["abstention_reasons"] = ["component_returned_no_triplets"]
        BUILDER.assert_public_boundary(output)
        return output

    shape_reasons = [triplet_shape_reasons(item) for item in triplets]
    signatures = [
        triplet_signature(item) if not reasons else None
        for item, reasons in zip(triplets, shape_reasons)
    ]
    signature_counts = Counter(item for item in signatures if item is not None)
    triplet_id_counts = Counter(
        item.get("triplet_id")
        for item, reasons in zip(triplets, shape_reasons)
        if not reasons
    )

    accepted: list[dict[str, Any]] = []
    rejections: list[dict[str, Any]] = []
    for index, (triplet, reasons, signature) in enumerate(
        zip(triplets, shape_reasons, signatures)
    ):
        triplet_id = (
            triplet.get("triplet_id", f"malformed-{index}")
            if isinstance(triplet, dict)
            else f"malformed-{index}"
        )
        item_reasons = list(reasons)
        if not item_reasons:
            item_reasons.extend(triplet_policy_reasons(triplet))
            if signature is not None and signature_counts[signature] > 1:
                item_reasons.append("duplicate_edge")
            if triplet_id_counts[triplet_id] > 1:
                item_reasons.append("duplicate_triplet_id")
            pointer = triplet["source_pointer"]
            key = (pointer["artifact_id"], pointer["record_id"])
            record_pair = records.get(key)
            if record_pair is None:
                item_reasons.append("unknown_source_pointer")
            elif pointer["artifact_id"] not in cti_artifact_ids:
                item_reasons.append("source_not_cti_text")
            else:
                artifact, record = record_pair
                support = recover_minimal_support(
                    record.get("payload"),
                    triplet["subject"]["value"],
                    triplet["object"]["value"],
                )
                if support is None:
                    item_reasons.append("source_surface_not_grounded")
                elif not item_reasons:
                    field_path, sentence = support
                    accepted.append(
                        {
                            "triplet": triplet,
                            "source_pointer": source_pointer(
                                artifact, record, field_path
                            ),
                            "support_sentence": sentence,
                        }
                    )
        if item_reasons:
            rejections.append(
                {
                    "triplet_id": str(triplet_id),
                    "reason_codes": sorted(set(item_reasons)),
                }
            )

    nodes: dict[tuple[str, str], dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    for row in accepted:
        triplet = row["triplet"]
        pointer = row["source_pointer"]
        endpoint_ids: dict[str, str] = {}
        for endpoint in ("subject", "object"):
            entity = triplet[endpoint]
            entity_type = normalize_token(entity["entity_type"])
            normalized_value = normalize_surface(entity["value"])
            key = (entity_type, normalized_value)
            node_id = BUILDER.derive_scoped_id(
                "SGNODE", request_id, entity_type, normalized_value
            )
            endpoint_ids[endpoint] = node_id
            if key not in nodes:
                nodes[key] = {
                    "node_id": node_id,
                    "request_id": request_id,
                    "entity_type": entity_type,
                    "normalized_value": normalized_value,
                    "surface_values": [],
                    "source_pointers": [],
                    "controller_eligible": False,
                }
            if entity["value"] not in nodes[key]["surface_values"]:
                nodes[key]["surface_values"].append(entity["value"])
            if pointer not in nodes[key]["source_pointers"]:
                nodes[key]["source_pointers"].append(copy.deepcopy(pointer))

        normalized_relation = normalize_token(triplet["relation"])
        edge_id = BUILDER.derive_scoped_id(
            "SGEDGE",
            request_id,
            endpoint_ids["subject"],
            normalized_relation,
            endpoint_ids["object"],
            pointer,
        )
        sentence = row["support_sentence"]
        edges.append(
            {
                "edge_id": edge_id,
                "request_id": request_id,
                "subject_node_id": endpoint_ids["subject"],
                "object_node_id": endpoint_ids["object"],
                "relation": triplet["relation"],
                "normalized_relation": normalized_relation,
                "source_pointer": copy.deepcopy(pointer),
                "support_sentence": sentence,
                "support_sentence_sha256": BUILDER.sha256_value(sentence),
                "support_method": SUPPORT_METHOD,
                "mechanical_eligibility": "passed",
                "controller_eligible": False,
            }
        )

    for node in nodes.values():
        node["surface_values"] = sorted(node["surface_values"])
        node["source_pointers"] = sorted(
            node["source_pointers"],
            key=lambda item: (
                item["artifact_id"],
                item["record_id"],
                item["field_path"],
            ),
        )
    output["nodes"] = sorted(nodes.values(), key=lambda item: item["node_id"])
    output["edges"] = sorted(edges, key=lambda item: item["edge_id"])
    output["rejections"] = sorted(
        rejections, key=lambda item: (item["triplet_id"], item["reason_codes"])
    )
    if edges and rejections:
        output["status"] = "completed_with_rejections"
    elif edges:
        output["status"] = "completed"
    else:
        output["status"] = "abstained"
        output["abstention_reasons"] = ["all_triplets_rejected"]
    output["counts"] = {
        "input_triplets": len(triplets),
        "accepted_edges": len(edges),
        "rejected_triplets": len(rejections),
        "output_nodes": len(nodes),
    }
    BUILDER.assert_public_boundary(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-request", type=Path, required=True)
    parser.add_argument("--public-root", type=Path, required=True)
    parser.add_argument("--component-bundle", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    request_path = BUILDER.ensure_public_path(args.public_request, args.public_root)
    bundle_path = ensure_not_private_path(args.component_bundle)
    catalog_path = ensure_not_private_path(args.catalog)
    request = load_json(request_path)
    bundle = load_json(bundle_path)
    catalog = load_json(catalog_path)
    output = adapt_bundle(request, bundle, catalog)
    write_json_no_overwrite(args.output, output)
    print(
        f"Wrote {output['status']} sidecar for {output['request_id']} "
        f"with {output['counts']['accepted_edges']} accepted edges"
    )


if __name__ == "__main__":
    main()
