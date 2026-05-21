#!/usr/bin/env python3
"""
ConfiMinas — Gera desenhos técnicos SVG com medidas para cada peça.
Execute: python3 gerar_desenhos.py
Abre os .svg gerados em qualquer navegador.
"""
import os, math

OUT = os.path.dirname(os.path.abspath(__file__))
S   = 2.8   # escala: pixels por mm
MAR = 55
RED = "#cc2200"
BLUE = "#1a3a6b"
GRAY = "#777777"
BLK  = "#000000"
FILL_PART  = "#cce0ff"
FILL_MOTOR = "#ffe0b0"

def svg(w, h, body, title, num):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
<style>
  text{{font-family:Arial,sans-serif;font-size:11px;fill:{BLK};}}
  .t{{font-size:15px;font-weight:bold;fill:{BLUE};}}
  .d{{font-size:10px;fill:{RED};}}
  .n{{font-size:9px;fill:{GRAY};}}
</style>
<rect width="{w}" height="{h}" fill="white" stroke="#bbbbbb"/>
<rect x="4" y="4" width="{w-8}" height="{h-8}" fill="none" stroke="{BLUE}" stroke-width="2"/>
<rect x="4" y="{h-42}" width="{w-8}" height="38" fill="{FILL_PART}" stroke="{BLUE}" stroke-width="1"/>
<text x="{w//2}" y="{h-24}" text-anchor="middle" class="t">Peça {num}: {title}</text>
<text x="{w//2}" y="{h-10}" text-anchor="middle" class="n">ConfiMinas Engenharia | PLA 0.2mm 20% infill | medidas em mm</text>
{body}
</svg>"""

def rct(x,y,w,h,fill=FILL_PART,stroke=BLUE,sw=2):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n'

def circ(cx,cy,r,fill="white",stroke=BLK,sw=1.5):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n'

def ln(x1,y1,x2,y2,stroke=BLK,sw=1,dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}/>\n'

def txt(x,y,s,cls="",anchor="middle",fill=BLK):
    c = f' class="{cls}"' if cls else ""
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}"{c} fill="{fill}">{s}</text>\n'

def dh(x1,x2,y,label,off=28):
    """Cota horizontal."""
    b=""
    b+=ln(x1,y+off,x2,y+off,RED,0.9)
    b+=ln(x1,y,x1,y+off+6,RED,0.6,"3,2")
    b+=ln(x2,y,x2,y+off+6,RED,0.6,"3,2")
    b+=f'<polygon points="{x1},{y+off} {x1+6},{y+off-3} {x1+6},{y+off+3}" fill="{RED}"/>\n'
    b+=f'<polygon points="{x2},{y+off} {x2-6},{y+off-3} {x2-6},{y+off+3}" fill="{RED}"/>\n'
    b+=txt((x1+x2)/2, y+off-5, label,"d")
    return b

def dv(x,y1,y2,label,off=28):
    """Cota vertical."""
    b=""
    b+=ln(x+off,y1,x+off,y2,RED,0.9)
    b+=ln(x,y1,x+off+6,y1,RED,0.6,"3,2")
    b+=ln(x,y2,x+off+6,y2,RED,0.6,"3,2")
    b+=f'<polygon points="{x+off},{y1} {x+off-3},{y1+6} {x+off+3},{y1+6}" fill="{RED}"/>\n'
    b+=f'<polygon points="{x+off},{y2} {x+off-3},{y2-6} {x+off+3},{y2-6}" fill="{RED}"/>\n'
    mx,my=(x+off+14),(y1+y2)/2
    b+=f'<text x="{mx}" y="{my+4}" text-anchor="middle" class="d" transform="rotate(-90 {mx} {my+4})">{label}</text>\n'
    return b

def label_box(x,y,text_lines):
    h=len(text_lines)*14+10
    b=rct(x,y,220,h,"#f0f6ff",BLUE,1)
    for i,t in enumerate(text_lines):
        b+=txt(x+8,y+18+i*14,t,"n","start")
    return b

# ─────────────────────────────────────────────────────────────
# PEÇA 1 — BASE MOINHO (220×90×10mm)
# ─────────────────────────────────────────────────────────────
def peca1():
    W,H=740,420; ox,oy=MAR,MAR
    bw,bl,bh = 220*S,90*S,10*S
    b=""
    b+=txt(ox+bw/2,oy-12,"VISTA SUPERIOR","t")
    b+=rct(ox,oy,bw,bl)
    for ry in [8*S,(90-10.5)*S]:
        b+=rct(ox,oy+ry,bw,2.5*S,"#99bbdd",BLUE,0.5)
    for rx in [10*S,80*S,150*S,(208)*S]:
        b+=rct(ox+rx,oy,2.5*S,bl,"#99bbdd",BLUE,0.5)
    for i in range(3):
        b+=rct(ox+22*S+i*60*S,oy+15*S,40*S,(90-30)*S,"white",GRAY,0.8)
    for fx,fy in [(6*S,6*S),(6*S,(84)*S),((214)*S,6*S),((214)*S,(84)*S)]:
        b+=circ(ox+fx,oy+fy,1.7*S)
    # Bolso do motor
    bpx = 12*S; bpy = (90/2-24.3/2)*S
    b+=rct(ox+bpx,oy+bpy,24.3*S,24.3*S,FILL_MOTOR,"#cc6600",1.5)
    b+=txt(ox+bpx+24.3*S/2,oy+bpy+24.3*S/2,"Motor DC","n")
    b+=txt(ox+bpx+24.3*S/2,oy+bpy+24.3*S/2+12,"24.3×24.3mm","n")
    b+=dh(ox,ox+bw,oy+bl,"220 mm",35)
    b+=dv(ox+bw,oy,oy+bl,"90 mm",35)
    b+=dh(ox+bpx,ox+bpx+24.3*S,oy+bpy,"24.3 mm",-30)
    # Vista lateral
    lx=ox+bw+90; ly=oy
    b+=txt(lx+50*S/2,ly-12,"VISTA LATERAL","t")
    b+=rct(lx,ly,50*S,bh)
    b+=rct(lx,ly+bh,50*S,6*S,"#99bbdd",BLUE,0.8)
    b+=dv(lx+50*S,ly,ly+bh+6*S,"16 mm",25)
    b+=dh(lx,lx+50*S,ly+bh+6*S,"50 mm",20)
    b+=label_box(ox,oy+bl+55,[
        "Bolso laranja: cavidade para motor DC flat (24.3×24.3×3.6mm) afundado na base",
        "Furos ø3.4mm cantos: parafuso M3 para fixação em superfície",
        "Vigas transversais e longitudinais: nervuras estruturais (visual skid industrial)",
    ])
    return svg(W,H,b,"BASE MOINHO (SKID)","1")

# ─────────────────────────────────────────────────────────────
# PEÇA 2 — CARCAÇA MOTOR (42×36×38mm)
# ─────────────────────────────────────────────────────────────
def peca2():
    W,H=620,420; ox,oy=MAR,MAR+20
    mw,ml,mh = 42*S,36*S,38*S
    b=""
    b+=txt(ox+mw/2,oy-12,"VISTA FRONTAL","t")
    b+=rct(ox,oy,mw,mh,"#4477cc",BLUE,2)
    for i in range(5):
        b+=rct(ox+5*S+i*7*S,oy,4*S,5*S,"#335588",BLUE,0.5)
    # Cavidade motor
    cx=(42-24.3)/2*S; cy=(38-3.6-2.5)*S
    b+=rct(ox+cx,oy+cy,24.3*S,3.6*S,FILL_MOTOR,"#cc6600",2)
    b+=txt(ox+mw/2,oy+cy-6,"cavidade motor DC","n")
    # Eixo (sai pela lateral direita)
    b+=circ(ox+mw+7*S/2,oy+mh/2,1.9*S/2+0.2,fill="white")
    b+=txt(ox+mw+7*S+8,oy+mh/2+4,"eixo ø2.3mm","n","start")
    # Furos M3
    for fx,fy in [(5*S,5*S),(5*S,(31)*S),((37)*S,5*S),((37)*S,(31)*S)]:
        b+=circ(ox+fx,oy+fy,1.7*S)
    b+=dh(ox,ox+mw,oy+mh,"42 mm",30)
    b+=dv(ox+mw,oy,oy+mh,"38 mm",28)
    b+=dh(ox+cx,ox+cx+24.3*S,oy+cy,"24.3 mm",-22)
    b+=dv(ox+mw+28+15,oy+cy,oy+cy+3.6*S,"3.6 mm",12)
    # Vista lateral
    lx=ox+mw+90; ly=oy
    b+=txt(lx+ml/2,ly-12,"VISTA LATERAL","t")
    b+=rct(lx,ly,ml,mh,"#4477cc",BLUE,2)
    b+=circ(lx+ml/2,ly+mh/2,1.9*S/2+0.2)
    b+=dh(lx,lx+ml,ly+mh,"36 mm",25)
    b+=label_box(ox,oy+mh+55,[
        "Cavidade laranja: motor DC flat encaixa por pressão (fica no bolso da base abaixo)",
        "Furo lateral ø2.3mm: eixo do motor passa para o redutor",
        "Carcaça parafusa na base com M3 sobre o motor (tampa decorativa visual WEG)",
    ])
    return svg(W,H,b,"CARCAÇA MOTOR (DECORATIVA)","2")

# ─────────────────────────────────────────────────────────────
# PEÇA 3 — REDUTOR (28×28×30mm)
# ─────────────────────────────────────────────────────────────
def peca3():
    W,H=500,380; ox,oy=MAR+20,MAR+20
    rw,rl,rh = 28*S,28*S,30*S
    b=""
    b+=txt(ox+rw/2,oy-12,"VISTA FRONTAL","t")
    b+=rct(ox,oy,rw,rh,"#888888","#333",2)
    b+=rct(ox+rw/2-8*S,oy,16*S,12*S,"#999","#333",1)
    b+=txt(ox+rw/2,oy+8,"tampa inspeção","n")
    b+=circ(ox,oy+rh/2,1.9*S/2+0.2)
    b+=circ(ox+rw,oy+rh/2,1.9*S/2+0.2)
    b+=txt(ox-12,oy+rh/2+4,"entrada","n","end")
    b+=txt(ox+rw+4,oy+rh/2+4,"saída","n","start")
    for fx,fy in [(4*S,4*S),(4*S,(24)*S),((22)*S,4*S),((22)*S,(24)*S)]:
        b+=circ(ox+fx,oy+fy,1.7*S)
    b+=dh(ox,ox+rw,oy+rh,"28 mm",28)
    b+=dv(ox+rw,oy,oy+rh,"30 mm",25)
    lx=ox+rw+85; ly=oy
    b+=txt(lx+rl/2,ly-12,"VISTA LATERAL","t")
    b+=rct(lx,ly,rl,rh,"#888888","#333",2)
    b+=circ(lx+rl/2,ly+rh/2,1.9*S/2+0.2)
    b+=dh(lx,lx+rl,ly+rh,"28 mm",25)
    b+=label_box(ox,oy+rh+55,[
        "Eixo ø2.3mm atravessa horizontalmente: conecta carcaça motor → tambor",
        "Furos ø3.4mm na base: parafusos M3 para fixação no skid",
        "Peça decorativa — simula caixa redutora do moinho real",
    ])
    return svg(W,H,b,"REDUTOR (DECORATIVO)","3")

# ─────────────────────────────────────────────────────────────
# PEÇA 4 — TAMBOR MOINHO (ø70 × 100mm)
# ─────────────────────────────────────────────────────────────
def peca4():
    W,H=680,500; ox,oy=MAR+30,MAR+50
    dl=100*S; dr=35*S; fri=42*S; ft=5*S; hub_r=6*S; hub_h=8*S
    dri=(35-3)*S; hl=18*S
    b=""
    b+=txt(ox+dl/2,oy-14,"VISTA LATERAL (CORTE)","t")
    cy=fri
    # Corpo
    b+=rct(ox,oy+fri-dr,dl,dr*2,"#ee8822","#cc5500",2)
    b+=rct(ox+ft+3*S,oy+fri-dri,dl-ft*2-3*S,dri*2,"white",GRAY,0.8)
    # Flanges
    b+=rct(ox,oy+fri-fri,ft,fri*2,"#ffdd44","#cc9900",2)
    b+=rct(ox+dl-ft,oy+fri-fri,ft,fri*2,"#ffdd44","#cc9900",2)
    # Bocal
    b+=f'<polygon points="{ox},{oy+fri-11*S} {ox-hl},{oy+fri-7*S} {ox-hl},{oy+fri+7*S} {ox},{oy+fri+11*S}" fill="#ee8822" stroke="#cc5500" stroke-width="2"/>\n'
    # Hub
    b+=rct(ox-hub_h,oy+fri-hub_r,hub_h,hub_r*2,"#aaaaaa",BLK,1.5)
    # Linha de centro
    b+=ln(ox-hub_h-10,oy+fri,ox+dl+10,oy+fri,GRAY,0.6,"5,3")
    # Furo eixo
    b+=ln(ox-hub_h,oy+fri-0.95*S,ox-hub_h+hub_h+ft+3,oy+fri-0.95*S,BLK,1)
    b+=ln(ox-hub_h,oy+fri+0.95*S,ox-hub_h+hub_h+ft+3,oy+fri+0.95*S,BLK,1)
    b+=txt(ox-hub_h+hub_h/2,oy+fri+hub_r+14,"furo eixo ø1.9mm","n")
    # Cotas
    b+=dh(ox,ox+dl,oy+fri+fri+14,"100 mm",22)
    b+=dv(ox+dl+22,oy+fri-fri,oy+fri+fri,"ø84 mm (flange)",22)
    b+=dv(ox+dl+55,oy+fri-dr,oy+fri+dr,"ø70 mm (corpo)",15)
    b+=dh(ox,ox+ft,oy+fri-fri-14,"5 mm",-18)
    b+=dh(ox-hub_h,ox,oy+fri+hub_r+28,"8 mm (hub)",14)
    # Vista frontal
    ex=ox+dl+140; ey=oy+fri
    b+=txt(ex,oy-14,"VISTA FRONTAL (END)","t")
    b+=circ(ex,ey,fri,"#ffdd44","#cc9900",2)
    b+=circ(ex,ey,dr,"#ee8822","#cc5500",1.5)
    b+=circ(ex,ey,dri,"white",GRAY,0.8)
    b+=circ(ex,ey,hub_r,"#aaaaaa",BLK,1)
    b+=circ(ex,ey,0.95*S,"white",BLK,1)
    for a in range(0,360,30):
        rad=math.radians(a)
        b+=circ(ex+(fri-4*S)*math.cos(rad),ey+(fri-4*S)*math.sin(rad),1.25*S,"white",BLK,0.6)
    b+=txt(ex,ey+fri+20,"12× ø2.5mm decorativos","n")
    b+=label_box(ox,oy+fri+fri+60,[
        "Hub dianteiro (ø12mm): encaixa no eixo do motor por pressfit — furo ø1.9mm",
        "Flanges amarelas ø84mm: parafusos decorativos simulam flange real do moinho",
        "Bocal cônico: simula entrada de minério do moinho de bolas real",
    ])
    return svg(W,H,b,"TAMBOR MOINHO (DRUM)","4")

# ─────────────────────────────────────────────────────────────
# PEÇA 5 — MANCAL TRASEIRO (40×30mm)
# ─────────────────────────────────────────────────────────────
def peca5():
    W,H=480,420; ox,oy=MAR+20,MAR
    bw=40*S; bl=30*S; bh=3*S; col_h=50*S
    b=""
    b+=txt(ox+bw/2,oy-12,"VISTA FRONTAL","t")
    b+=rct(ox,oy+col_h,bw,bh,"#cccccc",BLK,2)
    b+=rct(ox+bw/2-2.5*S,oy+9*S,5*S,col_h-9*S,"#aaaaaa",BLK,1.5)
    b+=circ(ox+bw/2,oy+9*S,9*S,"#888888",BLK,2)
    b+=circ(ox+bw/2,oy+9*S,0.95*S+0.2,"white",BLK,1)
    b+=txt(ox+bw/2,oy+9*S+4,"ø2.3mm","n")
    for fx,fy in [(5*S,bh/2),((33)*S,bh/2)]:
        b+=circ(ox+fx,oy+col_h+fy,1.7*S)
    b+=dh(ox,ox+bw,oy+col_h+bh,"40 mm",22)
    b+=dv(ox+bw,oy+9*S,oy+col_h+bh,"50 mm",25)
    lx=ox+bw+90; ly=oy
    b+=txt(lx+bl/2,ly-12,"VISTA LATERAL","t")
    b+=rct(lx,ly+col_h,bl,bh,"#cccccc",BLK,2)
    b+=rct(lx+bl/2-2.5*S,ly+9*S,5*S,col_h-9*S,"#aaaaaa",BLK,1.5)
    b+=circ(lx+bl/2,ly+9*S,9*S,"#888888",BLK,2)
    b+=dh(lx,lx+bl,ly+col_h+bh,"30 mm",22)
    b+=label_box(ox,oy+col_h+bh+50,[
        "Suporta a extremidade traseira do tambor oposta ao motor",
        "Furo ø2.3mm no topo: eixo do tambor passa e gira livremente",
        "Furos M3 na base: parafusos fixam no skid",
    ])
    return svg(W,H,b,"MANCAL TRASEIRO","5")

# ─────────────────────────────────────────────────────────────
# PEÇA 6 — PAINEL CLP (44×20×80mm)
# ─────────────────────────────────────────────────────────────
def peca6():
    W,H=560,420; ox,oy=MAR+10,MAR
    pw=(28+2.5*2+6)*S; pd=20*S; ph=80*S
    b=""
    b+=txt(ox+pw/2,oy-12,"VISTA FRONTAL","t")
    b+=rct(ox,oy,pw,ph,"#dde8ff",BLUE,2)
    ex=ox+2.5*S+3*S; ey=oy+2.5*S
    b+=rct(ex,ey,28*S,55*S,"#222222",BLK,1.5)
    b+=txt(ox+pw/2,ey+55*S/2+1,"ESP32","t")
    b+=f'<text x="{ox+pw/2}" y="{ey+55*S/2+14}" text-anchor="middle" fill="white" font-size="9px">28×55mm</text>\n'
    b+=circ(ox+pw/2,oy+ph-20*S,2.6*S,"#00dd44",BLK,1)
    b+=txt(ox+pw/2,oy+ph-20*S+14,"LED ø5mm","n")
    for i in range(4):
        b+=rct(ox+6*S+i*10*S,oy+ph-2.5*S-1,6*S,3*S,"white",BLK,0.6)
    b+=rct(ox-1,oy+2.5*S+2*S,3*S,4*S,"white",BLK,0.8)
    b+=txt(ox-4,oy+2.5*S+2*S+8,"USB","n","end")
    b+=dh(ox,ox+pw,oy+ph,"44 mm",28)
    b+=dv(ox+pw,oy,oy+ph,"80 mm",28)
    lx=ox+pw+85; ly=oy
    b+=txt(lx+pd/2,ly-12,"VISTA LATERAL","t")
    b+=rct(lx,ly,pw,pd,"#dde8ff",BLUE,2)
    b+=dv(lx+pw,ly,ly+pd,"20 mm",22)
    b+=dh(lx,lx+pw,ly+pd,"44 mm",22)
    b+=label_box(ox,oy+ph+50,[
        "Janela frontal: ESP32 encaixa e fica visível (simula IHM do CLP industrial)",
        "Furo USB lateral: cabo de alimentação e gravação do firmware",
        "LED verde: indica status de conexão WiFi e envio de dados",
    ])
    return svg(W,H,b,"PAINEL CLP (ESP32)","6")


# ─── Salva todos ────────────────────────────────────────────────
pecas = {
    "peca1_base.svg":         peca1(),
    "peca2_carcaca_motor.svg": peca2(),
    "peca3_redutor.svg":      peca3(),
    "peca4_tambor.svg":       peca4(),
    "peca5_mancal.svg":       peca5(),
    "peca6_painel_clp.svg":   peca6(),
}

for nome, conteudo in pecas.items():
    caminho = os.path.join(OUT, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)
    print(f"✓ {caminho}")

print("\nAbra os arquivos .svg no navegador para ver os desenhos técnicos.")
