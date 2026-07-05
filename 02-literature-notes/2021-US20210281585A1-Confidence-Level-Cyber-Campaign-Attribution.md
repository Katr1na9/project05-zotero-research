# 2021 - Patent: Confidence Level in Cyber Campaign Attribution

## 基本信息

- 公开号：US20210281585A1
- 题名：System and method for determining the confidence level in attributing a cyber campaign to an activity group
- 来源：https://patents.google.com/patent/US20210281585A1/en
- 本地 HTML：`../07-zotero-exports/pdfs_20260705_round3/US20210281585A1_en.html`

## 一句话总结

这个专利已经覆盖了 cyber campaign attribution 的 confidence level、high/moderate/low confidence、information gap 和补充 hunting 建议；它是 Project05 专利方向的重大红线。

## 核心权利要求/机制

专利 claim 1 覆盖：

- 从 sensors 收集 intrusion set data；
- 从 threat intelligence feeds / vendor reports 收集 activity group data；
- 提取 EKID，包括 tools、tactics、techniques、procedures；
- 提取 AGID；
- 比较 EKID 与 AGID；
- 基于比较确定已知 activity group 及 associated confidence level。

claim 2 进一步覆盖：

- tool correlation；
- TTP correlation；
- unique techniques threshold；
- high / moderate / low confidence；
- moderate 或 low confidence 时确定 information gap。

说明书还提到：如果 confidence 不够，向用户提供 unique techniques 供 hunting，用户更新数据库后重新计算 confidence。

## 对 Project05 的红线影响

Project05 不能宽泛 claim：

- 根据 TTP/tool 匹配输出 attribution confidence；
- high/moderate/low confidence；
- confidence 不够时指出 information gap；
- 建议用户补充 hunting 后重新计算。

## 仍可能留下的空间

如果写专利，必须避开这个权利要求的核心，强调更具体的新机制，例如：

- 多源证据可用性画像不只 EKID/AGID；
- actor/campaign/intent/technique 分层降级；
- open-set / unknown actor / OOS；
- false flag / mimicry 风险识别；
- LLM 生成可审计解释；
- 引入证据引用真实性和跨源冲突检测。

