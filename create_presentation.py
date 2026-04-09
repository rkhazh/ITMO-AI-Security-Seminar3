#!/usr/bin/env python3
"""Generate PPTX presentation for LiteLLM security assessment."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Colors
BG_DARK = RGBColor(0x1A, 0x1A, 0x2E)
BG_CARD = RGBColor(0x25, 0x25, 0x3A)
ACCENT = RGBColor(0x42, 0xAF, 0xFA)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xCC, 0xCC, 0xCC)
MUTED = RGBColor(0x99, 0x99, 0x99)
RED = RGBColor(0xFF, 0x44, 0x44)
ORANGE = RGBColor(0xFF, 0xAA, 0x00)
YELLOW = RGBColor(0xFF, 0xDD, 0x57)
GREEN = RGBColor(0x4C, 0xAF, 0x50)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

SLIDE_W = prs.slide_width
SLIDE_H = prs.slide_height


def add_bg(slide):
    """Fill slide background with dark color."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = BG_DARK


def add_textbox(slide, left, top, width, height):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    txBox.text_frame.word_wrap = True
    return txBox.text_frame


def add_paragraph(tf, text, size=18, color=WHITE, bold=False, alignment=PP_ALIGN.LEFT, space_after=Pt(6)):
    if len(tf.paragraphs) == 1 and tf.paragraphs[0].text == "":
        p = tf.paragraphs[0]
    else:
        p = tf.add_paragraph()
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.alignment = alignment
    p.space_after = space_after
    return p


def add_bullet(tf, text, size=16, color=WHITE, bold=False, level=0):
    p = tf.add_paragraph()
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.level = level
    p.space_after = Pt(4)
    return p


def add_rich_bullet(tf, prefix, prefix_color, rest, size=16, level=0):
    """Add a bullet with colored prefix and white rest."""
    p = tf.add_paragraph()
    p.level = level
    p.space_after = Pt(4)
    run1 = p.add_run()
    run1.text = prefix
    run1.font.size = Pt(size)
    run1.font.color.rgb = prefix_color
    run1.font.bold = True
    run2 = p.add_run()
    run2.text = rest
    run2.font.size = Pt(size)
    run2.font.color.rgb = WHITE
    return p


def add_card(slide, left, top, width, height, border_color=None):
    """Add a rounded rectangle card."""
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = BG_CARD
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(2)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


# ============================================================
# SLIDE 1: Title
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
add_bg(slide)

tf = add_textbox(slide, Inches(1), Inches(0.8), Inches(11.3), Inches(1.2))
add_paragraph(tf, "Аудит безопасности LiteLLM v1.81.9-stable", size=36, color=ACCENT, bold=True, alignment=PP_ALIGN.CENTER)
add_paragraph(tf, "Tool-based security assessment инфраструктуры для LLM", size=20, color=MUTED, alignment=PP_ALIGN.CENTER)

tf = add_textbox(slide, Inches(1.5), Inches(2.5), Inches(10.3), Inches(3.8))
add_rich_bullet(tf, "Объект: ", ACCENT, "LiteLLM — unified proxy для 100+ LLM-провайдеров", size=18)
add_rich_bullet(tf, "Предмет: ", ACCENT, "уязвимости кода и зависимостей, влияющие на безопасность LLM-инфраструктуры", size=18)
add_rich_bullet(tf, "Цель: ", ACCENT, "провести security assessment и классифицировать найденные проблемы", size=18)
add_rich_bullet(tf, "Подход: ", ACCENT, "Bandit + Semgrep + pip-audit/OSV + skillscan + ручной триаж", size=18)
add_rich_bullet(tf, "Результат: ", ACCENT, "4 подтвержденные проблемы, 8 потенциальных, ~340 ложных срабатываний отфильтровано", size=18)

tf = add_textbox(slide, Inches(1), Inches(6.3), Inches(11.3), Inches(0.6))
add_paragraph(tf, "Безопасность ИИ / AI Security  •  ИТМО  •  2026-04-09", size=14, color=MUTED, alignment=PP_ALIGN.CENTER)

# ============================================================
# SLIDE 2: Why it matters
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)

tf = add_textbox(slide, Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.8))
add_paragraph(tf, "Почему это важно для AI Security", size=32, color=ACCENT, bold=True, alignment=PP_ALIGN.CENTER)

tf = add_textbox(slide, Inches(1), Inches(1.5), Inches(11.3), Inches(4.5))
add_bullet(tf, "LiteLLM — точка концентрации рисков: API-ключи всех провайдеров, пользовательские данные, prompt-ы проходят через один proxy", size=18)
add_bullet(tf, "Компрометация proxy = компрометация всех подключенных LLM-сервисов (OpenAI, Anthropic, Azure и др.)", size=18)
add_bullet(tf, "Custom guardrails используют exec() — потенциальный вектор удалённого выполнения кода (RCE)", size=18)
add_bullet(tf, "Supply chain: одна уязвимая зависимость (aiohttp) = 10 CVE разом, включая CRLF injection и утечку credentials", size=18)
add_bullet(tf, "Безопасность AI-контура зависит не только от модели, но и от инфраструктуры оркестрации, интеграций и прав доступа", size=18)

card = add_card(slide, Inches(1.5), Inches(5.5), Inches(10.3), Inches(0.8), border_color=ACCENT)
tf2 = card.text_frame
tf2.word_wrap = True
add_paragraph(tf2, "20 000+ GitHub stars  •  используется в production  •  68 прямых зависимостей  •  поддержка 100+ LLM-провайдеров", size=15, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# ============================================================
# SLIDE 3: Methodology
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)

tf = add_textbox(slide, Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.8))
add_paragraph(tf, "Объект и методология исследования", size=32, color=ACCENT, bold=True, alignment=PP_ALIGN.CENTER)

# Table
rows, cols = 5, 4
tbl_shape = slide.shapes.add_table(rows, cols, Inches(0.8), Inches(1.4), Inches(11.7), Inches(2.5))
tbl = tbl_shape.table

# Column widths
tbl.columns[0].width = Inches(2.5)
tbl.columns[1].width = Inches(1.5)
tbl.columns[2].width = Inches(4.5)
tbl.columns[3].width = Inches(3.2)

headers = ["Инструмент", "Версия", "Назначение", "Findings"]
data = [
    ["Bandit", "1.9.4", "SAST, паттерн-матчинг Python", "356 (10 релевантных)"],
    ["Semgrep", "1.157.0", "Семантический SAST, taint tracking", "9 (8 релевантных)"],
    ["pip-audit + OSV", "2.9.0", "Аудит зависимостей (CVE/GHSA)", "15 CVE в 5 пакетах"],
    ["skillscan-security", "—", "Сканер AI agent skills", "Неприменим"],
]

for i, h in enumerate(headers):
    cell = tbl.cell(0, i)
    cell.text = h
    for p in cell.text_frame.paragraphs:
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = ACCENT
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(0x1F, 0x1F, 0x35)

for r, row_data in enumerate(data):
    for c, val in enumerate(row_data):
        cell = tbl.cell(r + 1, c)
        cell.text = val
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(13)
            p.font.color.rgb = WHITE if not (r == 3 and c == 3) else MUTED
        cell.fill.solid()
        cell.fill.fore_color.rgb = BG_CARD

tf = add_textbox(slide, Inches(0.8), Inches(4.1), Inches(11.7), Inches(3.0))
add_rich_bullet(tf, "Версия: ", ACCENT, "LiteLLM v1.81.9-stable, commit a09d3e91", size=16)
add_rich_bullet(tf, "Scope: ", ACCENT, "пакет litellm/, 68 пинированных зависимостей", size=16)
add_rich_bullet(tf, "Триаж: ", ACCENT, "ручная классификация каждого finding → confirmed / potential / false positive", size=16)
add_rich_bullet(tf, "Ограничение: ", ACCENT, "pip-audit не смог разрешить зависимости на Python 3.14 — использован прямой запрос к OSV API", size=16)

# ============================================================
# SLIDE 4: Confirmed vulnerabilities
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)

tf = add_textbox(slide, Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.8))
add_paragraph(tf, "Подтверждённые уязвимости (4)", size=32, color=ACCENT, bold=True, alignment=PP_ALIGN.CENTER)

findings = [
    ("F-01", RED, "HIGH", "exec() в custom guardrails: ", "выполнение произвольного кода. Sandbox через __builtins__={} обходится через ().__class__.__bases__[0].__subclasses__()"),
    ("F-02", ORANGE, "MEDIUM", "Wildcard CORS: ", 'allow_origins=["*"] + allow_credentials=True в FastAPI proxy-сервере'),
    ("F-03", RED, "HIGH", "10 CVE в aiohttp 3.13.3: ", "CRLF injection, утечка Cookie/Proxy-Authorization при redirect, response splitting, DoS"),
    ("F-04", ORANGE, "MEDIUM", "JWT без верификации подписи: ", "verify_signature=False — хрупкая зависимость от SSO flow"),
]

y = Inches(1.4)
for fid, sev_color, sev_text, title, desc in findings:
    card = add_card(slide, Inches(0.8), y, Inches(11.7), Inches(1.15), border_color=sev_color)
    ctf = card.text_frame
    ctf.word_wrap = True
    ctf.paragraphs[0].space_before = Pt(0)

    p = ctf.paragraphs[0]
    run = p.add_run()
    run.text = f"{fid}  "
    run.font.size = Pt(15)
    run.font.color.rgb = ACCENT
    run.font.bold = True

    run = p.add_run()
    run.text = f"{sev_text}  "
    run.font.size = Pt(15)
    run.font.color.rgb = sev_color
    run.font.bold = True

    run = p.add_run()
    run.text = title
    run.font.size = Pt(15)
    run.font.color.rgb = WHITE
    run.font.bold = True

    run = p.add_run()
    run.text = desc
    run.font.size = Pt(14)
    run.font.color.rgb = LIGHT_GRAY

    y += Inches(1.3)

card = add_card(slide, Inches(1.5), Inches(6.6), Inches(10.3), Inches(0.6), border_color=ACCENT)
ctf = card.text_frame
ctf.word_wrap = True
add_paragraph(ctf, "Источники: Bandit (exec, MD5) + Semgrep (JWT, CORS, exec) + pip-audit/OSV (aiohttp CVE)", size=13, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# ============================================================
# SLIDE 5: Potential + False positives
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)

tf = add_textbox(slide, Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.8))
add_paragraph(tf, "Потенциальные проблемы и ложные срабатывания", size=32, color=ACCENT, bold=True, alignment=PP_ALIGN.CENTER)

# Left column: Potential
card_left = add_card(slide, Inches(0.5), Inches(1.4), Inches(5.9), Inches(4.2))
ltf = card_left.text_frame
ltf.word_wrap = True
add_paragraph(ltf, "Потенциальные (8)", size=18, color=ORANGE, bold=True)
potentials = [
    "SQL injection через f-string (8 мест)",
    "XML parsing без defusedxml (XXE)",
    "MD5 для хеширования spend logs",
    "HTTP-запросы без timeout (DoS)",
    "CVE в cryptography 44.0.1",
    "CVE в orjson 3.11.2 (рекурсия → DoS)",
    "CVE в pyjwt 2.10.1 (crit headers)",
    "CVE в Pillow 11.0.0 (OOB write)",
]
for item in potentials:
    add_bullet(ltf, item, size=14, color=LIGHT_GRAY)

# Right column: False positives
card_right = add_card(slide, Inches(6.9), Inches(1.4), Inches(5.9), Inches(4.2))
rtf = card_right.text_frame
rtf.word_wrap = True
add_paragraph(rtf, "Ложные срабатывания (~340)", size=18, color=MUTED, bold=True)

fp_items = [
    ("try/except/pass", "144", "опциональные импорты"),
    ("Tokenizer-строки", "53", '"пароли" вроде <s>, </s>'),
    ("assert usage", "51", "не в production-путях"),
    ("random (не security)", "31", "для request ID"),
    ("Прочие", "~61", "subprocess, binding и др."),
]
for name, count, reason in fp_items:
    p = rtf.add_paragraph()
    p.space_after = Pt(3)
    run = p.add_run()
    run.text = f"{name} — {count}"
    run.font.size = Pt(14)
    run.font.color.rgb = WHITE
    run.font.bold = True
    run = p.add_run()
    run.text = f"  ({reason})"
    run.font.size = Pt(13)
    run.font.color.rgb = MUTED

# Bottom insight
card_bot = add_card(slide, Inches(0.8), Inches(5.9), Inches(11.7), Inches(1.2), border_color=ACCENT)
btf = card_bot.text_frame
btf.word_wrap = True
add_paragraph(btf, "~95% Bandit-находок — шум. Ручной триаж необходим.", size=15, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_paragraph(btf, "Semgrep нашёл JWT/CORS (Bandit не нашёл)  •  Bandit нашёл SQL/timeout (Semgrep не нашёл)", size=14, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)

# ============================================================
# SLIDE 6: Conclusions
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)

tf = add_textbox(slide, Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.8))
add_paragraph(tf, "Выводы для защиты AI-систем", size=32, color=ACCENT, bold=True, alignment=PP_ALIGN.CENTER)

tf = add_textbox(slide, Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.0))

conclusions = [
    ("exec() в guardrails — самый критичный риск: ", "sandbox bypass тривиален, требуется контейнерная изоляция или AST-based whitelist"),
    ("Supply chain (aiohttp) — скрытая атакуемая поверхность: ", "10 CVE в одной зависимости, которую используют все HTTP-запросы к провайдерам"),
    ("Статический анализ не покрывает runtime-риски: ", "авторизация, multi-tenant isolation, SSRF, prompt injection, обход guardrails"),
    ("Взаимодополняемость инструментов: ", "ни Bandit, ни Semgrep по отдельности не нашли все проблемы — комбинация даёт лучшее покрытие"),
    ("skillscan неприменим: ", "несоответствие threat model (AI agent skills vs. инфраструктурный код) — важно выбирать инструменты по типу проекта"),
]

for title, desc in conclusions:
    p = tf.add_paragraph()
    p.space_after = Pt(10)
    run = p.add_run()
    run.text = title
    run.font.size = Pt(17)
    run.font.color.rgb = WHITE
    run.font.bold = True
    run = p.add_run()
    run.text = desc
    run.font.size = Pt(16)
    run.font.color.rgb = LIGHT_GRAY

# ============================================================
# SLIDE 7: Recommendations
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_bg(slide)

tf = add_textbox(slide, Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.8))
add_paragraph(tf, "Практические рекомендации", size=32, color=ACCENT, bold=True, alignment=PP_ALIGN.CENTER)

sections = [
    (GREEN, "Quick wins (низкие усилия, высокий эффект)", [
        "Обновить aiohttp ≥ 3.13.4 — закрывает 10 CVE",
        "Обновить orjson ≥ 3.11.6, pyjwt ≥ 2.12.0",
        "Добавить timeout ко всем HTTP-запросам",
        "Заменить MD5 на SHA-256 для spend logs",
    ]),
    (ORANGE, "Структурные изменения", [
        "Заменить exec() на AST whitelist или sandboxed subprocess",
        "Настроить CORS с явным списком доверенных origins",
        "Добавить явную верификацию JWT-подписи",
        "Заменить xml.etree на defusedxml",
    ]),
    (ACCENT, "Процесс", [
        "Включить SAST в CI/CD pipeline",
        "Дополнить DAST/пентестом для runtime-рисков (auth, SSRF, prompt injection)",
        "Полный аудит транзитивных зависимостей на совместимой Python-версии",
    ]),
]

y = Inches(1.3)
for sec_color, sec_title, items in sections:
    tf = add_textbox(slide, Inches(0.8), y, Inches(11.7), Inches(0.4))
    add_paragraph(tf, sec_title, size=18, color=sec_color, bold=True)
    y += Inches(0.4)

    tf = add_textbox(slide, Inches(1.2), y, Inches(11.3), Inches(len(items) * 0.35))
    for item in items:
        add_bullet(tf, item, size=15, color=LIGHT_GRAY)
    y += Inches(len(items) * 0.35 + 0.15)


# Save
output_path = "/home/user/ITMO-AI-Security-Seminar3/presentation.pptx"
prs.save(output_path)
print(f"Saved: {output_path}")
