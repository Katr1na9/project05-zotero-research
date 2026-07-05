# 2025 - Patent: Automatic Threat Actor Attribution Based on Multiple Evidence

## 基本信息

- 专利号：US12368730B2
- 题名：Automatic threat actor attribution based on multiple evidence
- 来源：https://patents.google.com/patent/US12368730B2/en
- 授权日：2025-07-22
- 申请人：Forescout Technologies Inc.
- 状态：本轮网页可检索，但本地 HTML 抓取被连接重置；按公开专利页面与交叉引用信息做红线笔记。

## 一句话总结

这个专利几乎直接堵住 “多源证据融合 + 威胁行为体归因” 的宽泛专利表述。

## 已确认的危险点

该专利标题本身就是 direct collision。公开页面和相关专利引用显示其核心包括：

- 多个 evidence attributors；
- IoC attributor；
- TTP attributor；
- 每个 attributor 输出 actor probability / PMF；
- 使用 opinion pool / aggregation；
- threshold / confidence；
- 处理候选 actor 概率接近的歧义。

## 对 Project05 的红线影响

不能 claim：

- multiple evidence threat actor attribution；
- IoC + TTP 多模块归因器；
- actor PMF 融合；
- opinion pool 融合；
- broad confidence threshold。

## 仍可能留下的空间

Project05 必须跳出 “融合得到 actor” 的框架，把创新落在：

1. 缺失证据画像；
2. 当前证据不足时不输出 actor；
3. 输出可审计的降级结论；
4. open-set / unknown actor；
5. false flag / mimicry；
6. LLM 解释缺失证据与补充取证路径。

这仍需后续详细研读该专利 claims，避免权利要求撞线。

