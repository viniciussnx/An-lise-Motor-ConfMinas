// ═══════════════════════════════════════════════════════════════
//  ConfiMinas — Protótipo Moinho de Bolas (Ball Mill Miniatura)
//  Impressão 3D — PLA 0.2mm / 20% infill
//
//  PEÇAS (exportar uma por vez → F6 → Export as STL):
//    peca_1  base_moinho()
//    peca_2  carcaca_motor()
//    peca_3  redutor()
//    peca_4  tambor_moinho()
//    peca_5  mancal_traseiro()
//    peca_6  painel_clp()
//
//  Na seção RENDER no final: descomente a peça desejada.
//  Para ver tudo montado: descomente "visualizacao_completa()"
// ═══════════════════════════════════════════════════════════════

$fn = 60;
TOL  = 0.3;
WALL = 2.5;

// ── Motor DC flat (medidas reais fornecidas) ──────────────────
//    Corpo flat: 24.3 × 24.3 × 3.6mm
//    Eixo aponta PARA CIMA: diâm 1.9mm, sobe 7.6mm acima do corpo
//    Motor fica deitado na base → eixo aponta para o tambor (horizontal)
M_W     = 24.3;
M_L     = 24.3;
M_BODY  = 3.6;
SHAFT_D = 1.9;
SHAFT_UP = 7.6;   // comprimento do eixo acima do corpo

// ── ESP32 ─────────────────────────────────────────────────────
ESP_W = 28.0;
ESP_L = 55.0;

// ── Conjunto ─────────────────────────────────────────────────
BASE_W = 220;
BASE_L = 90;
BASE_H = 10;

MOT_W  = 42;   // carcaça motor externa
MOT_L  = 36;
MOT_H  = 38;

RED_W  = 28;
RED_L  = 28;
RED_H  = 30;

DRUM_R  = 35;   // raio externo do tambor (ø70)
DRUM_L  = 100;
FLANGE_R = 42;  // raio da flange (ø84)


// ═══════════════════════════════════════════════════════════════
//  PLACEHOLDER — mostra o motor DC na cena (não imprimir)
//  Cor laranja para diferenciar das peças impressas
// ═══════════════════════════════════════════════════════════════
module motor_placeholder() {
    color("orange", 0.8) {
        // Corpo flat do motor
        cube([M_W, M_L, M_BODY]);
        // Eixo (aponta no eixo Y para o tambor)
        translate([M_W/2, M_L, M_BODY/2])
            rotate([90, 0, 0])
                cylinder(d=SHAFT_D, h=-( M_L + SHAFT_UP + RED_L + 5));
    }
    // Label
    color("black")
    translate([0, -8, 0])
        linear_extrude(0.4)
            text("Motor DC flat", size=4, halign="left");
}


// ═══════════════════════════════════════════════════════════════
//  1. BASE MOINHO — skid estrutural (220×90×10mm)
// ═══════════════════════════════════════════════════════════════
module base_moinho() {
    difference() {
        union() {
            cube([BASE_W, BASE_L, BASE_H]);
            // Vigas longitudinais
            for (y = [8, BASE_L - 8 - WALL])
                translate([0, y, BASE_H]) cube([BASE_W, WALL, 6]);
            // Vigas transversais
            for (x = [10, 80, 150, BASE_W-12])
                translate([x, 0, BASE_H]) cube([WALL, BASE_L, 6]);
        }
        // Alivio de material
        for (i = [0:2])
            translate([22 + i*60, 15, -0.5]) cube([40, BASE_L-30, BASE_H+1]);
        // Furos M3 cantos
        for (x = [6, BASE_W-8], y = [6, BASE_L-8])
            translate([x, y, -0.5]) cylinder(d=3.4, h=BASE_H+1);
        // Bolso do motor DC (motor fica deitado → eixo aponta horizontal)
        //   Motor entra pelo lado, eixo para o redutor
        translate([12, BASE_L/2 - M_L/2, BASE_H - M_BODY - 1])
            cube([M_W + TOL*2, M_L + TOL*2, M_BODY + TOL + 2]);
    }
    // Pinos de encaixe painel CLP (lateral direita da base)
    for (p = [[BASE_W+2, 15], [BASE_W+2, 65]])
        translate([p[0], p[1], BASE_H]) cylinder(d=3, h=5);
}


// ═══════════════════════════════════════════════════════════════
//  2. CARCAÇA MOTOR — tampa decorativa sobre motor DC
//     (simula visual WEG trifásico)
//     O motor DC flat encaixa no BOLSO DA BASE embaixo desta carcaça
// ═══════════════════════════════════════════════════════════════
module carcaca_motor() {
    difference() {
        union() {
            // Corpo arredondado (hull = transição suave)
            hull() {
                cube([MOT_W, MOT_L, MOT_H - 8]);
                translate([MOT_W/2, MOT_L/2, MOT_H - 4])
                    scale([1, 0.85, 1]) sphere(d=MOT_W * 0.85);
            }
            // Caixa de bornes lateral
            translate([MOT_W, MOT_L/2 - 6, MOT_H/2])
                cube([7, 12, 10]);
            // Aletas de resfriamento no topo
            for (i = [0:5])
                translate([5 + i*6, 3, MOT_H - 2])
                    cube([4, MOT_L - 6, 5]);
        }
        // Furo para eixo (eixo horizontal, sai pelo lado do redutor)
        translate([MOT_W + 7.5, MOT_L/2, MOT_H/2])
            rotate([0, 90, 0]) cylinder(d=SHAFT_D + 0.4, h=10);
        // Cavidade inferior = encaixa no bolso da base (apenas cobre o motor)
        translate([(MOT_W - M_W)/2, (MOT_L - M_L)/2, -0.5])
            cube([M_W + TOL*2, M_L + TOL*2, M_BODY + TOL + 1]);
        // Furos M3 base (fixa no skid sobre o motor)
        for (x = [5, MOT_W-7], y = [5, MOT_L-7])
            translate([x, y, -0.5]) cylinder(d=3.4, h=WALL+1);
        // Olhal de içamento (detalhe visual, topo)
        translate([MOT_W/2, MOT_L/2, MOT_H + 2])
            cylinder(d=6, h=4);
        translate([MOT_W/2, MOT_L/2, MOT_H + 6])
            rotate_extrude() translate([4, 0]) circle(r=1.5);
    }
}


// ═══════════════════════════════════════════════════════════════
//  3. REDUTOR — caixa decorativa entre motor e tambor (28×28×30mm)
// ═══════════════════════════════════════════════════════════════
module redutor() {
    difference() {
        union() {
            hull() {
                cube([RED_W, RED_L, RED_H - 5]);
                translate([3, 3, RED_H-5]) cube([RED_W-6, RED_L-6, 5]);
            }
            // Tampa de inspeção
            translate([RED_W/2-8, RED_L/2-6, RED_H-1]) cube([16, 12, 4]);
        }
        // Furo eixo (passa de lado a lado — horizontal)
        translate([-0.5, RED_L/2, RED_H/2])
            rotate([0, 90, 0]) cylinder(d=SHAFT_D + 0.4, h=RED_W+1);
        // Furos M3 base
        for (x = [4, RED_W-6], y = [4, RED_L-6])
            translate([x, y, -0.5]) cylinder(d=3.4, h=WALL+1);
    }
}


// ═══════════════════════════════════════════════════════════════
//  4. TAMBOR MOINHO — cilindro giratório ø70 × 100mm
//     Hub dianteiro encaixa no eixo do motor (pressfit ø1.9mm)
// ═══════════════════════════════════════════════════════════════
module tambor_moinho() {
    DRUM_WALL = 3;
    FT = 5;   // espessura flange
    hub_r = 6;
    hub_h = 8;

    difference() {
        union() {
            // Corpo cilíndrico
            cylinder(r=DRUM_R, h=DRUM_L);
            // Flange dianteira
            cylinder(r=FLANGE_R, h=FT);
            // Flange traseira
            translate([0, 0, DRUM_L-FT]) cylinder(r=FLANGE_R, h=FT);
            // Bocal de alimentação (cone, entrada do minério)
            translate([0, 0, FT]) cylinder(r1=11, r2=7, h=18);
            // Hub acoplamento eixo
            translate([0, 0, -hub_h]) cylinder(r=hub_r, h=hub_h+1);
        }
        // Interior oco
        translate([0, 0, FT+3]) cylinder(r=DRUM_R-DRUM_WALL, h=DRUM_L-FT*2-3);
        // Furo do eixo (pressfit)
        translate([0, 0, -hub_h-0.5]) cylinder(d=SHAFT_D, h=hub_h+FT+4);
        // Parafusos decorativos flange dianteira (12×)
        for (a=[0:30:330])
            rotate([0,0,a]) translate([FLANGE_R-4, 0, -0.5])
                cylinder(d=2.5, h=FT+1);
        // Parafusos decorativos flange traseira (12×)
        for (a=[0:30:330])
            rotate([0,0,a]) translate([FLANGE_R-4, 0, DRUM_L-FT-0.5])
                cylinder(d=2.5, h=FT+1);
        // Fundo traseiro aberto para leveza
        translate([0, 0, DRUM_L-FT]) cylinder(r=DRUM_R-DRUM_WALL, h=FT+1);
    }
}


// ═══════════════════════════════════════════════════════════════
//  5. MANCAL TRASEIRO — suporte do lado oposto ao motor (40×30mm)
// ═══════════════════════════════════════════════════════════════
module mancal_traseiro() {
    BW = 40; BL = 30; COL_H = 50;
    difference() {
        union() {
            cube([BW, BL, WALL]);
            translate([BW/2-WALL, 0, 0]) cube([WALL*2, BL, COL_H]);
            translate([BW/2, BL/2, COL_H]) sphere(r=9);
        }
        translate([BW/2, BL/2, COL_H])
            cylinder(d=SHAFT_D+0.4, h=20, center=true);
        for (x=[5, BW-7], y=[5, BL-7])
            translate([x, y, -0.5]) cylinder(d=3.4, h=WALL+1);
    }
}


// ═══════════════════════════════════════════════════════════════
//  6. PAINEL CLP — caixa vertical para ESP32 (44×20×80mm)
// ═══════════════════════════════════════════════════════════════
module painel_clp() {
    PW = ESP_W + WALL*2 + 6;  // ~44mm
    PD = 20;
    PH = 80;
    difference() {
        cube([PW, PD, PH]);
        // Janela ESP32 (frente)
        translate([WALL+3, -0.5, WALL]) cube([ESP_W, WALL+1, ESP_L]);
        // Furo USB (lateral)
        translate([-0.5, PD/2-4.5, WALL+2]) cube([WALL+1, 9, 4]);
        // Furos ventilação topo
        for (i=[0:3]) translate([6+i*10, PD/2-4, PH-0.5]) cube([6, 8, WALL+2]);
        // LED status (frente)
        translate([PW/2, -0.5, PH-20]) rotate([-90,0,0]) cylinder(d=5.2, h=WALL+1);
        // Furos M3 base
        for (x=[5, PW-7]) translate([x, PD/2, -0.5]) cylinder(d=3.4, h=WALL+1);
    }
}


// ═══════════════════════════════════════════════════════════════
//  VISUALIZAÇÃO MONTADA
// ═══════════════════════════════════════════════════════════════
module visualizacao_completa() {
    // Base
    color("#3355aa") base_moinho();

    // Motor DC real (laranja = placeholder, NÃO imprimir)
    translate([12 + TOL, BASE_L/2 - M_L/2 + TOL, BASE_H - M_BODY - 1 + TOL])
        motor_placeholder();

    // Carcaça sobre o motor
    color("#2255aa")
    translate([12 + (MOT_W - M_W)/2 - (MOT_W-M_W)/2,
               BASE_L/2 - MOT_L/2,
               BASE_H - M_BODY - 1])
        carcaca_motor();

    // Redutor
    color("#555555")
    translate([12 + MOT_W + 4, BASE_L/2 - RED_L/2, BASE_H])
        redutor();

    // Tambor (eixo horizontal → rotate 90° em Y)
    color("#dd6600")
    translate([12 + MOT_W + 4 + RED_W + 2, BASE_L/2, BASE_H + RED_H/2])
        rotate([0, 90, 0]) tambor_moinho();

    // Mancal traseiro
    color("#888888")
    translate([12 + MOT_W + 4 + RED_W + 2 + DRUM_L + 5,
               BASE_L/2 - 20, BASE_H])
        mancal_traseiro();

    // Painel CLP (vertical, lateral)
    color("#aabbdd")
    translate([BASE_W + 12, BASE_L/2 - 20, 0])
        painel_clp();
}


// ═══════════════════════════════════════════════════════════════
//  RENDER — descomente UMA linha por vez para exportar STL
//  (ou descomente visualizacao_completa para ver tudo montado)
// ═══════════════════════════════════════════════════════════════

// base_moinho();          // peca_1 — ~3h impressão
// carcaca_motor();        // peca_2 — ~1.5h
// redutor();              // peca_3 — ~30min
// tambor_moinho();        // peca_4 — ~2h
// mancal_traseiro();      // peca_5 — ~45min
// painel_clp();           // peca_6 — ~1.5h

visualizacao_completa();   // prévia montada (não exportar)
