"""
Geração de PDF de Ordem de Serviço Preditiva — Layout Clean.
Usa ReportLab (puro Python).
"""
import json
from pathlib import Path

PDF_DIR = Path(__file__).parent / "pdfs"
PDF_DIR.mkdir(exist_ok=True)


def generate_pdf(os_obj) -> str | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            Table, TableStyle, HRFlowable, KeepTogether,
        )
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    except ImportError:
        print("[PDF] ReportLab nao instalado. Execute: pip3 install reportlab")
        return None

    pdf_filename = f"Ordem de Servico {os_obj.os_number}.pdf"
    pdf_path = str(PDF_DIR / pdf_filename)
    W, _ = A4

    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        leftMargin=2.0 * cm, rightMargin=2.0 * cm,
        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
    )

    INK      = colors.HexColor("#0f172a")
    BLUE     = colors.HexColor("#3b6cf4")
    BLUE_LT  = colors.HexColor("#eff4ff")
    RED      = colors.HexColor("#dc2626")
    RED_LT   = colors.HexColor("#fef2f2")
    AMBER    = colors.HexColor("#d97706")
    AMBER_LT = colors.HexColor("#fffbeb")
    GREEN    = colors.HexColor("#059669")
    GREEN_LT = colors.HexColor("#f0fdf4")
    GRAY     = colors.HexColor("#64748b")
    GRAY_LT  = colors.HexColor("#f8fafc")
    BORDER   = colors.HexColor("#e2e8f0")
    WHITE    = colors.white

    is_crit   = os_obj.priority == "critica"
    PRI_COLOR = RED if is_crit else AMBER
    PRI_LT    = RED_LT if is_crit else AMBER_LT
    PRI_LABEL = ("CRITICA" if is_crit else "ALTA").upper()

    st = getSampleStyleSheet()

    def S(n, **k):
        return ParagraphStyle(n, parent=st["Normal"], **k)

    anomalies = json.loads(os_obj.anomalies) if os_obj.anomalies else []
    actions   = json.loads(os_obj.actions)   if os_obj.actions   else []

    W_FULL = W - 4.0 * cm
    story  = []

    # ── CABEÇALHO ────────────────────────────────────────────────────────────
    header = Table([[
        Paragraph(
            "ORDEM DE SERVIÇO PREDITIVA",
            S("h1", fontSize=13, fontName="Helvetica-Bold", textColor=WHITE),
        ),
        Paragraph(
            os_obj.os_number,
            S("h2", fontSize=12, fontName="Helvetica-Bold", textColor=WHITE, alignment=TA_RIGHT),
        ),
    ]], colWidths=[W_FULL * 0.58, W_FULL * 0.42])
    header.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BLUE),
        ("PADDING",    (0, 0), (-1, -1), 12),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(header)

    sub = Table([[
        Paragraph(
            f"Emitida em {os_obj.created_at.strftime('%d/%m/%Y')} às "
            f"{os_obj.created_at.strftime('%H:%M:%S')}  ·  Manutenção Preditiva Automatizada",
            S("sub", fontSize=8, fontName="Helvetica", textColor=GRAY),
        ),
        Paragraph(
            f"PRIORIDADE {PRI_LABEL}",
            S("pri", fontSize=9, fontName="Helvetica-Bold", textColor=PRI_COLOR, alignment=TA_RIGHT),
        ),
    ]], colWidths=[W_FULL * 0.62, W_FULL * 0.38])
    sub.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRAY_LT),
        ("PADDING",    (0, 0), (-1, -1), 8),
        ("LINEBELOW",  (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    story.append(sub)
    story.append(Spacer(1, 0.65 * cm))

    def section_title(text, color=BLUE):
        return [
            Paragraph(text, S("st", fontSize=9, fontName="Helvetica-Bold",
                              textColor=color, spaceAfter=3)),
            HRFlowable(width="100%", thickness=0.8, color=color, spaceAfter=8),
        ]

    def info_row(label, value):
        return Table([[
            Paragraph(label, S("lbl", fontSize=7, fontName="Helvetica", textColor=GRAY)),
            Paragraph(str(value), S("val", fontSize=10, fontName="Helvetica-Bold", textColor=INK)),
        ]], colWidths=[4.0 * cm, W_FULL - 4.0 * cm])

    # ── EQUIPAMENTO ──────────────────────────────────────────────────────────
    story += section_title("EQUIPAMENTO")
    equip_rows = [
        ("Equipamento",        os_obj.equipment),
        ("Localização",        os_obj.location),
        ("Tipo de Manutenção", "Preditiva — Geração Automática por Sensor"),
    ]
    for i, (lbl, val) in enumerate(equip_rows):
        t = info_row(lbl, val)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GRAY_LT if i % 2 == 0 else WHITE),
            ("PADDING",    (0, 0), (-1, -1), 10),
            ("BOX",        (0, 0), (-1, -1), 0.5, BORDER),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.15 * cm))
    story.append(Spacer(1, 0.55 * cm))

    # ── LEITURAS ─────────────────────────────────────────────────────────────
    story += section_title("LEITURAS NO MOMENTO DA DETECÇÃO")

    col_w = W_FULL / 4
    readings_data = [
        [
            Paragraph("TEMPERATURA", S("rl1", fontSize=7, fontName="Helvetica",
                                       textColor=GRAY, alignment=TA_CENTER)),
            Paragraph("VIBRAÇÃO", S("rl2", fontSize=7, fontName="Helvetica",
                                     textColor=GRAY, alignment=TA_CENTER)),
            Paragraph("CORRENTE", S("rl3", fontSize=7, fontName="Helvetica",
                                     textColor=GRAY, alignment=TA_CENTER)),
            Paragraph("TENSÃO", S("rl4", fontSize=7, fontName="Helvetica",
                                   textColor=GRAY, alignment=TA_CENTER)),
        ],
        [
            Paragraph(f"{os_obj.temperature:.1f}", S("rv1", fontSize=18, fontName="Helvetica-Bold",
                                                       textColor=RED, alignment=TA_CENTER)),
            Paragraph(f"{os_obj.vibration:.2f}", S("rv2", fontSize=18, fontName="Helvetica-Bold",
                                                    textColor=colors.HexColor("#7c3aed"), alignment=TA_CENTER)),
            Paragraph(f"{os_obj.current:.2f}", S("rv3", fontSize=18, fontName="Helvetica-Bold",
                                                  textColor=AMBER, alignment=TA_CENTER)),
            Paragraph(f"{os_obj.voltage:.1f}", S("rv4", fontSize=18, fontName="Helvetica-Bold",
                                                  textColor=GREEN, alignment=TA_CENTER)),
        ],
        [
            Paragraph("°C",   S("ru1", fontSize=8, textColor=GRAY, alignment=TA_CENTER)),
            Paragraph("mm/s", S("ru2", fontSize=8, textColor=GRAY, alignment=TA_CENTER)),
            Paragraph("A",    S("ru3", fontSize=8, textColor=GRAY, alignment=TA_CENTER)),
            Paragraph("V",    S("ru4", fontSize=8, textColor=GRAY, alignment=TA_CENTER)),
        ],
    ]
    rd = Table(readings_data, colWidths=[col_w] * 4)
    rd.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), RED_LT),
        ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#f5f3ff")),
        ("BACKGROUND", (2, 0), (2, -1), AMBER_LT),
        ("BACKGROUND", (3, 0), (3, -1), GREEN_LT),
        ("BOX",        (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID",  (0, 0), (-1, -1), 0.5, BORDER),
        ("PADDING",    (0, 0), (-1, -1), 10),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 1), (-1, 1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 4),
    ]))
    story.append(rd)
    story.append(Spacer(1, 0.65 * cm))

    # ── ANOMALIAS ────────────────────────────────────────────────────────────
    story += section_title("ANOMALIAS DETECTADAS", PRI_COLOR)
    for a in (anomalies or ["Sem anomalias registradas"]):
        row = Table([[
            Paragraph("!", S("ai", fontSize=10, fontName="Helvetica-Bold",
                             textColor=PRI_COLOR, alignment=TA_CENTER)),
            Paragraph(a, S("at", fontSize=9, fontName="Helvetica", textColor=INK)),
        ]], colWidths=[0.8 * cm, W_FULL - 0.8 * cm])
        row.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PRI_LT),
            ("BOX",        (0, 0), (-1, -1), 0.5, BORDER),
            ("PADDING",    (0, 0), (-1, -1), 10),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(row)
        story.append(Spacer(1, 0.2 * cm))
    story.append(Spacer(1, 0.45 * cm))

    # ── AÇÕES ────────────────────────────────────────────────────────────────
    story += section_title("AÇÕES SUGERIDAS", GREEN)
    for ac in (actions or ["Aguardando diagnostico tecnico"]):
        row = Table([[
            Paragraph("→", S("gi", fontSize=10, fontName="Helvetica-Bold",
                             textColor=GREEN, alignment=TA_CENTER)),
            Paragraph(ac, S("gt", fontSize=9, fontName="Helvetica", textColor=INK)),
        ]], colWidths=[0.8 * cm, W_FULL - 0.8 * cm])
        row.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), GREEN_LT),
            ("BOX",        (0, 0), (-1, -1), 0.5, BORDER),
            ("PADDING",    (0, 0), (-1, -1), 10),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(row)
        story.append(Spacer(1, 0.2 * cm))

    story.append(Spacer(1, 0.85 * cm))

    # ── ASSINATURAS ──────────────────────────────────────────────────────────
    sig_col = W_FULL / 3
    sig_line_w = sig_col - 1.0 * cm

    def sig_block(title):
        return Table([
            [Spacer(1, 0.5 * cm)],
            [HRFlowable(width=sig_line_w, thickness=0.5, color=BORDER, spaceAfter=4)],
            [Paragraph(title, S(f"sn_{title[:4]}", fontSize=8, textColor=GRAY, alignment=TA_CENTER))],
        ], colWidths=[sig_col])

    sigs = Table(
        [[sig_block("Técnico Responsável"), sig_block("Supervisor de Manutenção"), sig_block("Data de Conclusão")]],
        colWidths=[sig_col] * 3,
    )
    sigs.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(KeepTogether(sigs))

    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=4, spaceAfter=6))
    story.append(Table([[
        Paragraph("Sistema de Manutenção Preditiva — CONFIMINAS",
                  S("f1", fontSize=7, textColor=GRAY)),
        Paragraph(
            f"{os_obj.os_number}  ·  {os_obj.created_at.strftime('%d/%m/%Y %H:%M')}",
            S("f2", fontSize=7, textColor=GRAY, alignment=TA_RIGHT),
        ),
    ]], colWidths=[W_FULL * 0.58, W_FULL * 0.42]))

    doc.build(story)
    print(f"[PDF] Gerado: {pdf_path}")
    return pdf_path
