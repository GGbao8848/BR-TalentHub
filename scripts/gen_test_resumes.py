"""给现有简历记录生成带文字内容的测试 PDF（内容无意义，仅用于验证查看器渲染）。"""
import sqlite3
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "br_talenthub.db"

pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))

DUTIES = ["设备调试", "产线维护", "工艺参数优化", "客户技术支持", "质量检测", "自动化改造", "售后维修", "项目协调"]

lorem_lines = [
    "工作中主要负责现场设备安装、调试与验收，跟进客户需求并输出技术方案。",
    "参与多批次产线改造项目，完成设备参数标定与运行数据记录，汇总形成文档。",
    "负责产品售后问题响应，跨部门协调资源，确保问题闭环与客户满意度。",
    "独立完成工艺文件编制与更新，配合质量部门开展首件检验与过程审核。",
    "协助完成自动化产线升级，包括电气图纸核对、PLC 程序上载与联机测试。",
    "定期整理设备点检记录与故障台账，输出月度运维报告并推动改进事项。",
    "参与新机型试制，负责样机装配、功能测试及问题清单的跟踪关闭。",
    "支持区域销售团队完成技术交流与方案宣讲，整理行业竞品信息。",
]


def build_pdf(path: Path, name: str, position: str, school: str, phone: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    c.setFont("STSong-Light", 22)
    c.drawString(28 * mm, height - 30 * mm, f"{name}  个人简历")
    c.setFont("STSong-Light", 12)
    c.setStrokeColorRGB(0.15, 0.4, 0.9)
    c.setLineWidth(1.2)
    c.line(28 * mm, height - 36 * mm, width - 28 * mm, height - 36 * mm)

    y = height - 48 * mm
    info_lines = [
        f"姓名：{name}",
        f"应聘岗位：{position}",
        f"毕业院校：{school}",
        f"联系电话：{phone}",
        "期望城市：苏州",
        "求职意向：全职",
    ]
    c.setFont("STSong-Light", 13)
    for line in info_lines:
        c.drawString(32 * mm, y, line)
        y -= 11 * mm

    y -= 6 * mm
    c.setFont("STSong-Light", 16)
    c.drawString(32 * mm, y, "自我评价")
    y -= 12 * mm

    style = ParagraphStyle(
        "body",
        fontName="STSong-Light",
        fontSize=11.5,
        leading=18,
        wordWrap="CJK",
    )
    for duty, text in zip(DUTIES[:5], lorem_lines[:5]):
        c.setFont("STSong-Light", 12.5)
        c.drawString(32 * mm, y, f"· {duty}")
        y -= 8 * mm
        p = Paragraph(text, style)
        w, h = p.wrap(width - 64 * mm, 60 * mm)
        p.drawOn(c, 36 * mm, y - h)
        y -= h + 6 * mm
        if y < 60 * mm:  # 换页
            c.showPage()
            c.setFont("STSong-Light", 12)
            y = height - 40 * mm

    c.showPage()
    c.save()
    return path.stat().st_size


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT id, name, phone, position, school_id, filepath FROM resumes").fetchall()
    print(f"共 {len(rows)} 条简历")

    school_map = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM schools").fetchall()}
    done = skipped = 0
    for row in rows:
        fp = row["filepath"]
        if not fp:
            skipped += 1
            continue
        path = BASE_DIR / fp
        school = school_map.get(row["school_id"], "未知院校")
        try:
            size = build_pdf(path, row["name"] or "未留名", row["position"] or "通用岗位", school, row["phone"] or "")
            conn.execute("UPDATE resumes SET filesize=? WHERE id=?", (size, row["id"]))
            done += 1
        except Exception as e:  # noqa: BLE001
            print(f"  跳过 {fp}: {e}")
            skipped += 1
    conn.commit()
    conn.close()
    print(f"生成 {done} 份，跳过 {skipped} 份")


if __name__ == "__main__":
    main()
