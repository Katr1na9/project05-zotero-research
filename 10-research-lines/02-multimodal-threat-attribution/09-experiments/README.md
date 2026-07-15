# P05-L2 Experiments

状态：未启动。已完成 [数据集可行性审计](dataset-feasibility-audit-v0.1-20260715.md)，但 G1/G5 和 pilot annotation gate 前禁止下载数据、添加模型代码或结果文件。

## 未来最低结构

只有在方法/实验 Gate 通过后，才建立：

```text
protocols/
data_schema/
data_manifests/
baselines/
scripts/
tests/
results/
```

## 必须预注册

- 研究任务和独立样本单位；
- 模态定义及配对规则；
- 单模态、简单融合和检索 baseline；
- modality ablation；
- missing/conflicting modality 条件；
- leakage 与时间/实体对齐检查；
- 主要指标、次要指标和失败条件；
- 训练、开发、参数锁定测试边界。

## 数据红线

原始大文件、PDF、PCAP、恶意样本、密钥和本地 trace 不进入 Git。数据来源、许可证、版本、hash 和提取摘要必须进入可提交 manifest。

## 当前候选数据顺序

1. ProvICS pilot；
2. AIT Log Dataset 2.0 external validation；
3. CICAPT-IIoT/ProvCon after license verification；
4. OpTC only for flow/log ablation.

用户选题前不得执行上述下载。
