# COW160x4 bounded gzip audit result

Status: `fail_closed_sensitive_field_key_detected`

| Gate | Result |
|---|---|
| Compressed identity | pass |
| Reader identity | pass |
| Bounded JSONL lines | 4096 |
| Schema probe | true |
| Field-isolation probe | false |
| Nested-notice Gate | false |
| Unique session candidates in bounded probe | 4096 |
| Statistical independence | false |
| Pointer binding | unbound |
| Lineage / quota credit | 0 / 0 |
| Source role / L2 Gate | false / false |

No raw line, field value, session identifier, IP, timestamp, pointer, or local
payload path is persisted.
