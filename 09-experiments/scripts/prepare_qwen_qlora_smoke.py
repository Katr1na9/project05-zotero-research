"""Prepare and lock the fixed-revision Qwen2.5 QLoRA smoke runtime.

The server-facing command is fail-closed: its run root must be the exact
contracted directory below /home/myy, all Hugging Face cache bytes stay under
that root, and only the files listed in the smoke contract may be downloaded.
No model inference or training is performed here.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def git_blob_sha1(path: Path) -> str:
    path = Path(path)
    size = path.stat().st_size
    digest = hashlib.sha1()
    digest.update(f"blob {size}\0".encode("ascii"))
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json_no_overwrite(path: Path, value: Any) -> None:
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"refusing to overwrite: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        raise FileExistsError(f"temporary output already exists: {temporary}")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def is_within(path: Path, root: Path) -> bool:
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def require_within(path: Path, root: Path, label: str) -> Path:
    resolved = Path(path).resolve()
    if not is_within(resolved, root):
        raise ValueError(f"{label} escapes the execution boundary")
    return resolved


def validate_server_boundary(
    contract: dict[str, Any], run_root: Path, repo_root: Path = REPO_ROOT
) -> tuple[Path, Path]:
    boundary = contract["server_execution_boundary"]
    allowed_home = Path(boundary["allowed_home"]).resolve()
    expected_root = (allowed_home / boundary["run_directory_name"]).resolve()
    observed_root = Path(run_root).resolve()
    if os.name != "posix":
        raise ValueError("the 4090 preparation command is Linux-only")
    if observed_root != expected_root:
        raise ValueError("run root differs from the exact contracted server path")
    observed_repo = Path(repo_root).resolve()
    require_within(observed_repo, allowed_home, "repository")
    if observed_root == allowed_home:
        raise ValueError("run root must be a dedicated child of /home/myy")
    return allowed_home, observed_root


def unique_physical_bytes(paths: Iterable[Path]) -> int:
    observed: set[Path] = set()
    total = 0
    for root in paths:
        root = Path(root)
        if not root.exists():
            continue
        if root.is_file():
            candidates = [root]
        else:
            candidates = (path for path in root.rglob("*") if path.is_file())
        for path in candidates:
            physical = path.resolve()
            if physical in observed:
                continue
            observed.add(physical)
            total += physical.stat().st_size
    return total


def expected_package_versions(contract: dict[str, Any]) -> dict[str, str]:
    aliases = {"huggingface-hub": "huggingface-hub"}
    return {
        aliases.get(name, name): version
        for name, version in contract["runtime_packages"].items()
        if name != "python"
    }


def probe_runtime(contract: dict[str, Any]) -> dict[str, Any]:
    import platform

    expected_python = contract["runtime_packages"]["python"]
    observed_python = f"{platform.python_version_tuple()[0]}.{platform.python_version_tuple()[1]}"
    if observed_python != expected_python:
        raise ValueError("Python major/minor differs from the smoke contract")
    packages = {}
    for package, expected in expected_package_versions(contract).items():
        observed = importlib.metadata.version(package)
        if observed != expected:
            raise ValueError(f"runtime package version mismatch: {package}")
        packages[package] = observed

    try:
        import bitsandbytes as bnb
        import torch
    except ImportError as error:
        raise RuntimeError("the frozen torch/bitsandbytes runtime is unavailable") from error

    if not torch.cuda.is_available():
        raise ValueError("CUDA is unavailable")
    gpu_name = torch.cuda.get_device_name(0)
    hardware = contract["execution_host_amendment"]
    if gpu_name != hardware["gpu_name_required"]:
        raise ValueError("GPU identity differs from the contracted RTX 4090")
    capability = torch.cuda.get_device_capability(0)
    minimum = tuple(contract["training_config_snapshot"]["hardware"]["minimum_compute_capability"])
    if capability < minimum:
        raise ValueError("GPU compute capability is below the contract")
    total_vram = torch.cuda.get_device_properties(0).total_memory
    minimum_vram = int(
        contract["training_config_snapshot"]["hardware"]["minimum_total_vram_bytes"]
    )
    if total_vram < minimum_vram:
        raise ValueError("GPU memory is below the contracted minimum")

    sample = torch.randn((32, 32), device="cuda", dtype=torch.float16)
    quantized, state = bnb.functional.quantize_4bit(
        sample, quant_type="nf4", compress_statistics=True
    )
    restored = bnb.functional.dequantize_4bit(quantized, state)
    if restored.shape != sample.shape or not torch.isfinite(restored).all().item():
        raise ValueError("bitsandbytes NF4 CUDA probe failed")
    del sample, quantized, restored, state
    torch.cuda.empty_cache()
    return {
        "python": platform.python_version(),
        "packages": packages,
        "torch_cuda": torch.version.cuda,
        "gpu_name": gpu_name,
        "compute_capability": list(capability),
        "total_vram_bytes": total_vram,
        "nf4_cuda_probe": "passed",
        "operating_system": platform.platform(),
    }


def download_allowlisted_snapshot(
    contract: dict[str, Any], run_root: Path
) -> Path:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as error:
        raise RuntimeError("the frozen huggingface-hub runtime is unavailable") from error

    cache_root = require_within(run_root / "local-cache" / "huggingface", run_root, "cache")
    cache_root.mkdir(parents=True, exist_ok=True)
    model = contract["model"]
    downloaded: list[Path] = []
    for entry in model["files"]:
        path = Path(
            hf_hub_download(
                repo_id=model["repository_id"],
                filename=entry["path"],
                revision=model["revision"],
                cache_dir=str(cache_root),
                local_files_only=False,
            )
        )
        require_within(path, run_root, f"downloaded file {entry['path']}")
        downloaded.append(path)
    parents = {path.parent for path in downloaded}
    if len(parents) != 1:
        raise ValueError("allowlisted model files did not resolve to one snapshot")
    return parents.pop()


def verify_snapshot(
    contract: dict[str, Any], snapshot_dir: Path, run_root: Path
) -> dict[str, Any]:
    snapshot_dir = require_within(snapshot_dir, run_root, "model snapshot")
    expected = {entry["path"]: entry for entry in contract["model"]["files"]}
    observed = {
        str(path.relative_to(snapshot_dir)).replace("\\", "/")
        for path in snapshot_dir.rglob("*")
        if path.is_file()
    }
    if observed != set(expected):
        missing = sorted(set(expected) - observed)
        extra = sorted(observed - set(expected))
        raise ValueError(f"model snapshot allowlist mismatch: missing={missing}, extra={extra}")

    files = []
    total = 0
    for relative, entry in sorted(expected.items()):
        path = snapshot_dir / relative
        require_within(path, run_root, relative)
        size = path.stat().st_size
        if size != entry["bytes"]:
            raise ValueError(f"model snapshot byte mismatch: {relative}")
        record = {"path": relative, "bytes": size}
        if "lfs_sha256" in entry:
            observed_hash = sha256_file(path).lower()
            if observed_hash != entry["lfs_sha256"].lower():
                raise ValueError(f"model snapshot SHA-256 mismatch: {relative}")
            record["sha256"] = observed_hash.upper()
        else:
            observed_hash = git_blob_sha1(path)
            if observed_hash != entry["git_blob_sha1"]:
                raise ValueError(f"model snapshot Git blob mismatch: {relative}")
            record["git_blob_sha1"] = observed_hash
        files.append(record)
        total += size
    if total != contract["model"]["repository_bytes"]:
        raise ValueError("model repository byte total differs from the contract")
    return {
        "repository_id": contract["model"]["repository_id"],
        "revision": contract["model"]["revision"],
        "snapshot_dir": str(snapshot_dir),
        "files": files,
        "file_count": len(files),
        "repository_bytes": total,
        "weight_bytes": sum(
            entry["bytes"] for entry in contract["model"]["files"] if "lfs_sha256" in entry
        ),
    }


def prepare(contract_path: Path, run_root: Path, output: Path) -> dict[str, Any]:
    contract = load_json(contract_path)
    _, run_root = validate_server_boundary(contract, run_root)
    output = Path(output).resolve()
    require_within(output, run_root, "preparation audit")
    runtime = probe_runtime(contract)
    snapshot = download_allowlisted_snapshot(contract, run_root)
    model_lock = verify_snapshot(contract, snapshot, run_root)
    resource_paths = [
        run_root / "local-runtime",
        run_root / "local-cache",
        run_root / "local-output",
    ]
    resource_bytes = unique_physical_bytes(resource_paths)
    maximum = contract["training_config_snapshot"]["resource_limits"][
        "maximum_environment_cache_adapter_bytes"
    ]
    if resource_bytes > maximum:
        raise ValueError("environment/cache/output bytes exceed the smoke limit")
    return {
        "schema_version": "project05-qwen25-qlora-smoke-preparation-v0.1",
        "status": "passed_runtime_and_fixed_revision_weight_gate",
        "contract_id": contract["contract_id"],
        "contract_sha256": sha256_file(contract_path),
        "runtime": runtime,
        "model_snapshot": model_lock,
        "resource_bytes": resource_bytes,
        "resource_limit_bytes": maximum,
        "training_run": False,
        "formal_inference_run": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = prepare(args.contract, args.run_root, args.output)
    write_json_no_overwrite(args.output, result)
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
