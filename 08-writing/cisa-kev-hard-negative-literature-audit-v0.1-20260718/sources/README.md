# Source capture

该目录保存 2026-07-18 快速证据审查的原始检索结果和全文提取。检索输出只作为证据定位材料；最终结论回到官方原文、论文全文/权威摘要与 DOI 元数据，不把搜索引擎摘要当最终证据。

## Discovery searches

- `search-official-kev-20260718.json`: CISA/NIST 官方语义，20 条；
- `search-academic-kev-usage-20260718.json`: KEV 学术用法，16 条；
- `search-kev-groundtruth-peerreviewed-20260718.json`: KEV ground-truth/标签语义，12 条；
- `search-pu-openworld-security-20260718.json`: PU/open-world/security negative，19 条；
- `search-hard-negative-methods-20260718.json`: hard-negative/关系抽取，18 条。

发现检索合计 85 条，按 URL 去重后 82 条。`search-bibliographic-verification-20260718.json` 是后续定向书目核验，不重复计入发现样本。

## Full-text / authoritative-page extraction

- `extract-official-kev-primary-20260718.json`;
- `extract-kev-ml-primary-20260718.json`;
- `extract-pu-re-negative-primary-20260718.json`;
- `extract-bibliographic-verification-20260718.json`。

最终报告、去重证据矩阵和 DOI 核验记录位于父目录。11 个唯一全文/权威详情页接受全文核对，9 个证据源纳入最终矩阵。
