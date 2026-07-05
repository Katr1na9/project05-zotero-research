# 2024 - SAGA

## 基本信息

- 题名：SAGA: Synthetic Audit Log Generation for APT Campaigns
- 作者：Yi-Ting Huang, Ying-Ren Guo, Yu-Sheng Yang, Guo-Wei Wong, Yu-Zih Jheng, Yeali Sun, Jessemyn Modini, Timothy Lynar, Meng Chang Chen
- 年份：2024
- 来源：arXiv:2411.13138
- 本地文件：`../07-zotero-exports/pdfs_20260705_round3/SAGA_Synthetic_Audit_Log_Generation_APT_2024.pdf`

## 一句话总结

SAGA 是 APT campaign 合成审计日志生成框架，能生成带细粒度 ATT&CK technique 标签的 synthetic audit logs；它不是归因方法，但可能成为 Project05 论文实验的数据来源。

## 做了什么

SAGA 解决 APT 日志数据稀缺和标签不足的问题。它生成：

- 任意时长的 synthetic audit logs；
- 混合正常行为和 stealthy APT malicious logs；
- 按 APT lifecycle 嵌入 ATT&CK techniques；
- 细粒度事件标签；
- 更高层次的 attack representation。

## 与 Project05 的关系

这篇不撞 Project05 的专利核心，但会影响实验设计：

- 如果 Project05 需要构造 evidence missing / provenance evidence ablation，可以考虑用 SAGA 或类似 synthetic audit log；
- 但 Project05 不能声称 “生成 APT 合成日志” 是创新；
- 它能支撑日志侧 evidence channel 的可控实验。

## 结论

纳入实验资源线。后续如果要做论文，SAGA 可以用于构造可控缺失证据、TTP-only、provenance-only、multi-source evidence 的消融场景。

