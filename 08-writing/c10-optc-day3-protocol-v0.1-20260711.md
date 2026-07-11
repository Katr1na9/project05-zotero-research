# C10 OpTC Day 3 参数锁定测试协议 v0.1

日期：2026-07-11  
状态：**已编译并完成参数锁定评估**
源案例：`R07`  
拟编译案例：`C10-darpa-optc-sysclient0351-0925`

## 1. 目的与边界

C10 检验已冻结的 Logistic M3b、XGBoost、M2 和 Oracle 在一条未参与训练、未参与模型选择的 OpTC Day 3 攻击链上的表现。它增加攻击工具与日期多样性，但与 C09 同属 OpTC，因此只能称为**跨日同语料的参数锁定稳健性案例**，不能作为第四个独立数据源家族。

独立实验单位是 C10 这一条攻击链。不同 mask、intensity 和 seed 是同一案例的重复测量，不得扩张为独立攻击样本数。

## 2. 先验锁定

- 场景：Day 3 “Malicious Upgrade”。
- 主机：`Sysclient0351.systemia.com`。
- Ground Truth 本地时间窗：`2019-09-25 11:20–11:35 EDT`。
- UTC 抽取窗：`2019-09-25T15:20:00Z–15:35:00Z`。
- 报告链：Notepad++ 恶意升级 → `update.exe` Meterpreter → reverse TCP C2 → `f.exe` 迁移到 `lwabeat`。
- 冻结状态：XGBoost v0.1 的 16 个特征、150 rounds、depth 3、eta 0.05、seed 11、成本惩罚 0.1 均不得因 C10 改动。

## 3. 只需下载的文件

不需要下载新的数据集，也不需要下载完整 OpTC；只需补齐 OpTC 中一个官方 eCAR 主机分片：

```text
OpTCNCR/ecar/evaluation/25Sept/AIA-351-375/
  AIA-351-375.ecar-last.json.gz
```

- 文件 ID：`1-yxi3k1Duc5Uuu_gbu1vjtdEU3FoDSIA`
- 文件夹 ID：`1j97jgNd-xsDlcCuc0mbTP5v2uBUWtFXT`
- 官方下载响应体积：`1,610,345,177 bytes`（约 `1.61 GB`）
- 浏览器文件链接：`https://drive.google.com/file/d/1-yxi3k1Duc5Uuu_gbu1vjtdEU3FoDSIA/view`
- 本地目标：`09-experiments/real_data/darpa_optc/raw/ecar/evaluation/25Sept/AIA-351-375/AIA-351-375.ecar-last.json.gz`

现有 `raw/errata_av_bypass/AIA-351-375...zip` 是 **23Sep19**，日期错误；现有 24Sep AIA-201-225 包只覆盖到 `09:55 EDT`，也早于锁定的 Day 2 候选事件。二者均不得替代 R07。

## 4. 数据到位后的流水线

1. 记录文件字节数和 SHA-256，不先搜索 IOC。
2. 按精确 FQDN 和锁定 UTC 窗口流式抽取。
3. 只从抽取窗口编译可回查的 eCAR motif；报告存在但事件不可见的内容保留为缺失证据。
4. 若窗口内至少恢复两个相互独立的攻击阶段，编译 C10；若不足，则降低 `support_ceiling` 或记录为不可编译负结果，不换窗找“更好看”的事件。
5. 使用冻结模型重放 Logistic、XGBoost、M2、M3a 与 Oracle，不在 C10 上调参。

计划抽取命令：

```powershell
python 09-experiments/scripts/stream_ecar_event_window.py `
  --input 09-experiments/real_data/darpa_optc/raw/ecar/evaluation/25Sept/AIA-351-375/AIA-351-375.ecar-last.json.gz `
  --hostname Sysclient0351.systemia.com `
  --start-utc 2019-09-25T15:20:00Z `
  --end-utc 2019-09-25T15:35:00Z `
  --output 09-experiments/real_data/darpa_optc/extracted/R07_sysclient0351_window.jsonl `
  --summary 09-experiments/real_data/darpa_optc/derived/R07_extraction_summary.json
```

## 5. 预登记评价

| 层级 | 指标 |
|---|---|
| 数据可用性 | 精确主机行数、对象类型、坏 JSON/时间戳、事件 UUID 可回查 |
| 动作标签 | AUROC、AP、Brier、top-1 critical-gap hit |
| 序贯策略 | success、cost-to-target、regret、zero-yield、premature STOP、ceiling violation |
| 主要比较 | XGBoost vs Logistic；XGBoost vs M2；全部对照 Oracle 上界 |

C10 可以加强或削弱“XGBoost 比 Logistic 更稳”的结论，但单个 C10 不能证明广泛泛化，也不能单独打开 DQN Gate。DQN 仍需独立的非短视诊断环境。

## 6. 完成记录

- [x] 官方文件大小与文件名核验
- [x] SHA-256 登记：`D52C3FC...A32CC75`
- [x] 精确 FQDN + 锁定窗口抽取：扫描 `27,832,841` 行，选中 `37,301` 行，坏 JSON/时间戳均为 0
- [x] 编译 5/5 motifs：恶意升级落盘、执行、C2、远程线程迁移、良性上下文
- [x] C10 冻结 MVP：M2 `45/45`；M3a `36/45`
- [x] XGBoost v0.2：训练仍为 C01–C06；C10 `45/45`，均成本 `5.0444`
- [x] 明确边界：C10 同属 OpTC，不作为第四独立来源家族
