"""
Genera PDF profesional con los documentos de ObraYa.
Combina PROCESOS_OBRAYA.md y ANALISIS_VARIANTES.md en un solo PDF.
"""
import re
from fpdf import FPDF


class ObraYaPDF(FPDF):
    def __init__(self):
        super().__init__('P', 'mm', 'Letter')
        self.set_auto_page_break(auto=True, margin=20)
        # Unicode fonts from Windows system
        self.add_font('Arial', '', 'C:/Windows/Fonts/arial.ttf', uni=True)
        self.add_font('Arial', 'B', 'C:/Windows/Fonts/arialbd.ttf', uni=True)
        self.add_font('Arial', 'I', 'C:/Windows/Fonts/ariali.ttf', uni=True)
        self.add_font('Courier', '', 'C:/Windows/Fonts/cour.ttf', uni=True)

    def header(self):
        if self.page_no() > 1:
            self.set_font('Arial', 'I', 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, 'ObraYa - Documentacion Completa de Procesos', align='L')
            self.cell(0, 8, f'Pagina {self.page_no()}', align='R', new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(200, 200, 200)
            self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, 'Confidencial - ObraYa 2026', align='C')

    def cover_page(self):
        self.add_page()
        self.ln(60)
        # Orange bar
        self.set_fill_color(255, 107, 43)
        self.rect(20, 55, 175, 4, 'F')

        self.set_font('Arial', 'B', 36)
        self.set_text_color(15, 23, 42)
        self.cell(0, 20, 'ObraYa', align='C', new_x="LMARGIN", new_y="NEXT")

        self.set_font('Arial', '', 18)
        self.set_text_color(71, 85, 105)
        self.cell(0, 12, 'Documentacion Completa de Procesos', align='C', new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 10, 'y Analisis de Variantes', align='C', new_x="LMARGIN", new_y="NEXT")

        self.ln(10)
        self.set_font('Arial', '', 12)
        self.set_text_color(100, 116, 139)
        self.cell(0, 8, 'Plataforma de abastecimiento de materiales de construccion', align='C', new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 8, 'Agente inteligente WhatsApp-to-WhatsApp', align='C', new_x="LMARGIN", new_y="NEXT")

        self.ln(20)
        self.set_draw_color(200, 200, 200)
        self.line(60, self.get_y(), 155, self.get_y())
        self.ln(10)

        self.set_font('Arial', '', 11)
        self.set_text_color(71, 85, 105)
        self.cell(0, 7, 'Fecha: Abril 2026', align='C', new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 7, 'Version: 1.0', align='C', new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 7, 'Clasificacion: Confidencial', align='C', new_x="LMARGIN", new_y="NEXT")

    def section_divider(self, title):
        """Full page divider between major sections."""
        self.add_page()
        self.ln(80)
        self.set_fill_color(255, 107, 43)
        self.rect(20, 75, 175, 3, 'F')
        self.set_font('Arial', 'B', 28)
        self.set_text_color(15, 23, 42)
        self.cell(0, 20, title, align='C', new_x="LMARGIN", new_y="NEXT")

    def write_markdown(self, md_text):
        """Parse markdown and write to PDF."""
        lines = md_text.split('\n')
        in_code_block = False
        in_table = False
        table_rows = []
        table_col_count = 0

        i = 0
        while i < len(lines):
            line = lines[i]

            # Code blocks
            if line.strip().startswith('```'):
                if in_code_block:
                    in_code_block = False
                    self.ln(2)
                else:
                    in_code_block = True
                    self.ln(2)
                i += 1
                continue

            if in_code_block:
                self.set_font('Courier', '', 8)
                self.set_fill_color(15, 23, 42)
                self.set_text_color(226, 232, 240)
                # Handle long code lines
                code_line = line.replace('\t', '    ')
                self.cell(0, 5, '  ' + code_line[:120], fill=True, new_x="LMARGIN", new_y="NEXT")
                self.set_text_color(30, 41, 59)
                i += 1
                continue

            # Table detection
            if '|' in line and line.strip().startswith('|'):
                cells = [c.strip() for c in line.strip().strip('|').split('|')]
                # Skip separator rows
                if all(re.match(r'^[-:]+$', c) for c in cells):
                    i += 1
                    continue

                if not in_table:
                    in_table = True
                    table_rows = []
                    table_col_count = len(cells)

                table_rows.append(cells)
                # Check if next line is still table
                if i + 1 < len(lines) and '|' in lines[i + 1] and lines[i + 1].strip().startswith('|'):
                    i += 1
                    continue
                else:
                    # Render table
                    self._render_table(table_rows)
                    in_table = False
                    table_rows = []
                    i += 1
                    continue

            stripped = line.strip()

            # Empty line
            if not stripped:
                self.ln(3)
                i += 1
                continue

            # Horizontal rule
            if stripped in ('---', '***', '___'):
                self.ln(3)
                self.set_draw_color(200, 200, 200)
                self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
                self.ln(5)
                i += 1
                continue

            # Headers
            if stripped.startswith('#'):
                level = len(stripped) - len(stripped.lstrip('#'))
                text = stripped.lstrip('#').strip()
                text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)

                if level == 1:
                    self.add_page()
                    self.ln(5)
                    self.set_font('Arial', 'B', 22)
                    self.set_text_color(15, 23, 42)
                    self.multi_cell(0, 10, text, new_x="LMARGIN", new_y="NEXT")
                    self.set_fill_color(255, 107, 43)
                    self.rect(self.l_margin, self.get_y() + 1, 50, 2, 'F')
                    self.ln(6)
                elif level == 2:
                    self.ln(6)
                    self.set_font('Arial', 'B', 16)
                    self.set_text_color(30, 41, 59)
                    self.multi_cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
                    self.set_draw_color(226, 232, 240)
                    self.line(self.l_margin, self.get_y() + 1, self.w - self.r_margin, self.get_y() + 1)
                    self.ln(4)
                elif level == 3:
                    self.ln(4)
                    self.set_font('Arial', 'B', 13)
                    self.set_text_color(51, 65, 85)
                    self.multi_cell(0, 8, text, new_x="LMARGIN", new_y="NEXT")
                    self.ln(2)
                elif level >= 4:
                    self.ln(3)
                    self.set_font('Arial', 'B', 11)
                    self.set_text_color(71, 85, 105)
                    self.multi_cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
                    self.ln(1)

                i += 1
                continue

            # Bullet points
            if stripped.startswith('- ') or stripped.startswith('* '):
                indent = len(line) - len(line.lstrip())
                text = stripped[2:]
                text = self._clean_md(text)
                x_offset = self.l_margin + (indent * 2) + 4
                self.set_font('Arial', '', 10)
                self.set_text_color(30, 41, 59)
                self.set_x(x_offset)
                bullet = chr(8226) + ' '
                self.multi_cell(self.w - self.r_margin - x_offset, 6, bullet + text, new_x="LMARGIN", new_y="NEXT")
                i += 1
                continue

            # Numbered lists
            num_match = re.match(r'^(\d+)\.\s+(.+)', stripped)
            if num_match:
                num = num_match.group(1)
                text = self._clean_md(num_match.group(2))
                self.set_font('Arial', '', 10)
                self.set_text_color(30, 41, 59)
                self.set_x(self.l_margin + 4)
                self.multi_cell(self.w - self.r_margin - self.l_margin - 4, 6, f'{num}. {text}', new_x="LMARGIN", new_y="NEXT")
                i += 1
                continue

            # Regular paragraph
            text = self._clean_md(stripped)
            if text:
                self.set_font('Arial', '', 10)
                self.set_text_color(30, 41, 59)
                self.multi_cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
                self.ln(1)

            i += 1

    def _clean_md(self, text):
        """Remove markdown formatting."""
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # italic
        text = re.sub(r'`(.+?)`', r'\1', text)        # inline code
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # links
        return text

    def _render_table(self, rows):
        """Render a table."""
        if not rows:
            return

        self.ln(3)
        col_count = max(len(r) for r in rows)
        available_w = self.w - self.l_margin - self.r_margin
        col_w = available_w / col_count

        for idx, row in enumerate(rows):
            # Pad row if needed
            while len(row) < col_count:
                row.append('')

            if idx == 0:
                # Header
                self.set_font('Arial', 'B', 8)
                self.set_fill_color(30, 41, 59)
                self.set_text_color(255, 255, 255)
            else:
                self.set_font('Arial', '', 8)
                self.set_text_color(30, 41, 59)
                if idx % 2 == 0:
                    self.set_fill_color(248, 250, 252)
                else:
                    self.set_fill_color(255, 255, 255)

            row_height = 6
            for j, cell in enumerate(row):
                cell_text = self._clean_md(cell)[:50]
                self.cell(col_w, row_height, cell_text, border=1, fill=True)

            self.ln()

        self.set_text_color(30, 41, 59)
        self.ln(3)


def main():
    # Read markdown files
    with open('C:/Users/geren/Downloads/CREAS/obra-ya/PROCESOS_OBRAYA.md', 'r', encoding='utf-8') as f:
        procesos_md = f.read()

    with open('C:/Users/geren/Downloads/CREAS/obra-ya/ANALISIS_VARIANTES.md', 'r', encoding='utf-8') as f:
        variantes_md = f.read()

    pdf = ObraYaPDF()

    # Cover page
    pdf.cover_page()

    # Part 1: Procesos
    pdf.section_divider('PARTE 1')
    pdf.set_font('Arial', '', 14)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 10, 'Mapa Completo de Procesos', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.write_markdown(procesos_md)

    # Part 2: Variantes
    pdf.section_divider('PARTE 2')
    pdf.set_font('Arial', '', 14)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 10, 'Analisis Exhaustivo de Variantes', align='C', new_x="LMARGIN", new_y="NEXT")
    pdf.write_markdown(variantes_md)

    # Save
    output_path = 'C:/Users/geren/Downloads/CREAS/obra-ya/OBRAYA_PROCESOS_COMPLETO.pdf'
    pdf.output(output_path)
    print(f'PDF generado: {output_path}')
    print(f'Paginas: {pdf.page_no()}')


if __name__ == '__main__':
    main()
