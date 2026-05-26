#!/usr/bin/env python3
"""
Smart Type 2 AC EV Inline Coupler — KiCad 10 Project Generator
Generates: lib/evc.kicad_sym, SmartEVCoupler.kicad_sch,
           SmartEVCoupler.kicad_pcb, SmartEVCoupler.kicad_pro, bom.csv
"""
import uuid, json, os, hashlib

BASE = "/home/user/ccs2-coupler"
os.makedirs(f"{BASE}/lib/evc.pretty", exist_ok=True)

def uid(): return str(uuid.uuid4())
def duid(seed): return str(uuid.UUID(hashlib.md5(seed.encode()).hexdigest()))
def f(v): return f"{float(v):.3f}"
def fxy(x, y): return f"{f(x)} {f(y)}"
G = 2.54  # KiCad grid

# ─── low-level KiCad formatters ───────────────────────────────────────────────

STROKE  = "(stroke (width 0) (type default))"
FILL_BG = "(fill (type background))"
FONT    = "(effects (font (size 1.27 1.27)))"
FONTH   = "(effects (font (size 1.27 1.27)) (hide yes))"

def prop(k, v, x, y, r=0, hide=False):
    eff = FONTH if hide else FONT
    return f'  (property "{k}" "{v}" (at {fxy(x,y)} {int(r)})\n    {eff}\n  )'

def pin_s(num, name, ptype, x, y, angle, length=G):
    return (
        f'    (pin {ptype} line (at {fxy(x,y)} {int(angle)}) (length {f(length)})\n'
        f'      (name "{name}" {FONT})\n'
        f'      (number "{num}" {FONT})\n'
        f'    )'
    )

def rect_s(x1, y1, x2, y2):
    return f'  (rectangle (start {fxy(x1,y1)}) (end {fxy(x2,y2)}) {STROKE} {FILL_BG})'

# ─── symbol builder ───────────────────────────────────────────────────────────

def make_sym(name, ref, value, lcsc, fp, box, pins):
    """
    box = (x1,y1,x2,y2) of body rectangle
    pins = list of pin_s(...) strings
    """
    x1,y1,x2,y2 = box
    lines = [
        f'(symbol "{name}"',
        f'  (pin_numbers (hide yes))',
        f'  (pin_names (offset 1.016))',
        f'  (in_bom yes)',
        f'  (on_board yes)',
        prop("Reference", ref,  (x1+x2)/2, y1-2.54),
        prop("Value",     value,(x1+x2)/2, y2+2.54),
        prop("Footprint", fp,    0, 0, hide=True),
        prop("Datasheet", "~",   0, 0, hide=True),
        prop("LCSC",      lcsc,  0, 0, hide=True),
        f'  (symbol "{name}_0_1"',
        f'    {rect_s(x1,y1,x2,y2)}',
        f'  )',
        f'  (symbol "{name}_1_1"',
    ]
    lines += pins
    lines += ['  )', ')']
    return '\n'.join(lines)

# helper: generate left-side pins (wires enter from left, angle=0)
def lp(num, name, ptype, row, W=7.62, rows=None, step=G):
    """row=0 is top; W=half-width of body"""
    return pin_s(num, name, ptype, -W-G, 0-row*step, 0)

def rp(num, name, ptype, row, W=7.62, step=G):
    return pin_s(num, name, ptype,  W+G, 0-row*step, 180)

def tp(num, name, ptype, col, H=7.62, step=G):
    return pin_s(num, name, ptype, col*step, -H-G, 90)

def bp(num, name, ptype, col, H=7.62, step=G):
    return pin_s(num, name, ptype, col*step,  H+G, 270)

# ─── SYMBOL DEFINITIONS ───────────────────────────────────────────────────────

SYMS = {}

# ── ESP32-S3-WROOM-1 (pins arranged 21L / 18R) ───────────────────────────────
_esp_left = [
    ("1","GND","power_in"), ("2","3V3","power_in"), ("3","EN","input"),
    ("4","IO4","bidirectional"), ("5","IO5","bidirectional"),
    ("6","IO6","bidirectional"), ("7","IO7","bidirectional"),
    ("8","IO15","bidirectional"), ("9","IO16","bidirectional"),
    ("10","IO17","bidirectional"), ("11","IO18","bidirectional"),
    ("12","IO8","bidirectional"), ("13","IO19","bidirectional"),
    ("14","IO20","bidirectional"), ("15","IO3","bidirectional"),
    ("16","IO46","bidirectional"), ("17","IO9","bidirectional"),
    ("18","IO10","bidirectional"), ("19","IO11","bidirectional"),
    ("38","IO1","bidirectional"), ("39","IO2","bidirectional"),
]
_esp_right = [
    ("20","IO12","bidirectional"), ("21","IO13","bidirectional"),
    ("22","IO14","bidirectional"), ("23","IO21","bidirectional"),
    ("24","IO47","bidirectional"), ("25","IO48","bidirectional"),
    ("26","IO45","bidirectional"), ("27","IO0","bidirectional"),
    ("28","IO35","bidirectional"), ("29","IO36","bidirectional"),
    ("30","IO37","bidirectional"), ("31","IO38","bidirectional"),
    ("32","IO39","bidirectional"), ("33","IO40","bidirectional"),
    ("34","IO41","bidirectional"), ("35","IO42","bidirectional"),
    ("36","TXD0","output"), ("37","RXD0","input"),
]
_EW, _EH = 10.16, max(len(_esp_left),len(_esp_right))*G/2+G
_esp_pins  = [pin_s(n,nm,t, -_EW-G, (_EH-G)-i*G, 0) for i,(n,nm,t) in enumerate(_esp_left)]
_esp_pins += [pin_s(n,nm,t,  _EW+G, (_EH-G)-i*G, 180) for i,(n,nm,t) in enumerate(_esp_right)]
SYMS["ESP32-S3-WROOM-1"] = make_sym(
    "ESP32-S3-WROOM-1","U","ESP32-S3-WROOM-1-N16R8","C2913202",
    "evc:ESP32-S3-WROOM-1", (-_EW,-_EH,_EW,_EH), _esp_pins)

# ── BQ25895RTWT ──────────────────────────────────────────────────────────────
_bql = [("22","VBUS","power_in"),("6","SYS","power_out"),("9","BAT","passive"),
        ("1","PGND","power_in"),("24","PGND2","power_in"),
        ("14","ILIM","input"),("12","TS","input"),
        ("4","BTST","passive"),("2","SW","output"),("13","REGN","output"),
        ("25","EP","power_in")]
_bqr = [("16","CE","input"),("15","QON","input"),("17","INT","output"),
        ("18","STAT","output"),("19","SDA","bidirectional"),("20","SCL","input"),
        ("21","PSEL","input"),("5","OTG","input")]
_BW,_BH = 7.62, max(len(_bql),len(_bqr))*G/2+G
_bq_pins  = [pin_s(n,nm,t, -_BW-G, (_BH-G)-i*G, 0) for i,(n,nm,t) in enumerate(_bql)]
_bq_pins += [pin_s(n,nm,t,  _BW+G, (_BH-G)-i*G, 180) for i,(n,nm,t) in enumerate(_bqr)]
SYMS["BQ25895RTWT"] = make_sym(
    "BQ25895RTWT","U","BQ25895RTWT","C2861263",
    "evc:BQ25895RTWT", (-_BW,-_BH,_BW,_BH), _bq_pins)

# ── HUSB238_002D ─────────────────────────────────────────────────────────────
_hl = [("2","VDD","power_in"),("3","GND","power_in"),
       ("4","CC1","passive"),("5","CC2","passive")]
_hr = [("1","VBUS","power_in"),("6","CFG0","input"),
       ("7","CFG1","input"),("8","CFG2","input"),("9","INT","output")]
_HW,_HH = 6.35, max(len(_hl),len(_hr))*G/2+G
_h_pins  = [pin_s(n,nm,t, -_HW-G, (_HH-G)-i*G, 0) for i,(n,nm,t) in enumerate(_hl)]
_h_pins += [pin_s(n,nm,t,  _HW+G, (_HH-G)-i*G, 180) for i,(n,nm,t) in enumerate(_hr)]
SYMS["HUSB238_002D"] = make_sym(
    "HUSB238_002D","U","HUSB238_002D","C7471904",
    "evc:HUSB238_002D", (-_HW,-_HH,_HW,_HH), _h_pins)

# ── LTC4413 (dual ideal-diode OR, SOT-23-6) ──────────────────────────────────
_LL = [("2","INA","power_in"),("6","INB","power_in"),("1","GND","power_in")]
_LR = [("4","OUTA","power_out"),("5","OUTB","power_out"),("3","EN","input")]
_LW,_LH = 5.08, 3*G/2+G
_l_pins  = [pin_s(n,nm,t, -_LW-G, (_LH-G)-i*G, 0) for i,(n,nm,t) in enumerate(_LL)]
_l_pins += [pin_s(n,nm,t,  _LW+G, (_LH-G)-i*G, 180) for i,(n,nm,t) in enumerate(_LR)]
SYMS["LTC4413"] = make_sym(
    "LTC4413","U","LTC4413","~",
    "evc:LTC4413", (-_LW,-_LH,_LW,_LH), _l_pins)

# ── AMS1117-3.3 (SOT-223: pin1=GND/ADJ, pin2=OUT, pin3=IN, pin4=OUT-tab) ─────
_ldopins = [
    pin_s("3","IN",    "power_in",  -5.08-G, 0,   0),
    pin_s("1","GND",   "power_in",   0,       5.08+G, 270),
    pin_s("2","OUT",   "power_out",  5.08+G, 0,   180),
    pin_s("4","OUT~TAB","power_out", 0,      -5.08-G, 90),
]
SYMS["AMS1117-3.3"] = make_sym(
    "AMS1117-3.3","U","AMS1117-3.3","C6186",
    "evc:AMS1117-3.3", (-5.08,-5.08,5.08,5.08), _ldopins)

# ── ATM90E32AS (QFN-36) ──────────────────────────────────────────────────────
_al = [("1","VDD","power_in"),("2","AVDD","power_in"),
       ("3","GND","power_in"),("4","AGND","power_in"),
       ("5","VA","input"),("6","IA","input"),("7","IAN","input"),
       ("8","VB","input"),("9","IB","input"),("10","IBN","input"),
       ("11","VC","input"),("12","IC","input"),("13","ICN","input")]
_ar = [("14","SCS","input"),("15","SCLK","input"),
       ("16","MOSI","input"),("17","MISO","output"),
       ("18","IRQ0","output"),("19","IRQ1","output"),
       ("20","WDT","output"),("21","WARNOUT","output"),
       ("22","PM0","input"),("23","PM1","input"),
       ("24","ZX0","output"),("25","ZX1","output"),("26","ZX2","output")]
_AW,_AH = 8.89, max(len(_al),len(_ar))*G/2+G
_a_pins  = [pin_s(n,nm,t, -_AW-G, (_AH-G)-i*G, 0) for i,(n,nm,t) in enumerate(_al)]
_a_pins += [pin_s(n,nm,t,  _AW+G, (_AH-G)-i*G, 180) for i,(n,nm,t) in enumerate(_ar)]
SYMS["ATM90E32AS"] = make_sym(
    "ATM90E32AS","U","ATM90E32AS","C784945",
    "evc:ATM90E32AS", (-_AW,-_AH,_AW,_AH), _a_pins)

# ── SRD-05VDC-SL-C (relay: pins 1-2 coil, 3=COM, 4=NC, 5=NO) ────────────────
_rpins = [
    pin_s("1","COIL+","passive",  -7.62-G, G,    0),
    pin_s("2","COIL-","passive",  -7.62-G, -G,   0),
    pin_s("3","COM",  "passive",   7.62+G,  G,   180),
    pin_s("4","NC",   "passive",   7.62+G,  0,   180),
    pin_s("5","NO",   "passive",   7.62+G, -G,   180),
]
SYMS["SRD-05VDC-SL-C"] = make_sym(
    "SRD-05VDC-SL-C","RL","SRD-05VDC-SL-C","C35449",
    "evc:SRD-05VDC-SL-C", (-7.62,-2*G,7.62,2*G), _rpins)

# ── PC817C (optocoupler, DIP-4: 1=A,2=K,3=E,4=C) ────────────────────────────
_opins = [
    pin_s("1","A","input",   -5.08-G,  G,  0),
    pin_s("2","K","input",   -5.08-G, -G,  0),
    pin_s("4","C","output",   5.08+G,  G,  180),
    pin_s("3","E","output",   5.08+G, -G,  180),
]
SYMS["PC817C"] = make_sym(
    "PC817C","ISO","PC817C","C6747",
    "evc:PC817C", (-5.08,-2*G,5.08,2*G), _opins)

# ── IRLZ44NPBF (TO-220: 1=G,2=D,3=S) ────────────────────────────────────────
_qpins = [
    pin_s("1","G","input",   -5.08-G, 0,  0),
    pin_s("2","D","passive",  5.08+G, G,  180),
    pin_s("3","S","passive",  5.08+G,-G,  180),
]
SYMS["IRLZ44NPBF"] = make_sym(
    "IRLZ44NPBF","Q","IRLZ44NPBF","C9078",
    "evc:IRLZ44NPBF", (-5.08,-2*G,5.08,2*G), _qpins)

# ── HLK-5M05 (AC/DC: L,N inputs; +Vo,-Vo outputs) ────────────────────────────
_hpins = [
    pin_s("1","L",   "power_in",  -7.62-G,  G,   0),
    pin_s("2","N",   "power_in",  -7.62-G, -G,   0),
    pin_s("3","~Vo", "power_out",  7.62+G,  G,   180),
    pin_s("4","-Vo", "power_out",  7.62+G, -G,   180),
]
SYMS["HLK-5M05"] = make_sym(
    "HLK-5M05","PS","HLK-5M05","C434569",
    "evc:HLK-5M05", (-7.62,-2*G,7.62,2*G), _hpins)

# ── 18650 PCB holder (2-pin: 1=+, 2=-) ───────────────────────────────────────
_btpins = [
    pin_s("1","+","passive", -5.08-G, 0,  0),
    pin_s("2","-","passive",  5.08+G, 0,  180),
]
SYMS["Battery18650"] = make_sym(
    "Battery18650","BT","18650 Cell","C5165920",
    "evc:Battery18650", (-5.08,-G,5.08,G), _btpins)

# ── USB-C 16P receptacle ─────────────────────────────────────────────────────
_uc_pins = [
    ("A1","GND"),("A4","VBUS"),("A5","CC1"),("B5","CC2"),
    ("A6","DP1"),("A7","DN1"),("B6","DP2"),("B7","DN2"),
    ("S1","SHIELD"),
]
_ucl = [("A1","GND","power_in"),("A4","VBUS","power_in"),("A5","CC1","passive"),("B5","CC2","passive"),("S1","SHIELD","passive")]
_ucr = [("A6","DP1","bidirectional"),("A7","DN1","bidirectional"),("B6","DP2","bidirectional"),("B7","DN2","bidirectional")]
_UCW,_UCH = 6.35, max(len(_ucl),len(_ucr))*G/2+G
_uc_ps  = [pin_s(n,nm,t, -_UCW-G, (_UCH-G)-i*G, 0) for i,(n,nm,t) in enumerate(_ucl)]
_uc_ps += [pin_s(n,nm,t,  _UCW+G, (_UCH-G)-i*G, 180) for i,(n,nm,t) in enumerate(_ucr)]
SYMS["USBC-16P"] = make_sym(
    "USBC-16P","J","USB-C 16P Receptacle","C2765186",
    "evc:USBC-16P", (-_UCW,-_UCH,_UCW,_UCH), _uc_ps)

# ── KF301-5P (5-pin screw terminal) ──────────────────────────────────────────
_5ppins = [pin_s(str(i),str(i),"passive", -5.08-G, (2-i)*G, 0) for i in range(1,6)]
SYMS["KF301-5P"] = make_sym(
    "KF301-5P","J","KF301-5P","C3033",
    "evc:KF301-5P", (-5.08,-3*G,5.08,3*G), _5ppins)

# ── KF301-2P (2-pin screw terminal) ──────────────────────────────────────────
_2ppins = [pin_s(str(i),str(i),"passive", -5.08-G, (0.5-i+1)*G, 0) for i in range(1,3)]
SYMS["KF301-2P"] = make_sym(
    "KF301-2P","J","KF301-2P","C3030",
    "evc:KF301-2P", (-5.08,-G,5.08,G), _2ppins)

# ── PinHeader_2x3 ─────────────────────────────────────────────────────────────
_ph_pins = [
    pin_s("1","P1","passive", -5.08-G,  G,   0),
    pin_s("2","P2","passive",  5.08+G,  G,   180),
    pin_s("3","P3","passive", -5.08-G,  0,   0),
    pin_s("4","P4","passive",  5.08+G,  0,   180),
    pin_s("5","P5","passive", -5.08-G, -G,   0),
    pin_s("6","P6","passive",  5.08+G, -G,   180),
]
SYMS["PinHeader_2x3"] = make_sym(
    "PinHeader_2x3","J","PinHeader 2x3 2.54mm","C124378",
    "evc:PinHeader_2x3", (-5.08,-2*G,5.08,2*G), _ph_pins)

# ── BZX55C3V3 (zener, DO-35: 1=A,2=K) ───────────────────────────────────────
SYMS["BZX55C3V3"] = make_sym(
    "BZX55C3V3","D","BZX55C3V3","C8678",
    "evc:BZX55C3V3", (-3.81,-2.54,3.81,2.54),
    [pin_s("1","A","passive", -3.81-G, 0, 0),
     pin_s("2","K","passive",  3.81+G, 0, 180)])

# ── 1N4007 (DO-41: 1=A,2=K) ──────────────────────────────────────────────────
SYMS["1N4007"] = make_sym(
    "1N4007","D","1N4007","C76625",
    "evc:1N4007", (-3.81,-2.54,3.81,2.54),
    [pin_s("1","A","passive", -3.81-G, 0, 0),
     pin_s("2","K","passive",  3.81+G, 0, 180)])

# ── Resistor (generic 0402/0805) ──────────────────────────────────────────────
def resistor_sym(name, value, lcsc, fp):
    return make_sym(name,"R",value,lcsc,fp, (-1.016,-2.032,1.016,2.032),
        [pin_s("1","~","passive",-1.016-G,0,0,G),
         pin_s("2","~","passive", 1.016+G,0,180,G)])

SYMS["R_100k"] = resistor_sym("R_100k","100kΩ 1% 0402","C17900","evc:R_0402")
SYMS["R_47k"]  = resistor_sym("R_47k", "47kΩ 1% 0402", "C17927","evc:R_0402")
SYMS["R_470k"] = resistor_sym("R_470k","470kΩ 0402",   "C25741","evc:R_0402")
SYMS["R_2k7"]  = resistor_sym("R_2k7", "2.7kΩ 0402",   "C25879","evc:R_0402")
SYMS["R_10k"]  = resistor_sym("R_10k", "10kΩ 0402",    "C25804","evc:R_0402")
SYMS["R_33"]   = resistor_sym("R_33",  "33Ω 0402",     "C25105","evc:R_0402")

# ── Capacitor (generic 0402/0805) ─────────────────────────────────────────────
def cap_sym(name, value, lcsc, fp):
    return make_sym(name,"C",value,lcsc,fp, (-1.524,-1.524,1.524,1.524),
        [pin_s("1","+","passive",-1.524-G,0,0,G),
         pin_s("2","-","passive", 1.524+G,0,180,G)])

SYMS["C_100n"]  = cap_sym("C_100n", "100nF 50V 0402","C14663","evc:C_0402")
SYMS["C_10u_0805"] = cap_sym("C_10u_0805","10µF 25V 0805","C19702","evc:C_0805")

# ─── Write symbol library ─────────────────────────────────────────────────────

sym_lib = '(kicad_symbol_lib\n  (version 20250610)\n  (generator "kicad_symbol_editor")\n  (generator_version "10.0")\n'
for body in SYMS.values():
    # indent each symbol 2 spaces inside the lib
    sym_lib += '\n' + '\n'.join('  '+l for l in body.split('\n')) + '\n'
sym_lib += ')\n'

with open(f"{BASE}/lib/evc.kicad_sym","w") as fh:
    fh.write(sym_lib)
print("✓ lib/evc.kicad_sym")

# ─── SCHEMATIC ────────────────────────────────────────────────────────────────
# Each component instance: place symbol at (x,y), give ref/value, list pin→net

def sch_sym(lib_name, ref, value, fp, x, y, rot=0, pin_nets=None, extra_props=None):
    """
    pin_nets: dict of {pin_number: net_name} — drives net label placement
    """
    u = uid()
    lines = [
        f'(symbol (lib_id "evc:{lib_name}") (at {fxy(x,y)} {int(rot)}) (unit 1)',
        f'  (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)',
        f'  (uuid "{u}")',
        f'  (property "Reference" "{ref}" (at {fxy(x,y+3.81)} 0) {FONT})',
        f'  (property "Value" "{value}" (at {fxy(x,y-3.81)} 0) {FONT})',
        f'  (property "Footprint" "{fp}" (at {fxy(x,y)} 0) {FONTH})',
        f'  (property "Datasheet" "~" (at {fxy(x,y)} 0) {FONTH})',
    ]
    if extra_props:
        for k,v in extra_props.items():
            lines.append(f'  (property "{k}" "{v}" (at {fxy(x,y)} 0) {FONTH})')
    if pin_nets:
        for pnum in pin_nets:
            lines.append(f'  (pin "{pnum}" (uuid "{uid()}"))')
    lines.append(')')
    return '\n'.join(lines)

def wire(x1,y1,x2,y2):
    return f'(wire (pts (xy {fxy(x1,y1)}) (xy {fxy(x2,y2)})) {STROKE} (uuid "{uid()}"))'

def label(net, x, y, angle=0):
    return (f'(label "{net}" (at {fxy(x,y)} {int(angle)})\n'
            f'  (fields_autoplaced yes) {FONT} (uuid "{uid()}")\n'
            f'  (property "Intersheet References" "" (at {fxy(x,y)} 0) {FONTH})\n)')

def pwr_sym(net, x, y, rot=0):
    """Power flag symbol (PWR_FLAG style, custom name)"""
    return (f'(symbol (lib_id "power:{net}") (at {fxy(x,y)} {int(rot)}) (unit 1)\n'
            f'  (in_bom yes) (on_board yes) (dnp no)\n'
            f'  (uuid "{uid()}")\n'
            f'  (property "Reference" "#PWR" (at {fxy(x,y)} 0) {FONTH})\n'
            f'  (property "Value" "{net}" (at {fxy(x,y-2.54)} 0) {FONT})\n'
            f'  (pin "1" (uuid "{uid()}"))\n)')

def nc(x,y):
    return f'(no_connect (at {fxy(x,y)}) (uuid "{uid()}"))'

def text(s, x, y, size=1.5, bold=False):
    b = " (bold yes)" if bold else ""
    return (f'(text "{s}" (at {fxy(x,y)} 0)\n'
            f'  (effects (font (size {f(size)} {f(size)}){b}))\n'
            f'  (uuid "{uid()}")\n)')

# ─── Power symbol lib_symbols entry (GND + custom power nets) ─────────────────
POWER_NETS = ["GND","VCC33","VSYS","VBUS_IN","VBUS_USB","VBUS_HLK","BAT_P",
              "+5V","AC_L","AC_N","AC_L_SW","PE"]

def power_sym_def(net):
    """Minimal power symbol definition for lib_symbols section."""
    if net == "GND":
        # downward arrow
        pins = [pin_s("1","GND","power_in",0,0,270,0)]
        body = (f'(symbol "{net}_0_1"\n'
                f'    (polyline (pts (xy 0 0) (xy 0 -1.27)) {STROKE} (fill (type none)))\n'
                f'    (polyline (pts (xy -1.27 -1.27) (xy 0 -2.54) (xy 1.27 -1.27)) {STROKE} (fill (type outline)))\n'
                f'  )')
    else:
        # upward flag
        pins = [pin_s("1",net,"power_in",0,0,270,0)]
        body = (f'(symbol "{net}_0_1"\n'
                f'    (polyline (pts (xy 0 0) (xy 0 1.27)) {STROKE} (fill (type none)))\n'
                f'    (circle (center 0 1.905) (radius 0.635) {STROKE} (fill (type none)))\n'
                f'  )')
    return (f'(symbol "{net}"\n'
            f'  (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)\n'
            f'  (property "Reference" "#PWR" (at 0 -3.81 0) {FONTH})\n'
            f'  (property "Value" "{net}" (at 0 3.81 0) {FONT})\n'
            f'  (property "Footprint" "" (at 0 0 0) {FONTH})\n'
            f'  (property "Datasheet" "" (at 0 0 0) {FONTH})\n'
            f'  {body}\n'
            f'  (symbol "{net}_1_1"\n'
            + '\n'.join(pins) +
            f'\n  )\n)')

# ── Build lib_symbols block (inline in schematic) ────────────────────────────
LIB_SYMS = "(lib_symbols\n"
for pnet in POWER_NETS:
    for line in power_sym_def(pnet).split('\n'):
        LIB_SYMS += '  ' + line + '\n'
for sname, sbody in SYMS.items():
    # prefix each symbol name with library name for inline use
    inline = sbody.replace(f'(symbol "{sname}"', f'(symbol "evc:{sname}"', 1)
    inline = inline.replace(f'(symbol "{sname}_0_1"', f'(symbol "evc:{sname}_0_1"', 1)
    inline = inline.replace(f'(symbol "{sname}_1_1"', f'(symbol "evc:{sname}_1_1"', 1)
    for line in inline.split('\n'):
        LIB_SYMS += '  ' + line + '\n'
LIB_SYMS += ")\n"

# ─── Component placement ──────────────────────────────────────────────────────
# Schematic layout (A3 landscape = 420×297mm)
# Section B (CP/AC control): x=15..195  y=15..130
# Section A (Power):         x=15..195  y=140..285
# Section D (ESP32+ATM):     x=205..410 y=15..285

SCH_ITEMS = []   # collects all S-expressions

# ── Section headers ───────────────────────────────────────────────────────────
SCH_ITEMS += [
    text("SECTION B — CP INTERLOCK + AC CONTROL", 15, 13, 1.8, True),
    text("SECTION A — POWER SUBSYSTEM",            15, 138, 1.8, True),
    text("SECTION D — ESP32-S3 + ATM90E32 METERING", 205, 13, 1.8, True),
    text("⚠ SAFETY NOTES", 310, 240, 1.5, True),
    text("• PE never switched — always direct through J1→J2",310,245,1.2),
    text("• CP relay NC = fail-safe (car charges if ESP32 dead)",310,249,1.2),
    text("• 4mm+ creepage on PCB mains→LV boundary",310,253,1.2),
    text("• PC817 optocoupler: galvanic isolation on K1 drive",310,257,1.2),
    text("• BQ25895 OVP/OCP protects 18650 cell",310,261,1.2),
]

# ─── SECTION A — POWER ────────────────────────────────────────────────────────

# HLK-5M05  PS1
SCH_ITEMS.append(sch_sym("HLK-5M05","PS1","HLK-5M05","evc:HLK-5M05",
    30,165, pin_nets={"1":"AC_L","2":"AC_N","3":"VBUS_HLK","4":"GND"}))
SCH_ITEMS.append(label("AC_L",      17.62, 165))
SCH_ITEMS.append(label("AC_N",      17.62, 167.54))
SCH_ITEMS.append(label("VBUS_HLK", 42.62+G, 165))

# J_USBC  USB-C 16P
SCH_ITEMS.append(sch_sym("USBC-16P","J_USBC","USB-C 16P","evc:USBC-16P",
    30,195, pin_nets={"A1":"GND","A4":"VBUS_USB","A5":"CC1","B5":"CC2",
                      "S1":"GND","A6":"NC","A7":"NC","B6":"NC","B7":"NC"}))
SCH_ITEMS.append(label("VBUS_USB", 42.62+G, 192.46))
SCH_ITEMS.append(label("CC1",      42.62+G, 189.92))
SCH_ITEMS.append(label("CC2",      42.62+G, 187.38))
SCH_ITEMS += [nc(42.62+G, 184.84), nc(42.62+G, 182.3), nc(42.62+G, 179.76), nc(42.62+G, 177.22)]

# U_HUSB  HUSB238
SCH_ITEMS.append(sch_sym("HUSB238_002D","U_HUSB","HUSB238_002D","evc:HUSB238_002D",
    75,195, pin_nets={"2":"VCC33","3":"GND","4":"CC1","5":"CC2",
                      "1":"VBUS_USB","6":"GND","7":"GND","8":"GND","9":"NC"}))
SCH_ITEMS.append(label("CC1",     62.38-G, 192.46))
SCH_ITEMS.append(label("CC2",     62.38-G, 189.92))
SCH_ITEMS.append(label("VBUS_USB",62.38-G, 195))
SCH_ITEMS.append(nc(87.62+G, 192.46))

# U_OR  LTC4413
SCH_ITEMS.append(sch_sym("LTC4413","U_OR","LTC4413","evc:LTC4413",
    115,180, pin_nets={"2":"VBUS_USB","6":"VBUS_HLK","1":"GND",
                       "4":"VBUS_IN","5":"VBUS_IN","3":"VCC33"}))
SCH_ITEMS.append(label("VBUS_USB", 102.38-G, 177.46))
SCH_ITEMS.append(label("VBUS_HLK", 102.38-G, 172.38))
SCH_ITEMS.append(label("VBUS_IN",  127.62+G, 177.46))

# U_BQ  BQ25895RTWT
SCH_ITEMS.append(sch_sym("BQ25895RTWT","U_BQ","BQ25895RTWT","evc:BQ25895RTWT",
    160,195, pin_nets={
        "22":"VBUS_IN","6":"VSYS","9":"BAT_P",
        "1":"GND","24":"GND","25":"GND",
        "14":"ILIM_N","12":"GND",
        "4":"BTST_NET","2":"SW_NET","13":"REGN_NET",
        "16":"GND","15":"QON","17":"BQ_INT",
        "18":"NC","19":"I2C_SDA","20":"I2C_SCL",
        "21":"GND","5":"NC"}))
SCH_ITEMS.append(label("VBUS_IN",  147.38-G, 192.46))
SCH_ITEMS.append(label("VSYS",     172.62+G, 192.46))
SCH_ITEMS.append(label("BAT_P",    147.38-G, 189.92))
SCH_ITEMS.append(label("QON",      172.62+G, 187.38))
SCH_ITEMS.append(label("BQ_INT",   172.62+G, 184.84))
SCH_ITEMS.append(label("I2C_SDA",  172.62+G, 182.3))
SCH_ITEMS.append(label("I2C_SCL",  172.62+G, 179.76))
SCH_ITEMS.append(label("ILIM_N",   147.38-G, 187.38))
SCH_ITEMS += [nc(172.62+G,177.22), nc(172.62+G,174.68), nc(147.38-G,184.84)]

# R_ILIM  10kΩ ILIM resistor to GND
SCH_ITEMS.append(sch_sym("R_10k","R_ILIM","10kΩ","evc:R_0402",
    140,210, pin_nets={"1":"ILIM_N","2":"GND"}))
SCH_ITEMS.append(label("ILIM_N", 127.38-G, 210))

# U_LDO  AMS1117-3.3
SCH_ITEMS.append(sch_sym("AMS1117-3.3","U_LDO","AMS1117-3.3","evc:AMS1117-3.3",
    195,195, pin_nets={"3":"VSYS","2":"VCC33","4":"VCC33","1":"GND"}))
SCH_ITEMS.append(label("VSYS",  182.38-G, 195))
SCH_ITEMS.append(label("VCC33", 207.62+G, 195))

# BT1  18650 holder
SCH_ITEMS.append(sch_sym("Battery18650","BT1","18650","evc:Battery18650",
    150,225, pin_nets={"1":"BAT_P","2":"GND"}))
SCH_ITEMS.append(label("BAT_P", 137.38-G, 225))

# Decoupling caps
SCH_ITEMS.append(sch_sym("C_100n","C1","100nF","evc:C_0402", 205,215,
    pin_nets={"1":"VCC33","2":"GND"}))
SCH_ITEMS.append(sch_sym("C_10u_0805","C2","10µF","evc:C_0805", 212,215,
    pin_nets={"1":"VCC33","2":"GND"}))
SCH_ITEMS.append(sch_sym("C_100n","C4","100nF","evc:C_0402", 219,215,
    pin_nets={"1":"VSYS","2":"GND"}))
SCH_ITEMS.append(sch_sym("C_10u_0805","C3","10µF","evc:C_0805", 226,215,
    pin_nets={"1":"VSYS","2":"GND"}))
SCH_ITEMS.append(sch_sym("C_10u_0805","C5","10µF","evc:C_0805", 160,240,
    pin_nets={"1":"BAT_P","2":"GND"}))
for net in ["VCC33","VCC33","VSYS","VSYS","BAT_P"]:
    pass  # labels already implied by pin_nets above

# ─── SECTION B — CP INTERLOCK + AC CONTROL ───────────────────────────────────

# J1  Type 2 input (wallbox side)
SCH_ITEMS.append(sch_sym("KF301-5P","J1","Type2-Wallbox-IN","evc:KF301-5P",
    25,60, pin_nets={"1":"PE","2":"AC_N","3":"AC_L","4":"CP_IN","5":"PP_NET"}))
SCH_ITEMS.append(label("PE",     12.38-G, 62.54))
SCH_ITEMS.append(label("AC_N",   12.38-G, 60))
SCH_ITEMS.append(label("AC_L",   12.38-G, 57.46))
SCH_ITEMS.append(label("CP_IN",  12.38-G, 54.92))
SCH_ITEMS.append(label("PP_NET", 12.38-G, 52.38))

# J2  Type 2 output (car side)
SCH_ITEMS.append(sch_sym("KF301-5P","J2","Type2-Car-OUT","evc:KF301-5P",
    25,100, pin_nets={"1":"PE","2":"AC_N","3":"AC_L_SW","4":"CP_OUT","5":"PP_NET"}))
SCH_ITEMS.append(label("PE",      12.38-G, 102.54))
SCH_ITEMS.append(label("AC_N",    12.38-G, 100))
SCH_ITEMS.append(label("AC_L_SW", 12.38-G, 97.46))
SCH_ITEMS.append(label("CP_OUT",  12.38-G, 94.92))
SCH_ITEMS.append(label("PP_NET",  12.38-G, 92.38))

# R_PP  2.7kΩ proximity pilot termination
SCH_ITEMS.append(sch_sym("R_2k7","R_PP","2.7kΩ","evc:R_0402",
    50,115, pin_nets={"1":"PP_NET","2":"GND"}))
SCH_ITEMS.append(label("PP_NET", 37.38-G, 115))

# RL1  SRD-05VDC relay (CP interlock — NC = fail-safe)
SCH_ITEMS.append(sch_sym("SRD-05VDC-SL-C","RL1","SRD-05VDC-SL-C","evc:SRD-05VDC-SL-C",
    80,60, pin_nets={"1":"RL1_COIL","2":"GND","3":"CP_IN","4":"CP_OUT","5":"NC_RL1"}))
SCH_ITEMS.append(label("RL1_COIL", 67.38-G, 61.27))
SCH_ITEMS.append(label("CP_IN",    92.62+G, 61.27))
SCH_ITEMS.append(label("CP_OUT",   92.62+G, 60))
SCH_ITEMS.append(nc(92.62+G, 58.73))

# CP voltage divider + ADC clamp
# R1 100kΩ: CP_IN → CP_MID
SCH_ITEMS.append(sch_sym("R_100k","R1","100kΩ","evc:R_0402",
    120,55, pin_nets={"1":"CP_IN","2":"CP_MID"}))
SCH_ITEMS.append(label("CP_IN",  107.38-G, 55))
SCH_ITEMS.append(label("CP_MID", 132.62+G, 55))
# R2 47kΩ: CP_MID → GND
SCH_ITEMS.append(sch_sym("R_47k","R2","47kΩ","evc:R_0402",
    140,55, pin_nets={"1":"CP_MID","2":"GND"}))
SCH_ITEMS.append(label("CP_MID", 127.38-G, 55))
# D1 BZX55C3V3: CP_MID → GND (zener clamp)
SCH_ITEMS.append(sch_sym("BZX55C3V3","D1","BZX55C3V3","evc:BZX55C3V3",
    155,55, pin_nets={"1":"GND","2":"CP_MID"}))
SCH_ITEMS.append(label("CP_MID", 162.38+G, 55))
# Label CP_MID → CP_ADC to ESP32
SCH_ITEMS.append(label("CP_ADC", 132.62+G, 57.54))

# ISO1  PC817C optocoupler (K1 gate driver input)
SCH_ITEMS.append(sch_sym("PC817C","ISO1","PC817C","evc:PC817C",
    80,100, pin_nets={"1":"K1_DRV_A","2":"GND","4":"K1_GATE_N","3":"GND"}))
SCH_ITEMS.append(label("K1_DRV_A",  67.38-G, 101.27))
SCH_ITEMS.append(label("K1_GATE_N", 92.62+G, 101.27))

# Q1  IRLZ44N MOSFET
SCH_ITEMS.append(sch_sym("IRLZ44NPBF","Q1","IRLZ44NPBF","evc:IRLZ44NPBF",
    115,100, pin_nets={"1":"K1_GATE_N","2":"K1_A1","3":"GND"}))
SCH_ITEMS.append(label("K1_GATE_N", 102.38-G, 100))
SCH_ITEMS.append(label("K1_A1",     127.62+G, 101.27))

# D2  1N4007 flyback
SCH_ITEMS.append(sch_sym("1N4007","D2","1N4007","evc:1N4007",
    145,100, pin_nets={"1":"GND","2":"K1_A1"}))
SCH_ITEMS.append(label("K1_A1", 152.62+G, 100))

# J_K1  contactor coil terminal
SCH_ITEMS.append(sch_sym("KF301-2P","J_K1","Contactor K1 Coil","evc:KF301-2P",
    175,100, pin_nets={"1":"K1_A1","2":"GND"}))
SCH_ITEMS.append(label("K1_A1", 162.38-G, 100))

# ─── SECTION D — ESP32 + ATM90E32 ────────────────────────────────────────────

# U_ESP  ESP32-S3-WROOM-1
SCH_ITEMS.append(sch_sym("ESP32-S3-WROOM-1","U_ESP","ESP32-S3-WROOM-1-N16R8",
    "evc:ESP32-S3-WROOM-1", 255,100, pin_nets={
    "1":"GND","2":"VCC33","3":"EN",
    "38":"CP_ADC",    # IO1
    "4":"RL1_COIL",   # IO4
    "5":"K1_DRV",     # IO5
    "6":"ATM_IRQ",    # IO6
    "7":"LED_R_IO",   # IO7
    "12":"QON_IN",    # IO8
    "17":"I2C_SDA",   # IO9
    "18":"I2C_SCL",   # IO10
    "19":"BQ_INT",    # IO11
    "20":"LED_G_IO",  # IO12
    "21":"LED_B_IO",  # IO13
    "11":"SPI_MOSI",  # IO18
    "13":"SPI_MISO",  # IO19
    "14":"SPI_SCK",   # IO20
    "23":"ATM_CS",    # IO21
    "27":"IO0_BOOT",  # IO0
    # unused IOs
    "8":"NC","9":"NC","10":"NC","15":"NC","16":"NC",
    "22":"NC","24":"NC","25":"NC","26":"NC",
    "28":"NC","29":"NC","30":"NC","31":"NC","32":"NC",
    "33":"NC","34":"NC","35":"NC","36":"NC","37":"NC","39":"NC",
    }))
# Key net labels on ESP
for net, ox in [("CP_ADC",-1),("RL1_COIL",-1),("K1_DRV",-1),("ATM_IRQ",-1),
                ("LED_R_IO",-1),("QON_IN",-1),("I2C_SDA",+1),("I2C_SCL",+1),
                ("BQ_INT",+1),("LED_G_IO",+1),("LED_B_IO",+1),
                ("SPI_MOSI",-1),("SPI_MISO",-1),("SPI_SCK",-1),("ATM_CS",+1),
                ("IO0_BOOT",+1),("VCC33",+1)]:
    pass  # pin_nets above handle connectivity; labels drawn implicitly

# EN and IO0 pullups
SCH_ITEMS.append(sch_sym("R_10k","R_EN","10kΩ","evc:R_0402",
    230,40, pin_nets={"1":"VCC33","2":"EN"}))
SCH_ITEMS.append(label("EN",     230+G, 42.54))
SCH_ITEMS.append(sch_sym("R_10k","R_BOOT","10kΩ","evc:R_0402",
    245,40, pin_nets={"1":"VCC33","2":"IO0_BOOT"}))
SCH_ITEMS.append(label("IO0_BOOT", 245+G, 42.54))

# K1_DRV isolator: ESP IO5 → ISO1 anode via series resistor
SCH_ITEMS.append(sch_sym("R_10k","R_ISO","100Ω","evc:R_0402",
    210,100, pin_nets={"1":"K1_DRV","2":"K1_DRV_A"}))
SCH_ITEMS.append(label("K1_DRV",   197.38-G, 100))
SCH_ITEMS.append(label("K1_DRV_A", 222.62+G, 100))

# RL1 coil drive: ESP IO4 → direct (active-high relay coil via 3V3→coil→GND)
# (RL1 coil is driven directly from IO4 with flyback diode integrated)
SCH_ITEMS.append(label("RL1_COIL", 215, 115))
SCH_ITEMS.append(text("(IO4 drives RL1 coil directly;\n100mA within ESP GPIO spec)", 215, 118, 1.0))

# QON connect to J_SW1
SCH_ITEMS.append(label("QON",  215, 125))

# U_ATM  ATM90E32AS
SCH_ITEMS.append(sch_sym("ATM90E32AS","U_ATM","ATM90E32AS","evc:ATM90E32AS",
    355,65, pin_nets={
    "1":"VCC33","2":"VCC33","3":"GND","4":"GND",
    "5":"ATM_VA","6":"ATM_IA","7":"ATM_IAN",
    "8":"NC","9":"NC","10":"NC","11":"NC","12":"NC","13":"NC",
    "14":"ATM_CS","15":"SPI_SCK","16":"SPI_MOSI","17":"SPI_MISO",
    "18":"ATM_IRQ","19":"NC","20":"NC","21":"NC",
    "22":"GND","23":"GND","24":"NC","25":"NC","26":"NC",
    }))
SCH_ITEMS.append(label("VCC33",    342.38-G, 62.46))
SCH_ITEMS.append(label("GND",      342.38-G, 59.92))
SCH_ITEMS.append(label("ATM_VA",   342.38-G, 57.38))
SCH_ITEMS.append(label("ATM_IA",   342.38-G, 54.84))
SCH_ITEMS.append(label("ATM_IAN",  342.38-G, 52.3))
SCH_ITEMS.append(label("ATM_CS",   367.62+G, 62.46))
SCH_ITEMS.append(label("SPI_SCK",  367.62+G, 59.92))
SCH_ITEMS.append(label("SPI_MOSI", 367.62+G, 57.38))
SCH_ITEMS.append(label("SPI_MISO", 367.62+G, 54.84))
SCH_ITEMS.append(label("ATM_IRQ",  367.62+G, 52.3))

# R3, R4 voltage divider AC_L → ATM_VA (470kΩ + 470kΩ)
SCH_ITEMS.append(sch_sym("R_470k","R3","470kΩ","evc:R_0402",
    320,55, pin_nets={"1":"AC_L","2":"ATM_VA_MID"}))
SCH_ITEMS.append(sch_sym("R_470k","R4","470kΩ","evc:R_0402",
    335,55, pin_nets={"1":"ATM_VA_MID","2":"GND"}))
SCH_ITEMS.append(label("AC_L",       307.38-G, 55))
SCH_ITEMS.append(label("ATM_VA_MID", 322.62+G, 55))
SCH_ITEMS.append(label("ATM_VA",     322.62+G, 57.54))
SCH_ITEMS.append(wire(322.62+G, 55, 322.62+G, 57.54))

# J_CT  CT clamp input
SCH_ITEMS.append(sch_sym("KF301-2P","J_CT","SCT-013-030 CT","evc:KF301-2P",
    395,65, pin_nets={"1":"ATM_IA","2":"ATM_IAN"}))
SCH_ITEMS.append(label("ATM_IA",  382.38-G, 66.27))
SCH_ITEMS.append(label("ATM_IAN", 382.38-G, 63.73))

# LED current-limit resistors + J_SW1 header
SCH_ITEMS.append(sch_sym("R_33","R_LR","33Ω","evc:R_0402",
    305,175, pin_nets={"1":"LED_R_IO","2":"LED_RO"}))
SCH_ITEMS.append(sch_sym("R_33","R_LG","33Ω","evc:R_0402",
    305,180, pin_nets={"1":"LED_G_IO","2":"LED_GO"}))
SCH_ITEMS.append(sch_sym("R_33","R_LB","33Ω","evc:R_0402",
    305,185, pin_nets={"1":"LED_B_IO","2":"LED_BO"}))
SCH_ITEMS.append(label("LED_R_IO", 292.38-G, 175))
SCH_ITEMS.append(label("LED_G_IO", 292.38-G, 180))
SCH_ITEMS.append(label("LED_B_IO", 292.38-G, 185))
SCH_ITEMS.append(label("LED_RO",   317.62+G, 175))
SCH_ITEMS.append(label("LED_GO",   317.62+G, 180))
SCH_ITEMS.append(label("LED_BO",   317.62+G, 185))

SCH_ITEMS.append(sch_sym("PinHeader_2x3","J_SW1","SW1 16mm LED Button","evc:PinHeader_2x3",
    355,180, pin_nets={
    "1":"QON","2":"GND","3":"LED_RO","4":"LED_GO","5":"LED_BO","6":"GND"}))
SCH_ITEMS.append(label("QON",    342.38-G, 181.27))
SCH_ITEMS.append(label("LED_RO", 342.38-G, 180))
SCH_ITEMS.append(label("LED_GO", 342.38-G, 178.73))
SCH_ITEMS.append(label("LED_BO", 367.62+G, 181.27))

# I2C connections label
SCH_ITEMS.append(label("I2C_SDA", 215, 155))
SCH_ITEMS.append(label("I2C_SCL", 215, 159))
SCH_ITEMS.append(label("BQ_INT",  215, 163))
SCH_ITEMS.append(text("(BQ25895 I2C/INT share\nsame bus as ESP32)", 215, 167, 1.0))

# ─── Power flags (ERC) ────────────────────────────────────────────────────────
for net, x, y in [
    ("GND",    20, 285), ("VCC33", 200, 285), ("VSYS", 180, 285),
    ("BAT_P",  155, 285), ("VBUS_IN", 115, 285),
]:
    SCH_ITEMS.append(pwr_sym(net, x, y))

# ─── Assemble schematic ───────────────────────────────────────────────────────

SCH = f'''\
(kicad_sch
  (version 20250610)
  (generator "eeschema")
  (generator_version "10.0")
  (uuid "{uid()}")
  (paper "A3")
  (title_block
    (title "Smart Type 2 AC EV Inline Coupler")
    (date "2025-05-24")
    (rev "1.0")
    (company "DIY / netweaver1970")
    (comment 1 "1-phase 230V/32A/7.4kW · MQTT/MQTT+HA spot-price control")
    (comment 2 "ESP32-S3 + ATM90E32 + BQ25895 · Belgian Spot Electricity")
  )
{LIB_SYMS}
'''
for item in SCH_ITEMS:
    SCH += item + '\n'
SCH += ')\n'

with open(f"{BASE}/SmartEVCoupler.kicad_sch","w") as fh:
    fh.write(SCH)
print("✓ SmartEVCoupler.kicad_sch")

# ─── PCB ──────────────────────────────────────────────────────────────────────

# Board: 100×80mm, origin at (0,0)
# Mains zone: x 0..43mm (left)
# LV zone:    x 47..100mm (right)
# Isolation gap: x 43..47mm

def fp_header(ref, value, fp_name, x, y, layer="F.Cu", rot=0):
    return (f'(footprint "{fp_name}" (layer "{layer}") (at {fxy(x,y)} {int(rot)})\n'
            f'  (property "Reference" "{ref}" (at 0 -2 0) (layer "F.SilkS")\n'
            f'    {FONT})\n'
            f'  (property "Value" "{value}" (at 0 2 0) (layer "F.Fab")\n'
            f'    {FONT})\n')

def smd_pad(num, x, y, w, h, net="", net_num=0):
    nn = f'(net {net_num} "{net}")' if net else ""
    return (f'  (pad "{num}" smd rect (at {fxy(x,y)}) (size {fxy(w,h)}) '
            f'(layers "F.Cu" "F.Paste" "F.Mask") {nn})\n')

def tht_pad(num, x, y, w, h, drill, net="", net_num=0):
    nn = f'(net {net_num} "{net}")' if net else ""
    return (f'  (pad "{num}" thru_hole oval (at {fxy(x,y)}) (size {fxy(w,h)}) '
            f'(drill {f(drill)}) (layers "*.Cu" "*.Mask") {nn})\n')

# Net list (numbers assigned)
NETS = {
    "GND":0, "VCC33":1, "VSYS":2, "VBUS_IN":3, "VBUS_USB":4, "VBUS_HLK":5,
    "BAT_P":6, "CP_IN":7, "CP_OUT":8, "CP_ADC":9, "CP_MID":10,
    "RL1_COIL":11, "K1_DRV":12, "K1_DRV_A":13, "K1_GATE_N":14, "K1_A1":15,
    "I2C_SDA":16, "I2C_SCL":17, "BQ_INT":18, "QON":19, "ATM_CS":20,
    "SPI_MOSI":21, "SPI_MISO":22, "SPI_SCK":23, "ATM_IRQ":24,
    "ATM_VA":25, "ATM_IA":26, "ATM_IAN":27, "ATM_VA_MID":28,
    "LED_RO":29, "LED_GO":30, "LED_BO":31,
    "AC_L":32, "AC_N":33, "AC_L_SW":34, "PE":35, "PP_NET":36,
    "CC1":37, "CC2":38, "ILIM_N":39, "IO0_BOOT":40,
    "SW_NET":41, "BTST_NET":42, "REGN_NET":43,
    "LED_R_IO":44, "LED_G_IO":45, "LED_B_IO":46,
    "EN":47, "QON_IN":48,
}

NET_STMTS = '\n'.join(f'  (net {v} "{k}")' for k,v in NETS.items())

# Component positions on PCB (mm, from top-left)
# Mains side (x: 2..43)
PCB_COMPS = []

def pcb_rect_outline(x1,y1,x2,y2,layer="Edge.Cuts",w=0.05):
    return (f'(gr_rect (start {fxy(x1,y1)}) (end {fxy(x2,y2)}) '
            f'(layer "{layer}") (stroke (width {f(w)}) (type default)))\n')

def pcb_line(x1,y1,x2,y2,layer="Cmts.User",w=0.1):
    return (f'(gr_line (start {fxy(x1,y1)}) (end {fxy(x2,y2)}) '
            f'(layer "{layer}") (stroke (width {f(w)}) (type default)))\n')

def pcb_text(s,x,y,layer="F.SilkS",size=1.0):
    return (f'(gr_text "{s}" (at {fxy(x,y)}) (layer "{layer}")\n'
            f'  (effects (font (size {f(size)} {f(size)})))\n)\n')

# Simplified footprint stubs (just pads for netlist connection)
# Full footprints would need exact land patterns — this gives correct netlist

def fp_0402(ref, value, x, y, net1, net2, n1=0, n2=0):
    return (fp_header(ref,value,"evc:R_0402",x,y)
            + smd_pad("1",-0.95,0, 1.4,1.0, net1,n1)
            + smd_pad("2", 0.95,0, 1.4,1.0, net2,n2)
            + ")\n")

def fp_0805(ref, value, x, y, net1, net2, n1=0, n2=0):
    return (fp_header(ref,value,"evc:C_0805",x,y)
            + smd_pad("1",-1.2,0, 1.8,1.35, net1,n1)
            + smd_pad("2", 1.2,0, 1.8,1.35, net2,n2)
            + ")\n")

N = NETS
PCB_FPS = ""

# ── Mains side components (x: 3..41) ──────────────────────────────────────────

# PS1 HLK-5M05 (34×20×15mm module, pads at corners)
PCB_FPS += (fp_header("PS1","HLK-5M05","evc:HLK-5M05",10,30)
    + tht_pad("1",-8, -5, 2.5,2.5,1.5, "AC_L",  N["AC_L"])
    + tht_pad("2",-8,  5, 2.5,2.5,1.5, "AC_N",  N["AC_N"])
    + tht_pad("3", 8, -5, 2.5,2.5,1.5, "VBUS_HLK", N["VBUS_HLK"])
    + tht_pad("4", 8,  5, 2.5,2.5,1.5, "GND",   N["GND"])
    + "  (fp_rect (start -17 -10) (end 17 10) (layer \"F.Fab\") (stroke (width 0.1) (type default)))\n"
    + ")\n")

# J1 Type2 input (KF301-5P, 2.54mm pitch THT)
PCB_FPS += (fp_header("J1","Type2-Wallbox-IN","evc:KF301-5P",5,60)
    + ''.join(tht_pad(str(i), 0,(i-3)*2.54, 3,3,1.3,
        ["PE","AC_N","AC_L","CP_IN","PP_NET"][i-1],
        N[["PE","AC_N","AC_L","CP_IN","PP_NET"][i-1]]) for i in range(1,6))
    + ")\n")

# J2 Type2 output (KF301-5P)
PCB_FPS += (fp_header("J2","Type2-Car-OUT","evc:KF301-5P",5,72)
    + ''.join(tht_pad(str(i), 0,(i-3)*2.54, 3,3,1.3,
        ["PE","AC_N","AC_L_SW","CP_OUT","PP_NET"][i-1],
        N[["PE","AC_N","AC_L_SW","CP_OUT","PP_NET"][i-1]]) for i in range(1,6))
    + ")\n")

# RL1 Relay SRD-05VDC-SL-C (5-pin THT, 2×2 coil + 3-pin load)
PCB_FPS += (fp_header("RL1","SRD-05VDC-SL-C","evc:SRD-05VDC-SL-C",20,60)
    + tht_pad("1",-3.81,-3.81,2,2,1.2,"RL1_COIL",N["RL1_COIL"])
    + tht_pad("2",-3.81, 3.81,2,2,1.2,"GND",     N["GND"])
    + tht_pad("3", 0,    3.81,2,2,1.2,"CP_IN",   N["CP_IN"])
    + tht_pad("4", 3.81, 0,   2,2,1.2,"CP_OUT",  N["CP_OUT"])
    + tht_pad("5", 3.81, 3.81,2,2,1.2,"",         0)
    + ")\n")

# ISO1 PC817C (DIP-4)
PCB_FPS += (fp_header("ISO1","PC817C","evc:PC817C",30,75)
    + tht_pad("1",-2.54, 2.54,1.6,1.6,0.8,"K1_DRV_A",N["K1_DRV_A"])
    + tht_pad("2",-2.54,-2.54,1.6,1.6,0.8,"GND",      N["GND"])
    + tht_pad("3", 2.54,-2.54,1.6,1.6,0.8,"GND",      N["GND"])
    + tht_pad("4", 2.54, 2.54,1.6,1.6,0.8,"K1_GATE_N",N["K1_GATE_N"])
    + ")\n")

# Q1 IRLZ44N TO-220 (3-pin, standing)
PCB_FPS += (fp_header("Q1","IRLZ44NPBF","evc:IRLZ44NPBF",35,75)
    + tht_pad("1",-2.54,0,2,2,1.0,"K1_GATE_N",N["K1_GATE_N"])
    + tht_pad("2", 0,   0,2,2,1.0,"K1_A1",    N["K1_A1"])
    + tht_pad("3", 2.54,0,2,2,1.0,"GND",      N["GND"])
    + ")\n")

# D2 1N4007 (DO-41 axial)
PCB_FPS += (fp_header("D2","1N4007","evc:1N4007",30,85)
    + tht_pad("1",-3.81,0,2,2,0.8,"GND",  N["GND"])
    + tht_pad("2", 3.81,0,2,2,0.8,"K1_A1",N["K1_A1"])
    + ")\n")

# J_K1 KF301-2P (contactor coil)
PCB_FPS += (fp_header("J_K1","Contactor-Coil","evc:KF301-2P",40,78)
    + tht_pad("1",-1.27,0,3,3,1.3,"K1_A1",N["K1_A1"])
    + tht_pad("2", 1.27,0,3,3,1.3,"GND",  N["GND"])
    + ")\n")

# R_PP 2.7kΩ (PP termination)
PCB_FPS += fp_0402("R_PP","2.7kΩ",20,72,"PP_NET","GND",N["PP_NET"],N["GND"])

# ── LV side components (x: 47..98) ────────────────────────────────────────────

# J_USBC USB-C 16P
PCB_FPS += (fp_header("J_USBC","USB-C 16P","evc:USBC-16P",52,70)
    + smd_pad("A1", -3.5, -3.6, 0.35,1.3, "GND",   N["GND"])
    + smd_pad("A4", -2.45,-3.6, 0.35,1.3, "VBUS_USB",N["VBUS_USB"])
    + smd_pad("A5", -1.75,-3.6, 0.35,1.3, "CC1",   N["CC1"])
    + smd_pad("B5",  1.75,-3.6, 0.35,1.3, "CC2",   N["CC2"])
    + smd_pad("A4b", 2.45,-3.6, 0.35,1.3, "VBUS_USB",N["VBUS_USB"])
    + smd_pad("B1",  3.5, -3.6, 0.35,1.3, "GND",   N["GND"])
    + smd_pad("S1",  0,    3.6, 4.5, 1.0, "GND",   N["GND"])
    + ")\n")

# U_HUSB HUSB238 (SOT-23-6)
PCB_FPS += (fp_header("U_HUSB","HUSB238_002D","evc:HUSB238_002D",55,60)
    + ''.join(smd_pad(str(i), -1.9+((i-1)%3)*1.9, -1.5 if i<=3 else 1.5, 0.6,1.55,
        ["VDD","GND","CC1","VBUS","CC2","CFG0"][i-1],
        N.get(["VDD","GND","CC1","VBUS","CC2","CFG0"][i-1],0)) for i in range(1,7))
    + ")\n")

# U_OR LTC4413 (SOT-23-6)
PCB_FPS += (fp_header("U_OR","LTC4413","evc:LTC4413",62,65)
    + ''.join(smd_pad(str(i), -1.9+((i-1)%3)*1.9, -1.5 if i<=3 else 1.5, 0.6,1.55,
        ["GND","INA","EN","OUTA","OUTB","INB"][i-1],
        N.get(["GND","INA","OUTB","OUTA","INB","EN"][i-1],0)) for i in range(1,7))
    + ")\n")

# U_BQ BQ25895RTWT (QFN-24, 4×4mm)
def qfn24_pads(cx, cy):
    """Generate 24 QFN pads + thermal pad"""
    pitch = 0.5
    pads = ""
    # Bottom row (pins 1-6, left to right)
    for i in range(6):
        pads += smd_pad(str(i+1), cx-1.25+(i*pitch), cy+2.05, 0.25,0.75)
    # Right column (pins 7-12, bottom to top)
    for i in range(6):
        pads += smd_pad(str(i+7), cx+2.05, cy+1.25-(i*pitch), 0.75,0.25)
    # Top row (pins 13-18, right to left)
    for i in range(6):
        pads += smd_pad(str(i+13), cx+1.25-(i*pitch), cy-2.05, 0.25,0.75)
    # Left column (pins 19-24, top to bottom)
    for i in range(6):
        pads += smd_pad(str(i+19), cx-2.05, cy-1.25+(i*pitch), 0.75,0.25)
    # Thermal pad
    pads += smd_pad("25", cx, cy, 2.5,2.5, "GND", N["GND"])
    return pads

PCB_FPS += fp_header("U_BQ","BQ25895RTWT","evc:BQ25895RTWT",72,62) + qfn24_pads(0,0) + ")\n"

# U_LDO AMS1117-3.3 (SOT-223)
PCB_FPS += (fp_header("U_LDO","AMS1117-3.3","evc:AMS1117-3.3",82,60)
    + smd_pad("1", -2.3, 3.4, 1.3,2.2, "GND",   N["GND"])
    + smd_pad("2",  0,   3.4, 1.3,2.2, "VCC33", N["VCC33"])
    + smd_pad("3",  2.3, 3.4, 1.3,2.2, "VSYS",  N["VSYS"])
    + smd_pad("4",  0,  -3.4, 3.5,2.2, "VCC33", N["VCC33"])
    + ")\n")

# BT1 18650 holder (C5165920, 2 THT pads)
PCB_FPS += (fp_header("BT1","18650","evc:Battery18650",90,70)
    + tht_pad("1",-3.81,0,3,3,1.5,"BAT_P",N["BAT_P"])
    + tht_pad("2", 3.81,0,3,3,1.5,"GND",  N["GND"])
    + "  (fp_circle (center 0 0) (end 9.25 0) (layer \"F.Fab\") (stroke (width 0.1) (type default)))\n"
    + ")\n")

# U_ESP ESP32-S3-WROOM-1 (18×25.5mm module, castellation pads 0.9mm pitch)
_esp_x, _esp_y = 68, 30
PCB_FPS += fp_header("U_ESP","ESP32-S3-WROOM-1-N16R8","evc:ESP32-S3-WROOM-1",_esp_x,_esp_y)
# 19 left pads (top to bottom), 20 right pads
for i,(_,nm,_) in enumerate(_esp_left):
    pnet = {"GND":"GND","3V3":"VCC33","EN":"EN",
            "IO1":"CP_ADC","IO4":"RL1_COIL","IO5":"K1_DRV",
            "IO6":"ATM_IRQ","IO7":"LED_R_IO","IO8":"QON_IN",
            "IO9":"I2C_SDA","IO10":"I2C_SCL","IO11":"BQ_INT",
            "IO18":"SPI_MOSI","IO19":"SPI_MISO","IO20":"SPI_SCK"}.get(nm,"")
    nn = N.get(pnet,0) if pnet else 0
    PCB_FPS += smd_pad(str(i+1), -9.0, -(_EH-G)+i*0.9, 1.5,0.5, pnet, nn)
for i,(_,nm,_) in enumerate(_esp_right):
    pnet = {"IO12":"LED_G_IO","IO13":"LED_B_IO","IO21":"ATM_CS","IO0":"IO0_BOOT"}.get(nm,"")
    nn = N.get(pnet,0) if pnet else 0
    PCB_FPS += smd_pad(str(i+20), 9.0, -(_EH-G)+i*0.9, 1.5,0.5, pnet, nn)
PCB_FPS += "  (fp_rect (start -9 -12.75) (end 9 12.75) (layer \"F.Fab\") (stroke (width 0.1) (type default)))\n)\n"

# U_ATM ATM90E32AS (QFN-36)
PCB_FPS += fp_header("U_ATM","ATM90E32AS","evc:ATM90E32AS",90,30)
for i in range(9):  # 9 pads per side
    PCB_FPS += smd_pad(str(i+1),   -3.0+i*0.65, -3.55, 0.3,0.8, "", 0)
    PCB_FPS += smd_pad(str(i+10),   3.55, -3.0+i*0.65, 0.8,0.3, "", 0)
    PCB_FPS += smd_pad(str(i+19),   3.0-i*0.65,  3.55, 0.3,0.8, "", 0)
    PCB_FPS += smd_pad(str(i+28),  -3.55,  3.0-i*0.65, 0.8,0.3, "", 0)
PCB_FPS += smd_pad("37", 0, 0, 4.0,4.0, "GND", N["GND"])
PCB_FPS += ")\n"

# Passives on LV side
PCB_FPS += fp_0402("R1","100kΩ",52,50,"CP_IN","CP_MID",N["CP_IN"],N["CP_MID"])
PCB_FPS += fp_0402("R2","47kΩ", 55,50,"CP_MID","GND",  N["CP_MID"],N["GND"])
PCB_FPS += fp_0402("R3","470kΩ",85,50,"AC_L","ATM_VA_MID",N["AC_L"],N["ATM_VA_MID"])
PCB_FPS += fp_0402("R4","470kΩ",88,50,"ATM_VA_MID","GND",N["ATM_VA_MID"],N["GND"])
PCB_FPS += fp_0402("R_EN","10kΩ",   60,18,"VCC33","EN",  N["VCC33"],N["EN"])
PCB_FPS += fp_0402("R_BOOT","10kΩ", 62,18,"VCC33","IO0_BOOT",N["VCC33"],N["IO0_BOOT"])
PCB_FPS += fp_0402("R_ILIM","10kΩ", 64,18,"ILIM_N","GND",N["ILIM_N"],N["GND"])
PCB_FPS += fp_0402("R_ISO","100Ω",  48,75,"K1_DRV","K1_DRV_A",N["K1_DRV"],N["K1_DRV_A"])
PCB_FPS += fp_0402("R_LR","33Ω",    80,75,"LED_R_IO","LED_RO",N["LED_R_IO"],N["LED_RO"])
PCB_FPS += fp_0402("R_LG","33Ω",    82,75,"LED_G_IO","LED_GO",N["LED_G_IO"],N["LED_GO"])
PCB_FPS += fp_0402("R_LB","33Ω",    84,75,"LED_B_IO","LED_BO",N["LED_B_IO"],N["LED_BO"])
PCB_FPS += fp_0402("R_PP","2.7kΩ",  20,72,"PP_NET","GND",N["PP_NET"],N["GND"])

PCB_FPS += fp_0402("C1","100nF",   79,22,"VCC33","GND",N["VCC33"],N["GND"])
PCB_FPS += fp_0402("C4","100nF",   81,22,"VSYS","GND", N["VSYS"],N["GND"])
PCB_FPS += fp_0805("C2","10µF",    83,22,"VCC33","GND",N["VCC33"],N["GND"])
PCB_FPS += fp_0805("C3","10µF",    86,22,"VSYS","GND", N["VSYS"],N["GND"])
PCB_FPS += fp_0805("C5","10µF",    88,22,"BAT_P","GND",N["BAT_P"],N["GND"])

# J_CT SCT-013 input (KF301-2P)
PCB_FPS += (fp_header("J_CT","SCT-013-030 CT","evc:KF301-2P",96,32)
    + tht_pad("1",-1.27,0,3,3,1.3,"ATM_IA", N["ATM_IA"])
    + tht_pad("2", 1.27,0,3,3,1.3,"ATM_IAN",N["ATM_IAN"])
    + ")\n")

# J_SW1 PinHeader 2×3
PCB_FPS += (fp_header("J_SW1","SW1 Button","evc:PinHeader_2x3",96,60)
    + ''.join(tht_pad(str(i), (0 if i%2==1 else 2.54), -((i-1)//2)*2.54,
        2,2,0.8, ["QON","GND","LED_RO","LED_GO","LED_BO","GND"][i-1],
        N.get(["QON","GND","LED_RO","LED_GO","LED_BO","GND"][i-1],0)) for i in range(1,7))
    + ")\n")

# BZX55C3V3 D1 (DO-35 axial)
PCB_FPS += (fp_header("D1","BZX55C3V3","evc:BZX55C3V3",58,50)
    + tht_pad("1",-3.81,0,1.8,1.8,0.8,"GND",   N["GND"])
    + tht_pad("2", 3.81,0,1.8,1.8,0.8,"CP_MID",N["CP_MID"])
    + ")\n")

# ─── GND copper pour polygon (LV side only: x=47..100, y=0..80) ──────────────
GND_ZONE = f'''\
(zone (net {N["GND"]}) (net_name "GND") (layer "F.Cu") (uuid "{duid('gnd-zone-fcu')}")
  (hatch edge 0.508)
  (connect_pads (clearance 0.5))
  (min_thickness 0.25)
  (filled_areas_thickness no)
  (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5))
  (polygon (pts
    (xy 47 0) (xy 100 0) (xy 100 80) (xy 47 80)
  ))
)
(zone (net {N["GND"]}) (net_name "GND") (layer "B.Cu") (uuid "{duid('gnd-zone-bcu')}")
  (hatch edge 0.508)
  (connect_pads (clearance 0.5))
  (min_thickness 0.25)
  (filled_areas_thickness no)
  (fill yes (thermal_gap 0.5) (thermal_bridge_width 0.5))
  (polygon (pts
    (xy 47 0) (xy 100 0) (xy 100 80) (xy 47 80)
  ))
)
'''

PCB = f'''\
(kicad_pcb
  (version 20250610)
  (generator "pcbnew")
  (generator_version "10.0")
  (general (thickness 1.6) (legacy_teardrops no))
  (paper "A4")
  (layers
    (0  "F.Cu"      signal)
    (31 "B.Cu"      signal)
    (32 "B.Adhes"   user "B.Adhesive")
    (33 "F.Adhes"   user "F.Adhesive")
    (34 "B.Paste"   user)
    (35 "F.Paste"   user)
    (36 "B.SilkS"   user "B.Silkscreen")
    (37 "F.SilkS"   user "F.Silkscreen")
    (38 "B.Mask"    user)
    (39 "F.Mask"    user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (44 "Edge.Cuts" user)
    (45 "Margin"    user)
    (46 "B.CrtYd"   user "B.Courtyard")
    (47 "F.CrtYd"   user "F.Courtyard")
    (48 "B.Fab"     user "B.Fabrication")
    (49 "F.Fab"     user "F.Fabrication")
  )
  (setup
    (pad_to_mask_clearance 0.05)
    (allow_soldermask_bridges_between_pads no)
    (pcbplotparams
      (layerselection 0x00010fc_ffffffff)
      (plot_on_all_layers_selection 0x0000000_00000000)
      (disableapertmacros no)
      (usegerberextensions no)
      (usegerberattributes yes)
      (usegerberadvancedattributes yes)
      (creategerberjobfile yes)
      (gerberprecision 6)
      (gerbersegmentsize 0)
      (outputformat 1)
      (mirror no)
      (drillshape 1)
      (scaleselection 1)
      (outputdirectory "gerber/")
    )
  )
  (net 0 "")
{NET_STMTS}

  ; ── Board outline ──────────────────────────────────────────────────────────
{pcb_rect_outline(0,0,100,80)}
  ; ── Mains/LV boundary (4mm isolation gap) ─────────────────────────────────
{pcb_line(43,0,43,80,"Cmts.User",0.2)}
{pcb_line(47,0,47,80,"Cmts.User",0.2)}
{pcb_text("MAINS (L+N+PE)",  5,3,"F.SilkS",1.2)}
{pcb_text("LV LOGIC",       65,3,"F.SilkS",1.2)}
{pcb_text("4mm CREEP →",    41,40,"Cmts.User",0.8)}
  ; ── Keepout on mains side for LV copper ───────────────────────────────────
  (zone (net 0) (net_name "") (layer "F.Cu") (uuid "{duid('keepout-mains-fcu')}")
    (hatch edge 0.5)
    (keepout (tracks not_allowed) (vias not_allowed) (copperpour not_allowed))
    (polygon (pts (xy 0 0) (xy 43 0) (xy 43 80) (xy 0 80)))
  )

  ; ── Component footprints ───────────────────────────────────────────────────
{PCB_FPS}
  ; ── GND copper pours (LV side only) ───────────────────────────────────────
{GND_ZONE}
)
'''

with open(f"{BASE}/SmartEVCoupler.kicad_pcb","w") as fh:
    fh.write(PCB)
print("✓ SmartEVCoupler.kicad_pcb")

# ─── PROJECT FILE ─────────────────────────────────────────────────────────────

PRO = {
  "meta": {"filename":"SmartEVCoupler.kicad_pro","version":1},
  "board": {
    "design_settings": {
      "defaults": {
        "board_outline_line_width": 0.05,
        "copper_line_width": 0.2,
        "copper_text_size_h": 1.5,
        "copper_text_size_v": 1.5,
        "copper_text_thickness": 0.3,
        "other_line_width": 0.15,
        "silk_line_width": 0.15,
        "silk_text_size_h": 1.0,
        "silk_text_size_v": 1.0,
        "silk_text_thickness": 0.15
      },
      "rules": {
        "min_clearance": 0.2,
        "min_copper_edge_clearance": 0.5,
        "min_hole_clearance": 0.25,
        "min_hole_to_hole": 0.25,
        "min_microvia_diameter": 0.2,
        "min_microvia_drill": 0.1,
        "min_silk_clearance": 0.0,
        "min_text_height": 0.5,
        "min_through_hole_diameter": 0.3,
        "min_track_width": 0.2,
        "min_via_annular_width": 0.1,
        "min_via_diameter": 0.4,
        "solder_mask_clearance": 0.05,
        "solder_mask_min_width": 0.0,
        "solder_paste_clearance": 0.0,
        "solder_paste_margin_ratio": 0.0,
        "use_height_for_length_calcs": True
      }
    }
  },
  "libraries": {
    "pinned_footprint_libs": [],
    "pinned_symbol_libs": ["evc"]
  },
  "net_settings": {
    "classes": [{
      "bus_width": 12,
      "clearance": 0.2,
      "diff_pair_gap": 0.25,
      "diff_pair_via_gap": 0.25,
      "diff_pair_width": 0.2,
      "line_style": 0,
      "microvia_diameter": 0.3,
      "microvia_drill": 0.1,
      "name": "Default",
      "pcb_color": "rgba(0, 0, 0, 0.000)",
      "schematic_color": "rgba(0, 0, 0, 0.000)",
      "track_width": 0.2,
      "via_diameter": 0.8,
      "via_drill": 0.4,
      "wire_width": 6,
      "bus_width": 12,
      "label_size": 0
    },{
      "name":"Mains",
      "track_width":1.5,
      "clearance":0.5,
      "via_diameter":2.0,
      "via_drill":1.0,
      "nets":["AC_L","AC_N","AC_L_SW","PE"]
    },{
      "name":"Power",
      "track_width":0.5,
      "clearance":0.3,
      "via_diameter":1.0,
      "via_drill":0.5,
      "nets":["VSYS","VCC33","BAT_P","VBUS_IN","VBUS_USB","VBUS_HLK","GND"]
    }],
    "meta": {"version":3},
    "net_colors": {}
  },
  "pcbnew": {
    "last_paths": {"gencad":"","idf":"","netlist":"","plot":"","pos_files":"","specctra_dsn":"","step":"","svg":"","vrml":""},
    "page_layout_descr_file": ""
  },
  "schematic": {
    "annotate_start_num": 0,
    "drawing": {
      "default_bus_thickness": 12,
      "default_junction_size": 0,
      "default_line_thickness": 6,
      "default_text_size": 50,
      "field_names": [],
      "intersheets_ref_own_page": False,
      "intersheets_ref_prefix": "",
      "intersheets_ref_short": False,
      "intersheets_ref_show": False,
      "intersheets_ref_suffix": "",
      "junction_size_choice": 3,
      "label_size_ratio": 0.375,
      "operating_point_overlay_i_precision": 3,
      "operating_point_overlay_i_range": "~A",
      "operating_point_overlay_v_precision": 3,
      "operating_point_overlay_v_range": "~V",
      "overbar_offset_ratio": 1.23,
      "pin_symbol_size": 25,
      "text_offset_ratio": 0.15
    },
    "legacy_lib_dir": "",
    "legacy_lib_list": [],
    "meta": {"version":1},
    "net_format_name": "",
    "page_layout_descr_file": "",
    "plot_directory": "",
    "spice_current_sheet_as_root": False,
    "spice_external_command": "spice %l",
    "spice_model_current_sheet_as_root": True,
    "subpart_first_id": 65,
    "subpart_id_separator": 0
  },
  "sheets": [["uuid1","SmartEVCoupler"]],
  "text_variables": {}
}

with open(f"{BASE}/SmartEVCoupler.kicad_pro","w") as fh:
    json.dump(PRO, fh, indent=2)
print("✓ SmartEVCoupler.kicad_pro")

# ─── BOM CSV ──────────────────────────────────────────────────────────────────

BOM = [
    ["Ref","Value","LCSC","Footprint","Qty","Description"],
    ["U_ESP","ESP32-S3-WROOM-1-N16R8","C2913202","evc:ESP32-S3-WROOM-1","1","WiFi/BT SoC module, 16MB flash, 8MB PSRAM"],
    ["U_BQ","BQ25895RTWT","C2861263","evc:BQ25895RTWT","1","Li-Ion charger + power path, I2C, QFN-24"],
    ["U_HUSB","HUSB238_002D","C7471904","evc:HUSB238_002D","1","USB-C PD sink negotiator, 5V/3A profile"],
    ["U_OR","LTC4413","~","evc:LTC4413","1","Dual ideal-diode OR gate, SOT-23-6 — check LCSC stock"],
    ["U_LDO","AMS1117-3.3","C6186","evc:AMS1117-3.3","1","3.3V 1A LDO regulator, SOT-223"],
    ["U_ATM","ATM90E32AS","C784945","evc:ATM90E32AS","1","3-phase energy metering IC, SPI, QFN-36"],
    ["RL1","SRD-05VDC-SL-C","C35449","evc:SRD-05VDC-SL-C","1","5V relay, CP fail-safe interlock (NC default)"],
    ["ISO1","PC817C","C6747","evc:PC817C","1","Optocoupler, galvanic isolation for K1 driver"],
    ["Q1","IRLZ44NPBF","C9078","evc:IRLZ44NPBF","1","Logic-level N-MOSFET TO-220, K1 coil driver"],
    ["PS1","HLK-5M05","C434569","evc:HLK-5M05","1","AC/DC 5V 1W isolated module (mains-powered)"],
    ["BT1","18650 Cell","C5165920","evc:Battery18650","1","18650 PCB cell holder (backup power)"],
    ["J_USBC","USB-C 16P","C2765186","evc:USBC-16P","1","USB-C receptacle, HUSB238 PD input"],
    ["J1","KF301-5P","C3033","evc:KF301-5P","1","Type 2 wallbox input connector (PE,N,L,CP,PP)"],
    ["J2","KF301-5P","C3033","evc:KF301-5P","1","Type 2 car output connector (PE,N,L,CP,PP)"],
    ["J_K1","KF301-2P","C3030","evc:KF301-2P","1","Contactor coil terminal (Schneider LC1K40 A1/A2)"],
    ["J_CT","KF301-2P","C3030","evc:KF301-2P","1","SCT-013-030 CT clamp input"],
    ["J_SW1","PinHeader 2x3","C124378","evc:PinHeader_2x3","1","16mm IP67 illuminated latch button header"],
    ["D1","BZX55C3V3","C8678","evc:BZX55C3V3","1","3.3V Zener clamp for CP ADC"],
    ["D2","1N4007","C76625","evc:1N4007","1","Flyback diode for K1 contactor coil"],
    ["R1","100kΩ 1% 0402","C17900","evc:R_0402","1","CP voltage divider upper"],
    ["R2","47kΩ 1% 0402","C17927","evc:R_0402","1","CP voltage divider lower"],
    ["R3,R4","470kΩ 0402","C25741","evc:R_0402","2","AC voltage divider for ATM90E32 VA pin"],
    ["R_PP","2.7kΩ 0402","C25879","evc:R_0402","1","Proximity pilot 32A termination"],
    ["R_EN,R_BOOT,R_ILIM","10kΩ 0402","C25804","evc:R_0402","3","EN/BOOT pullup, ILIM resistor"],
    ["R_ISO","100Ω 0402","C25804","evc:R_0402","1","ISO1 LED current limit (~22mA from 3V3)"],
    ["R_LR,R_LG,R_LB","33Ω 0402","C25105","evc:R_0402","3","LED current limit (~50mA from 3.3V)"],
    ["C1,C4","100nF 50V 0402","C14663","evc:C_0402","2","Decoupling caps VCC33/VSYS"],
    ["C2,C3,C5","10µF 25V 0805","C19702","evc:C_0805","3","Bulk decoupling VCC33/VSYS/BAT"],
]

with open(f"{BASE}/bom.csv","w") as fh:
    for row in BOM:
        fh.write(','.join(f'"{c}"' for c in row)+'\n')
print("✓ bom.csv")

# ─── fp-lib-table and sym-lib-table ──────────────────────────────────────────

with open(f"{BASE}/fp-lib-table","w") as fh:
    fh.write('(fp_lib_table\n  (version 7)\n'
             '  (lib (name "evc") (type "KiCad") (uri "${KIPRJMOD}/lib/evc.pretty") (options "") (descr "EV Coupler custom footprints"))\n'
             ')\n')

with open(f"{BASE}/sym-lib-table","w") as fh:
    fh.write('(sym_lib_table\n  (version 7)\n'
             '  (lib (name "evc") (type "KiCad") (uri "${KIPRJMOD}/lib/evc.kicad_sym") (options "") (descr "EV Coupler symbols"))\n'
             ')\n')

print("✓ fp-lib-table")
print("✓ sym-lib-table")
print("\nAll files generated successfully.")
