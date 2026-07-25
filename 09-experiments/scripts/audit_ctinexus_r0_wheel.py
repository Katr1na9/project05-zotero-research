#!/usr/bin/env python3
"""Static, non-executing audit of the fixed CTINexus wheel for Gate R0."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from email.parser import BytesParser
from email.policy import default
from pathlib import Path, PurePosixPath
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
EXPERIMENT_ROOT = SCRIPT_DIR.parent
DEFAULT_WHEEL = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "wp5"
    / "r0"
    / "downloads"
    / "ctinexus-0.2.1-py3-none-any.whl"
)
DEFAULT_AUTHORITY = (
    EXPERIMENT_ROOT
    / "llm_evidence_compiler_mainline"
    / "wp5"
    / "r0"
    / "r0-authority.json"
)
EXPECTED_ENTRY_POINT = "ctinexus = ctinexus.app:main"
NATIVE_SUFFIXES = (".dll", ".dylib", ".pyd", ".so")
DATA_PREFIXES = ("ctinexus/data/annotation/", "ctinexus/data/demo/")
APT_LIKE_FILENAME = re.compile(
    r"(?:^|[-_/])(?:apt|actor|campaign|lazarus|kimsuky|typhoon)(?:[-_/]|$)",
    re.IGNORECASE,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json_no_overwrite(path: Path, value: Any) -> None:
    output = Path(path)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite R0 wheel audit: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def safe_archive_path(name: str) -> bool:
    path = PurePosixPath(name)
    return not path.is_absolute() and ".." not in path.parts and "" not in path.parts


def audit_wheel(wheel: Path, authority: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    wheel = Path(wheel)
    expected = authority.get("component", {})
    if not wheel.is_file():
        return {
            "schema_version": "project05-ctinexus-r0-wheel-audit-v0.1",
            "status": "failed_closed",
            "errors": ["wheel_missing"],
            "warnings": [],
        }
    actual_sha = sha256_file(wheel)
    if wheel.name != expected.get("wheel_filename"):
        errors.append("wheel_filename_mismatch")
    if actual_sha != expected.get("wheel_sha256"):
        errors.append("wheel_sha256_mismatch")

    with zipfile.ZipFile(wheel) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        unsafe = sorted(name for name in names if not safe_archive_path(name))
        if unsafe:
            errors.append("unsafe_archive_paths")
        encrypted = sorted(info.filename for info in infos if info.flag_bits & 0x1)
        if encrypted:
            errors.append("encrypted_wheel_entries")
        native = sorted(name for name in names if name.casefold().endswith(NATIVE_SUFFIXES))
        metadata_names = [name for name in names if name.endswith(".dist-info/METADATA")]
        entrypoint_names = [name for name in names if name.endswith(".dist-info/entry_points.txt")]
        if len(metadata_names) != 1:
            errors.append("metadata_entry_count_not_one")
            metadata = None
        else:
            metadata = BytesParser(policy=default).parsebytes(
                archive.read(metadata_names[0])
            )
        if len(entrypoint_names) != 1:
            errors.append("entrypoint_entry_count_not_one")
            entrypoint_text = ""
        else:
            entrypoint_text = archive.read(entrypoint_names[0]).decode("utf-8")
        init_source = (
            archive.read("ctinexus/__init__.py").decode("utf-8")
            if "ctinexus/__init__.py" in names
            else ""
        )

    if native:
        warnings.append("wheel_contains_native_binaries")
    if metadata is None:
        package_name = package_version = requires_python = license_text = None
        dependencies: list[str] = []
    else:
        package_name = metadata.get("Name")
        package_version = metadata.get("Version")
        requires_python = metadata.get("Requires-Python")
        license_text = metadata.get("License") or ""
        dependencies = sorted(metadata.get_all("Requires-Dist") or [])
        if package_name != "ctinexus":
            errors.append("metadata_package_name_mismatch")
        if package_version != expected.get("package_version"):
            errors.append("metadata_package_version_mismatch")
        if "MIT License" not in license_text:
            errors.append("metadata_license_not_mit")
    if EXPECTED_ENTRY_POINT not in entrypoint_text:
        errors.append("console_entrypoint_mismatch")
    if "_load_environment()" not in init_source or "load_dotenv" not in init_source:
        errors.append("expected_import_environment_side_effect_not_observed")

    annotation = sorted(name for name in names if name.startswith(DATA_PREFIXES[0]))
    demo = sorted(name for name in names if name.startswith(DATA_PREFIXES[1]))
    apt_like = sorted(name for name in annotation + demo if APT_LIKE_FILENAME.search(name))
    if annotation or demo:
        warnings.append("bundled_third_party_examples_present_and_quarantined")
    dependency_names = {
        re.split(r"[ ;(<>=\[]", item, maxsplit=1)[0].casefold()
        for item in dependencies
    }
    for required in ("litellm", "python-dotenv", "gradio"):
        if required not in dependency_names:
            errors.append(f"expected_dependency_missing:{required}")

    py_ok = (3, 10) <= sys.version_info[:2] < (3, 14)
    if not py_ok:
        errors.append("python_version_outside_package_range")
    status = "ready_for_minimal_no_model_import_smoke" if not errors else "failed_closed"
    return {
        "schema_version": "project05-ctinexus-r0-wheel-audit-v0.1",
        "status": status,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "wheel": {
            "filename": wheel.name,
            "bytes": wheel.stat().st_size,
            "sha256": actual_sha,
            "entry_count": len(names),
            "unsafe_path_count": len(unsafe),
            "encrypted_entry_count": len(encrypted),
            "native_binary_count": len(native),
        },
        "package": {
            "name": package_name,
            "version": package_version,
            "requires_python": requires_python,
            "license_verified_as_mit": bool(license_text and "MIT License" in license_text),
            "console_entrypoint": EXPECTED_ENTRY_POINT,
            "declared_dependencies": dependencies,
            "declared_dependency_count": len(dependencies),
            "full_dependency_closure_installed": False,
        },
        "import_risk": {
            "loads_dotenv_at_import": True,
            "required_clean_working_directory": True,
            "required_provider_environment_sanitization": True,
            "network_or_model_call_authorized": False,
        },
        "bundled_data_quarantine": {
            "annotation_file_count": len(annotation),
            "demo_file_count": len(demo),
            "apt_or_actor_like_filename_count": len(apt_like),
            "bundled_data_authorized_as_project05_input": False,
            "bundled_data_access_authorized_during_smoke": False,
        },
        "minimal_smoke_install": {
            "wheel_install_with_no_deps": True,
            "only_additional_import_dependency": "python-dotenv==1.2.1",
            "dependency_closure_complete": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, default=DEFAULT_WHEEL)
    parser.add_argument("--authority", type=Path, default=DEFAULT_AUTHORITY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_wheel(args.wheel, load_json(args.authority))
    if args.output:
        write_json_no_overwrite(args.output, report)
    print(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    if report["status"] == "failed_closed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
