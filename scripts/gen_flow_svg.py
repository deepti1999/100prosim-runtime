"""Generate SVG flow diagram from Excel WS.xlsm sheet 1 shapes + cell labels."""
import zipfile, xml.etree.ElementTree as ET
from openpyxl import load_workbook
import warnings; warnings.filterwarnings('ignore')

NS = {'xdr':'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
EMU = 9525

with zipfile.ZipFile('docs/100prosim_d_250517_250517.1817m/WS.xlsm') as z:
    data = z.read('xl/drawings/drawing1.xml')
root = ET.fromstring(data)

shapes = []
for anchor in list(root.findall('xdr:twoCellAnchor', NS)) + list(root.findall('xdr:oneCellAnchor', NS)):
    target = anchor.find('xdr:sp', NS)
    if target is None:
        target = anchor.find('xdr:cxnSp', NS)
    if target is None:
        continue
    spPr = target.find('xdr:spPr', NS)
    if spPr is None: continue
    xfrm = spPr.find('a:xfrm', NS)
    if xfrm is None: continue
    flipH = xfrm.get('flipH') == '1'; flipV = xfrm.get('flipV') == '1'
    off = xfrm.find('a:off', NS); ext = xfrm.find('a:ext', NS)
    if off is None or ext is None: continue
    x, y = int(off.get('x'))/EMU, int(off.get('y'))/EMU
    w, h = int(ext.get('cx'))/EMU, int(ext.get('cy'))/EMU
    prst_el = spPr.find('a:prstGeom', NS)
    prst = prst_el.get('prst') if prst_el is not None else '?'
    ln_el = spPr.find('a:ln/a:solidFill/a:srgbClr', NS)
    ln = ln_el.get('val') if ln_el is not None else None
    texts = []
    tx = target.find('xdr:txBody', NS)
    if tx is not None:
        for p in tx.findall('a:p', NS):
            line = ''.join(t.text or '' for t in p.findall('.//a:t', NS))
            if line: texts.append(line)
    shapes.append({'prst':prst,'x':round(x),'y':round(y),'w':round(w),'h':round(h),'flipH':flipH,'flipV':flipV,'ln':ln,'text':texts})

out = []
A = out.append

A('<svg class="ws1-svg" viewBox="0 0 1030 800" xmlns="http://www.w3.org/2000/svg" aria-label="Annual electricity flow">')
A('  <defs>')
A('    <marker id="arrE" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><polygon points="0 0, 10 3, 0 6" fill="#d89a00"/></marker>')
A('    <marker id="arrG" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto"><polygon points="0 0, 10 3, 0 6" fill="#2b7bd6"/></marker>')
A('  </defs>')
A('  <style>')
A('    .box-src{fill:#FFE3B2;stroke:#000;stroke-width:1}')
A('    .box-proc{fill:#E8F1FF;stroke:#000;stroke-width:1}')
A('    .box-grid{fill:#FFE3B2;stroke:#000;stroke-width:1}')
A('    .box-store{fill:#CFE4FF;stroke:#000;stroke-width:1}')
A('    .lbl-src{font:bold 11px Arial;fill:#000;text-anchor:middle}')
A('    .lbl-src-sub{font:italic 10px Arial;fill:#000;text-anchor:middle}')
A('    .key{font:italic bold 12px Arial;fill:#1f4e79}')
A('    .val{font:bold 12px Arial;fill:#000;text-anchor:middle}')
A('    .tag{font:italic 10px Arial;fill:#1f4e79;text-anchor:middle}')
A('    .pct{font:10px Arial;fill:#000;text-anchor:middle}')
A('    .red{font:bold 10px Arial;fill:#c0392b;text-anchor:middle}')
A('    .hdr{font:bold 12px Arial;fill:#000;text-decoration:underline}')
A('    .line-e{stroke:#d89a00;stroke-width:2.2;fill:none;marker-end:url(#arrE)}')
A('    .line-g{stroke:#2b7bd6;stroke-width:2.2;fill:none;marker-end:url(#arrG)}')
A('    .circ{fill:#fff;stroke:#d89a00;stroke-width:2}')
A('  </style>')

A('  <text x="22" y="40" class="hdr" style="font-size:16px">Jahresbilanz Strom</text>')
A('  <text x="22" y="60" style="font:bold 11px Arial;fill:#333">{{ diagram_scenario_label|default:"Aktuelles Szenario" }} | Stand {{ diagram_generated_on }}</text>')
A('  <text x="22" y="78" style="font:italic 10px Arial;fill:#555">Verwendete Zeitreihen: Anlagenpark Deutschland 2023 [SMARD]</text>')

A('  <text x="164" y="195" class="hdr">Bruttostromerzeugung:</text>')
A('  <text x="852" y="195" class="hdr">Nettostromerzeugung:</text>')

A('  <rect x="540" y="218" width="150" height="40" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="615" y="234" class="lbl-src" style="font-size:10px">Eta Stromspeicherung (%):</text>')
A('  <text x="615" y="253" class="val" id="eta_storage_value">0,0</text>')

label_map = {
    'Wind(fluktuierend)': ['Wind', '(fluktuierend)'],
    'PV(fluktuierend)': ['PV', '(fluktuierend)'],
    'LaufwasserTief.-Geoth.|(konstant)': ['Laufwasser', 'Tief.-Geoth.', '(konstant)'],
    'Bedarfs-KraftwerkeBiobrennstoffe (Mangelausgl.)': ['Bedarfs-', 'Kraftwerke', 'Biobrennstoffe'],
    'ElektrolyseStromspeicher(Überschuss)': ['Elektrolyse', 'Stromspeicher', '(Überschuss)'],
    'Gasspeicher Strom': ['Gasspeicher Strom'],
    'Rückver-stromung(Mangelausgl.)': ['Rückver-', 'stromung', '(Mangelausgl.)'],
    'GasspeicherDirektverbr.': ['Gasspeicher', 'Direktverbr.'],
    'ElektrolysePower to Gas(nach Angebot)': ['Elektrolyse', 'Power to Gas', '(nach Angebot)'],
    'Stromnetz zumEndverbrauch': ['Stromnetz zum', 'Endverbrauch'],
}
store_set = {'Gasspeicher Strom', 'GasspeicherDirektverbr.'}
proc_set = {'ElektrolysePower to Gas(nach Angebot)', 'ElektrolyseStromspeicher(Überschuss)'}

# Lines
for s in shapes:
    if 'Connector' not in s['prst']: continue
    if s['prst'] == 'flowChartConnector': continue
    x1, y1 = s['x'], s['y']
    x2, y2 = s['x']+s['w'], s['y']+s['h']
    if s['flipH']: x1, x2 = x2, x1
    if s['flipV']: y1, y2 = y2, y1
    is_gas = s['ln'] is None
    cls = 'line-g' if is_gas else 'line-e'
    if s['w'] < 2 and s['h'] < 2: continue
    A(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}"/>')

# Rectangles + labels
for s in shapes:
    if s['prst'] != 'flowChartProcess': continue
    joined = '|'.join(s['text']) if s['text'] else ''
    if joined in proc_set: cls = 'box-proc'
    elif joined in store_set: cls = 'box-store'
    else: cls = 'box-src'
    A(f'  <rect x="{s["x"]}" y="{s["y"]}" width="{s["w"]}" height="{s["h"]}" class="{cls}"/>')
    lines = label_map.get(joined, s['text'])
    cx = s['x'] + s['w']/2; cy = s['y'] + s['h']/2
    n = len(lines); line_h = 13
    start_y = cy - (n-1)*line_h/2 + 4
    for j, line in enumerate(lines):
        c = 'lbl-src-sub' if line.startswith('(') else 'lbl-src'
        A(f'    <text x="{cx:.0f}" y="{start_y + j*line_h:.0f}" class="{c}">{line}</text>')

# Circles
for s in shapes:
    if s['prst'] != 'flowChartConnector': continue
    cx = s['x'] + s['w']/2; cy = s['y'] + s['h']/2
    r = max(s['w'], s['h']) / 2
    A(f'  <circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" class="circ"/>')

# Source stacks
A('  <text x="164" y="234" class="key">S</text>')
A('  <rect x="138" y="240" width="56" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="164" y="253" class="val" style="font-size:11px" id="bio_value">0</text>')
A('  <text x="164" y="271" class="tag" id="bio_tages">1</text>')
A('  <text x="164" y="289" class="pct" id="bio_pct">0,2%</text>')
A('  <text x="164" y="337" class="key">K</text>')
A('  <rect x="130" y="343" width="72" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="164" y="356" class="val" style="font-size:11px" id="pv_value">0</text>')
A('  <text x="164" y="375" class="tag" id="pv_tages">397</text>')
A('  <text x="164" y="392" class="pct" id="pv_pct">62,2%</text>')
A('  <text x="164" y="456" class="key">J</text>')
A('  <rect x="130" y="462" width="72" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="164" y="475" class="val" style="font-size:11px" id="wind_value">0</text>')
A('  <text x="164" y="494" class="tag" id="wind_tages">186</text>')
A('  <text x="164" y="511" class="pct" id="wind_pct">29,2%</text>')
A('  <text x="164" y="573" class="key">L</text>')
A('  <rect x="138" y="579" width="56" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="164" y="592" class="val" style="font-size:11px" id="hydro_value">0</text>')
A('  <text x="164" y="611" class="tag" id="hydro_tages">5</text>')
A('  <text x="164" y="628" class="pct" id="hydro_pct">0,8%</text>')

# Main flow values in the single row at y=456/476/493
A('  <text x="293" y="456" class="key">M</text>')
A('  <rect x="255" y="462" width="76" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="293" y="475" class="val" style="font-size:11px" id="m_value">0</text>')
A('  <text x="293" y="493" class="tag">509</text>')

A('  <rect x="355" y="462" width="72" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="390" y="475" class="val" style="font-size:11px" id="o_value_svg">0</text>')

A('  <text x="497" y="416" class="lbl-src">Abregelung</text>')
A('  <rect x="465" y="422" width="68" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="497" y="435" class="val" style="font-size:11px" id="q_value">0</text>')
A('  <text x="566" y="436" class="key">Q</text>')
A('  <text x="497" y="455" class="tag" id="q_tages">62</text>')

A('  <rect x="594" y="462" width="70" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="628" y="475" class="val" style="font-size:11px" id="bio_rejoin_value">0</text>')
A('  <text x="697" y="476" class="key">N</text>')
A('  <text x="628" y="493" class="tag">313</text>')

A('  <text x="785" y="436" class="val" style="font-size:11px">4.525</text>')
A('  <text x="852" y="436" class="key">S</text>')
A('  <text x="785" y="456" class="tag">1</text>')

A('  <rect x="790" y="462" width="80" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="828" y="475" class="val" style="font-size:11px" id="final_value">0</text>')
A('  <text x="900" y="456" class="key">I</text>')
A('  <text x="828" y="493" class="tag">365</text>')

# Down-branches and Rückv paths
A('  <rect x="255" y="520" width="76" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="293" y="533" class="val" style="font-size:11px" id="ely_branch_value">0</text>')
A('  <text x="345" y="534" class="key">P</text>')

A('  <rect x="459" y="520" width="76" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="497" y="533" class="val" style="font-size:11px" id="n_output_branch_value">0</text>')
A('  <text x="566" y="533" class="key">P/Eta</text>')
A('  <text x="497" y="553" class="tag">134</text>')
A('  <text x="566" y="573" class="red">194 GW</text>')

A('  <rect x="752" y="520" width="72" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="785" y="533" class="val" style="font-size:11px" id="reconversion_value">0</text>')
A('  <text x="852" y="533" class="key">T</text>')
A('  <text x="785" y="553" class="tag">51</text>')
A('  <text x="785" y="573" class="pct" id="reconversion_share">13,9%</text>')
A('  <text x="852" y="573" class="red">261 GW</text>')

A('  <rect x="608" y="580" width="48" height="56" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="628" y="593" class="lbl-src" style="font-size:9px">Pmax/Pv</text>')
A('  <text x="628" y="611" class="red">100%</text>')
A('  <text x="628" y="626" class="pct">65%</text>')
A('  <text x="628" y="648" class="lbl-src" style="font-size:9px">Eta ES</text>')

A('  <text x="429" y="634" class="val" style="font-size:11px;text-anchor:middle">65%</text>')
A('  <text x="429" y="648" class="lbl-src" style="font-size:9px">Eta Ely.</text>')

A('  <text x="773" y="567" class="val" style="font-size:10px">59%</text>')
A('  <text x="773" y="578" class="lbl-src" style="font-size:9px">Eta RS</text>')

A('  <rect x="255" y="680" width="76" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="293" y="693" class="val" style="font-size:11px" id="gasspeicher_direkt_value">0</text>')
A('  <text x="345" y="694" class="key">P</text>')
A('  <text x="293" y="713" class="tag">87</text>')
A('  <text x="390" y="713" class="lbl-src-sub">Gas-Verbraucher</text>')

A('  <rect x="459" y="680" width="76" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="497" y="693" class="val" style="font-size:11px" id="gas_storage_arrow_value">0</text>')
A('  <text x="566" y="694" class="key">P</text>')
A('  <text x="497" y="713" class="tag">87</text>')

A('  <rect x="752" y="680" width="72" height="16" fill="#fff" stroke="#000" stroke-width="0.8"/>')
A('  <text x="785" y="693" class="val" style="font-size:11px" id="t_value_svg">0</text>')
A('  <text x="852" y="694" class="key">U</text>')
A('  <text x="785" y="713" class="tag">87</text>')

A('  <text x="649" y="760" class="lbl-src" style="font-size:11px">Speicherkapazit&#228;t:</text>')
A('  <text x="649" y="775" class="val" style="font-size:12px" id="storage_capacity_value">0 GWh</text>')
A('  <text x="649" y="790" class="tag">80</text>')

A('  <text x="890" y="775" class="lbl-src" style="font-size:10px;text-anchor:start">Abgleichdifferenz</text>')
A('  <text x="990" y="775" class="val" style="font-size:11px">160</text>')
A('  <text x="990" y="790" class="tag">80</text>')

A('  <text x="22" y="586" class="lbl-src" style="font-size:11px;text-anchor:start">Legende:</text>')
A('  <text x="22" y="612" class="val" style="font-size:11px;text-anchor:start">31.799</text>')
A('  <text x="85" y="612" class="lbl-src-sub" style="text-anchor:start">Wert in GWh/a</text>')
A('  <text x="22" y="630" class="tag" style="text-anchor:start">146</text>')
A('  <text x="85" y="630" class="lbl-src-sub" style="text-anchor:start">Wert in &#216; Tagesladungen</text>')
A('  <text x="22" y="648" class="key">K</text>')
A('  <text x="85" y="648" class="lbl-src-sub" style="text-anchor:start">Zeitreihenkennung</text>')
A('  <line x1="33" y1="660" x2="74" y2="660" class="line-e"/>')
A('  <text x="85" y="664" class="lbl-src-sub" style="text-anchor:start">Strom</text>')
A('  <line x1="33" y1="677" x2="74" y2="677" class="line-g"/>')
A('  <text x="85" y="681" class="lbl-src-sub" style="text-anchor:start">Gas</text>')

A('  <text x="1020" y="795" style="font:italic 9px Arial;fill:#888;text-anchor:end">100prosim Web &#183; {{ diagram_generated_on }}</text>')
A('</svg>')

with open('scripts/generated_flow_svg.xml', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('Wrote scripts/generated_flow_svg.xml', len(out), 'lines')
