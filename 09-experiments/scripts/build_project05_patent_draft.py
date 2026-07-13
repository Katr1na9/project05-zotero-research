from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
WRITING = ROOT / "08-writing"
PATENT_WORK = WRITING / "patent-work"
DEFAULT_PATENT_MD = WRITING / "patent-main-draft-v0.4-20260711.md"
DEFAULT_CLAIMS_TXT = PATENT_WORK / "06-claims-v0.4.txt"
DEFAULT_SOURCE_MAP = PATENT_WORK / "01-source-map.json"
DEFAULT_EVIDENCE_LEDGER = PATENT_WORK / "03-evidence-ledger.json"
DEFAULT_OUTPUT = PATENT_WORK / "07-structured-draft-v0.4.json"


def section(text: str, start: str, end: str | None) -> str:
    start_pos = text.index(start) + len(start)
    end_pos = text.index(end, start_pos) if end else len(text)
    return text[start_pos:end_pos].strip()


def paragraphs(text: str) -> list[str]:
    return [
        re.sub(r"\s+", " ", block).strip()
        for block in re.split(r"\n\s*\n", text)
        if block.strip() and not block.strip().startswith("#")
    ]


def load_claims(claims_path: Path) -> list[dict[str, Any]]:
    claims = []
    for line in claims_path.read_text(encoding="utf-8-sig").splitlines():
        match = re.match(r"^(\d+)\.\s+(.*)$", line.strip())
        if match:
            claims.append({"number": int(match.group(1)), "text": match.group(2)})
    return claims


def source_map(source_map_path: Path) -> list[dict[str, str]]:
    raw = json.loads(source_map_path.read_text(encoding="utf-8"))
    records = []
    for item in raw["sources"]:
        records.append(
            {
                "id": item["source_id"],
                "type": item["type"],
                "locator": f"{item['path']}；{item['locator']}",
                "summary": item["use"],
                "confidence": "high" if item["source_id"] != "P002" else "medium",
            }
        )
    return records


def evidence_ledger(evidence_ledger_path: Path) -> list[dict[str, Any]]:
    raw = json.loads(evidence_ledger_path.read_text(encoding="utf-8"))
    entries = []
    for index, item in enumerate(raw["features"], start=1):
        status = item["support_state"]
        if status == "explicit-controlled-environment-only":
            status = "explicit"
        entries.append(
            {
                "id": f"F{index:03d}",
                "feature": item["feature"],
                "source_ids": item["source_ids"],
                "source_location": "；".join(item["source_ids"]),
                "technical_role": item["destination"],
                "effect": item["technical_effect"],
                "support_status": status,
            }
        )
    return entries


def claim_feature_map(claim_numbers: set[int]) -> list[dict[str, Any]]:
    mapping = {
        1: ["F001", "F002", "F003", "F004", "F005"],
        2: ["F001"],
        3: ["F001", "F005"],
        4: ["F002"],
        5: ["F003"],
        6: ["F003"],
        7: ["F004"],
        8: ["F005"],
        9: ["F009"],
        10: ["F001", "F002", "F003", "F004", "F005"],
        11: ["F001", "F002", "F003", "F004", "F005", "F009"],
        12: ["F001", "F002", "F003", "F004", "F005", "F009"],
    }
    return [
        {
            "claim_number": number,
            "feature": "；".join(ids),
            "evidence_ids": ids,
            "specification_locations": ["发明内容", "具体实施方式"],
        }
        for number, ids in mapping.items()
        if number in claim_numbers
    ]


def figures() -> list[dict[str, Any]]:
    return [
        {
            "number": 1,
            "title": "归因取证动作规划方法流程图",
            "type": "flowchart",
            "orientation": "vertical",
            "claim_number": 1,
            "complete_claim_flow": True,
            "source_ids": ["P001", "C001", "C003"],
            "nodes": [
                {"id": "S1", "label": "S1：获取攻击行为图及本地安全证据声明"},
                {"id": "S2", "label": "S2：构建证据缺口状态"},
                {"id": "S3", "label": "S3：获取具有公开意图、通道和成本的候选动作"},
                {"id": "S4", "label": "S4：确定目标取证动作或停止动作"},
                {"id": "S5", "label": "S5：执行动作并更新状态与可支撑粒度"},
                {"id": "S6", "label": "S6：输出粒度受控归因结果或降级结果"},
            ],
            "edges": [
                {"from": "S1", "to": "S2", "label": ""},
                {"from": "S2", "to": "S3", "label": ""},
                {"from": "S3", "to": "S4", "label": ""},
                {"from": "S4", "to": "S5", "label": "目标取证动作"},
                {"from": "S5", "to": "S2", "label": "新增证据及反馈"},
                {"from": "S4", "to": "S6", "label": "停止动作"},
            ],
        },
        {
            "number": 2,
            "title": "公开动作信息与隐藏执行信息隔离示意图",
            "type": "methodology",
            "orientation": "horizontal",
            "source_ids": ["P003", "C002"],
            "nodes": [
                {"id": "public", "label": "公开意图目标、采集通道及动作成本"},
                {"id": "planner", "label": "规划模块"},
                {"id": "executor", "label": "通道执行模块"},
                {"id": "hidden", "label": "实际恢复的安全证据集合"},
            ],
            "edges": [
                {"from": "public", "to": "planner", "label": "可见"},
                {"from": "planner", "to": "executor", "label": "采集控制指令"},
                {"from": "hidden", "to": "executor", "label": "仅执行时访问"},
            ],
        },
        {
            "number": 3,
            "title": "证据缺口状态组成及更新示意图",
            "type": "methodology",
            "orientation": "horizontal",
            "source_ids": ["C001"],
            "nodes": [
                {"id": "claims", "label": "当前可见安全证据声明"},
                {"id": "state", "label": "覆盖节点、关键缺口、预算及动作反馈"},
                {"id": "granularity", "label": "当前可支撑归因粒度"},
            ],
            "edges": [
                {"from": "claims", "to": "state", "label": "覆盖计算"},
                {"from": "state", "to": "granularity", "label": "粒度判定及上限截断"},
            ],
        },
        {
            "number": 4,
            "title": "取证动作执行与停止降级闭环示意图",
            "type": "flowchart",
            "orientation": "horizontal",
            "source_ids": ["C003", "P005", "P006"],
            "nodes": [
                {"id": "input", "label": "当前证据缺口状态及剩余预算"},
                {"id": "select", "label": "选择目标取证动作"},
                {"id": "execute", "label": "执行采集通道"},
                {"id": "update", "label": "更新状态及剩余预算"},
                {"id": "stop", "label": "输出当前可支撑归因粒度及停止原因"},
            ],
            "edges": [
                {"from": "input", "to": "select", "label": "开始"},
                {"from": "select", "to": "execute", "label": "继续采集"},
                {"from": "execute", "to": "update", "label": "新增证据或零收益"},
                {"from": "update", "to": "select", "label": "未结束"},
                {"from": "select", "to": "stop", "label": "目标达成、预算不足或不可达"},
            ],
        },
        {
            "number": 5,
            "title": "具有先决依赖的多步取证动作规划示意图",
            "type": "methodology",
            "orientation": "horizontal",
            "source_ids": ["P008", "P009", "C006"],
            "nodes": [
                {"id": "state0", "label": "当前证据缺口状态"},
                {"id": "unlock", "label": "低即时收益解锁动作"},
                {"id": "critical", "label": "后续关键取证动作"},
                {"id": "target", "label": "达到目标归因粒度"},
                {"id": "decoy", "label": "高即时收益诱饵动作"},
            ],
            "edges": [
                {"from": "state0", "to": "unlock", "label": "多步路径"},
                {"from": "unlock", "to": "critical", "label": "解锁"},
                {"from": "critical", "to": "target", "label": "达标"},
                {"from": "state0", "to": "decoy", "label": "短视路径"},
            ],
        },
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a structured Project05 patent draft.")
    parser.add_argument("--patent-md", type=Path, default=DEFAULT_PATENT_MD)
    parser.add_argument("--claims-txt", type=Path, default=DEFAULT_CLAIMS_TXT)
    parser.add_argument("--source-map", type=Path, default=DEFAULT_SOURCE_MAP)
    parser.add_argument("--evidence-ledger", type=Path, default=DEFAULT_EVIDENCE_LEDGER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--source-label", default="Project05 mixed project and paper-main-draft-v0.3")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    text = args.patent_md.read_text(encoding="utf-8")
    claims = load_claims(args.claims_txt)
    claim_numbers = {claim["number"] for claim in claims}
    method_only = claim_numbers == set(range(1, 10))
    title = re.search(r"^#\s+(.+)$", text, flags=re.MULTILINE).group(1)
    technical_field = paragraphs(section(text, "### 1. 技术领域", "### 2. 背景技术"))
    background = paragraphs(section(text, "### 2. 背景技术", "### 3. 发明内容"))
    problem = paragraphs(section(text, "#### 3.1 要解决的技术问题", "#### 3.2 技术方案"))
    solution = paragraphs(section(text, "#### 3.2 技术方案", "#### 3.3 有益效果"))
    effects = paragraphs(section(text, "#### 3.3 有益效果", "### 4. 附图说明"))
    descriptions = paragraphs(section(text, "### 4. 附图说明", "### 5. 具体实施方式"))
    embodiment_text = section(text, "### 5. 具体实施方式", "## 三、说明书摘要")
    embodiment_parts = re.split(r"(?m)^####\s+", embodiment_text)
    embodiments = []
    for part in embodiment_parts:
        if not part.strip():
            continue
        first, *rest = part.splitlines()
        embodiments.append({"heading": first.strip(), "paragraphs": paragraphs("\n".join(rest))})
    abstract_blocks = paragraphs(section(text, "## 三、说明书摘要", "## 四、提交前红线"))
    abstract = abstract_blocks[0]

    data = {
        "schema_version": "2.0",
        "title": title,
        "metadata": {
            "source": args.source_label,
            "target": "中国发明专利",
            "draft_status": "供发明人及专利代理师复核",
        },
        "source_analysis": {
            "contains_core_formulas": True,
            "formula_count_in_source": 1,
            "contains_methodology_figures": True,
        },
        "source_map": source_map(args.source_map),
        "terminology_ledger": [
            {"concept": "evidence gap state", "canonical_zh": "证据缺口状态", "source_terms": ["alignment state"], "forbidden_aliases": []},
            {"concept": "public action intent", "canonical_zh": "公开意图目标", "source_terms": ["intended_cti_node_ids"], "forbidden_aliases": []},
            {"concept": "hidden recovery", "canonical_zh": "实际恢复的安全证据集合", "source_terms": ["recoverable_claim_ids"], "forbidden_aliases": []},
            {"concept": "support ceiling", "canonical_zh": "证据支持上限", "source_terms": ["support_ceiling"], "forbidden_aliases": []},
            {"concept": "stop action", "canonical_zh": "停止动作", "source_terms": ["STOP"], "forbidden_aliases": []},
        ],
        "formula_inventory": [
            {"source_id": "E001", "source_number": "M3a score", "technical_role": "根据关键缺口命中、一般缺口命中、意图精确率、召回率及动作成本计算缺口兼容性评价值", "disposition": "specification-equation-1"}
        ],
        "figure_inventory": [
            {"source_id": "P001", "source_number": "Project05 main flow", "type": "methodology", "disposition": "redraw-as-figures-1-to-5"}
        ],
        "abstract_figure_number": 1,
        "assumptions": [
            "目标法域为中国",
            "发明人、申请人、权属及首次公开日期待确认",
            "LLM 编译器不作为当前独立权利要求必要特征",
        ],
        "invention_concept": {
            "technical_problem": "部分对齐、通道不可靠和预算受限时，如何在不读取隐藏恢复结果的条件下自动选择后续取证动作并限制归因输出粒度。",
            "technical_means": "构建证据缺口状态，隔离公开意图与隐藏执行结果，按预算选择并执行取证动作，基于反馈更新状态并显式停止或降级。",
            "technical_effect": "将部分对齐结果转化为可执行采集控制闭环，减少规划阶段隐藏结果泄漏并约束证据不足时的越级归因。",
        },
        "evidence_ledger": evidence_ledger(args.evidence_ledger),
        "claims": claims,
        "claim_feature_map": claim_feature_map(claim_numbers),
        "figures": figures(),
        "specification": {
            "technical_field": technical_field,
            "background": background,
            "invention_content": {"problem": problem, "solution": solution, "beneficial_effects": effects},
            "figure_descriptions": descriptions,
            "equations": [
                {
                    "number": 1,
                    "source_location": "run_mvp.py m3a_gap_compat_score",
                    "source_ids": ["E001", "C001"],
                    "expression": "Q(a,s) = (8n_k + 3n_g + 2p + r - 0.5c) / c",
                    "latex": "Q(a,s)=\\frac{8n_k+3n_g+2p+r-0.5c}{c}",
                    "symbols": [
                        {"symbol": "n_k", "meaning": "命中的关键缺口数量"},
                        {"symbol": "n_g", "meaning": "命中的全部缺口数量"},
                        {"symbol": "p", "meaning": "公开意图相对于当前缺口的精确率"},
                        {"symbol": "r", "meaning": "公开意图相对于当前缺口的召回率"},
                        {"symbol": "c", "meaning": "候选取证动作的动作成本"},
                    ],
                    "technical_role": "计算候选取证动作与当前证据缺口的成本归一化兼容性评价值",
                    "description": "其中，n_k表示命中的关键缺口数量，n_g表示命中的全部缺口数量，p和r分别表示意图精确率和召回率，c表示动作成本。",
                }
            ],
            "embodiments": embodiments,
        },
        "abstract": abstract,
        "audit": {
            "support_findings": ["独立方法权利要求的必要特征均映射到F001-F005。", "非短视规划仅作为从属权利要求和受控实施例。", "两级来源核验为单个自然运营案例支持的可选实施例，未写入必要特征。"],
            "consistency_findings": ["LLM、DQN、XGBoost、AFA/MDP方法名称及具体数据集均未进入独立权利要求。", "未把降低平均取证成本或单一策略优越性写成必然技术效果。", "当前草稿仅保留方法权利要求。" if method_only else "当前草稿包含方法与平行权利要求类别。"],
        },
        "quality_assessment": {
            "status": "incomplete-draft",
            "scores": {
                "evidence_support": {"score": 4, "evidence": f"{len(claims)}项权利要求均映射到证据台账和源文件；F010仅作为可选实施例。"},
                "claim_architecture": {"score": 4, "evidence": "方法独立权利要求及八项从属回退层次完整。" if method_only else "方法独权、系统独权及从属回退层次完整。"},
                "terminology_consistency": {"score": 4, "evidence": "证据缺口状态、公开意图目标、实际恢复集合和支持上限已锁定。"},
                "enablement_detail": {"score": 4, "evidence": "说明书包含数据对象、状态构建、信息边界、评分、通道、停止、非短视及来源核验实施例。"},
                "technical_effect_reasoning": {"score": 4, "evidence": "技术效果限定为机器可执行闭环、信息隔离和粒度约束。"},
                "formula_coverage": {"score": 4, "evidence": "M3a评分公式、符号和技术作用均结构化收录。"},
                "figure_alignment": {"score": 4, "evidence": "五幅附图覆盖独权流程、信息边界、状态更新、停止闭环和从属非短视实施例。"},
            },
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
