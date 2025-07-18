from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Table, TableStyle, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas
from datetime import datetime
import os


def draw_encabezado_mantenimientos(canvas: Canvas, doc):
    canvas.saveState()
    x = doc.leftMargin
    y = doc.pagesize[1] - doc.topMargin
    height = 55
    col_widths_header = [98, 222, 244, 120, 80]

    # Borde general
    canvas.rect(x, y - height, sum(col_widths_header), height)
    for i in range(1, 5):
        canvas.line(x + sum(col_widths_header[:i]), y - height, x + sum(col_widths_header[:i]), y)

    # Logo ficticio
    logo_w, logo_h = 55, 35
    logo_x = x + (col_widths_header[0] / 2) - (logo_w / 2)
    logo_y = y - (height / 2) - (logo_h / 2)
    canvas.setFillColor(colors.grey)
    canvas.rect(logo_x, logo_y, logo_w, logo_h, fill=True)
    canvas.setFillColor(colors.black)

    # Empresa
    canvas.setFont('Helvetica-Bold', 11)
    center_x = x + sum(col_widths_header[:1]) + col_widths_header[1] / 2
    center_y = y - height / 2
    canvas.drawCentredString(center_x, center_y + 6, "INR INVERSIONES")
    canvas.drawCentredString(center_x, center_y - 8, "REINOSO Y CIA. LTDA.")

    # Título
    canvas.setFont('Helvetica-Bold', 10)
    center_x2 = x + sum(col_widths_header[:2]) + col_widths_header[2] / 2
    canvas.drawCentredString(center_x2, center_y, "CONTROL DE ACTIVIDADES DE MANTENIMIENTO")

    # Mes
    canvas.setFont('Helvetica-Bold', 13)
    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio',
             'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    mes_actual = meses[datetime.now().month - 1]
    center_x3 = x + sum(col_widths_header[:3]) + col_widths_header[3] / 2
    canvas.drawCentredString(center_x3, center_y, mes_actual)

    # Código/Edición
    cuadro_x = x + sum(col_widths_header[:4])
    cuadro_w = col_widths_header[4]
    row_h = height / 4
    for i, (txt, font) in enumerate([
        ("Código", 'Helvetica-Bold'),
        ("71-MT-43", 'Helvetica'),
        ("Edición", 'Helvetica-Bold'),
        ("4/Jul/2025", 'Helvetica')
    ]):
        canvas.setFont(font, 8)
        center_x4 = cuadro_x + cuadro_w / 2
        sub_top = y - i * row_h
        sub_bot = y - (i + 1) * row_h
        center_y4 = (sub_top + sub_bot) / 2 - 2
        canvas.drawCentredString(center_x4, center_y4, txt)

    for i in range(1, 4):
        canvas.line(cuadro_x, y - i * row_h, cuadro_x + cuadro_w, y - i * row_h)

    canvas.restoreState()


def add_pagination_footer(canvas: Canvas, doc):
    canvas.saveState()
    canvas.setFont('Helvetica', 8)
    page_num = canvas.getPageNumber()
    text = f"Página {page_num}"
    canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 15 * mm, text)
    canvas.restoreState()


def encabezado_y_footer_mantenimientos(canvas, doc):
    draw_encabezado_mantenimientos(canvas, doc)
    add_pagination_footer(canvas, doc)


def generate_multi_page_pdf(output_path="prueba_mantenimiento.pdf"):
    encabezado_height = 55
    doc = BaseDocTemplate(output_path, pagesize=A4,
                          leftMargin=20, rightMargin=20,
                          topMargin=80, bottomMargin=40)

    frame = Frame(doc.leftMargin, doc.bottomMargin,
                  doc.width, doc.height - encabezado_height,
                  id='normal')

    template = PageTemplate(id='all', frames=[frame], onPage=encabezado_y_footer_mantenimientos)
    doc.addPageTemplates([template])

    # --- Crear datos ficticios para varias páginas ---
    data = [['Código', 'Nombre', 'Fecha', 'Descripción', 'Estado', 'Responsable', 'Área', 'Tipo', 'Equipo', 'Observaciones']]
    for i in range(200):
        data.append([f'CÓD-{i:03}', f'Nombre {i}', '2025-07-17', 'Mantenimiento correctivo',
                     'Completado', 'Juan Pérez', 'Planta 1', 'Preventivo', f'Equipo-{i}', 'Ninguna'])

    table = Table(data, repeatRows=1, colWidths=[50, 60, 60, 90, 50, 70, 50, 50, 50, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))

    elements = [table]
    doc.build(elements)


# Ejecutar
if __name__ == '__main__':
    generate_multi_page_pdf()
    print("PDF generado correctamente.")
