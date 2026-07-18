#!/usr/bin/env python3
"""Retrieve and audit the bounded WP4 CTI text sources.

This program is deliberately narrower than a corpus downloader.  It accepts only
the three user-approved, fixed-revision catalog entries, verifies repository
license blobs, checks each CISA validation document at its original government
URL, normalizes only the eligible records, and removes any record matching the
hash-only protected-test exclusion lock.  Raw upstream corpora are not retained.

Running this program does not authorize or execute a component, model, embedding,
training job, formal inference, C07-C12 evaluation, or M3 controller integration.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import re
import shutil
import sys
import tempfile
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
REPO_ROOT = EXPERIMENT_ROOT.parent
DEFAULT_CATALOG = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "wp4"
    / "cti-text-source-catalog-v0.1.json"
)
DEFAULT_EXCLUSION_LOCK = (
    REPO_ROOT
    / ".worktrees"
    / "llm-apt-phase1"
    / "09-experiments"
    / "llm_finetuning_v0.3"
    / "generated"
    / "frozen"
    / "test-exclusion-lock.json"
)
DEFAULT_OUTPUT = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "wp4"
    / "generated"
    / "retrieval-v0.1"
)
USER_AGENT = "Project05-WP4-bounded-source-retrieval/0.1"
EXPECTED_SOURCE_IDS = frozenset(
    {
        "ctid_blueprints_intrusion_sample",
        "mitre_attack_software_procedure_text",
        "tram_cisa_first_party_advisory_subset",
    }
)
EXPECTED_BLOCKED_FAMILIES = frozenset(
    {
        "darpa_tc_e3",
        "darpa_tc_e5",
        "darpa_optc",
        "otrf_apt29",
        "witfoo_precinct6",
    }
)
PRIVATE_FIELD_NAMES = frozenset({"gold", "oracle", "private"})
FORBIDDEN_TEXT_PATTERNS = (
    ("apt29", re.compile(r"\bAPT[ -]?29\b", re.IGNORECASE)),
    ("otrf", re.compile(r"\bOTRF\b", re.IGNORECASE)),
    ("project05_case_id", re.compile(r"\bC(?:07|08|09|10|11|12)\b", re.IGNORECASE)),
    ("darpa_tc_e3_e5", re.compile(r"\bDARPA\s+(?:TC\s+)?E(?:3|5)\b", re.IGNORECASE)),
    ("darpa_optc", re.compile(r"\b(?:DARPA\s+)?OpTC\b", re.IGNORECASE)),
    ("witfoo", re.compile(r"\bWitFoo\b", re.IGNORECASE)),
    ("precinct6", re.compile(r"\bPrecinct\s*6\b", re.IGNORECASE)),
)
MAX_GITHUB_BYTES = 150 * 1024 * 1024
MAX_ORIGIN_BYTES = 8 * 1024 * 1024


def load_sibling(name: str, filename: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SOURCE_GATE = load_sibling(
    "project05_wp4_source_gate_for_retrieval",
    "validate_compiler_cti_source_gate.py",
)


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def git_blob_sha1(value: bytes) -> str:
    header = f"blob {len(value)}\0".encode("ascii")
    return hashlib.sha1(header + value).hexdigest()


def normalized_text(value: Any) -> str:
    if isinstance(value, (dict, list)):
        raw = canonical_json(value).decode("utf-8")
    else:
        raw = str(value)
    return " ".join(unicodedata.normalize("NFKC", raw).casefold().split())


def normalized_text_hash(value: Any) -> str:
    return sha256_bytes(normalized_text(value).encode("utf-8"))


def hashed_character_ngrams(value: str, n: int) -> set[str]:
    text = normalized_text(value)
    if not text:
        return set()
    grams = {text} if len(text) < n else {
        text[index : index + n] for index in range(len(text) - n + 1)
    }
    return {sha256_bytes(gram.encode("utf-8")) for gram in grams}


def iter_text_leaves(value: Any, path: str = "payload") -> Iterator[tuple[str, str]]:
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


def forbidden_field_paths(value: Any, path: str = "payload") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).casefold()
            child_path = f"{path}.{key}"
            if key_text in PRIVATE_FIELD_NAMES:
                hits.append(child_path)
            hits.extend(forbidden_field_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(forbidden_field_paths(child, f"{path}[{index}]"))
    return sorted(set(hits))


def fetch_url(
    url: str,
    *,
    max_bytes: int,
    timeout: int = 90,
) -> tuple[bytes, dict[str, Any]]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,text/plain,text/html;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "identity",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read(max_bytes + 1)
        if len(payload) > max_bytes:
            raise ValueError(f"retrieval exceeds byte cap for {url}")
        return payload, {
            "requested_url": url,
            "final_url": response.geturl(),
            "http_status": int(getattr(response, "status", 200)),
            "content_type": response.headers.get_content_type(),
            "bytes": len(payload),
            "sha256": sha256_bytes(payload),
        }


def raw_github_url(repository: str, revision: str, path: str) -> str:
    parsed = urllib.parse.urlparse(repository)
    if parsed.netloc.casefold() != "github.com":
        raise ValueError(f"unsupported repository host: {repository}")
    repo_path = parsed.path.strip("/")
    encoded_path = "/".join(urllib.parse.quote(part) for part in path.split("/"))
    return f"https://raw.githubusercontent.com/{repo_path}/{revision}/{encoded_path}"


def raw_license_url(evidence_url: str) -> str:
    parsed = urllib.parse.urlparse(evidence_url)
    parts = parsed.path.strip("/").split("/")
    if parsed.netloc.casefold() != "github.com" or len(parts) < 5 or parts[2] != "blob":
        raise ValueError(f"unsupported license evidence URL: {evidence_url}")
    repository = f"https://github.com/{parts[0]}/{parts[1]}"
    revision = parts[3]
    path = "/".join(parts[4:])
    return raw_github_url(repository, revision, path)


def verified_catalog(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    report = SOURCE_GATE.validate_catalog(catalog, repo_root=REPO_ROOT)
    if report["status"] != "ready_for_bounded_retrieval_and_payload_scan":
        raise ValueError(f"source catalog is not retrieval-ready: {report['status']}")
    if report["authorization"]["bounded_retrieval"] is not True:
        raise ValueError("bounded retrieval is not authorized")
    for key in (
        "component_runtime",
        "model_or_embedding",
        "training",
        "formal_inference",
        "C07_C12_execution",
        "controller_integration",
    ):
        if report["authorization"][key] is not False:
            raise ValueError(f"out-of-scope authorization present: {key}")
    activated = [
        item
        for item in catalog.get("candidates", [])
        if item.get("user_decision") in {"approve", "conditional_approve"}
        and item.get("retrieval_authorized") is True
    ]
    source_ids = {item.get("source_id") for item in activated}
    if source_ids != EXPECTED_SOURCE_IDS:
        raise ValueError(f"unexpected activated source set: {sorted(source_ids)}")
    return activated


def verify_license(
    source: dict[str, Any], fetcher: Callable[..., tuple[bytes, dict[str, Any]]]
) -> dict[str, Any]:
    license_info = source.get("license", {})
    evidence_url = license_info.get("evidence_url")
    expected_blob = license_info.get("evidence_blob_sha")
    if evidence_url is None:
        # CISA documents are verified individually and the repository code license
        # is not used as authority for copied report content.
        return {
            "source_id": source["source_id"],
            "status": "per_document_origin_required",
        }
    payload, retrieval = fetcher(
        raw_license_url(evidence_url), max_bytes=2 * 1024 * 1024
    )
    actual_blob = git_blob_sha1(payload)
    if actual_blob != expected_blob:
        raise ValueError(
            f"license blob mismatch for {source['source_id']}: {actual_blob}"
        )
    return {
        "source_id": source["source_id"],
        "status": "verified",
        "license_id": license_info.get("id"),
        "expected_git_blob_sha1": expected_blob,
        "actual_git_blob_sha1": actual_blob,
        "retrieval": retrieval,
        "required_attribution": license_info.get("required_attribution"),
    }


def stable_record_id(prefix: str, *parts: Any) -> str:
    digest = sha256_bytes(canonical_json(list(parts)))[:24]
    return f"{prefix}-{digest}"


def normalize_blueprints(
    source: dict[str, Any], raw: bytes, retrieval: dict[str, Any]
) -> list[dict[str, Any]]:
    value = json.loads(raw.decode("utf-8-sig"))
    field_hits = forbidden_field_paths(value)
    if field_hits:
        raise ValueError(f"CTID Blueprints contains forbidden fields: {field_hits}")
    path = source["eligible_paths"][0]
    return [
        {
            "source_family_id": source["publisher_family"],
            "source_id": source["source_id"],
            "split_role": source["split_role"],
            "record_id": stable_record_id("CTID", source["revision"], path),
            "document_unit_id": stable_record_id(
                "DOC", source["publisher_family"], source["revision"], path
            ),
            "source_revision": source["revision"],
            "source_path": path,
            "source_url": retrieval["requested_url"],
            "raw_document_sha256": retrieval["sha256"],
            "payload": value,
            "controller_eligible": False,
        }
    ]


def citation_labels(description: str) -> list[str]:
    return sorted(
        {
            match.strip()
            for match in re.findall(r"\[Citation:\s*([^\]]+)\]", description)
            if match.strip()
        }
    )


def normalize_mitre_attack(
    source: dict[str, Any], raw: bytes, retrieval: dict[str, Any]
) -> list[dict[str, Any]]:
    value = json.loads(raw.decode("utf-8-sig"))
    objects = value.get("objects") if isinstance(value, dict) else None
    if not isinstance(objects, list):
        raise ValueError("MITRE ATT&CK STIX bundle has no objects array")
    by_id = {
        item["id"]: item
        for item in objects
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    allowed_software = {
        object_id: item
        for object_id, item in by_id.items()
        if item.get("type") in {"malware", "tool"}
        and item.get("revoked") is not True
        and item.get("x_mitre_deprecated") is not True
    }
    output: list[dict[str, Any]] = []
    for relationship in objects:
        if not isinstance(relationship, dict):
            continue
        if relationship.get("type") != "relationship":
            continue
        if relationship.get("relationship_type") != "uses":
            continue
        if relationship.get("revoked") is True or relationship.get(
            "x_mitre_deprecated"
        ) is True:
            continue
        software = allowed_software.get(relationship.get("source_ref"))
        if software is None:
            continue
        target = by_id.get(relationship.get("target_ref"), {})
        if target.get("type") != "attack-pattern":
            continue
        if target.get("revoked") is True or target.get("x_mitre_deprecated") is True:
            continue
        description = relationship.get("description")
        if not isinstance(description, str) or not description.strip():
            continue
        software_name = software.get("name")
        if not isinstance(software_name, str) or not software_name.strip():
            continue
        screening_text = " ".join(
            [software_name, description, *[str(x) for x in software.get("aliases", [])]]
        )
        if any(pattern.search(screening_text) for _, pattern in FORBIDDEN_TEXT_PATTERNS):
            continue
        payload = {
            "software_name": software_name,
            "software_type": software["type"],
            "procedure_description": description,
            "citation_labels": citation_labels(description),
        }
        if forbidden_field_paths(payload):
            raise ValueError("MITRE normalizer created a forbidden field")
        relationship_id = str(relationship.get("id") or "missing")
        output.append(
            {
                "source_family_id": source["publisher_family"],
                "source_id": source["source_id"],
                "split_role": source["split_role"],
                "record_id": stable_record_id(
                    "MITRE", source["revision"], relationship_id, description
                ),
                "document_unit_id": stable_record_id(
                    "DOC",
                    source["publisher_family"],
                    source["revision"],
                    "enterprise-attack.json",
                ),
                "source_revision": source["revision"],
                "source_path": source["eligible_paths"][0],
                "source_url": retrieval["requested_url"],
                "raw_document_sha256": retrieval["sha256"],
                "upstream_record_id": relationship_id,
                "payload": payload,
                "controller_eligible": False,
            }
        )
    return sorted(output, key=lambda item: item["record_id"])


def parse_tram_signal(value: Any) -> tuple[str, str, str]:
    if not isinstance(value, dict) or not isinstance(value.get("signal"), str):
        raise ValueError("TRAM mjson has no string signal")
    signal = value["signal"].replace("\r\n", "\n")
    title_match = re.search(r"(?mi)^title:\s*(.+?)\s*$", signal)
    url_match = re.search(r"(?mi)^url:\s*(https?://\S+)\s*$", signal)
    if title_match is None or url_match is None:
        raise ValueError("TRAM signal lacks title or original URL")
    title = title_match.group(1).strip()
    original_url = url_match.group(1).strip()
    body = re.sub(r"(?mi)^title:\s*.+?\s*$", "", signal, count=1)
    body = re.sub(r"(?mi)^url:\s*https?://\S+\s*$", "", body, count=1).strip()
    if not body:
        raise ValueError("TRAM signal has no advisory body")
    return title, original_url, body


def government_host(url: str) -> bool:
    hostname = (urllib.parse.urlparse(url).hostname or "").casefold().rstrip(".")
    return hostname == "cisa.gov" or hostname.endswith(".cisa.gov")


def normalize_cisa_documents(
    source: dict[str, Any],
    fetcher: Callable[..., tuple[bytes, dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    admitted: list[dict[str, Any]] = []
    origin_audit: list[dict[str, Any]] = []
    raw_manifest: list[dict[str, Any]] = []
    prefix = source["eligible_path_prefix"]
    for title_path in source["eligible_path_titles"]:
        path = prefix + title_path
        raw_url = raw_github_url(source["repository"], source["revision"], path)
        raw, retrieval = fetcher(raw_url, max_bytes=MAX_GITHUB_BYTES)
        raw_manifest.append({"source_path": path, "retrieval": retrieval})
        row: dict[str, Any] = {
            "source_path": path,
            "raw_sha256": retrieval["sha256"],
            "status": "rejected_fail_closed",
            "reason_codes": [],
        }
        try:
            value = json.loads(raw.decode("utf-8-sig"))
            title, original_url, body = parse_tram_signal(value)
            row["document_title"] = title
            row["original_url"] = original_url
            if not government_host(original_url):
                row["reason_codes"].append("original_url_not_cisa_government_host")
            origin_bytes, origin_retrieval = fetcher(
                original_url, max_bytes=MAX_ORIGIN_BYTES
            )
            row["origin_retrieval"] = origin_retrieval
            if not government_host(origin_retrieval["final_url"]):
                row["reason_codes"].append("redirect_left_cisa_government_host")
            if origin_retrieval["http_status"] != 200:
                row["reason_codes"].append("original_url_not_http_200")
            if not re.search(
                r"\b(?:CISA|Cybersecurity and Infrastructure Security Agency)\b",
                body,
                flags=re.IGNORECASE,
            ):
                row["reason_codes"].append("government_authorship_marker_missing")
            if forbidden_field_paths({"advisory_text": body}):
                row["reason_codes"].append("forbidden_field_created")
            # The admitted payload is plain text only.  HTML, images, scripts,
            # labels, and other third-party embedded media are never copied.
            row["third_party_embedded_media_copied"] = False
            row["origin_probe_sha256"] = sha256_bytes(origin_bytes)
            if not row["reason_codes"]:
                row["status"] = "verified_first_party_government_origin"
                admitted.append(
                    {
                        "source_family_id": source["publisher_family"],
                        "source_id": source["source_id"],
                        "split_role": source["split_role"],
                        "record_id": stable_record_id(
                            "CISA", source["revision"], path, retrieval["sha256"]
                        ),
                        "document_unit_id": stable_record_id(
                            "DOC", source["publisher_family"], original_url
                        ),
                        "source_revision": source["revision"],
                        "source_path": path,
                        "source_url": original_url,
                        "resolved_source_url": origin_retrieval["final_url"],
                        "raw_document_sha256": retrieval["sha256"],
                        "payload": {
                            "title": title,
                            "advisory_text": body,
                        },
                        "controller_eligible": False,
                    }
                )
        except Exception as error:  # Per-document fail closed is intentional.
            row["reason_codes"].append(
                "origin_or_format_verification_error:" + type(error).__name__
            )
            row["error"] = str(error)
        row["reason_codes"] = sorted(set(row["reason_codes"]))
        origin_audit.append(row)
    return admitted, origin_audit, raw_manifest


def validate_exclusion_lock(lock: dict[str, Any]) -> None:
    if lock.get("contains_raw_test_payload") is not False:
        raise ValueError("exclusion lock contains raw test payload")
    if lock.get("contains_raw_private_gold") is not False:
        raise ValueError("exclusion lock contains raw private gold")
    if set(lock.get("blocked_family_ids", [])) != EXPECTED_BLOCKED_FAMILIES:
        raise ValueError("exclusion lock blocked-family set mismatch")
    if int(lock.get("character_ngram_n", 0)) != 5:
        raise ValueError("exclusion lock n-gram size mismatch")
    if float(lock.get("near_duplicate_threshold", 0)) != 0.85:
        raise ValueError("exclusion lock threshold mismatch")
    if int(lock.get("minimum_protected_text_chars", 0)) != 16:
        raise ValueError("exclusion lock minimum text length mismatch")
    if not lock.get("normalized_text_hashes") or not lock.get("ngram_signatures"):
        raise ValueError("exclusion lock is empty")


def audit_records(
    records: Iterable[dict[str, Any]], lock: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    validate_exclusion_lock(lock)
    n = int(lock["character_ngram_n"])
    threshold = float(lock["near_duplicate_threshold"])
    minimum_chars = int(lock["minimum_protected_text_chars"])
    exact_hashes = set(lock["normalized_text_hashes"])
    signatures_by_count: dict[int, list[set[str]]] = defaultdict(list)
    for row in lock["ngram_signatures"]:
        signatures_by_count[int(row["ngram_count"])].append(set(row["ngram_hashes"]))
    admitted: list[dict[str, Any]] = []
    matches: list[dict[str, Any]] = []
    maximum_jaccard = 0.0
    literal_counts: dict[str, int] = defaultdict(int)
    for record in records:
        record_matches: list[dict[str, Any]] = []
        field_hits = forbidden_field_paths(record.get("payload"))
        for path in field_hits:
            record_matches.append(
                {"match_type": "forbidden_field", "field_path": path}
            )
        for field_path, value in iter_text_leaves(record.get("payload")):
            normalized = normalized_text(value)
            if len(normalized) < minimum_chars:
                continue
            for name, pattern in FORBIDDEN_TEXT_PATTERNS:
                if pattern.search(value):
                    literal_counts[name] += 1
                    record_matches.append(
                        {
                            "match_type": "forbidden_literal",
                            "literal_code": name,
                            "field_path": field_path,
                            "candidate_value_hash": normalized_text_hash(value),
                        }
                    )
            value_hash = normalized_text_hash(value)
            if value_hash in exact_hashes:
                maximum_jaccard = 1.0
                record_matches.append(
                    {
                        "match_type": "normalized_exact_match",
                        "field_path": field_path,
                        "candidate_value_hash": value_hash,
                        "jaccard": 1.0,
                    }
                )
                continue
            candidate = hashed_character_ngrams(value, n)
            candidate_count = len(candidate)
            if not candidate_count:
                continue
            lower = math.ceil(candidate_count * threshold)
            upper = math.floor(candidate_count / threshold)
            best = 0.0
            for protected_count in range(lower, upper + 1):
                for protected in signatures_by_count.get(protected_count, []):
                    intersection = len(candidate.intersection(protected))
                    union = candidate_count + protected_count - intersection
                    score = 1.0 if union == 0 else intersection / union
                    if score > best:
                        best = score
            maximum_jaccard = max(maximum_jaccard, best)
            if best >= threshold:
                record_matches.append(
                    {
                        "match_type": "near_duplicate_5gram",
                        "field_path": field_path,
                        "candidate_value_hash": value_hash,
                        "jaccard": round(best, 12),
                    }
                )
        if record_matches:
            for match in record_matches:
                matches.append(
                    {
                        "source_family_id": record["source_family_id"],
                        "record_id": record["record_id"],
                        **match,
                    }
                )
        else:
            admitted.append(record)
    matches.sort(
        key=lambda row: (
            row["source_family_id"],
            row["record_id"],
            row["match_type"],
            row.get("field_path", ""),
        )
    )
    return admitted, {
        "schema_version": "project05-mainline-compiler-payload-exclusion-audit-v0.1",
        "status": "passed_with_record_exclusions" if matches else "passed_clean",
        "threshold": threshold,
        "candidate_record_count": len(admitted) + len(
            {(row["source_family_id"], row["record_id"]) for row in matches}
        ),
        "admitted_record_count": len(admitted),
        "excluded_record_count": len(
            {(row["source_family_id"], row["record_id"]) for row in matches}
        ),
        "normalized_exact_match_count": sum(
            row["match_type"] == "normalized_exact_match" for row in matches
        ),
        "near_duplicate_match_count": sum(
            row["match_type"] == "near_duplicate_5gram" for row in matches
        ),
        "forbidden_literal_match_count": sum(
            row["match_type"] == "forbidden_literal" for row in matches
        ),
        "forbidden_field_match_count": sum(
            row["match_type"] == "forbidden_field" for row in matches
        ),
        "literal_match_counts": dict(sorted(literal_counts.items())),
        "maximum_jaccard": round(maximum_jaccard, 12),
        "matches": matches,
        "contains_raw_protected_payload": False,
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_jsonl(path: Path, values: Iterable[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for value in values:
            handle.write(
                json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n"
            )


def run_retrieval(
    catalog: dict[str, Any],
    exclusion_lock: dict[str, Any],
    *,
    fetcher: Callable[..., tuple[bytes, dict[str, Any]]] = fetch_url,
) -> dict[str, Any]:
    sources = verified_catalog(catalog)
    by_id = {item["source_id"]: item for item in sources}
    license_audit = [verify_license(item, fetcher) for item in sources]
    raw_manifest: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []

    blueprints = by_id["ctid_blueprints_intrusion_sample"]
    blueprints_path = blueprints["eligible_paths"][0]
    blueprints_url = raw_github_url(
        blueprints["repository"], blueprints["revision"], blueprints_path
    )
    raw, retrieval = fetcher(blueprints_url, max_bytes=MAX_GITHUB_BYTES)
    raw_manifest.append({"source_path": blueprints_path, "retrieval": retrieval})
    records.extend(normalize_blueprints(blueprints, raw, retrieval))

    mitre = by_id["mitre_attack_software_procedure_text"]
    mitre_path = mitre["eligible_paths"][0]
    mitre_url = raw_github_url(mitre["repository"], mitre["revision"], mitre_path)
    raw, retrieval = fetcher(mitre_url, max_bytes=MAX_GITHUB_BYTES)
    raw_manifest.append({"source_path": mitre_path, "retrieval": retrieval})
    records.extend(normalize_mitre_attack(mitre, raw, retrieval))

    cisa = by_id["tram_cisa_first_party_advisory_subset"]
    cisa_records, origin_audit, cisa_raw_manifest = normalize_cisa_documents(
        cisa, fetcher
    )
    raw_manifest.extend(cisa_raw_manifest)
    records.extend(cisa_records)

    admitted, exclusion_audit = audit_records(records, exclusion_lock)
    candidate_counts: dict[str, int] = defaultdict(int)
    admitted_counts: dict[str, int] = defaultdict(int)
    document_units: dict[str, set[str]] = defaultdict(set)
    for record in records:
        candidate_counts[record["source_family_id"]] += 1
    for record in admitted:
        admitted_counts[record["source_family_id"]] += 1
        document_units[record["source_family_id"]].add(record["document_unit_id"])
    verified_cisa = sum(
        row["status"] == "verified_first_party_government_origin"
        for row in origin_audit
    )
    blockers: list[str] = []
    for family in ("ctid_blueprints", "mitre_attack", "cisa_first_party_advisories"):
        if admitted_counts.get(family, 0) == 0:
            blockers.append(f"no_admitted_records:{family}")
    if verified_cisa == 0:
        blockers.append("no_verified_cisa_document")
    status = "passed" if not blockers else "failed_closed"
    return {
        "manifest": {
            "schema_version": "project05-mainline-compiler-cti-retrieval-manifest-v0.1",
            "status": status,
            "catalog_id": catalog.get("catalog_id"),
            "catalog_version": catalog.get("version"),
            "raw_upstream_corpora_retained": False,
            "retrieved_files": raw_manifest,
            "license_audit": license_audit,
            "candidate_record_counts": dict(sorted(candidate_counts.items())),
            "admitted_record_counts": dict(sorted(admitted_counts.items())),
            "admitted_document_unit_counts": {
                key: len(value) for key, value in sorted(document_units.items())
            },
            "verified_cisa_document_count": verified_cisa,
            "rejected_cisa_document_count": len(origin_audit) - verified_cisa,
            "blockers": blockers,
            "authorization": {
                "component_runtime": False,
                "model_or_embedding": False,
                "training": False,
                "formal_inference": False,
                "C07_C12_execution": False,
                "controller_integration": False,
            },
        },
        "records": admitted,
        "origin_audit": origin_audit,
        "exclusion_audit": exclusion_audit,
    }


def write_retrieval_output(
    output: Path,
    result: dict[str, Any],
    exclusion_lock_path: Path,
    exclusion_lock: dict[str, Any],
) -> None:
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite retrieval output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(
        tempfile.mkdtemp(prefix=output.name + ".tmp-", dir=str(output.parent))
    )
    try:
        write_json(temp_root / "retrieval-manifest.json", result["manifest"])
        write_json(temp_root / "source-origin-audit.json", result["origin_audit"])
        write_json(temp_root / "payload-exclusion-audit.json", result["exclusion_audit"])
        write_jsonl(temp_root / "admitted-records.jsonl", result["records"])
        lock_target = temp_root / "protected-signature-lock-v0.1.json"
        shutil.copyfile(exclusion_lock_path, lock_target)
        write_json(
            temp_root / "protected-signature-lock-provenance.json",
            {
                "source_path": str(Path(exclusion_lock_path).resolve()),
                "source_file_sha256": sha256_file(exclusion_lock_path),
                "copied_file_sha256": sha256_file(lock_target),
                "internal_lock_sha256": exclusion_lock.get("lock_sha256"),
                "contains_raw_test_payload": False,
                "contains_raw_private_gold": False,
            },
        )
        temp_root.replace(output)
    except Exception:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--exclusion-lock", type=Path, default=DEFAULT_EXCLUSION_LOCK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    exclusion_lock = json.loads(args.exclusion_lock.read_text(encoding="utf-8"))
    result = run_retrieval(catalog, exclusion_lock)
    write_retrieval_output(args.output, result, args.exclusion_lock, exclusion_lock)
    rendered = json.dumps(
        result["manifest"], ensure_ascii=False, indent=2, sort_keys=True
    ) + "\n"
    # Windows PowerShell may expose a GBK text stream that cannot encode the
    # required MITRE copyright line.  Emit UTF-8 bytes without changing data.
    sys.stdout.buffer.write(rendered.encode("utf-8"))
    if result["manifest"]["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
