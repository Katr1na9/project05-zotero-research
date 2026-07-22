"""P7 read-only Epistemic Firewall admission API.

No admission write, Promote/Revoke ledger, certificate, planner, or system STOP
authority is exposed from this package.
"""

from .admission import AdmissionDecision, ECaseAdmissionFirewall

__all__ = ["AdmissionDecision", "ECaseAdmissionFirewall"]
