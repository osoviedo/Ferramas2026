"""Extrae texto azul / InfoBlue de la plantilla Word 3.2.4."""
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

path = Path(r"c:\Users\Jose\Desktop\test\3.2.4 Plantilla_Plan_de_Pruebas.docx")
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = NS["w"]


def q(tag):
    return f"{{{W}}}{tag}"


with zipfile.ZipFile(path) as z:
    styles_xml = z.read("word/styles.xml").decode("utf-8")
    doc_xml = z.read("word/document.xml").decode("utf-8")

print("=== ESTILOS InfoBlue / AZUL en styles.xml ===")
for m in re.finditer(r"<w:style\b.*?</w:style>", styles_xml, re.DOTALL):
    block = m.group(0)
    if not any(x in block for x in ("InfoBlue", "0000FF", "0563C1", "2F5496", "4472C4")):
        continue
    sid = re.search(r'w:styleId="([^"]+)"', block)
    name = re.search(r'w:name w:val="([^"]+)"', block)
    color = re.search(r'w:color w:val="([^"]+)"', block)
    print(
        f"  id={sid.group(1) if sid else '?'}, "
        f"name={name.group(1) if name else '?'}, "
        f"color={color.group(1) if color else '?'}"
    )

# Map style ids that are blue guidance
blue_style_ids = set()
for m in re.finditer(r'w:styleId="([^"]+)".*?w:name w:val="([^"]+)"', styles_xml, re.DOTALL):
    sid, name = m.group(1), m.group(2)
    if "Info" in name or "Blue" in name or "Placeholder" in name:
        blue_style_ids.add(sid)

root = ET.fromstring(doc_xml)
blue_parts = []
current_section = []

for para in root.iter(q("p")):
    p_style = para.find(q("pPr"))
    heading = ""
    if p_style is not None:
        ps = p_style.find(q("pStyle"))
        if ps is not None:
            heading = ps.get(q("val"), "")

    para_blue_chunks = []
    para_black_chunks = []

    for r in para.iter(q("r")):
        text = "".join(t.text or "" for t in r.iter(q("t")))
        if not text:
            continue
        rpr = r.find(q("rPr"))
        is_blue = False
        reasons = []
        if rpr is not None:
            color_el = rpr.find(q("color"))
            if color_el is not None:
                val = (color_el.get(q("val")) or "").upper()
                if val and val not in ("AUTO", "000000", "FFFFFF", "1F3864"):
                    is_blue = True
                    reasons.append(f"color={val}")
            rstyle = rpr.find(q("rStyle"))
            if rstyle is not None:
                sid = rstyle.get(q("val"), "")
                if sid in blue_style_ids or "Info" in sid or "Blue" in sid:
                    is_blue = True
                    reasons.append(f"style={sid}")

        if is_blue:
            para_blue_chunks.append(text)
            blue_parts.append({"text": text, "reasons": reasons, "heading": heading})
        else:
            para_black_chunks.append(text)

print(f"\n=== FRAGMENTOS AZUL / GUÍA ({len(blue_parts)}) ===\n")
full_blue = []
for i, item in enumerate(blue_parts, 1):
    t = item["text"].strip()
    if not t:
        continue
    full_blue.append(t)
    print(f"{i}. [{', '.join(item['reasons'])}]")
    print(f"   {t[:300]}")
    print()

print("=== TEXTO AZUL COMPLETO (concatenado) ===\n")
print(" ".join(full_blue))

print("\n\n=== PÁRRAFOS COMPLETOS DEL DOCUMENTO (negro + títulos) ===\n")
for para in root.iter(q("p")):
    parts = []
    has_blue = False
    for r in para.iter(q("r")):
        text = "".join(t.text or "" for t in r.iter(q("t")))
        if not text:
            continue
        rpr = r.find(q("rPr"))
        is_blue = False
        if rpr is not None:
            color_el = rpr.find(q("color"))
            if color_el is not None:
                val = (color_el.get(q("val")) or "").upper()
                if val and val not in ("AUTO", "000000", "FFFFFF", "1F3864"):
                    is_blue = True
            rstyle = rpr.find(q("rStyle"))
            if rstyle is not None:
                sid = rstyle.get(q("val"), "")
                if sid in blue_style_ids or "Info" in sid or "Blue" in sid:
                    is_blue = True
        if is_blue:
            has_blue = True
        else:
            parts.append(text)
    line = "".join(parts).strip()
    if line:
        marker = " [TITULO/CONTENIDO]" if not has_blue else ""
        print(line + marker)
