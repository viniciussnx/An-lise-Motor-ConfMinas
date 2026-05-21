#!/usr/bin/env python3
"""
ConfiMinas — Vistas ortogonais do protótipo montado
Gera 3 SVGs: frente, lateral direita, cima
Execute: python3 gerar_vistas_montagem.py
"""
import os, math

OUT = os.path.dirname(os.path.abspath(__file__))

# ─── Paleta ─────────────────────────────────────────────────────
C_BASE    = "#1a3a8f"
C_BASE_L  = "#2255cc"
C_MOTOR   = "#2244aa"
C_MOTOR_L = "#3366dd"
C_RED     = "#555555"
C_RED_L   = "#777777"
C_DRUM    = "#dd6600"
C_FLANGE  = "#ddaa00"
C_MANCAL  = "#888888"
C_CLP     = "#aabbdd"
C_CLP_L   = "#ccddf0"
C_RIB     = "#335599"
C_LABEL   = "#cc2200"
C_SHADOW  = "#00000033"
BLACK     = "#000000"
WHITE     = "#ffffff"
GRAY      = "#aaaaaa"

# ─── Dimensões corrigidas (mm) ───────────────────────────────────
BASE_W, BASE_L, BASE_H = 220, 90, 10
RIB_H = 6           # altura das vigas acima da base

# Eixo do tambor/motor (z medido do chão)
AXIS_Z = 38

MOT_W,  MOT_L,  MOT_H  = 42, 36, 56   # carcaça motor
RED_W,  RED_L,  RED_H  = 28, 28, 56   # redutor
DRUM_R  = 22           # raio do tambor (ø44mm)
FLANGE_R = 28          # raio da flange (ø56mm)
DRUM_LEN = 100         # comprimento do tambor
HUB_H    = 8           # hub de acoplamento
MANx     = 12 + MOT_W + 4 + RED_W + 2 + DRUM_LEN + 5  # x do mancal
MAN_W, MAN_L = 40, 30  # base do mancal

# Posições X na montagem
MOT_X  = 12
RED_X  = MOT_X + MOT_W + 4
DRUM_X = RED_X + RED_W + 2
CLP_X  = BASE_W + 14

# Posições Y (centro em BASE_L/2 = 45)
MOT_Y  = BASE_L//2 - MOT_L//2
RED_Y  = BASE_L//2 - RED_L//2
MAN_Y  = BASE_L//2 - MAN_W//2
CLP_Y  = BASE_L//2 - 20

SCALE  = 2.4    # px/mm
MAR    = 60

def s(v): return v * SCALE    # mm → px


def svg_doc(w, h, content, title):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
<defs>
  <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
    <feDropShadow dx="2" dy="2" stdDeviation="2" flood-color="#00000044"/>
  </filter>
</defs>
<style>
  text{{font-family:Arial,sans-serif;font-size:11px;fill:{BLACK};}}
  .t{{font-size:16px;font-weight:bold;fill:{C_MOTOR};}}
  .d{{font-size:10px;fill:{C_LABEL};}}
  .lbl{{font-size:9px;fill:#444;}}
  .big{{font-size:13px;font-weight:bold;}}
</style>
<rect width="{w}" height="{h}" fill="#f5f7fa"/>
<rect x="3" y="3" width="{w-6}" height="{h-6}" fill="none" stroke="{C_BASE}" stroke-width="2"/>
<!-- {title} -->
{content}
<rect x="3" y="{h-40}" width="{w-6}" height="37" fill="{C_CLP_L}" stroke="{C_BASE}" stroke-width="1"/>
<text x="{w//2}" y="{h-22}" text-anchor="middle" class="big" fill="{C_BASE}">ConfiMinas — Protótipo Moinho de Bolas | {title}</text>
<text x="{w//2}" y="{h-8}" text-anchor="middle" class="lbl">Medidas em mm | Escala aproximada | PLA 0.2mm</text>
</svg>"""


def R(x,y,w,h,fill,stroke=BLACK,sw=1,rx=0,opacity=1):
    op = f' opacity="{opacity}"' if opacity<1 else ""
    r  = f' rx="{rx}"' if rx else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{r}{op}/>\n'

def C(cx,cy,r,fill,stroke=BLACK,sw=1):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n'

def L(x1,y1,x2,y2,stroke=BLACK,sw=1,dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{sw}"{d}/>\n'

def T(x,y,text,cls="",anchor="middle",fill=BLACK,size=None):
    c = f' class="{cls}"' if cls else ""
    fs = f' font-size="{size}px"' if size else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}"{c} fill="{fill}"{fs}>{text}</text>\n'

def poly(pts, fill, stroke=BLACK, sw=1):
    p = " ".join(f"{x:.1f},{y:.1f}" for x,y in pts)
    return f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n'

def dim_h(x1,x2,y,lbl,off=22,above=False):
    sign = -1 if above else 1
    b=""
    b+=L(x1,y+sign*off,x2,y+sign*off,C_LABEL,0.9)
    b+=L(x1,y,x1,y+sign*(off+6),C_LABEL,0.6,"3,2")
    b+=L(x2,y,x2,y+sign*(off+6),C_LABEL,0.6,"3,2")
    b+=f'<polygon points="{x1:.1f},{y+sign*off:.1f} {x1+6:.1f},{y+sign*off-3:.1f} {x1+6:.1f},{y+sign*off+3:.1f}" fill="{C_LABEL}"/>\n'
    b+=f'<polygon points="{x2:.1f},{y+sign*off:.1f} {x2-6:.1f},{y+sign*off-3:.1f} {x2-6:.1f},{y+sign*off+3:.1f}" fill="{C_LABEL}"/>\n'
    b+=T((x1+x2)/2, y+sign*off-(4 if not above else -12), lbl,"d")
    return b

def dim_v(x,y1,y2,lbl,off=22):
    b=""
    b+=L(x+off,y1,x+off,y2,C_LABEL,0.9)
    b+=L(x,y1,x+off+6,y1,C_LABEL,0.6,"3,2")
    b+=L(x,y2,x+off+6,y2,C_LABEL,0.6,"3,2")
    b+=f'<polygon points="{x+off:.1f},{y1:.1f} {x+off-3:.1f},{y1+6:.1f} {x+off+3:.1f},{y1+6:.1f}" fill="{C_LABEL}"/>\n'
    b+=f'<polygon points="{x+off:.1f},{y2:.1f} {x+off-3:.1f},{y2-6:.1f} {x+off+3:.1f},{y2-6:.1f}" fill="{C_LABEL}"/>\n'
    mx,my = x+off+14, (y1+y2)/2
    b+=f'<text x="{mx:.1f}" y="{my+4:.1f}" text-anchor="middle" class="d" transform="rotate(-90 {mx:.1f} {my:.1f})">{lbl}</text>\n'
    return b

def badge(x,y,label,color,text_color=WHITE):
    bw=len(label)*7+14
    return (R(x-bw/2,y-11,bw,16,color,color,0,4)
            +T(x,y,label,"lbl","middle",text_color))

# ════════════════════════════════════════════════════════════════
#  VISTA DE FRENTE  (XZ plane — olhando de frente, Y=0)
#  X = horizontal, Z = vertical (invertido porque SVG y cresce para baixo)
# ════════════════════════════════════════════════════════════════
def vista_frente():
    # origem canvas: ox,oz → ponto (x=0, z=0) na cena
    CW = 820
    CH = 500
    ox = MAR
    oz_ground = CH - 110   # y-canvas onde z=0 (chão)
    def px(xmm): return ox + s(xmm)
    def pz(zmm): return oz_ground - s(zmm)   # z cresce para cima

    b = ""

    # ── chão
    b += L(ox-10, pz(0), px(BASE_W+60), pz(0), GRAY, 1, "6,4")

    # ── BASE
    b += R(px(0), pz(BASE_H+RIB_H), s(BASE_W), s(BASE_H+RIB_H), C_BASE_L, C_BASE, 1.5)
    # vigas
    for xr in [10,80,150,208]:
        b += R(px(xr), pz(BASE_H+RIB_H), s(2.5), s(RIB_H), C_RIB, C_BASE, 0.5)

    # ── CARCAÇA MOTOR
    b += R(px(MOT_X), pz(BASE_H+MOT_H), s(MOT_W), s(MOT_H), C_MOTOR, C_MOTOR, 1.5, 3)
    # aletas
    for i in range(5):
        b += R(px(MOT_X+5+i*7), pz(BASE_H+MOT_H+5), s(4), s(5), C_MOTOR_L, C_MOTOR, 0.5)
    # caixa bornes
    b += R(px(MOT_X+MOT_W), pz(BASE_H+MOT_H/2+5), s(7), s(10), C_MOTOR, C_MOTOR, 1)
    b += badge(px(MOT_X+MOT_W/2), pz(BASE_H+MOT_H/2), "MOTOR DC", C_MOTOR)

    # ── REDUTOR
    b += R(px(RED_X), pz(BASE_H+RED_H), s(RED_W), s(RED_H), C_RED, C_RED, 1.5, 2)
    b += badge(px(RED_X+RED_W/2), pz(BASE_H+RED_H/2), "REDUTOR", C_RED)

    # ── TAMBOR — vista de frente = retângulo
    drum_bottom = AXIS_Z - DRUM_R
    drum_top    = AXIS_Z + DRUM_R
    fl_bottom   = AXIS_Z - FLANGE_R
    fl_top      = AXIS_Z + FLANGE_R
    # flanges (fins das extremidades)
    b += R(px(DRUM_X-HUB_H), pz(AXIS_Z+FLANGE_R), s(5+HUB_H), s(FLANGE_R*2), C_FLANGE, C_FLANGE, 2, 2)
    b += R(px(DRUM_X+DRUM_LEN-5), pz(AXIS_Z+FLANGE_R), s(5), s(FLANGE_R*2), C_FLANGE, C_FLANGE, 2, 2)
    # corpo
    b += R(px(DRUM_X), pz(AXIS_Z+DRUM_R), s(DRUM_LEN), s(DRUM_R*2), C_DRUM, C_DRUM, 1.5)
    # bocal
    b += poly([
        (px(DRUM_X), pz(AXIS_Z+11)),
        (px(DRUM_X-18), pz(AXIS_Z+7)),
        (px(DRUM_X-18), pz(AXIS_Z-7)),
        (px(DRUM_X), pz(AXIS_Z-11)),
    ], C_DRUM, C_DRUM, 1.5)
    # interior oco (indicativo)
    b += R(px(DRUM_X+5), pz(AXIS_Z+DRUM_R-3), s(DRUM_LEN-10), s((DRUM_R-3)*2), WHITE, GRAY, 0.6)
    # parafusos decorativos flange dianteira
    for dz in [-24,-12,0,12,24]:
        b += C(px(DRUM_X+2), pz(AXIS_Z+dz), 2, WHITE, BLACK, 0.7)
    b += badge(px(DRUM_X+DRUM_LEN/2), pz(AXIS_Z), "TAMBOR ø44mm", C_DRUM)

    # ── LINHA DE EIXO
    b += L(px(MOT_X+5), pz(AXIS_Z), px(DRUM_X+DRUM_LEN+15), pz(AXIS_Z), GRAY, 0.7, "5,3")

    # ── MANCAL
    man_top = AXIS_Z + 9   # cabeça do mancal
    b += R(px(MANx), pz(BASE_H+RIB_H), s(MAN_W), s(RIB_H), C_MANCAL, C_RED, 0.5)
    b += R(px(MANx+MAN_W/2-2.5), pz(man_top), s(5), s(man_top-BASE_H-RIB_H), C_MANCAL, C_MANCAL, 1.2)
    b += C(px(MANx+MAN_W/2), pz(man_top), s(9), C_MANCAL, BLACK, 1.5)
    b += C(px(MANx+MAN_W/2), pz(AXIS_Z), 2.5, WHITE, BLACK, 1)
    b += badge(px(MANx+MAN_W/2), pz(BASE_H+RIB_H+10), "MANCAL", C_MANCAL)

    # ── PAINEL CLP
    CLP_H = 80
    b += R(px(CLP_X), pz(CLP_H), s(44), s(CLP_H), C_CLP, C_MOTOR, 1.5, 2)
    b += R(px(CLP_X+8), pz(CLP_H-7), s(28), s(55), "#222", BLACK, 1)
    b += C(px(CLP_X+22), pz(CLP_H-65), 4, "#00dd44", BLACK, 1)
    b += badge(px(CLP_X+22), pz(CLP_H/2+10), "PAINEL CLP", C_MOTOR)

    # ── COTAS
    b += dim_h(px(0), px(BASE_W), pz(0), "220 mm", 28)
    b += dim_v(px(BASE_W)+8, pz(BASE_H+MOT_H), pz(0), f"{BASE_H+MOT_H} mm", 22)
    b += dim_v(px(DRUM_X+DRUM_LEN)+8, pz(AXIS_Z+FLANGE_R), pz(AXIS_Z-FLANGE_R), "ø56mm", 18)
    b += dim_h(px(DRUM_X), px(DRUM_X+DRUM_LEN), pz(AXIS_Z+FLANGE_R), "100 mm", 28, above=True)
    b += dim_v(px(0)-10, pz(AXIS_Z), pz(0), f"{AXIS_Z}mm eixo", 25)

    # ── TÍTULO
    b += T(px(BASE_W/2), 28, "VISTA DE FRENTE", "t")

    return svg_doc(CW, CH, b, "Vista de Frente")


# ════════════════════════════════════════════════════════════════
#  VISTA LATERAL DIREITA  (YZ plane — olhando do lado direito)
#  Y = horizontal, Z = vertical
# ════════════════════════════════════════════════════════════════
def vista_lateral():
    CW = 560
    CH = 480
    oy = MAR + 20
    oz_ground = CH - 100
    def py(ymm): return oy + s(ymm)
    def pz(zmm): return oz_ground - s(zmm)

    b = ""
    b += L(oy-10, pz(0), py(BASE_L+40), pz(0), GRAY, 1, "6,4")

    # ── BASE (vista lateral = retângulo 90×10)
    b += R(py(0), pz(BASE_H+RIB_H), s(BASE_L), s(BASE_H+RIB_H), C_BASE_L, C_BASE, 1.5)

    # ── CARCAÇA MOTOR (vista lateral = retângulo 36×56 centrado em y=45)
    b += R(py(MOT_Y), pz(BASE_H+MOT_H), s(MOT_L), s(MOT_H), C_MOTOR, C_MOTOR, 1.5, 3)
    b += badge(py(MOT_Y+MOT_L/2), pz(BASE_H+MOT_H/2), "MOTOR", C_MOTOR)

    # ── TAMBOR (vista lateral = círculo ø44 + flange ø56)
    drum_cy = py(BASE_L/2)
    drum_cz = pz(AXIS_Z)
    b += C(drum_cy, drum_cz, s(FLANGE_R), C_FLANGE, C_FLANGE, 2)
    b += C(drum_cy, drum_cz, s(DRUM_R), C_DRUM, C_DRUM, 2)
    b += C(drum_cy, drum_cz, s(DRUM_R-3), WHITE, GRAY, 0.7)
    # parafusos decorativos flange
    for a in range(0, 360, 30):
        rad = math.radians(a)
        b += C(drum_cy + s(FLANGE_R-4)*math.cos(rad),
               drum_cz + s(FLANGE_R-4)*math.sin(rad), 2, WHITE, BLACK, 0.6)
    b += badge(drum_cy, drum_cz, "TAMBOR", C_DRUM)

    # ── PAINEL CLP (vista lateral = 20mm profundidade)
    b += R(py(CLP_Y), pz(80), s(20), s(80), C_CLP, C_MOTOR, 1.5)
    b += badge(py(CLP_Y+10), pz(50), "CLP", C_MOTOR)

    # ── COTAS
    b += dim_h(py(0), py(BASE_L), pz(0), "90 mm", 26)
    b += dim_v(py(BASE_L)+8, pz(AXIS_Z+FLANGE_R), pz(AXIS_Z-FLANGE_R), "ø56mm", 18)
    b += dim_v(py(BASE_L)+30, pz(AXIS_Z+DRUM_R), pz(AXIS_Z-DRUM_R), "ø44mm", 14)
    b += dim_v(py(0)-10, pz(AXIS_Z), pz(0), f"{AXIS_Z}mm", 22)
    b += dim_v(py(0)-30, pz(BASE_H+MOT_H), pz(0), f"{BASE_H+MOT_H}mm", 14)

    b += T(py(BASE_L/2), 22, "VISTA LATERAL DIREITA", "t")

    return svg_doc(CW, CH, b, "Vista Lateral Direita")


# ════════════════════════════════════════════════════════════════
#  VISTA DE CIMA  (XY plane — olhando de cima)
#  X = horizontal, Y = vertical
# ════════════════════════════════════════════════════════════════
def vista_cima():
    CW = 900
    CH = 520
    ox = MAR
    oy = MAR + 60
    def px(xmm): return ox + s(xmm)
    def py(ymm): return oy + s(ymm)

    b = ""

    # ── BASE
    b += R(px(0), py(0), s(BASE_W), s(BASE_L), C_BASE_L, C_BASE, 2)
    for yr in [8, BASE_L-10.5]:
        b += R(px(0), py(yr), s(BASE_W), s(2.5), C_RIB, C_BASE, 0.4)
    for xr in [10, 80, 150, 208]:
        b += R(px(xr), py(0), s(2.5), s(BASE_L), C_RIB, C_BASE, 0.4)
    # janelas alivio
    for i in range(3):
        b += R(px(22+i*60), py(15), s(40), s(60), C_BASE, C_BASE, 0.3, 2, 0.4)

    # ── CARCAÇA MOTOR (vista de cima = 42×36)
    b += R(px(MOT_X), py(MOT_Y), s(MOT_W), s(MOT_L), C_MOTOR, C_MOTOR, 1.5, 3)
    # aletas (vistas de cima = linhas)
    for i in range(5):
        b += L(px(MOT_X+5+i*7), py(MOT_Y+2), px(MOT_X+5+i*7), py(MOT_Y+MOT_L-2), C_MOTOR_L, 0.8)
    b += badge(px(MOT_X+MOT_W/2), py(MOT_Y+MOT_L/2), "MOTOR DC", C_MOTOR)

    # ── REDUTOR (vista de cima = 28×28)
    b += R(px(RED_X), py(RED_Y), s(RED_W), s(RED_L), C_RED, C_RED, 1.5, 2)
    b += badge(px(RED_X+RED_W/2), py(RED_Y+RED_L/2), "REDUTOR", C_RED)

    # ── TAMBOR (vista de cima = retângulo 100×44 centrado em y=45)
    drum_top_y = BASE_L/2 - DRUM_R
    b += R(px(DRUM_X-5-HUB_H), py(BASE_L/2-FLANGE_R), s(5+HUB_H), s(FLANGE_R*2), C_FLANGE, C_FLANGE, 1.5, 1)
    b += R(px(DRUM_X+DRUM_LEN-5), py(BASE_L/2-FLANGE_R), s(5), s(FLANGE_R*2), C_FLANGE, C_FLANGE, 1.5, 1)
    b += R(px(DRUM_X), py(drum_top_y), s(DRUM_LEN), s(DRUM_R*2), C_DRUM, C_DRUM, 2)
    # linha de eixo central
    b += L(px(DRUM_X-30), py(BASE_L/2), px(DRUM_X+DRUM_LEN+20), py(BASE_L/2), GRAY, 0.7, "5,3")
    b += badge(px(DRUM_X+DRUM_LEN/2), py(BASE_L/2), "TAMBOR ø44×100mm", C_DRUM)

    # ── MANCAL (vista de cima = 40×30)
    b += R(px(MANx), py(MAN_Y), s(MAN_W), s(MAN_L), C_MANCAL, C_MANCAL, 1.5, 2)
    b += badge(px(MANx+MAN_W/2), py(MAN_Y+MAN_L/2), "MANCAL", C_MANCAL)

    # ── PAINEL CLP (vista de cima = 44×20)
    b += R(px(CLP_X), py(CLP_Y), s(44), s(20), C_CLP, C_MOTOR, 1.5, 2)
    b += badge(px(CLP_X+22), py(CLP_Y+10), "PAINEL CLP", C_MOTOR)

    # ── COTAS
    b += dim_h(px(0), px(BASE_W), py(BASE_L), "220 mm", 28)
    b += dim_v(px(BASE_W)+8, py(0), py(BASE_L), "90 mm", 25)
    b += dim_h(px(DRUM_X), px(DRUM_X+DRUM_LEN), py(BASE_L/2-FLANGE_R), "100 mm", 28, above=True)
    b += dim_v(px(DRUM_X+DRUM_LEN)+8, py(BASE_L/2-DRUM_R), py(BASE_L/2+DRUM_R), "ø44mm", 18)
    b += dim_h(px(MOT_X), px(RED_X+RED_W), py(RED_Y+RED_L), "74 mm (motor+red.)", 22)

    b += T(px(BASE_W/2), oy-30, "VISTA DE CIMA", "t")

    # ── LEGENDA
    lx = px(0); ly = py(BASE_L)+65
    b += R(lx, ly, s(BASE_W), 60, "#f0f4ff", C_BASE, 1)
    legenda = [
        (C_BASE_L,  "Base/Skid (220×90×10mm)"),
        (C_MOTOR,   "Carcaça Motor DC (42×36×56mm)"),
        (C_RED,     "Redutor decorativo (28×28×56mm)"),
        (C_DRUM,    "Tambor moinho ø44×100mm"),
        (C_MANCAL,  "Mancal traseiro (40×30mm)"),
        (C_CLP,     "Painel CLP / ESP32 (44×20×80mm)"),
    ]
    for i, (cor, nome) in enumerate(legenda):
        col = i % 3; row = i // 3
        xi = lx + col * s(75) + 10
        yi = ly + row * 26 + 14
        b += R(xi, yi-9, 14, 14, cor, cor, 1, 2)
        b += T(xi+18, yi+1, nome, "lbl", "start")

    return svg_doc(CW, CH, b, "Vista de Cima")


# ─── Salva ──────────────────────────────────────────────────────
vistas = {
    "montagem_frente.svg":  vista_frente(),
    "montagem_lateral.svg": vista_lateral(),
    "montagem_cima.svg":    vista_cima(),
}

for nome, conteudo in vistas.items():
    caminho = os.path.join(OUT, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"✓ {caminho}")

print("\nAbra no navegador para visualizar as vistas montadas.")
