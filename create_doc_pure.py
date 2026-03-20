"""
Pure Python script to create PTU_Predictive_Tracking_Plan.docx
No external libraries required - uses only Python stdlib (zipfile, os)
"""
import zipfile
import os
from io import BytesIO

OUTPUT_PATH = r'C:\Users\divya\OBJECT DETECTION\PTU_Predictive_Tracking_Plan.docx'

DARK_BLUE = "1F4E79"
GRAY_BG = "D9D9D9"
CODE_BG = "F2F2F2"

# DXA values (1 inch = 1440 DXA)
PAGE_W = 12240
PAGE_H = 15840
MARGIN = 1440
CONTENT_W = PAGE_W - 2 * MARGIN  # 9360

# ─── helpers ───────────────────────────────────────────────────────────────

def esc(text):
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))

def rpr(font="Arial", size=22, bold=False, color=None, italic=False):
    s = "<w:rPr>"
    s += f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/>'
    s += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    if bold: s += '<w:b/><w:bCs/>'
    if italic: s += '<w:i/>'
    if color: s += f'<w:color w:val="{color}"/>'
    s += "</w:rPr>"
    return s

def run(text, font="Arial", size=22, bold=False, color=None, italic=False):
    preserve = ' xml:space="preserve"' if (text.startswith(' ') or text.endswith(' ') or '  ' in text) else ''
    return f'<w:r>{rpr(font,size,bold,color,italic)}<w:t{preserve}>{esc(text)}</w:t></w:r>'

def ppr_style(style_id, numId=None, ilvl=0, spacing_before=0, spacing_after=120, jc=None):
    s = "<w:pPr>"
    if style_id: s += f'<w:pStyle w:val="{style_id}"/>'
    if numId is not None:
        s += f'<w:numPr><w:ilvl w:val="{ilvl}"/><w:numId w:val="{numId}"/></w:numPr>'
    s += f'<w:spacing w:before="{spacing_before}" w:after="{spacing_after}"/>'
    if jc: s += f'<w:jc w:val="{jc}"/>'
    s += "</w:pPr>"
    return s

def para(runs_xml, style_id=None, numId=None, ilvl=0, spacing_before=0, spacing_after=120, jc=None, page_break=False):
    pb = '<w:r><w:br w:type="page"/></w:r>' if page_break else ''
    return f'<w:p>{ppr_style(style_id, numId, ilvl, spacing_before, spacing_after, jc)}{pb}{runs_xml}</w:p>'

def h1(text):
    r = run(text, font="Arial", size=28, bold=True, color=DARK_BLUE)
    return para(r, style_id="Heading1", spacing_before=300, spacing_after=120)

def h2(text):
    r = run(text, font="Arial", size=24, bold=True)
    return para(r, style_id="Heading2", spacing_before=200, spacing_after=80)

def normal(text, bold=False, color=None, size=22, jc=None):
    r = run(text, font="Arial", size=size, bold=bold, color=color)
    return para(r, jc=jc)

def spacer():
    return '<w:p><w:pPr><w:spacing w:before="0" w:after="60"/></w:pPr></w:p>'

def bullet_para(text, numId=1):
    r = run(text, font="Arial", size=22)
    return para(r, numId=numId, ilvl=0, spacing_before=0, spacing_after=60)

def numbered_para(text, numId=2):
    r = run(text, font="Arial", size=22)
    return para(r, numId=numId, ilvl=0, spacing_before=0, spacing_after=60)

def page_break():
    return '<w:p><w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr><w:r><w:br w:type="page"/></w:r></w:p>'

# ─── code block as table ───────────────────────────────────────────────────

def code_block(lines):
    def code_para(line):
        preserve = ' xml:space="preserve"' if line == '' or line.startswith(' ') or '  ' in line else ''
        text_content = esc(line) if line else ' '
        if not line:
            preserve = ' xml:space="preserve"'
        return (f'<w:p><w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr>'
                f'<w:r><w:rPr>'
                f'<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New" w:cs="Courier New"/>'
                f'<w:sz w:val="18"/><w:szCs w:val="18"/>'
                f'</w:rPr><w:t{preserve}>{text_content}</w:t></w:r></w:p>')

    cell_content = ''.join(code_para(l) for l in lines)
    border_xml = ('<w:top w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>'
                  '<w:left w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>'
                  '<w:bottom w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>'
                  '<w:right w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>')
    cell = (f'<w:tc>'
            f'<w:tcPr>'
            f'<w:tcW w:w="{CONTENT_W}" w:type="dxa"/>'
            f'<w:tcBorders>{border_xml}</w:tcBorders>'
            f'<w:shd w:val="clear" w:color="auto" w:fill="{CODE_BG}"/>'
            f'<w:tcMar><w:top w:w="80" w:type="dxa"/><w:left w:w="160" w:type="dxa"/>'
            f'<w:bottom w:w="80" w:type="dxa"/><w:right w:w="160" w:type="dxa"/></w:tcMar>'
            f'</w:tcPr>{cell_content}</w:tc>')
    row = f'<w:tr>{cell}</w:tr>'
    return (f'<w:tbl>'
            f'<w:tblPr>'
            f'<w:tblW w:w="{CONTENT_W}" w:type="dxa"/>'
            f'<w:tblLayout w:type="fixed"/>'
            f'</w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="{CONTENT_W}"/></w:tblGrid>'
            f'{row}</w:tbl>')

# ─── data table ────────────────────────────────────────────────────────────

def data_table(headers, rows, col_widths):
    border_xml = ('<w:top w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>'
                  '<w:left w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>'
                  '<w:bottom w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>'
                  '<w:right w:val="single" w:sz="1" w:space="0" w:color="CCCCCC"/>')
    total_w = sum(col_widths)
    grid = ''.join(f'<w:gridCol w:w="{w}"/>' for w in col_widths)

    def cell_xml(text, width, is_header=False):
        fill = GRAY_BG if is_header else "FFFFFF"
        r = (f'<w:r><w:rPr>'
             f'<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
             f'<w:sz w:val="20"/><w:szCs w:val="20"/>'
             + ('<w:b/><w:bCs/>' if is_header else '') +
             f'</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r>')
        return (f'<w:tc>'
                f'<w:tcPr>'
                f'<w:tcW w:w="{width}" w:type="dxa"/>'
                f'<w:tcBorders>{border_xml}</w:tcBorders>'
                f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
                f'<w:tcMar><w:top w:w="80" w:type="dxa"/><w:left w:w="120" w:type="dxa"/>'
                f'<w:bottom w:w="80" w:type="dxa"/><w:right w:w="120" w:type="dxa"/></w:tcMar>'
                f'</w:tcPr>'
                f'<w:p><w:pPr><w:spacing w:before="0" w:after="0"/></w:pPr>{r}</w:p>'
                f'</w:tc>')

    hdr_row = '<w:tr>' + ''.join(cell_xml(h, w, True) for h, w in zip(headers, col_widths)) + '</w:tr>'
    data_rows = ''.join(
        '<w:tr>' + ''.join(cell_xml(c, w) for c, w in zip(row, col_widths)) + '</w:tr>'
        for row in rows
    )
    return (f'<w:tbl>'
            f'<w:tblPr>'
            f'<w:tblW w:w="{total_w}" w:type="dxa"/>'
            f'<w:tblLayout w:type="fixed"/>'
            f'</w:tblPr>'
            f'<w:tblGrid>{grid}</w:tblGrid>'
            f'{hdr_row}{data_rows}</w:tbl>')

# ─── numbering XML ─────────────────────────────────────────────────────────

NUMBERING_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:numbering xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:o="urn:schemas-microsoft-com:office:office"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
  xmlns:v="urn:schemas-microsoft-com:vml"
  xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"
  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
  xmlns:w10="urn:schemas-microsoft-com:office:word"
  xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
  xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
  xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"
  xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"
  xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
  <w:abstractNum w:abstractNumId="0">
    <w:multiLevelType w:val="hybridMultilevel"/>
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="bullet"/>
      <w:lvlText w:val="&#x2022;"/>
      <w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>
      <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr>
    </w:lvl>
  </w:abstractNum>
  <w:abstractNum w:abstractNumId="1">
    <w:multiLevelType w:val="hybridMultilevel"/>
    <w:lvl w:ilvl="0">
      <w:start w:val="1"/>
      <w:numFmt w:val="decimal"/>
      <w:lvlText w:val="%1."/>
      <w:lvlJc w:val="left"/>
      <w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr>
      <w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/></w:rPr>
    </w:lvl>
  </w:abstractNum>
  <w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>
  <w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>
</w:numbering>'''

# ─── styles XML ────────────────────────────────────────────────────────────

STYLES_XML = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
        <w:sz w:val="22"/><w:szCs w:val="22"/>
      </w:rPr>
    </w:rPrDefault>
    <w:pPrDefault>
      <w:pPr><w:spacing w:after="120"/></w:pPr>
    </w:pPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:pPr><w:spacing w:after="120"/></w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
      <w:sz w:val="22"/><w:szCs w:val="22"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:pPr>
      <w:outlineLvl w:val="0"/>
      <w:spacing w:before="300" w:after="120"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
      <w:b/><w:bCs/>
      <w:color w:val="{DARK_BLUE}"/>
      <w:sz w:val="28"/><w:szCs w:val="28"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:pPr>
      <w:outlineLvl w:val="1"/>
      <w:spacing w:before="200" w:after="80"/>
    </w:pPr>
    <w:rPr>
      <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
      <w:b/><w:bCs/>
      <w:sz w:val="24"/><w:szCs w:val="24"/>
    </w:rPr>
  </w:style>
</w:styles>'''

# ─── settings XML ──────────────────────────────────────────────────────────

SETTINGS_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:defaultTabStop w:val="720"/>
  <w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>
</w:settings>'''

# ─── footer XML ────────────────────────────────────────────────────────────

FOOTER_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <w:p>
    <w:pPr>
      <w:jc w:val="center"/>
      <w:spacing w:before="0" w:after="0"/>
    </w:pPr>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
        <w:sz w:val="18"/><w:szCs w:val="18"/>
      </w:rPr>
      <w:t xml:space="preserve">Page </w:t>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
        <w:sz w:val="18"/><w:szCs w:val="18"/>
      </w:rPr>
      <w:fldChar w:fldCharType="begin"/>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
        <w:sz w:val="18"/><w:szCs w:val="18"/>
      </w:rPr>
      <w:instrText xml:space="preserve"> PAGE </w:instrText>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
        <w:sz w:val="18"/><w:szCs w:val="18"/>
      </w:rPr>
      <w:fldChar w:fldCharType="end"/>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
        <w:sz w:val="18"/><w:szCs w:val="18"/>
      </w:rPr>
      <w:t xml:space="preserve"> of </w:t>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
        <w:sz w:val="18"/><w:szCs w:val="18"/>
      </w:rPr>
      <w:fldChar w:fldCharType="begin"/>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
        <w:sz w:val="18"/><w:szCs w:val="18"/>
      </w:rPr>
      <w:instrText xml:space="preserve"> NUMPAGES </w:instrText>
    </w:r>
    <w:r>
      <w:rPr>
        <w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>
        <w:sz w:val="18"/><w:szCs w:val="18"/>
      </w:rPr>
      <w:fldChar w:fldCharType="end"/>
    </w:r>
  </w:p>
</w:ftr>'''

# ─── document body ─────────────────────────────────────────────────────────

def build_body():
    body = []

    # Title
    title_run = (f'<w:r><w:rPr>'
                 f'<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
                 f'<w:b/><w:bCs/>'
                 f'<w:color w:val="{DARK_BLUE}"/>'
                 f'<w:sz w:val="52"/><w:szCs w:val="52"/>'
                 f'</w:rPr><w:t>PTU-Based Laser Pointing System</w:t></w:r>')
    body.append(f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="480" w:after="120"/></w:pPr>{title_run}</w:p>')

    subtitle_run = (f'<w:r><w:rPr>'
                    f'<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
                    f'<w:color w:val="555555"/>'
                    f'<w:sz w:val="26"/><w:szCs w:val="26"/>'
                    f'</w:rPr><w:t>From Reactive to Predictive Tracking \u2014 Complete Project Plan &amp; Pipeline</w:t></w:r>')
    body.append(f'<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="0" w:after="480"/></w:pPr>{subtitle_run}</w:p>')

    # SECTION 1
    body.append(h1("SECTION 1: PROJECT OVERVIEW"))

    body.append(h2("1.1 Objective"))
    body.append(normal("Replace the existing reactive \u201creduce-the-distance\u201d PTU tracking logic with a predictive, Kalman Filter-based algorithm to achieve \u226580% laser-on-drone time during active movement."))
    body.append(spacer())

    body.append(h2("1.2 Existing Infrastructure (Do Not Modify)"))
    for item in ["Working UI (User Interface)",
                 "Camera integration with 36x optical zoom",
                 "PTU (Pan-Tilt Unit) hardware control",
                 "YOLOv8-based drone detection pipeline",
                 "Basic reactive tracking loop"]:
        body.append(bullet_para(item))
    body.append(spacer())

    body.append(h2("1.3 Success Criteria"))
    body.append(data_table(
        ["Metric", "Target"],
        [["Drone speed handled", "Up to 1 m/s"],
         ["Drone distance", "Up to 50 meters"],
         ["Laser on-target rate", "\u226580% during movement"],
         ["System latency", "Minimized to meet 80% target"]],
        [4680, 4680]
    ))
    body.append(spacer())

    # SECTION 2
    body.append(page_break())
    body.append(h1("SECTION 2: CURRENT SYSTEM ANALYSIS (Phase 1)"))

    body.append(h2("2.1 Reactive Tracking \u2014 The Problem"))
    body.append(normal("Current logic (pseudo-code):"))
    body.append(spacer())
    body.append(code_block([
        "loop:",
        "    bbox = yolo_detect(frame)",
        "    dx = bbox.center_x - crosshair_x",
        "    dy = bbox.center_y - crosshair_y",
        "    ptu.move(step * sign(dx), step * sign(dy))"
    ]))
    body.append(spacer())
    body.append(normal("Problems:"))
    for item in ["No velocity estimation \u2014 the PTU always reacts to where the drone WAS",
                 "Constant step size causes oscillation near target",
                 "No prediction \u2014 laser lags behind moving drone",
                 "No Kalman smoothing \u2014 noisy detections cause jitter"]:
        body.append(bullet_para(item))
    body.append(spacer())

    body.append(h2("2.2 Latency Sources to Measure"))
    for item in ["YOLO inference time (typically 20\u201350 ms on GPU, 80\u2013150 ms on CPU)",
                 "Frame capture/buffer delay",
                 "PTU command round-trip time (serial/TCP)",
                 "Python GIL contention in main loop"]:
        body.append(bullet_para(item))
    body.append(spacer())

    body.append(h2("2.3 Analysis Tasks"))
    for item in ["Instrument the existing loop with timestamps at each stage",
                 "Log: frame_time, detection_time, ptu_command_time, ptu_ack_time",
                 "Calculate total lag = (ptu_ack_time) - (drone_actual_position_time)",
                 "Identify the dominant bottleneck"]:
        body.append(numbered_para(item))
    body.append(spacer())

    # SECTION 3
    body.append(page_break())
    body.append(h1("SECTION 3: IMPLEMENTATION PLAN (Phase 2)"))

    body.append(h2("3.1 Architecture Overview"))
    body.append(normal("The new pipeline:"))
    body.append(spacer())
    body.append(code_block(["Camera Frame \u2192 YOLOv8 Detection \u2192 Kalman Filter \u2192 Predictive Lookahead \u2192 Coordinate Transform \u2192 PTU Command"]))
    body.append(spacer())

    body.append(h2("3.2 Component 1 \u2014 Kalman Filter (State Estimator)"))
    body.append(normal("State vector: [x, y, vx, vy] (pixel position + velocity)"))
    body.append(spacer())
    body.append(normal("The Kalman Filter will:"))
    for item in ["Estimate the drone\u2019s true position from noisy YOLO bounding boxes",
                 "Predict the drone\u2019s state one step ahead (even when detection fails)",
                 "Smooth out jitter from YOLO fluctuations"]:
        body.append(bullet_para(item))
    body.append(spacer())
    body.append(normal("Key equations:"))
    body.append(bullet_para("Predict: x\u0302 = F\u00b7x + B\u00b7u (state transition)"))
    body.append(bullet_para("Update: x\u0302 = x\u0302 + K\u00b7(z - H\u00b7x\u0302) (measurement correction)"))
    body.append(spacer())
    body.append(normal("Recommended library: filterpy (pip install filterpy)"))
    body.append(spacer())

    body.append(h2("3.3 Component 2 \u2014 Predictive Lookahead"))
    body.append(normal("After the Kalman Filter estimates [x, y, vx, vy], aim at the FUTURE position:"))
    body.append(spacer())
    body.append(code_block([
        "lookahead_time = system_lag_ms / 1000.0  # measured in Phase 1",
        "predicted_x = kalman_x + vx * lookahead_time",
        "predicted_y = kalman_y + vy * lookahead_time"
    ]))
    body.append(spacer())
    body.append(normal("The lookahead_time compensates exactly for the measured system lag."))
    body.append(spacer())

    body.append(h2("3.4 Component 3 \u2014 Coordinate Transformation"))
    body.append(normal("Convert pixel coordinates to PTU pan/tilt angles:"))
    body.append(spacer())
    body.append(code_block([
        "pan_angle  = (predicted_x - frame_center_x) * (H_FOV / frame_width)",
        "tilt_angle = (predicted_y - frame_center_y) * (V_FOV / frame_height)"
    ]))
    body.append(spacer())
    body.append(normal("Where:"))
    for item in ["H_FOV = horizontal field of view (degrees) at current zoom level",
                 "V_FOV = vertical field of view (degrees) at current zoom level",
                 "These must be calibrated per zoom level (36x zoom \u2248 ~0.5\u00b0 \u00d7 0.3\u00b0 FOV)"]:
        body.append(bullet_para(item))
    body.append(spacer())

    body.append(h2("3.5 Component 4 \u2014 Adaptive Step / PID Controller (Optional Enhancement)"))
    body.append(normal("Replace fixed step moves with a PID controller:"))
    body.append(spacer())
    body.append(code_block([
        "error_pan  = target_pan  - current_pan",
        "error_tilt = target_tilt - current_tilt",
        "ptu_pan_cmd  = Kp*error_pan  + Ki*integral_pan  + Kd*derivative_pan",
        "ptu_tilt_cmd = Kp*error_tilt + Ki*integral_tilt + Kd*derivative_tilt"
    ]))
    body.append(spacer())
    body.append(normal("Benefits:"))
    for item in ["Proportional: faster response to large errors",
                 "Integral: eliminates steady-state offset",
                 "Derivative: damping to prevent overshoot"]:
        body.append(bullet_para(item))
    body.append(spacer())

    # SECTION 4
    body.append(page_break())
    body.append(h1("SECTION 4: COMPLETE CODE PIPELINE"))

    body.append(h2("4.1 File Structure"))
    body.append(code_block([
        "project/",
        "\u251c\u2500\u2500 tracker/",
        "\u2502   \u251c\u2500\u2500 __init__.py",
        "\u2502   \u251c\u2500\u2500 kalman_tracker.py      \u2190 Kalman Filter wrapper",
        "\u2502   \u251c\u2500\u2500 predictor.py           \u2190 Lookahead logic",
        "\u2502   \u251c\u2500\u2500 coord_transform.py     \u2190 Pixel \u2192 PTU angle",
        "\u2502   \u2514\u2500\u2500 pid_controller.py      \u2190 Optional PID",
        "\u251c\u2500\u2500 main_tracking_loop.py      \u2190 Replace existing loop",
        "\u2514\u2500\u2500 config.py                  \u2190 All tunable parameters"
    ]))
    body.append(spacer())

    body.append(h2("4.2 kalman_tracker.py"))
    body.append(code_block([
        "import numpy as np",
        "from filterpy.kalman import KalmanFilter",
        "",
        "class DroneKalmanTracker:",
        "    def __init__(self, dt=0.033):  # dt = 1/30 fps",
        "        self.kf = KalmanFilter(dim_x=4, dim_z=2)",
        "        self.dt = dt",
        "        # State: [x, y, vx, vy]",
        "        self.kf.F = np.array([[1,0,dt,0],",
        "                               [0,1,0,dt],",
        "                               [0,0,1, 0],",
        "                               [0,0,0, 1]])",
        "        # Measurement: [x, y]",
        "        self.kf.H = np.array([[1,0,0,0],",
        "                               [0,1,0,0]])",
        "        self.kf.R *= 10    # Measurement noise",
        "        self.kf.Q *= 0.1   # Process noise",
        "        self.initialized = False",
        "",
        "    def update(self, cx, cy):",
        "        if not self.initialized:",
        "            self.kf.x = np.array([cx, cy, 0, 0])",
        "            self.initialized = True",
        "        else:",
        "            self.kf.predict()",
        "            self.kf.update(np.array([cx, cy]))",
        "        return self.kf.x  # [x, y, vx, vy]",
        "",
        "    def predict_only(self):",
        '        """Call when detection fails -- extrapolate position"""',
        "        self.kf.predict()",
        "        return self.kf.x"
    ]))
    body.append(spacer())

    body.append(h2("4.3 predictor.py"))
    body.append(code_block([
        "class PredictiveLookahead:",
        "    def __init__(self, lag_seconds=0.1):",
        "        self.lag = lag_seconds  # Measured system lag",
        "",
        "    def get_target(self, state):",
        "        x, y, vx, vy = state",
        "        target_x = x + vx * self.lag",
        "        target_y = y + vy * self.lag",
        "        return target_x, target_y"
    ]))
    body.append(spacer())

    body.append(h2("4.4 coord_transform.py"))
    body.append(code_block([
        "class CoordTransform:",
        "    def __init__(self, frame_w, frame_h, h_fov_deg, v_fov_deg):",
        "        self.fw = frame_w",
        "        self.fh = frame_h",
        "        self.h_fov = h_fov_deg",
        "        self.v_fov = v_fov_deg",
        "",
        "    def pixel_to_angle(self, px, py):",
        "        cx, cy = self.fw / 2, self.fh / 2",
        "        pan   = (px - cx) / self.fw * self.h_fov",
        "        tilt  = (py - cy) / self.fh * self.v_fov",
        "        return pan, tilt"
    ]))
    body.append(spacer())

    body.append(h2("4.5 main_tracking_loop.py (New Logic)"))
    body.append(code_block([
        "tracker = DroneKalmanTracker(dt=1/fps)",
        "predictor = PredictiveLookahead(lag_seconds=measured_lag)",
        "transform = CoordTransform(1920, 1080, h_fov=0.5, v_fov=0.3)",
        "",
        "while True:",
        "    frame = camera.get_frame()",
        "    detections = yolo.detect(frame)",
        "",
        "    if detections:",
        "        cx, cy = get_bbox_center(detections[0])",
        "        state = tracker.update(cx, cy)",
        "    else:",
        "        state = tracker.predict_only()  # Coasting",
        "",
        "    if tracker.initialized:",
        "        target_x, target_y = predictor.get_target(state)",
        "        pan, tilt = transform.pixel_to_angle(target_x, target_y)",
        "        ptu.move_absolute(pan, tilt)"
    ]))
    body.append(spacer())

    # SECTION 5
    body.append(page_break())
    body.append(h1("SECTION 5: OPTIMIZATION (Phase 3)"))

    body.append(h2("5.1 Python Performance Optimizations"))
    for item in ["Run YOLO inference in a separate thread/process to avoid blocking the PTU command loop",
                 "Use a double-buffer: YOLO thread writes detection; main thread reads + sends PTU commands",
                 "Use numpy for all matrix operations (already used by filterpy)",
                 "Set Python process priority to high (os.nice(-10) on Linux)",
                 "Use asyncio or threading.Thread for non-blocking PTU communication"]:
        body.append(bullet_para(item))
    body.append(spacer())

    body.append(h2("5.2 Threading Architecture"))
    body.append(code_block([
        "Thread 1 (YOLO):    camera \u2192 yolo_detect \u2192 write to shared_detection (lock-free ring buffer)",
        "Thread 2 (Control): read shared_detection \u2192 kalman_update \u2192 predict \u2192 ptu_command"
    ]))
    body.append(spacer())

    body.append(h2("5.3 Kalman Tuning Parameters"))
    body.append(data_table(
        ["Parameter", "Effect", "Tune When"],
        [["R (measurement noise)", "Higher = trust model more", "YOLO detections are noisy/jittery"],
         ["Q (process noise)", "Higher = trust measurements more", "Drone changes direction suddenly"],
         ["dt (time step)", "Must match actual frame rate", "FPS changes"],
         ["lag_seconds", "Lookahead compensation", "Measured system lag changes"]],
        [2500, 3430, 3430]
    ))
    body.append(spacer())

    # SECTION 6
    body.append(page_break())
    body.append(h1("SECTION 6: TESTING & VALIDATION"))

    body.append(h2("6.1 Test Protocol"))
    for item in ["Record ground truth video with known drone trajectory (ruler-measured movement at 1 m/s)",
                 "Run new tracking code on recorded video",
                 "For each frame: log (laser_position, drone_position, on_target = distance < threshold)",
                 "Calculate success_rate = frames_on_target / total_frames"]:
        body.append(numbered_para(item))
    body.append(spacer())

    body.append(h2("6.2 Success Metrics"))
    body.append(data_table(
        ["Test", "Pass Condition"],
        [["Static drone", "100% on-target within 2 seconds"],
         ["Slow linear (0.3 m/s)", "\u226590% on-target"],
         ["Fast linear (1 m/s)", "\u226580% on-target"],
         ["Direction change", "\u22640.5s recovery time"],
         ["Detection dropout (0.5s)", "Resumes tracking after re-detection"]],
        [4680, 4680]
    ))
    body.append(spacer())

    body.append(h2("6.3 Validation Script (pseudo-code)"))
    body.append(code_block([
        "results = []",
        "for frame, gt_pos in zip(video_frames, ground_truth):",
        "    detections = yolo.detect(frame)",
        "    # ... run tracker ...",
        "    laser_pos = ptu.get_current_position()",
        "    on_target = distance(laser_pos, gt_pos) < THRESHOLD_PIXELS",
        "    results.append(on_target)",
        "",
        "success_rate = sum(results) / len(results)",
        'print(f"On-target rate: {success_rate:.1%}")',
        'assert success_rate >= 0.80, "Target not met -- tune Kalman parameters"'
    ]))
    body.append(spacer())

    # SECTION 7
    body.append(page_break())
    body.append(h1("SECTION 7: IMPLEMENTATION TIMELINE"))

    body.append(data_table(
        ["Week", "Phase", "Tasks"],
        [["Week 1", "Phase 1: Analysis", "Instrument loop, measure latency, document interfaces"],
         ["Week 2", "Phase 2: Kalman", "Implement KalmanTracker, unit test with synthetic data"],
         ["Week 3", "Phase 2: Integration", "Integrate predictor + coordinate transform, connect to PTU"],
         ["Week 4", "Phase 3: Testing", "Run validation tests, tune parameters, achieve \u226580%"],
         ["Week 5", "Phase 3: Optimization", "Threading, performance profiling, final validation"]],
        [1560, 2600, 5200]
    ))
    body.append(spacer())

    # SECTION 8
    body.append(page_break())
    body.append(h1("SECTION 8: DEPENDENCIES & SETUP"))

    body.append(h2("8.1 Python Packages"))
    body.append(code_block(["pip install filterpy numpy opencv-python ultralytics"]))
    body.append(spacer())

    body.append(h2("8.2 Key Configuration (config.py)"))
    body.append(code_block([
        "# Camera",
        "FRAME_WIDTH  = 1920",
        "FRAME_HEIGHT = 1080",
        "FPS = 30",
        "",
        "# Zoom-calibrated FOV (measure for each zoom level)",
        "H_FOV_DEG = 0.5   # 36x zoom horizontal FOV",
        "V_FOV_DEG = 0.3   # 36x zoom vertical FOV",
        "",
        "# Kalman tuning",
        "KALMAN_R = 10.0",
        "KALMAN_Q = 0.1",
        "",
        "# System lag (measure in Phase 1)",
        "SYSTEM_LAG_SECONDS = 0.10",
        "",
        "# On-target threshold",
        "ON_TARGET_PIXEL_RADIUS = 20"
    ]))
    body.append(spacer())

    # SECTION 9
    body.append(page_break())
    body.append(h1("SECTION 9: RISKS & MITIGATIONS"))

    body.append(data_table(
        ["Risk", "Mitigation"],
        [["FOV calibration error at 36x zoom", "Calibrate FOV per zoom level using known target distance"],
         ["Kalman diverges on fast maneuvers", "Increase Q (process noise) to track sudden acceleration"],
         ["YOLO detection gaps > 0.5s", "Implement coast mode with velocity decay"],
         ["PTU command latency spike", "Use non-blocking PTU commands; measure and compensate"],
         ["Python GIL limits throughput", "Separate YOLO to subprocess with multiprocessing.Queue"]],
        [4680, 4680]
    ))
    body.append(spacer())
    body.append(spacer())
    end_run = (f'<w:r><w:rPr>'
               f'<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>'
               f'<w:b/><w:bCs/>'
               f'<w:color w:val="{DARK_BLUE}"/>'
               f'<w:sz w:val="22"/><w:szCs w:val="22"/>'
               f'</w:rPr><w:t>END OF DOCUMENT</w:t></w:r>')
    body.append(f'<w:p><w:pPr><w:jc w:val="center"/></w:pPr>{end_run}</w:p>')

    # Sectional properties with page size, margins, footer reference
    sect_pr = f'''<w:sectPr>
      <w:footerReference w:type="default" r:id="rId1"/>
      <w:pgSz w:w="{PAGE_W}" w:h="{PAGE_H}"/>
      <w:pgMar w:top="{MARGIN}" w:right="{MARGIN}" w:bottom="{MARGIN}" w:left="{MARGIN}"
               w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>'''

    return ''.join(body) + sect_pr

# ─── assemble document XML ─────────────────────────────────────────────────

def build_document_xml():
    body = build_body()
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas"
  xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"
  xmlns:o="urn:schemas-microsoft-com:office:office"
  xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
  xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
  xmlns:v="urn:schemas-microsoft-com:vml"
  xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing"
  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
  xmlns:w10="urn:schemas-microsoft-com:office:word"
  xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
  xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"
  xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup"
  xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk"
  xmlns:wne="http://schemas.microsoft.com/office/word/2006/wordml"
  xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"
  mc:Ignorable="w14 wp14">
  <w:body>{body}</w:body>
</w:document>'''

# ─── relationships ─────────────────────────────────────────────────────────

RELS_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
</Relationships>'''

ROOT_RELS_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
</Relationships>'''

CONTENT_TYPES_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
  <Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
</Types>'''

CORE_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>PTU-Based Laser Pointing System</dc:title>
  <dc:subject>Predictive Tracking Project Plan</dc:subject>
  <dc:creator>Claude</dc:creator>
</cp:coreProperties>'''

# ─── pack into .docx ───────────────────────────────────────────────────────

def create_docx():
    document_xml = build_document_xml()

    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('[Content_Types].xml', CONTENT_TYPES_XML)
        zf.writestr('_rels/.rels', ROOT_RELS_XML)
        zf.writestr('word/document.xml', document_xml)
        zf.writestr('word/styles.xml', STYLES_XML)
        zf.writestr('word/numbering.xml', NUMBERING_XML)
        zf.writestr('word/settings.xml', SETTINGS_XML)
        zf.writestr('word/footer1.xml', FOOTER_XML)
        zf.writestr('word/_rels/document.xml.rels', RELS_XML)
        zf.writestr('docProps/core.xml', CORE_XML)

    with open(OUTPUT_PATH, 'wb') as f:
        f.write(buf.getvalue())

    print(f"SUCCESS: Created {OUTPUT_PATH}")
    size = os.path.getsize(OUTPUT_PATH)
    print(f"File size: {size:,} bytes")

if __name__ == '__main__':
    create_docx()
