# DARPA TC E3 Pilot Ingestion Design

日期：2026-07-09

## 目标

为 Project05 建立第一个真实数据接入边界。Phase 0 只固定官方来源、攻击时间窗、ground truth 和适配器接口，不下载或提交大型原始归档。

## 开发案例

### R01：FiveDirections 完整攻击链

- 日期：2018-04-11
- 场景：Firefox Backdoor with Drakon In-Memory
- 平台：Windows 10
- 官方 topic：`ta1-fivedirections-e3-official-2`
- 官方 JSON 归档：`ta1-fivedirections-e3-official-2.json.tar.gz`
- Google Drive 文件 ID：`1BeP80zUUmm4eZl0UuU43PsKNkl_xgskj`
- 本地分析窗口：2018-04-11 09:45-11:00 America/New_York
- UTC 窗口：2018-04-11T13:45:00Z 至 2018-04-11T15:00:00Z
- Ground truth：Firefox 利用、Drakon 内存植入、C2、netrecon、文档外传。

### R02：CADETS 天然不完整攻击链

- 日期：2018-04-06
- 场景：Nginx Backdoor with Drakon In-Memory
- 平台：FreeBSD
- 官方 topic：`ta1-cadets-e3-official`
- 官方 JSON 归档：`ta1-cadets-e3-official.json.tar.gz`
- Google Drive 文件 ID：`1AcWrYiBmgAqp7DizclKJYYJJBQbnDMfb`
- 本地分析窗口：2018-04-06 10:45-12:25 America/New_York
- UTC 窗口：2018-04-06T14:45:00Z 至 2018-04-06T16:25:00Z
- Ground truth：Nginx 利用、恶意进程落地与提权、sshd 注入失败、主机崩溃；没有完整的后续收集与外传链。

R01/R02 都是开发案例，不作为最终独立测试集。

## 官方来源

- E3 根目录：`https://drive.google.com/drive/folders/1QlbUFWAGq3Hpl8wVdzOdIoZLFxkII4EK`
- Ground truth PDF 文件 ID：`1mrs4LWkGk-3zA7t7v8zrhm0yEDHe57QU`
- Ground truth SHA-256：`021FC642E18544FDCC7BF0A79E2B5AAE001F5717D3ADBCE16744B68934523599`
- Operational event log 文件 ID：`1mnx73nb0KMX4EbgSiBLu0tkKrQ34P96H`
- Operational log SHA-256：`9B9F38DCB1984C243F1C64F993E0843429C0A38EB2B5F9AB50D0EAB46D5ECBF8`

## 数据边界

- 原始 `.tar.gz`、解压 JSON、临时索引和切片事件不进入 Git。
- Git 只保存 manifest、ground-truth slice、适配器代码、测试和小型派生 claim。
- 原始事件必须保留 topic、record UUID、时间戳和原始文件偏移，保证 claim 可回指。
- 适配器不得根据 ground truth 标签修改原始事件内容；ground truth 只用于筛选评估时间窗和建立 gold labels。

## Phase 0 输出

```text
09-experiments/real_data/darpa_tc_e3/manifest.json
09-experiments/real_data/darpa_tc_e3/ground_truth/R01.json
09-experiments/real_data/darpa_tc_e3/ground_truth/R02.json
09-experiments/scripts/validate_real_manifest.py
09-experiments/tests/test_real_manifest.py
```

## 后续阶段

Phase 1 获取归档并流式扫描时间戳，不整体解压；Phase 2 将命中事件转换为 provenance entities/edges；Phase 3 生成人工复核的 `evidence_claim`；Phase 4 才运行 mask、Oracle、M1 和消融。
