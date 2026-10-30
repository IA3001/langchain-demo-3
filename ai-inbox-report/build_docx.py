# -*- coding: utf-8 -*-
"""构建 AI Inbox 项目报告 DOCX（python-docx，中文课程论文格式）"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

BASE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE, "assets")
OUT = os.path.join(BASE, "AI-Inbox-项目报告.docx")

doc = Document()

# ---------- 页面 A4 + 页边距 ----------
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(2.54)
sec.left_margin = sec.right_margin = Cm(2.8)

# ---------- 字体工具 ----------

def set_font(run, ascii_font="Times New Roman", ea_font="宋体", size=12,
             bold=False, italic=False, color=None):
    run.font.name = ascii_font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)
    r = run._element.rPr
    rFonts = r.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        r.append(rFonts)
    rFonts.set(qn("w:ascii"), ascii_font)
    rFonts.set(qn("w:hAnsi"), ascii_font)
    rFonts.set(qn("w:eastAsia"), ea_font)


def para(text="", size=12, bold=False, align=None, ea="宋体", ascii_f="Times New Roman",
         space_after=6, first_indent=None, color=None):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    if first_indent:
        p.paragraph_format.first_line_indent = Pt(first_indent)
    if text:
        set_font(p.add_run(text), ascii_font=ascii_f, ea_font=ea, size=size, bold=bold, color=color)
    return p


def heading1(num, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(10)
    set_font(p.add_run(f"{num}  {text}"), ascii_font="Arial", ea_font="黑体", size=16, bold=True)
    return p


def heading2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(6)
    set_font(p.add_run(text), ascii_font="Arial", ea_font="黑体", size=14, bold=True)
    return p


def figure(path, caption, width_cm=15.2):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    run = p.add_run()
    run.add_picture(path, width=Cm(width_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(12)
    set_font(cap.add_run(caption), ea_font="宋体", size=10.5, bold=True)


def three_line_table(headers, rows, widths=None):
    t = doc.add_table(rows=1 + len(rows), cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER

    def borders(row, top=None, bottom=None):
        for cell in row.cells:
            tcPr = cell._tc.get_or_add_tcPr()
            tcB = tcPr.find(qn("w:tcBorders"))
            if tcB is None:
                tcB = OxmlElement("w:tcBorders")
                tcPr.append(tcB)
            for edge, sz in (("top", top), ("bottom", bottom)):
                if sz is not None:
                    el = tcB.find(qn(f"w:{edge}"))
                    if el is None:
                        el = OxmlElement(f"w:{edge}")
                        tcB.append(el)
                    el.set(qn("w:val"), "single")
                    el.set(qn("w:sz"), str(sz))
                    el.set(qn("w:color"), "000000")

    hdr = t.rows[0]
    for i, h in enumerate(headers):
        c = hdr.cells[i]
        c.text = ""
        set_font(c.paragraphs[0].add_run(h), ea_font="黑体", size=10.5, bold=True)
        c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    borders(hdr, top=12, bottom=6)
    for ri, row in enumerate(rows):
        tr = t.rows[ri + 1]
        for ci, val in enumerate(row):
            c = tr.cells[ci]
            c.text = ""
            set_font(c.paragraphs[0].add_run(str(val)), ea_font="宋体", size=10.5)
        if ri == len(rows) - 1:
            borders(tr, bottom=12)
    if widths:
        for ci, w in enumerate(widths):
            for r in t.rows:
                r.cells[ci].width = Cm(w)
    return t


def code_block(lines):
    for line in lines:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.left_indent = Pt(18)
        pPr = p._p.get_or_add_pPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:fill"), "F2F0EA")
        pPr.append(shd)
        set_font(p.add_run(line if line else " "), ascii_font="Consolas", ea_font="等线", size=9)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def caption(text, space_after=10):
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(space_after)
    set_font(cap.add_run(text), ea_font="宋体", size=10.5, bold=True)


# ================= 封面标题 =================
t = para("AI Inbox", size=26, bold=True, ea="黑体", ascii_f="Arial", space_after=8)
para("基于 LangChain 与云端大模型的个人智能收件箱", size=15, ea="宋体", space_after=30)

# ================= 1 项目简介 =================
heading1("1", "项目简介")
para("AI Inbox（个人智能收件箱）是一个“想到什么就说什么”的信息收纳工具。用户在一个对话框里随意输入——可以是待办事项、一闪而过的灵感，或纯粹一句闲聊——系统在后台自动完成三件事：理解语义、结构化提取、分类入库。", first_indent=24)
para("项目严格遵循“纯云端 LLM + 极简工程”的约束：不使用任何本地模型，不引入 Vue/React 等前端框架，仅用 FastAPI、LangChain、SQLite 与单文件原生 HTML 完成全部功能。核心价值在于用 LangChain 的 with_structured_output 能力，把非结构化的自然语言可靠地转换为可存储、可管理的结构化数据。", first_indent=24)
para("项目规模：核心源文件 7 个；输入三分类（待办/笔记/闲聊）；12+ 个 REST API 接口；0 前端框架依赖。", first_indent=24)

# ================= 2 需求分析 =================
heading1("2", "需求分析与功能设计")
para("产品形态围绕“一个大输入框”展开，功能按「对话区」与「数据管理区」两条线设计，具体如表 1 所示。", first_indent=24)
caption("表 1  功能清单", space_after=4)
three_line_table(
    ["功能模块", "功能点", "说明"],
    [
        ["智能对话", "流式回复", "SSE 协议逐字输出，带打字动画"],
        ["智能对话", "语义三分类", "待办/笔记/闲聊，闲聊只回复不入库"],
        ["智能对话", "提取状态条", "对话流内实时显示提取结果"],
        ["智能对话", "对话持久化", "消息全部存入 SQLite，刷新不丢失"],
        ["任务清单", "AI 自动捕获", "提取待办并去除冗余语气词"],
        ["任务清单", "手动增删改", "回车添加、双击行内编辑、两步删除确认"],
        ["任务清单", "完成切换", "勾选切换完成态，完成项置灰沉底"],
        ["灵感笔记", "AI 自动捕获", "识别有记录价值的想法、灵感、备忘"],
        ["灵感笔记", "手动增删改", "与任务清单一致的管理能力"],
        ["系统设置", "模型热配置", "页内配置 Key/URL/模型名，保存即生效"],
    ],
    widths=[3.2, 4.0, 8.2],
)

# ================= 3 系统架构 =================
heading1("3", "系统架构")
para("系统采用经典的前后端同构单体架构：FastAPI 同时承担 API 服务与静态文件托管，前端为单文件原生 HTML，数据层使用 SQLite 内嵌数据库，LLM 调用通过 OpenAI SDK 兼容协议访问云端模型，整体结构如图 1 所示。", first_indent=24)
figure(os.path.join(ASSETS, "arch.png"), "图 1  系统架构图")
para("各层技术选型与职责划分如表 2 所示。", first_indent=24)
caption("表 2  技术选型", space_after=4)
three_line_table(
    ["分层", "技术选型", "职责"],
    [
        ["前端展示", "原生 HTML/JS + Tailwind CDN", "单文件界面，Fetch 交互，SSE 流式渲染"],
        ["接口服务", "FastAPI + Uvicorn", "REST API、SSE 流式响应、静态托管"],
        ["智能层", "LangChain + langchain-openai", "结构化提取链，Pydantic 约束输出"],
        ["大模型", "DeepSeek（OpenAI 兼容）", "纯云端推理，无本地模型"],
        ["数据持久化", "SQLite3（Python 内置）", "四张表：todos/notes/messages/settings"],
        ["配置管理", "python-dotenv + DB 设置表", ".env 兜底，页内设置热更新优先"],
    ],
    widths=[3.0, 5.6, 6.8],
)

# ================= 4 核心流程 =================
heading1("4", "核心流程")
para("一次对话输入的处理链路是本项目最核心的设计：它把“结构化提取”与“流式对话”两条链路合并为一次请求——先判定语义类型并入库，再基于提取结果生成流式回复，完整时序如图 2 所示。", first_indent=24)
figure(os.path.join(ASSETS, "seq.png"), "图 2  核心流程时序图", width_cm=13.5)

# ================= 5 界面展示 =================
heading1("5", "界面展示")
para("界面采用暖白纸质感设计：米白底色、纸白卡片、暖灰文字，全程黑白灰三色、无彩色装饰。布局为「左对话 + 右清单」双卡片结构，右卡片内以标签页切换任务清单与灵感笔记，分别如图 3、图 4 所示。", first_indent=24)
figure(os.path.join(ASSETS, "ui_main_1920x1080.png"), "图 3  主界面：AI 对话 + 任务清单")
figure(os.path.join(ASSETS, "ui_notes_1920x1080.png"), "图 4  灵感笔记标签页")
para("细节设计：待回复时显示三点打字动画；提取结果以居中状态条呈现；所有删除/清空操作采用两步点击确认加页面内 toast 提示，不依赖原生弹窗，兼容禁用 prompt/confirm 的嵌入式浏览器环境。", first_indent=24)

# ================= 6 关键实现 =================
heading1("6", "关键实现")
heading2("6.1  Pydantic 模型驱动的结构化提取")
para("用 Literal 将输出约束为三个互斥类型，配合字段级 description 提示模型清洗内容，这是“说话不必正式，记录自动整洁”的关键。", first_indent=24)
code_block([
    "from typing import Literal",
    "from pydantic import BaseModel, Field",
    "",
    "class ExtractedData(BaseModel):",
    '    """从用户输入中提取出的结构化信息"""',
    '    type: Literal["todo", "note", "chat"] = Field(',
    '        description="todo=待办；note=值得记录的信息；chat=闲聊（不记录）")',
    "    content: str = Field(",
    '        description="核心内容，去除语气词冗余；chat 类型给空字符串")',
    "",
    "structured_llm = llm.with_structured_output(ExtractedData)",
])
heading2("6.2  SSE 流式对话")
para("后端以 StreamingResponse 推送标准 SSE 事件流：先发 extracted 事件驱动状态条，再逐 token 推送 delta，协议结构化、可扩展。", first_indent=24)
code_block([
    "def generate():",
    '    yield _sse({"event": "extracted", "type": result.type,',
    '                "content": result.content})',
    '    reply = ""',
    "    for chunk in stream_reply(text, result, history):",
    "        reply += chunk",
    '        yield _sse({"event": "delta", "text": chunk})',
    "    if reply.strip():",
    '        database.add_message("assistant", reply)',
    '    yield _sse({"event": "done"})',
    "",
    'return StreamingResponse(generate(), media_type="text/event-stream")',
])
heading2("6.3  配置热更新")
para("模型配置存于 SQLite settings 表，读取时数据库优先、.env 兜底；保存后重建提取链即时生效，实现“不改代码、不重启服务”切换模型。", first_indent=24)

# ================= 7 测试与验证 =================
heading1("7", "测试与验证")
para("开发过程中对关键路径做了系统性的接口实测与浏览器端到端验证，结果如表 3 所示。", first_indent=24)
caption("表 3  测试用例与结果", space_after=4)
three_line_table(
    ["测试项", "输入 / 操作", "预期结果", "实测"],
    [
        ["待办提取", "“帮我记一下明天要买牛奶”", "入库 todo：明天买牛奶", "通过"],
        ["笔记提取", "“这个产品可以用区块链重新做一遍”", "入库 note", "通过"],
        ["闲聊不记录", "“你能帮我做什么”", "chat，清单无新增", "通过"],
        ["流式输出", "任意输入", "extracted→delta→done", "通过"],
        ["对话持久化", "发送消息后刷新页面", "气泡与状态条完整恢复", "通过"],
        ["手动管理", "增删改、完成切换", "列表实时刷新", "通过"],
        ["异常兜底", "空输入/未配置 Key", "400/502 + 中文提示", "通过"],
        ["UI 兼容", "禁用原生弹窗的环境", "行内编辑、两步确认可用", "通过"],
    ],
    widths=[2.8, 5.6, 5.2, 1.8],
)

# ================= 8 从零运行 =================
heading1("8", "从零运行")
para("（1）安装依赖：pip install -r requirements.txt；", first_indent=24)
para("（2）配置密钥：复制 .env.example 为 .env 并填入 OPENAI_API_KEY，也可启动后在页面右上角“设置”中填写，保存即生效；", first_indent=24)
para("（3）启动服务：uvicorn main:app --reload；", first_indent=24)
para("（4）访问应用：浏览器打开 http://127.0.0.1:8000/。", first_indent=24)
code_block([
    "# .env 配置示例",
    "OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx",
    "OPENAI_BASE_URL=https://api.deepseek.com/v1",
    "MODEL_NAME=deepseek-chat",
])

# ================= 9 总结 =================
heading1("9", "总结与展望")
para("本项目以约七百行代码完成了一个端到端可用的 AI 信息收纳工具：LangChain 结构化输出解决了“自然语言到结构化数据”的可靠性问题，SSE 流式协议保证了对话体验，SQLite 持久化让数据可积累、可管理，极简前端则把维护成本压到最低。", first_indent=24)
para("可扩展方向：① 待办增加截止时间字段，由 LLM 一并抽取并支持到期提醒；② 引入 LangChain Retrieval，对历史笔记做语义检索与“回忆”问答；③ 增加多用户与登录，SQLite 平滑迁移至 PostgreSQL。", first_indent=24)
para("仓库地址：https://github.com/IA3001/langchain-demo-3", first_indent=24)

doc.save(OUT)
print("saved:", OUT, os.path.getsize(OUT), "bytes")
