# External AFA source and interface audit v0.1

Run:

```powershell
python 09-experiments/scripts/audit_external_afa_baselines.py `
  --clone-root C:/Users/35393/Desktop/workspace/Project05-external-audit
```

The three locally available repositories match their frozen commits; the WinRegRL archive hash also matches. All C07-C12 action types map to a WinRegRL action family, but `direct_same_task_claim_allowed` remains `false` because state, transition, endpoint and evidence-reveal semantics are not equivalent.
