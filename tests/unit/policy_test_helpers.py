"""Load the exact repository-approved admission-policy authority."""

from copy import deepcopy
from pathlib import Path

import yaml

from src.firewall.policy import AdmissionPolicyAuthority


ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def policy_documents():
    policy = load_yaml(ROOT / "configs" / "admission-policy-kernel-v0.8.yaml")
    pending = load_yaml(
        ROOT / "configs" / "admission-policy-approval-kernel-v0.8.yaml"
    )
    gamma = load_yaml(ROOT / "configs" / "gamma-kernel-v0.8.yaml")
    return policy, pending, gamma


def approved_policy_parts(gamma_reference=None):
    policy, manifest, gamma = policy_documents()
    gamma_ref = deepcopy(
        gamma["admission_policy"]
        if gamma_reference is None
        else gamma_reference
    )
    return policy, deepcopy(manifest), gamma_ref


def approved_policy_authority(gamma_reference=None):
    policy, manifest, gamma_ref = approved_policy_parts(gamma_reference)
    return AdmissionPolicyAuthority.from_documents(policy, manifest, gamma_ref)
