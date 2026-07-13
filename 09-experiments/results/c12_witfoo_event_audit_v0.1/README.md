# C12 WitFoo event-source audit v0.1

The audit checks five GraphML projections and the corresponding embedded incident leads. Two candidates have at least two independently recoverable stream channels; three product-label multisource candidates collapse to one actual stream and are rejected.

All five GraphML files contain only `INCIDENT_LINK` edges. Raw evidence is therefore recovered from incident leads, not from the vendor projection.

Run:

```powershell
python 09-experiments/scripts/audit_witfoo_c12_event_sources.py
```

Raw GraphML and incident JSON remain under the ignored `real_data/witfoo_precinct6/raw/` boundary.
