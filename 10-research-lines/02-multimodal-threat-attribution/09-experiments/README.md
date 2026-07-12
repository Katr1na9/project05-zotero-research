# P05-L2 Experiments

状态：未启动。G5 前禁止添加模型代码或结果文件。

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
