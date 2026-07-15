from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = (
    ROOT
    / "08-writing"
    / "patent-package-v0.9-zju-reference"
    / "Project05_调查取证动作规划方法-figures"
)

CANVAS = (1800, 2400)
BLACK = "#000000"
WHITE = "#ffffff"
LIGHT = "#f2f2f2"
LINE = 5


def font_path(*names: str) -> Path:
    fonts = Path("C:/Windows/Fonts")
    for name in names:
        path = fonts / name
        if path.exists():
            return path
    raise FileNotFoundError(f"No usable Chinese font found in {fonts}: {names}")


REGULAR_FONT = font_path("simsun.ttc", "msyh.ttc", "simfang.ttf")
BOLD_FONT = font_path("simhei.ttf", "msyhbd.ttc", "simsun.ttc")


def font(size: int, *, bold: bool = False):
    return ImageFont.truetype(str(BOLD_FONT if bold else REGULAR_FONT), size=size)


def text_width(draw: ImageDraw.ImageDraw, value: str, fnt) -> float:
    if not value:
        return 0
    box = draw.textbbox((0, 0), value, font=fnt)
    return box[2] - box[0]


def wrap_text(draw: ImageDraw.ImageDraw, value: str, fnt, max_width: int) -> list[str]:
    lines: list[str] = []
    for hard_line in value.split("\n"):
        if not hard_line:
            lines.append("")
            continue
        current = ""
        for char in hard_line:
            candidate = current + char
            if current and text_width(draw, candidate, fnt) > max_width:
                lines.append(current)
                current = char
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines


def multiline_center(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    value: str,
    *,
    size: int = 48,
    bold: bool = False,
    padding: int = 24,
    spacing: int = 12,
):
    fnt = font(size, bold=bold)
    x1, y1, x2, y2 = box
    lines = wrap_text(draw, value, fnt, max(1, x2 - x1 - 2 * padding))
    line_boxes = [draw.textbbox((0, 0), line, font=fnt) for line in lines]
    heights = [b[3] - b[1] for b in line_boxes]
    total_height = sum(heights) + spacing * max(0, len(lines) - 1)
    y = y1 + (y2 - y1 - total_height) / 2
    for line, b, height in zip(lines, line_boxes, heights):
        width = b[2] - b[0]
        draw.text(((x1 + x2 - width) / 2, y - b[1]), line, fill=BLACK, font=fnt)
        y += height + spacing


def box(
    draw: ImageDraw.ImageDraw,
    coords: tuple[int, int, int, int],
    value: str,
    *,
    size: int = 48,
    bold: bool = False,
    fill: str = WHITE,
    dashed: bool = False,
):
    if dashed:
        dashed_rectangle(draw, coords, width=LINE, dash=22, gap=14)
    else:
        draw.rectangle(coords, outline=BLACK, fill=fill, width=LINE)
    multiline_center(draw, coords, value, size=size, bold=bold)


def dashed_rectangle(
    draw: ImageDraw.ImageDraw,
    coords: tuple[int, int, int, int],
    *,
    width: int,
    dash: int,
    gap: int,
):
    x1, y1, x2, y2 = coords
    dashed_line(draw, (x1, y1), (x2, y1), width=width, dash=dash, gap=gap, arrow=False)
    dashed_line(draw, (x2, y1), (x2, y2), width=width, dash=dash, gap=gap, arrow=False)
    dashed_line(draw, (x2, y2), (x1, y2), width=width, dash=dash, gap=gap, arrow=False)
    dashed_line(draw, (x1, y2), (x1, y1), width=width, dash=dash, gap=gap, arrow=False)


def dashed_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    width: int = LINE,
    dash: int = 24,
    gap: int = 14,
    arrow: bool = False,
):
    x1, y1 = start
    x2, y2 = end
    length = math.hypot(x2 - x1, y2 - y1)
    if length == 0:
        return
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    distance = 0.0
    while distance < length:
        finish = min(distance + dash, length)
        draw.line(
            (
                x1 + ux * distance,
                y1 + uy * distance,
                x1 + ux * finish,
                y1 + uy * finish,
            ),
            fill=BLACK,
            width=width,
        )
        distance += dash + gap
    if arrow:
        arrow_head(draw, start, end, width=width)


def arrow_head(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    width: int = LINE,
):
    x1, y1 = start
    x2, y2 = end
    angle = math.atan2(y2 - y1, x2 - x1)
    head_len = 28 + width * 2
    head_half = 14 + width
    bx = x2 - head_len * math.cos(angle)
    by = y2 - head_len * math.sin(angle)
    px = head_half * math.sin(angle)
    py = -head_half * math.cos(angle)
    draw.polygon([(x2, y2), (bx + px, by + py), (bx - px, by - py)], fill=BLACK)


def arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    label: str | None = None,
    label_xy: tuple[int, int] | None = None,
    dashed: bool = False,
    width: int = LINE,
):
    if dashed:
        dashed_line(draw, start, end, width=width, arrow=True)
    else:
        draw.line((*start, *end), fill=BLACK, width=width)
        arrow_head(draw, start, end, width=width)
    if label:
        fnt = font(36)
        xy = label_xy or ((start[0] + end[0]) // 2 + 12, (start[1] + end[1]) // 2 - 42)
        bbox = draw.textbbox(xy, label, font=fnt)
        draw.rectangle((bbox[0] - 8, bbox[1] - 4, bbox[2] + 8, bbox[3] + 4), fill=WHITE)
        draw.text(xy, label, fill=BLACK, font=fnt)


def new_canvas():
    image = Image.new("RGB", CANVAS, WHITE)
    draw = ImageDraw.Draw(image)
    return image, draw


def save(image: Image.Image, output: Path, number: int):
    output.mkdir(parents=True, exist_ok=True)
    image.save(output / f"figure-{number}.png", dpi=(300, 300), optimize=True)


def draw_figure_1(output: Path):
    image, draw = new_canvas()
    x1, x2 = 190, 1610
    boxes = [
        (x1, 100, x2, 350, "S1  获取攻击行为图及可回指原始事件的\n安全证据声明"),
        (x1, 480, x2, 760, "S2  依据版本化来源支持规则构建证据缺口状态\n并计算证据支持上限"),
        (x1, 890, x2, 1190, "S3  载入公开动作视图、冻结成本档案和先验档案\n并通过运行时字段允许列表校验"),
        (x1, 1320, x2, 1580, "S4  根据状态、预算、动作成本和公开先验\n确定目标取证动作或停止动作"),
        (x1, 1710, x2, 1970, "S5  输出采集控制指令，接收新增证据、\n零收益或通道失败反馈并更新状态"),
        (x1, 2100, x2, 2320, "S6  输出不高于当前证据支持上限的\n调查结论或降级结果"),
    ]
    for coords in boxes:
        box(draw, coords[:4], coords[4], size=45)
    for index in range(4):
        start = ((x1 + x2) // 2, boxes[index][3])
        end = ((x1 + x2) // 2, boxes[index + 1][1])
        label = "目标动作" if index == 3 else None
        arrow(draw, start, end, label=label, label_xy=(930, 1615) if label else None)
    # STOP and other terminal conditions bypass channel execution.
    terminal_points = [(x2, 1450), (1730, 1450), (1730, 2210), (x2, 2210)]
    for a, b in zip(terminal_points[:-2], terminal_points[1:-1]):
        draw.line((*a, *b), fill=BLACK, width=LINE)
    arrow(draw, terminal_points[-2], terminal_points[-1])
    draw.rectangle((1320, 1500, 1700, 1660), fill=WHITE)
    multiline_center(
        draw,
        (1320, 1500, 1700, 1660),
        "停止、目标达成、\n预算不足或不可达",
        size=32,
        padding=8,
    )
    # Feedback returns to the state rather than to the planner input.
    points = [(x1, 1840), (70, 1840), (70, 620), (x1, 620)]
    for a, b in zip(points[:-1], points[1:]):
        draw.line((*a, *b), fill=BLACK, width=LINE)
    arrow_head(draw, points[-2], points[-1])
    draw.text((85, 1120), "执行反馈闭环", fill=BLACK, font=font(36))
    save(image, output, 1)


def draw_figure_2(output: Path):
    image, draw = new_canvas()
    box(draw, (100, 100, 750, 520), "规划阶段可见信息\n\n证据缺口状态\n预执行公开目标\n采集通道标识与动作成本\n版本化成本档案与规划先验", size=43, fill=LIGHT)
    box(draw, (950, 100, 1700, 520), "规划阶段禁止读取\n\n实际可恢复声明标识\n执行前实际通道状态\n遮蔽成员与随机参数\n目标结果标签与最优路径", size=43, dashed=True)
    box(draw, (500, 800, 1300, 1120), "递归字段允许列表 Gate\n仅将公开动作视图交给动作规划过程", size=50, bold=True)
    box(draw, (500, 1360, 1300, 1630), "动作规划过程\n输出目标动作标识或停止动作", size=50)
    box(draw, (180, 1950, 760, 2260), "完整动作对象\n仅在选定动作后读取", size=46)
    box(draw, (1040, 1950, 1620, 2260), "执行过程\n读取实际通道状态并返回证据", size=46)
    arrow(draw, (425, 520), (720, 800), label="允许")
    arrow(draw, (1325, 520), (1080, 800), label="拒绝", dashed=True)
    arrow(draw, (900, 1120), (900, 1360), label="公开视图")
    arrow(draw, (700, 1630), (470, 1950), label="动作标识")
    arrow(draw, (760, 2105), (1040, 2105), label="执行时访问")
    save(image, output, 2)


def draw_figure_3(output: Path):
    image, draw = new_canvas()
    box(draw, (100, 120, 600, 590), "可见安全证据声明\n\n来源组 G1\n来源组 G2\n…\n来源组 Gn", size=46)
    box(draw, (820, 120, 1700, 590), "版本化来源支持规则\n\n对行为节点设置 k-of-n 阈值\nk=1：任一来源支持\nk=n：全部来源支持\n1<k<n：中间支持规则", size=45, fill=LIGHT)
    box(draw, (360, 820, 1440, 1170), "覆盖判定 Gate\n当前独立来源组数量 ≥ k 时，节点确定为已覆盖", size=51, bold=True)
    box(draw, (120, 1430, 820, 1900), "证据缺口状态\n\n已覆盖节点与关联边\n未匹配关键节点\n剩余预算\n动作反馈历史", size=45)
    box(draw, (980, 1430, 1680, 1900), "原始可支撑粒度\n\n节点覆盖率\n关联边覆盖率\n阶段覆盖数量\n关键节点覆盖状态\n中的至少两项", size=43)
    box(draw, (420, 2120, 1380, 2340), "最终输出粒度 = min（原始可支撑粒度，案例级证据支持上限）", size=48, bold=True, fill=LIGHT)
    arrow(draw, (600, 355), (820, 355), label="按来源组汇总")
    arrow(draw, (900, 590), (900, 820))
    arrow(draw, (650, 1170), (470, 1430), label="更新覆盖")
    arrow(draw, (1150, 1170), (1330, 1430), label="计算")
    arrow(draw, (470, 1900), (720, 2120), label="状态约束")
    arrow(draw, (1330, 1900), (1080, 2120), label="上限截断")
    save(image, output, 3)


def draw_figure_4(output: Path):
    image, draw = new_canvas()
    box(draw, (80, 100, 720, 560), "版本化成本档案\n\n档案标识与语义版本\n冻结状态\n动作覆盖清单\n内容摘要值", size=43, fill=LIGHT)
    box(draw, (1080, 100, 1720, 560), "版本化先验档案\n\n先验来源\n缩放参数\n规划过程读取的\n通道可靠性先验", size=43, fill=LIGHT)
    box(draw, (500, 790, 1300, 1110), "正式运行 Gate\n检查冻结状态、动作覆盖、内容摘要和空结果目录", size=49, bold=True)
    box(draw, (80, 1330, 720, 1640), "拒绝正式运行\n草案、缺动作、摘要不一致\n或非空旧结果目录", size=43, dashed=True)
    box(draw, (1080, 1330, 1720, 1640), "动作规划过程\n依据公开状态、成本和规划先验\n选择动作或停止", size=43)
    box(draw, (1080, 1920, 1720, 2270), "采集通道执行\n使用固定执行可靠性配置\n返回新增、零收益或失败反馈", size=43)
    box(draw, (80, 1920, 720, 2270), "更新证据缺口状态\n扣减相应成本\n记录动作与通道反馈", size=43)
    arrow(draw, (400, 560), (700, 790), label="成本档案校验", label_xy=(360, 610))
    arrow(draw, (1400, 560), (1100, 790), label="先验档案校验", label_xy=(1160, 610))
    arrow(draw, (650, 1110), (400, 1330), label="未通过")
    arrow(draw, (1150, 1110), (1400, 1330), label="通过")
    arrow(draw, (1400, 1640), (1400, 1920), label="采集控制指令")
    arrow(draw, (1080, 2095), (720, 2095), label="执行反馈")
    points = [(400, 1920), (400, 1770), (1020, 1770), (1020, 1485), (1080, 1485)]
    for a, b in zip(points[:-2], points[1:-1]):
        draw.line((*a, *b), fill=BLACK, width=LINE)
    arrow(draw, points[-2], points[-1], label="新状态", label_xy=(750, 1710))
    save(image, output, 4)


def draw_figure_5(output: Path):
    image, draw = new_canvas()
    box(draw, (560, 120, 1240, 410), "当前证据缺口状态 s0", size=52, bold=True)
    box(draw, (100, 750, 720, 1050), "动作 A\n即时收益较高", size=48)
    box(draw, (1080, 750, 1700, 1050), "动作 B\n即时收益较低但满足先决条件", size=45)
    box(draw, (100, 1410, 720, 1710), "状态 sA\n关键动作仍未解锁", size=46)
    box(draw, (1080, 1410, 1700, 1710), "状态 sB\n解锁后续关键动作 C", size=46)
    box(draw, (1080, 2020, 1700, 2300), "执行动作 C\n达到目标支持粒度", size=48, fill=LIGHT)
    box(draw, (100, 2020, 720, 2300), "停止或继续高成本采集\n目标未达", size=45, dashed=True)
    arrow(draw, (700, 410), (410, 750), label="短视路径")
    arrow(draw, (1100, 410), (1390, 750), label="多步路径")
    arrow(draw, (410, 1050), (410, 1410))
    arrow(draw, (1390, 1050), (1390, 1410), label="解锁")
    arrow(draw, (410, 1710), (410, 2020))
    arrow(draw, (1390, 1710), (1390, 2020), label="累计价值更高")
    box(draw, (560, 1120, 1240, 1320), "深度 ≥ 2 的搜索比较累计达成概率与累计成本", size=42, bold=True, fill=LIGHT)
    save(image, output, 5)


def main():
    parser = argparse.ArgumentParser(description="Draw Project05 v0.9 Chinese patent figures.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    draw_figure_1(args.output_dir)
    draw_figure_2(args.output_dir)
    draw_figure_3(args.output_dir)
    draw_figure_4(args.output_dir)
    draw_figure_5(args.output_dir)
    for path in sorted(args.output_dir.glob("figure-*.png")):
        print(path)


if __name__ == "__main__":
    main()
