# C12 WitFoo metadata screen v0.1

The frozen stream reads 13,119 attack-report metadata records from revision `1c0be6c03713af68eb9badc404297a63546bf2b4`. Source hash and record count pass; five candidates satisfy the analyst-confirmed, normalized multisource and graph-complexity Gate.

Run:

```powershell
python 09-experiments/scripts/screen_witfoo_c12_candidates.py
```

This is a metadata Gate only. It does not establish independent ground truth or event-level recoverability.
