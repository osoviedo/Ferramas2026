"""Genera Plan_de_Pruebas_Ferramas.docx desde la plantilla 3.2.4."""
import copy
import re
import shutil
from pathlib import Path

from docx import Document
from docx.shared import RGBColor
from docx.oxml.ns import qn

SRC = Path(r"c:\Users\Jose\Desktop\test\3.2.4 Plantilla_Plan_de_Pruebas.docx")
DST = Path(r"c:\Users\Jose\Desktop\Ferramas2026-main\docs\Plan_de_Pruebas_Ferramas.docx")

BLUE = {(0, 0, 255), (0, 176, 80)}  # 0000FF y 00B050 placeholders

REPLACEMENTS = {
    "[Nombre del proyecto]": "Ferramas",
    "[nombre del proyecto]": "Ferramas",
    "[dd/mm/aaa]": "26/06/2026",
    "<aaaa-mm-dd>": "2026-06-26",
    "<1.1.0>": "1.0",
    "<Nombre>": "Fitzroyal",
    "[Nombre]": "Fitzroyal",
}

SECTION_INSERTS = {
    "Resumen ejecutivo": (
        "Ferramas es un e-commerce de ferretería desarrollado en Flask con API REST, "
        "SQLite y frontend Jinja2. Este plan detallado define la estrategia de pruebas "
        "para la evaluación académica: validar API REST, flujo carrito–checkout–pedido, "
        "autenticación y rendimiento. Se ejecutan 30 pruebas automatizadas con pytest "
        "(unitarias, integración, mock, aceptación, carga y estrés). Criterio de éxito: "
        "30 passed y cobertura igual o superior al 55%."
    ),
    "Elementos de pruebas": (
        "Módulos a probar: (1) API REST app/api/producto_api.py — /api/productos, "
        "/api/categorias, /api/divisas; (2) Vistas app/views/ — tienda, carrito, auth; "
        "(3) Servicios AuthService, DivisaService, PagoService; (4) Modelos Producto, "
        "Usuario, Carrito, Pedido; (5) Suite tests/ con 30 casos automatizados."
    ),
}

DELETE_PARAGRAPH_CONTAINS = [
    "Esta plantilla tiene por finalidad servir de base",
    "El texto entre paréntesis cuadrados y desplegado en azul",
    "estilo = InfoBlue",
    "debe ser borrado antes de la publicación",
]

GUIDANCE_STARTS = [
    "Resumen de todo el contenido del plan de pruebas",
    "El testing señalado",
    "Se proponen varios tipos de",
    "La siguiente tabla contiene algunos ejemplos",
    "La siguiente tabla corresponde a un ejemplo de identifica",
    "Incluir diagrama de la arqui",
    "Especifica el criterio que se usará para determinar si la ejecución del",
    "Esta subsección provee las definiciones de todos los términos",
    "Esta subsección provee una lista completa de todos los documentos",
    "A continuación se describe la estrategia de testing",
    "En esta sección se deben listar los documentos",
    "La documentación de casos de prueba y reportes puede hacerse",
    "Esta sección identifica los reportes del",
    "Describe los métodos y herramientas usadas para registrar",
    "Define los métodos y herramienta usados para registrar",
    "A continuación se enumeran las actividades a realizar",
    "El testing de rendimiento es una prueba para comprobar",
    "[Agregar o eliminar según corresponda]",
    "[Agregar  o eliminar según corresponda]",
    "Se puede referenciar el artefacto",
    "[Puede que no todas las propiedades sean verificadas",
    "[Esta sección es solo opcional y aplica en el caso",
]


def run_color(run):
    if run.font.color and run.font.color.rgb:
        c = run.font.color.rgb
        return (c[0], c[1], c[2])
    rpr = run._element.find(qn("w:rPr"))
    if rpr is not None:
        color = rpr.find(qn("w:color"))
        if color is not None:
            val = color.get(qn("w:val"), "")
            if val and val.upper() not in ("AUTO", "000000"):
                try:
                    v = int(val, 16)
                    return ((v >> 16) & 255, (v >> 8) & 255, v & 255)
                except ValueError:
                    pass
    return None


def is_blue_or_green_run(run):
    c = run_color(run)
    if c in BLUE:
        return True
    rpr = run._element.find(qn("w:rPr"))
    if rpr is not None:
        style = rpr.find(qn("w:rStyle"))
        if style is not None:
            sid = style.get(qn("w:val"), "")
            if "Info" in sid or "Blue" in sid or "infoblue" in sid.lower():
                return True
    return False


def set_run_black(run, text=None):
    if text is not None:
        run.text = text
    run.font.color.rgb = RGBColor(0, 0, 0)
    run.font.italic = False
    rpr = run._element.find(qn("w:rPr"))
    if rpr is not None:
        for tag in ("w:color", "w:rStyle", "w:i"):
            el = rpr.find(qn(tag))
            if el is not None:
                rpr.remove(el)


def paragraph_text(p):
    return "".join(r.text for r in p.runs).strip()


def should_delete_paragraph(text):
    if not text:
        return False
    for frag in DELETE_PARAGRAPH_CONTAINS:
        if frag.lower() in text.lower():
            return True
    for frag in GUIDANCE_STARTS:
        if text.startswith(frag) or frag in text:
            if len(text) < 300 or frag.startswith("[") or "Resumen de todo" in text:
                return True
    if text.startswith("[") and text.endswith("]") and len(text) > 40:
        return True
    if text.startswith("<") and "diagrama" in text.lower():
        return True
    if text in ("<nombre de cliente>", "<Indicar fecha testigo para obtención de datos>"):
        return True
    return False


def clean_paragraph_runs(p):
    """Elimina runs azules/verdes; reemplaza placeholders conocidos en negro."""
    new_runs = []
    for run in p.runs:
        txt = run.text
        if is_blue_or_green_run(run):
            replaced = False
            for old, new in REPLACEMENTS.items():
                if old in txt:
                    set_run_black(run, txt.replace(old, new))
                    replaced = True
                    break
            if not replaced:
                if any(txt.strip().startswith(g) for g in GUIDANCE_STARTS):
                    run.text = ""
                    continue
                if re.match(r"^\[.+\]$", txt.strip()) and "Agregar" in txt:
                    run.text = ""
                    continue
                # guidance fragment — drop
                if run_color(run) == (0, 0, 255):
                    run.text = ""
                    continue
            if run.text:
                set_run_black(run)
        else:
            for old, new in REPLACEMENTS.items():
                if old in txt:
                    run.text = txt.replace(old, new)
        if run.text:
            new_runs.append(run)
    # collapse empty paragraph marker
    return "".join(r.text for r in p.runs).strip()


def replace_table_hardware(doc):
    """Reemplaza celdas con ejemplos azules obsoletos en tablas."""
    hw_map = {
        "Pentium II": "Intel Core i5 o equivalente",
        "64 MB": "8 GB RAM",
        "600 MB": "10 GB disco libre",
        "SVGA": "Pantalla Full HD 1920x1080",
        "1.44 MB": "N/A",
        "Rational TeamTest": "pytest + pytest-cov",
        "Rational Robot": "Flask test client",
        "Rational Rose": "Visual Studio Code / Cursor",
        "Access": "SQLite",
        "Microsoft Explorer": "Chrome / Edge",
        "Microsoft Office": "Python 3.14 + pip",
    }
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    t = paragraph_text(p)
                    for old, new in hw_map.items():
                        if old in t:
                            p.clear()
                            r = p.add_run(new)
                            r.font.color.rgb = RGBColor(0, 0, 0)


def insert_after_heading(doc, heading, content):
    found = False
    for i, p in enumerate(doc.paragraphs):
        t = paragraph_text(p)
        if heading.lower() in t.lower() and len(t) < 80:
            found = True
            # siguiente párrafo: si vacío o era guía, reemplazar
            if i + 1 < len(doc.paragraphs):
                nxt = doc.paragraphs[i + 1]
                nt = paragraph_text(nxt)
                if not nt or should_delete_paragraph(nt) or "Listado de todos" in nt:
                    if "Listado de todos" not in nt:
                        nxt.clear()
                        r = nxt.add_run(content)
                        r.font.color.rgb = RGBColor(0, 0, 0)
                    else:
                        # después del listado genérico, añadir párrafo
                        pass
            break
    return found


def fill_criteria_sections(doc):
    entries = {
        "Criterio de entrada para el": (
            "Entrada: repositorio clonado, pip install -r requirements.txt exitoso, "
            "comando python -m pytest disponible."
        ),
        "Criterio de salida para el": (
            "Salida: 30 tests passed, 0 failed, cobertura de código igual o superior al 55%."
        ),
        "Criterio de suspensión": (
            "Suspensión: si Mercado Pago sandbox no responde, usar modo simulado "
            "(MP_ACCESS_TOKEN=TEST-...). Reanudar al validar credenciales."
        ),
    }
    for i, p in enumerate(doc.paragraphs):
        t = paragraph_text(p)
        for key, content in entries.items():
            if key in t:
                if i + 1 < len(doc.paragraphs):
                    nxt = doc.paragraphs[i + 1]
                    if should_delete_paragraph(paragraph_text(nxt)) or not paragraph_text(nxt):
                        nxt.clear()
                        r = nxt.add_run(content)
                        r.font.color.rgb = RGBColor(0, 0, 0)


def fill_use_cases(doc):
    mapping = {
        "Caso de uso 1": "CU01 — Cliente consulta catálogo y filtra por categoría",
        "Caso de uso 2": "CU02 — Cliente agrega productos al carrito y realiza checkout",
        "Caso de uso 3": "CU03 — Usuario inicia sesión; API expone productos en JSON",
        "Componente 1": "API REST (app/api/producto_api.py)",
        "Componente 2": "Módulo web carrito y tienda (app/views/)",
    }
    for p in doc.paragraphs:
        t = paragraph_text(p)
        for old, new in mapping.items():
            if t.strip() == old:
                p.clear()
                r = p.add_run(new)
                r.font.color.rgb = RGBColor(0, 0, 0)


def fill_risk_table(doc):
    for table in doc.tables:
        header = "".join(cell.text for cell in table.rows[0].cells)
        if "Riesgo" in header and "Gravedad" in header:
            if len(table.rows) >= 4:
                data = [
                    ("1", "API mindicador.cl no disponible", "Baja", "Mock y valores por defecto"),
                    ("2", "Token Mercado Pago inválido", "Media", "Modo simulado TEST"),
                    ("3", "Conflicto datos BD de prueba", "Baja", "SQLite temporal en pytest"),
                ]
                for idx, rowdata in enumerate(data, start=1):
                    if idx < len(table.rows):
                        row = table.rows[idx]
                        for j, val in enumerate(rowdata):
                            if j < len(row.cells):
                                row.cells[j].paragraphs[0].clear()
                                r = row.cells[j].paragraphs[0].add_run(val)
                                r.font.color.rgb = RGBColor(0, 0, 0)
            break


def fill_revision_table(doc):
    for table in doc.tables:
        cells_text = table.rows[0].cells[0].text if table.rows else ""
        if "Fecha" in cells_text and "Versión" in "".join(c.text for c in table.rows[0].cells):
            if len(table.rows) > 1:
                row = table.rows[1]
                vals = ["2026-06-26", "1.0", "Documento inicial Ferramas", "Fitzroyal"]
                for j, val in enumerate(vals):
                    if j < len(row.cells):
                        row.cells[j].paragraphs[0].clear()
                        r = row.cells[j].paragraphs[0].add_run(val)
                        r.font.color.rgb = RGBColor(0, 0, 0)
            break


def process_document():
    shutil.copy2(SRC, DST)
    doc = Document(DST)

    # Pasada 1: limpiar párrafos
    to_clear = []
    for p in doc.paragraphs:
        clean_paragraph_runs(p)
        t = paragraph_text(p)
        if should_delete_paragraph(t):
            to_clear.append(p)

    for p in to_clear:
        p.clear()

    # Pasada 2: insertar contenido Ferramas
    for heading, content in SECTION_INSERTS.items():
        for i, p in enumerate(doc.paragraphs):
            if heading.lower() in paragraph_text(p).lower() and len(paragraph_text(p)) < 60:
                # buscar siguiente párrafo útil
                for j in range(i + 1, min(i + 4, len(doc.paragraphs))):
                    nxt = doc.paragraphs[j]
                    nt = paragraph_text(nxt)
                    if not nt or should_delete_paragraph(nt):
                        nxt.clear()
                        r = nxt.add_run(content)
                        r.font.color.rgb = RGBColor(0, 0, 0)
                        break
                break

    fill_use_cases(doc)
    fill_criteria_sections(doc)
    fill_risk_table(doc)
    fill_revision_table(doc)
    replace_table_hardware(doc)

    # Título portada
    for p in doc.paragraphs[:5]:
        t = paragraph_text(p)
        if "Plan de pruebas de software" in t:
            for run in p.runs:
                if "[Nombre del proyecto]" in run.text or "Nombre del proyecto" in run.text:
                    set_run_black(run, "Ferramas")

    doc.save(DST)
    print(f"Guardado: {DST}")


if __name__ == "__main__":
    process_document()
