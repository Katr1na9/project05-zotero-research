# DARPA TC E5 / OpTC（C07 真留出数据根）

本目录预留给 **C07 真留出** 原始与派生数据（大型归档不进 Git）。

- 协议：[`../../08-writing/c07-true-holdout-protocol-v0.1-20260710.md`](../../08-writing/c07-true-holdout-protocol-v0.1-20260710.md)
- 现有 E3 管线参考：[`../darpa_tc_e3/manifest.json`](../darpa_tc_e3/manifest.json)

接入顺序：选定 E5 THEIA/ClearScope（或 OpTC）攻击窗 → 写 `manifest.json` + `ground_truth/` → 流式抽取 → 编译 `real_cases/C07-*`。

当前状态：**尚未下载官方归档；勿将 C06/R03 迁入此处冒充留出。**
