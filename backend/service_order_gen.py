"""
Geração de PDF de Ordem de Serviço Preditiva — ConfiMinas Engenharia.
Estética: documento técnico premium — branco, sem fundos decorativos,
cores apenas funcionais, tipografia com hierarquia clara, espaçamento generoso.
"""
import json
from pathlib import Path

PDF_DIR   = Path(__file__).parent / "pdfs"
LOGO_PATH = Path(__file__).parent.parent / "dashboard" / "public" / "login-logo.png"
PDF_DIR.mkdir(exist_ok=True)


def generate_pdf(os_obj) -> str | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm, mm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            Table, TableStyle, HRFlowable, KeepTogether, Image,
        )
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    except ImportError:
        print("[PDF] ReportLab nao instalado. Execute: pip3 install reportlab")
        return None

    pdf_filename = f"Ordem de Servico {os_obj.os_number}.pdf"
    pdf_path     = str(PDF_DIR / pdf_filename)
    PAGE_W, _    = A4

    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        leftMargin=2.0 * cm, rightMargin=2.0 * cm,
        topMargin=1.6 * cm, bottomMargin=1.8 * cm,
    )

    # ── Paleta funcional (cores apenas onde informam algo) ───────────────────
    INK        = colors.HexColor("#0f172a")   # texto principal
    INK_SOFT   = colors.HexColor("#334155")   # texto secundário
    GRAY       = colors.HexColor("#64748b")   # labels, hints
    GRAY_LT    = colors.HexColor("#f1f5f9")   # fundo alternado leve
    BORDER     = colors.HexColor("#e2e8f0")   # bordas suaves
    RULE       = colors.HexColor("#cbd5e1")   # linhas de seção
    ACCENT     = colors.HexColor("#2563eb")   # azul — só linhas e seções
    RED        = colors.HexColor("#dc2626")
    RED_LT     = colors.HexColor("#fff1f1")
    RED_RULE   = colors.HexColor("#fca5a5")
    AMBER      = colors.HexColor("#b45309")
    AMBER_LT   = colors.HexColor("#fffbeb")
    AMBER_RULE = colors.HexColor("#fcd34d")
    GREEN      = colors.HexColor("#059669")
    GREEN_LT   = colors.HexColor("#f0fdf4")
    GREEN_RULE = colors.HexColor("#6ee7b7")
    PURPLE     = colors.HexColor("#6d28d9")
    PURPLE_LT  = colors.HexColor("#f5f3ff")
    WHITE      = colors.white

    is_crit   = os_obj.priority == "critica"
    PRI_COLOR = RED   if is_crit else AMBER
    PRI_LT    = RED_LT if is_crit else AMBER_LT
    PRI_RULE  = RED_RULE if is_crit else AMBER_RULE
    PRI_LABEL = "PRIORIDADE CRÍTICA" if is_crit else "PRIORIDADE ALTA"

    _ss = getSampleStyleSheet()

    def S(name, **kw):
        return ParagraphStyle(name, parent=_ss["Normal"], **kw)

    anomalies = json.loads(os_obj.anomalies) if os_obj.anomalies else []
    actions   = json.loads(os_obj.actions)   if os_obj.actions   else []

    W     = PAGE_W - 4.0 * cm
    story = []

    # ═══════════════════════════════════════════════════════════════════════════
    # CABEÇALHO — sem fundo colorido
    # Layout: [logo grande] | [título + subtítulo] | [nº OS + badge prioridade]
    # ═══════════════════════════════════════════════════════════════════════════

    # Logo — proporcional, mais larga
    logo_w = 6.0 * cm
    logo_cell: list = []
    if LOGO_PATH.is_file():
        try:
            img = Image(str(LOGO_PATH))
            desired_w  = logo_w
            scale      = desired_w / img.drawWidth
            img.drawHeight = img.drawHeight * scale
            img.drawWidth  = desired_w
            logo_cell = [img]
        except Exception:
            logo_cell = []

    title_block = [
        Paragraph(
            "ORDEM DE SERVIÇO",
            S("hd_tit", fontSize=12, fontName="Helvetica-Bold",
              textColor=INK, spaceAfter=5, leading=15),
        ),
        Paragraph(
            (f'Emitida em <b>{os_obj.created_at.strftime("%d/%m/%Y")}</b> às '
             f'{os_obj.created_at.strftime("%H:%M:%S")}')
            if os_obj.created_at else "Ordem de Serviço Preditiva",
            S("hd_sub", fontSize=8, fontName="Helvetica", textColor=GRAY,
              spaceAfter=3),
        ),
        Paragraph(
            "Manutenção Preditiva Automatizada",
            S("hd_sub2", fontSize=8, fontName="Helvetica", textColor=GRAY),
        ),
    ]

    os_block = [
        Paragraph(
            f"<nobr>{os_obj.os_number}</nobr>",
            S("hd_os", fontSize=9, fontName="Helvetica-Bold",
              textColor=INK, alignment=TA_RIGHT, spaceAfter=8),
        ),
        # Badge de prioridade — borda colorida, fundo muito leve
        Table(
            [[Paragraph(PRI_LABEL,
                        S("pri_lbl", fontSize=8, fontName="Helvetica-Bold",
                          textColor=PRI_COLOR, alignment=TA_CENTER))]],
            colWidths=[3.6 * cm],
            hAlign='RIGHT',
        ),
    ]
    os_block[1].setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 1.2, PRI_COLOR),
        ("BACKGROUND", (0, 0), (-1, -1), PRI_LT),
        ("PADDING",    (0, 0), (-1, -1), 5),
    ]))

    div_w   = 0.3 * cm
    right_w = 5.0 * cm
    mid_w   = W - (logo_w + div_w) - right_w

    if logo_cell:
        hdr_data = [[logo_cell[0], title_block, os_block]]
        hdr_cols = [logo_w + 0.2 * cm, mid_w, right_w]
    else:
        hdr_data = [[title_block, os_block]]
        hdr_cols = [W - right_w, right_w]

    hdr_tbl = Table(hdr_data, colWidths=hdr_cols)
    hdr_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), WHITE),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("VALIGN",      (0, 0), (0, -1),  "TOP"),   # logo flushes to top
        ("PADDING",     (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (0, -1),  0),
        ("TOPPADDING",  (0, 0), (0, -1),  0),       # logo starts at very top
    ]))
    story.append(hdr_tbl)

    # Linha divisória dupla abaixo do cabeçalho
    story.append(HRFlowable(width="100%", thickness=2.5, color=ACCENT,
                             spaceBefore=4, spaceAfter=1))
    story.append(HRFlowable(width="100%", thickness=0.4, color=RULE,
                             spaceBefore=0, spaceAfter=14))

    # ── Helper: título de seção ───────────────────────────────────────────────
    def sec(text, color=ACCENT):
        return [
            Paragraph(
                text,
                S(f"sc_{text[:6]}", fontSize=8, fontName="Helvetica-Bold",
                  textColor=color, spaceAfter=5,
                  letterSpacing=0.8),
            ),
            HRFlowable(width="100%", thickness=0.7, color=color, spaceAfter=10),
        ]

    # ═══════════════════════════════════════════════════════════════════════════
    # EQUIPAMENTO
    # ═══════════════════════════════════════════════════════════════════════════
    story += sec("EQUIPAMENTO")

    equip_rows = [
        ("Equipamento",        os_obj.equipment),
        ("Localização",        os_obj.location),
        ("Tipo de Manutenção", "Preditiva — Geração Automática por Sensor"),
    ]
    eq_tbl = Table(
        [[
            Paragraph(lbl, S(f"el{i}", fontSize=8, fontName="Helvetica",
                             textColor=GRAY)),
            Paragraph(val, S(f"ev{i}", fontSize=10.5, fontName="Helvetica-Bold",
                             textColor=INK_SOFT)),
        ] for i, (lbl, val) in enumerate(equip_rows)],
        colWidths=[3.4 * cm, W - 3.4 * cm],
    )
    eq_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GRAY_LT),
        ("BACKGROUND", (0, 1), (-1, 1), WHITE),
        ("BACKGROUND", (0, 2), (-1, 2), GRAY_LT),
        ("BOX",        (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID",  (0, 0), (-1, -1), 0.4, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
        # Faixa azul à esquerda da coluna de labels
        ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
    ]))
    story.append(eq_tbl)
    story.append(Spacer(1, 0.7 * cm))

    # ═══════════════════════════════════════════════════════════════════════════
    # LEITURAS — cards brancos com faixa colorida superior, números grandes
    # ═══════════════════════════════════════════════════════════════════════════
    story += sec("LEITURAS NO MOMENTO DA DETECÇÃO")

    col_w = W / 4
    readings = [
        ("TEMPERATURA", f"{os_obj.temperature:.1f}", "°C",   RED,    RED_LT,    RED_RULE),
        ("VIBRAÇÃO",    f"{os_obj.vibration:.2f}",   "mm/s", PURPLE, PURPLE_LT, colors.HexColor("#c4b5fd")),
        ("CORRENTE",    f"{os_obj.current:.2f}",     "A",    AMBER,  AMBER_LT,  AMBER_RULE),
        ("TENSÃO",      f"{os_obj.voltage:.1f}",     "V",    GREEN,  GREEN_LT,  GREEN_RULE),
    ]

    def rdg_cell(label, value, unit, val_color, bg_color, rule_color):
        # Mini-tabela com alturas fixas — elimina sobreposição
        lbl_p = Paragraph(label,
            S(f"rl_{label[:3]}", fontSize=7, fontName="Helvetica",
              textColor=GRAY, alignment=TA_CENTER))
        val_p = Paragraph(value,
            S(f"rv_{label[:3]}", fontSize=26, fontName="Helvetica-Bold",
              textColor=val_color, alignment=TA_CENTER, leading=30))
        unt_p = Paragraph(unit,
            S(f"ru_{label[:3]}", fontSize=9, fontName="Helvetica",
              textColor=GRAY, alignment=TA_CENTER))

        inner = Table(
            [[lbl_p], [val_p], [unt_p]],
            colWidths=[col_w],
            rowHeights=[0.65 * cm, 1.30 * cm, 0.65 * cm],
        )
        inner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, -1), bg_color),
            ("TOPPADDING",    (0, 0), (0, 0),  14),
            ("BOTTOMPADDING", (0, 0), (0, 0),  4),
            ("TOPPADDING",    (0, 1), (0, 1),  4),
            ("BOTTOMPADDING", (0, 1), (0, 1),  4),
            ("TOPPADDING",    (0, 2), (0, 2),  6),
            ("BOTTOMPADDING", (0, 2), (0, 2),  14),
            ("LEFTPADDING",   (0, 0), (0, -1), 4),
            ("RIGHTPADDING",  (0, 0), (0, -1), 4),
            ("ALIGN",         (0, 0), (0, -1), "CENTER"),
            ("VALIGN",        (0, 0), (0, -1), "MIDDLE"),
            # Faixa colorida topo de cada card
            ("LINEABOVE",     (0, 0), (0, 0),  4, rule_color),
        ]))
        return inner

    rd_row = [[rdg_cell(*r) for r in readings]]
    rd_tbl = Table(rd_row, colWidths=[col_w] * 4)
    rd_tbl.setStyle(TableStyle([
        ("BOX",       (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("PADDING",   (0, 0), (-1, -1), 0),
        ("VALIGN",    (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(rd_tbl)
    story.append(Spacer(1, 0.75 * cm))

    # ═══════════════════════════════════════════════════════════════════════════
    # ANOMALIAS
    # ═══════════════════════════════════════════════════════════════════════════
    story += sec("ANOMALIAS DETECTADAS", PRI_COLOR)
    for a in (anomalies or ["Sem anomalias registradas"]):
        row = Table([[
            Paragraph("!",
                      S("ai", fontSize=11, fontName="Helvetica-Bold",
                        textColor=PRI_COLOR, alignment=TA_CENTER)),
            Paragraph(str(a),
                      S("at", fontSize=9.5, fontName="Helvetica",
                        textColor=INK_SOFT, leading=14)),
        ]], colWidths=[0.8 * cm, W - 0.8 * cm])
        row.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), PRI_LT),
            ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
            ("LINEBEFORE",    (0, 0), (0, -1),  3.5, PRI_COLOR),
            ("TOPPADDING",    (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
            ("LEFTPADDING",   (0, 0), (0, -1),  4),
            ("RIGHTPADDING",  (0, 0), (0, -1),  4),
            ("LEFTPADDING",   (1, 0), (1, -1),  12),
            ("RIGHTPADDING",  (1, 0), (1, -1),  12),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(row)
        story.append(Spacer(1, 0.22 * cm))
    story.append(Spacer(1, 0.5 * cm))

    # ═══════════════════════════════════════════════════════════════════════════
    # AÇÕES SUGERIDAS
    # ═══════════════════════════════════════════════════════════════════════════
    story += sec("AÇÕES SUGERIDAS", GREEN)
    for ac in (actions or ["Aguardando diagnóstico técnico"]):
        row = Table([[
            Paragraph("→",
                      S("gi", fontSize=11, fontName="Helvetica-Bold",
                        textColor=GREEN, alignment=TA_CENTER)),
            Paragraph(str(ac),
                      S("gt", fontSize=9.5, fontName="Helvetica",
                        textColor=INK_SOFT, leading=14)),
        ]], colWidths=[0.8 * cm, W - 0.8 * cm])
        row.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), GREEN_LT),
            ("BOX",           (0, 0), (-1, -1), 0.5, BORDER),
            ("LINEBEFORE",    (0, 0), (0, -1),  3.5, GREEN),
            ("TOPPADDING",    (0, 0), (-1, -1), 11),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 11),
            ("LEFTPADDING",   (0, 0), (0, -1),  4),
            ("RIGHTPADDING",  (0, 0), (0, -1),  4),
            ("LEFTPADDING",   (1, 0), (1, -1),  12),
            ("RIGHTPADDING",  (1, 0), (1, -1),  12),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(row)
        story.append(Spacer(1, 0.22 * cm))

    story.append(Spacer(1, 1.0 * cm))

    # ═══════════════════════════════════════════════════════════════════════════
    # ASSINATURAS
    # ═══════════════════════════════════════════════════════════════════════════
    sig_w = W / 3

    def sig_block(title):
        return [
            Spacer(1, 1.1 * cm),
            HRFlowable(width=sig_w - 1.6 * cm, thickness=0.7, color=RULE,
                       hAlign="CENTER", spaceAfter=5),
            Paragraph(title,
                      S(f"sg_{title[:3]}", fontSize=8, fontName="Helvetica",
                        textColor=GRAY, alignment=TA_CENTER)),
        ]

    sigs = Table(
        [[sig_block("Técnico Responsável"),
          sig_block("Supervisor de Manutenção"),
          sig_block("Data de Conclusão")]],
        colWidths=[sig_w] * 3,
    )
    sigs.setStyle(TableStyle([
        ("VALIGN",  (0, 0), (-1, -1), "BOTTOM"),
        ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(KeepTogether(sigs))

    # ═══════════════════════════════════════════════════════════════════════════
    # RODAPÉ
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=2.5, color=ACCENT,
                             spaceBefore=0, spaceAfter=1))
    story.append(HRFlowable(width="100%", thickness=0.4, color=RULE,
                             spaceAfter=5))
    story.append(Table([[
        Paragraph(
            "ConfiMinas Engenharia · Sistema de Manutenção Preditiva",
            S("ft1", fontSize=7, fontName="Helvetica", textColor=GRAY),
        ),
        Paragraph(
            f"{os_obj.os_number}"
            + (f"  ·  {os_obj.created_at.strftime('%d/%m/%Y %H:%M')}" if os_obj.created_at else ""),
            S("ft2", fontSize=7, fontName="Helvetica",
              textColor=GRAY, alignment=TA_RIGHT),
        ),
    ]], colWidths=[W * 0.56, W * 0.44]))

    doc.build(story)
    print(f"[PDF] Gerado: {pdf_path}")
    return pdf_path
