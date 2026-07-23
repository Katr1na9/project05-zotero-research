# REPROD `dots.zip` Acquisition Execution Authority v0.1

**状态：`frozen_one_initial_attempt_authorized`。**

用户已点名授权：

> `reprod_dots_derived_provenance_archive` → 一次获取 → exact size+MD5 硬停 → 再冻结 reader + central-directory/nested-notice 合同。

本执行授权仅打开 exact acquisition contract 中 `dots.zip` 的一次 initial attempt，不修改其他 Gate。

| 项 | 冻结值 |
|---|---|
| Target ID | `reprod_dots_derived_provenance_archive` |
| Record / revision | Zenodo `8123115` / `2` |
| Source key | `dots.zip` |
| URL | `https://zenodo.org/api/records/8123115/files/dots.zip/content` |
| Target path | `datasets/llm/local_audit_cache/reprod-bounded-v0.1/raw/dots.zip` |
| Exact bytes / hard ceiling | `10,928,971,753` |
| MD5 | `d9e3f24ba36a9b9503a55eb1cf677345` |
| Initial attempts | `1` |
| Retry / resume | `false / false` |

冻结 launcher：

- path：`datasets/llm/download_reprod_dots_v0_1.ps1`
- SHA-256：`e2fb2599b497e2973aeb6c126da9dbd9a3be9300244cfe6dd00375f65bba16fb`
- PowerShell parse errors：`0`
- curl：`C:\WINDOWS\system32\curl.exe`
- `--retry 0`
- 无 `--continue-at`
- 无 archive list/open/extract

Launcher 只允许把响应体写到 frozen target。curl 成功后先检查 exact size；只有 size 通过才计算 MD5。任一失败都记录脱敏 failure 并停止，不自动重试、续传、换源或切换 PML。

成功也必须在 size+MD5 后硬停。当前授权不允许：

- 打开 ZIP 或读取 central directory/member；
- 读取 ordinary DOT、notice 或 `summary.csv`；
- 下载 PML；
- 写 catalog、授 source role、family/lineage/sample/quota；
- 生成训练样本、baseline、微调；
- Kernel/Γ/M3*、L2 Gate 或 git push。

下一阶段仅可在 verified 后冻结独立 reader/tool identity 与 bounded central-directory + nested-notice contract；其执行仍需单独授权。
