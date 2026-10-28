import os
import sys
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from analytics_engine import AnalyticsEngine, format_money, format_number

# Ensure UTF-8 output
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def set_cell_background(cell, hex_color):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'))

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

class ExportEngine:
    def __init__(self, analytics_engine=None):
        if analytics_engine is None:
            self.analytics = AnalyticsEngine()
        else:
            self.analytics = analytics_engine

    def generate_docx_report(self, month_key="Thang 09", output_path=None):
        if output_path is None:
            output_path = os.path.join(os.path.dirname(__file__), f"Bao_Cao_Thu_Ngan_Hang_{month_key.replace(' ', '_')}.docx")

        rep = self.analytics.generate_expert_report(month_key)
        ov = self.analytics.get_overview(month_key, "TOÀN CÔNG TY")
        rankings = self.analytics.get_unit_rankings(month_key)
        bank_info = self.analytics.get_bank_breakdown(month_key, "TOÀN CÔNG TY")

        doc = docx.Document()

        # Set page margins (1 inch)
        for section in doc.sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.9)
            section.right_margin = Inches(0.8)

        # Header Table: 2 columns
        header_table = doc.add_table(rows=1, cols=2)
        header_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        header_table.autofit = False

        c_left = header_table.cell(0, 0)
        c_right = header_table.cell(0, 1)

        p_l = c_left.paragraphs[0]
        p_l.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_l1 = p_l.add_run("TỔNG CÔNG TY ĐIỆN LỰC MIỀN NAM\n")
        run_l1.font.size = Pt(10)
        run_l2 = p_l.add_run("CÔNG TY ĐIỆN LỰC LÂM ĐỒNG\n")
        run_l2.font.bold = True
        run_l2.font.size = Pt(11)
        run_l3 = p_l.add_run("PHÒNG TÀI CHÍNH KẾ TOÁN")
        run_l3.font.size = Pt(10)

        p_r = c_right.paragraphs[0]
        p_r.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_r1 = p_r.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n")
        run_r1.font.bold = True
        run_r1.font.size = Pt(10)
        run_r2 = p_r.add_run("Độc lập - Tự do - Hạnh phúc\n")
        run_r2.font.bold = True
        run_r2.font.size = Pt(10)
        run_r3 = p_r.add_run("-------------------\n")
        run_r3.font.size = Pt(9)
        run_r4 = p_r.add_run("Lâm Đồng, ngày ... tháng ... năm 2026")
        run_r4.font.italic = True
        run_r4.font.size = Pt(9.5)

        doc.add_paragraph()

        # Main Title
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_title = p_title.add_run(f"BÁO CÁO PHÂN TÍCH TÌNH HÌNH THU TIỀN ĐIỆN\nQUA NGÂN HÀNG & TRUNG GIAN THANH TOÁN\n(KỲ BÁO CÁO: {month_key.upper()}/2026)")
        run_title.font.bold = True
        run_title.font.size = Pt(14)
        run_title.font.color.rgb = RGBColor(15, 76, 129) # EVN Navy Blue

        # 1. Executive Summary
        h1 = doc.add_paragraph()
        r_h1 = h1.add_run("1. Tổng quan tình hình thực hiện trong kỳ")
        r_h1.font.bold = True
        r_h1.font.size = Pt(12)
        r_h1.font.color.rgb = RGBColor(15, 76, 129)

        p_ex = doc.add_paragraph(rep['executive_summary'])
        p_ex.paragraph_format.line_spacing = 1.2
        p_ex.paragraph_format.space_after = Pt(8)

        # 2. Channel Analysis
        h2 = doc.add_paragraph()
        r_h2 = h2.add_run("2. Cơ cấu theo phương thức và kênh thanh toán số hóa")
        r_h2.font.bold = True
        r_h2.font.size = Pt(12)
        r_h2.font.color.rgb = RGBColor(15, 76, 129)

        p_ch = doc.add_paragraph(rep['channel_analysis'])
        p_ch.paragraph_format.line_spacing = 1.2
        p_ch.paragraph_format.space_after = Pt(8)

        # Table: Channel Breakdown
        tbl_ch = doc.add_table(rows=1, cols=5)
        tbl_ch.alignment = WD_TABLE_ALIGNMENT.CENTER
        hdr_cells = tbl_ch.rows[0].cells
        hdr_titles = ["Kênh thanh toán", "Số HĐ (cái)", "Tỷ lệ % HĐ", "Số tiền (VNĐ)", "Tỷ lệ % Tiền"]
        for idx, t in enumerate(hdr_titles):
            hdr_cells[idx].text = t
            set_cell_background(hdr_cells[idx], "0F4C81")
            p = hdr_cells[idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)
                r.font.size = Pt(9.5)

        for ch in ov['channels']:
            row_cells = tbl_ch.add_row().cells
            row_cells[0].text = ch['name']
            row_cells[1].text = f"{ch['hd']:,.0f}"
            row_cells[2].text = f"{ch['pct_hd']:.2f}%"
            row_cells[3].text = f"{ch['st']:,.0f}"
            row_cells[4].text = f"{ch['pct_st']:.2f}%"
            for c_idx in range(1, 5):
                row_cells[c_idx].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

        # Total row
        row_tot = tbl_ch.add_row().cells
        row_tot[0].text = "TỔNG CỘNG"
        row_tot[1].text = f"{ov['total_hd']:,.0f}"
        row_tot[2].text = "100.00%"
        row_tot[3].text = f"{ov['total_st']:,.0f}"
        row_tot[4].text = "100.00%"
        for c_idx in range(5):
            set_cell_background(row_tot[c_idx], "E2E8F0")
            p = row_tot[c_idx].paragraphs[0]
            if c_idx > 0: p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            for r in p.runs: r.font.bold = True

        doc.add_paragraph()

        # 3. Unit Analysis & Table
        h3 = doc.add_paragraph()
        r_h3 = h3.add_run("3. Chi tiết tình hình thực hiện tại 12 Điện lực trực thuộc")
        r_h3.font.bold = True
        r_h3.font.size = Pt(12)
        r_h3.font.color.rgb = RGBColor(15, 76, 129)

        p_u = doc.add_paragraph(rep['unit_analysis'])
        p_u.paragraph_format.line_spacing = 1.2

        # Table: Unit rankings
        tbl_u = doc.add_table(rows=1, cols=7)
        tbl_u.alignment = WD_TABLE_ALIGNMENT.CENTER
        u_headers = ["STT", "Đơn vị Điện lực", "HĐ App/Ví", "HĐ UNC", "Tổng số HĐ", "Tổng số tiền (VNĐ)", "Tỷ lệ số hóa"]
        for idx, t in enumerate(u_headers):
            tbl_u.rows[0].cells[idx].text = t
            set_cell_background(tbl_u.rows[0].cells[idx], "0F4C81")
            p = tbl_u.rows[0].cells[idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)
                r.font.size = Pt(9)

        for idx, u in enumerate(rankings, 1):
            rc = tbl_u.add_row().cells
            rc[0].text = str(idx)
            rc[1].text = u['unit']
            rc[2].text = f"{u['hd_app']:,.0f}"
            rc[3].text = f"{u['hd_unc']:,.0f}"
            rc[4].text = f"{u['hd_tong']:,.0f}"
            rc[5].text = f"{u['st_tong']:,.0f}"
            rc[6].text = f"{u['pct_digital_hd']:.1f}%"
            rc[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            for c_idx in range(2, 7):
                rc[c_idx].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

        doc.add_paragraph()

        # 4. Bank Analysis & Table
        h4 = doc.add_paragraph()
        r_h4 = h4.add_run("4. Tình hình thu hộ qua các Ngân hàng & Tổ chức TGTT")
        r_h4.font.bold = True
        r_h4.font.size = Pt(12)
        r_h4.font.color.rgb = RGBColor(15, 76, 129)

        p_b = doc.add_paragraph(rep['bank_analysis'])
        p_b.paragraph_format.line_spacing = 1.2

        # Table: Top 10 Banks
        tbl_b = doc.add_table(rows=1, cols=6)
        tbl_b.alignment = WD_TABLE_ALIGNMENT.CENTER
        b_headers = ["STT", "Ngân hàng / TGTT", "Nhóm đối tác", "Số HĐ thu", "Số tiền (VNĐ)", "Thị phần tiền"]
        for idx, t in enumerate(b_headers):
            tbl_b.rows[0].cells[idx].text = t
            set_cell_background(tbl_b.rows[0].cells[idx], "0F4C81")
            p = tbl_b.rows[0].cells[idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.bold = True
                r.font.color.rgb = RGBColor(255, 255, 255)
                r.font.size = Pt(9)

        for idx, b in enumerate(bank_info['banks'][:10], 1):
            rc = tbl_b.add_row().cells
            rc[0].text = str(idx)
            rc[1].text = b['bank_short']
            rc[2].text = b['category']
            rc[3].text = f"{b['hd_tong']:,.0f}"
            rc[4].text = f"{b['st_tong']:,.0f}"
            rc[5].text = f"{b['share_st']:.2f}%"
            rc[0].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            for c_idx in range(3, 6):
                rc[c_idx].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

        doc.add_paragraph()

        # 5. Recommendations
        h5 = doc.add_paragraph()
        r_h5 = h5.add_run("5. Kiến nghị và Đề xuất giải pháp trọng tâm")
        r_h5.font.bold = True
        r_h5.font.size = Pt(12)
        r_h5.font.color.rgb = RGBColor(15, 76, 129)

        for rec in rep['recommendations']:
            p_rec = doc.add_paragraph(f"- {rec}")
            p_rec.paragraph_format.line_spacing = 1.2
            p_rec.paragraph_format.left_indent = Inches(0.2)

        # Signature Table
        doc.add_paragraph()
        sig_table = doc.add_table(rows=1, cols=2)
        sig_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        sig_l = sig_table.cell(0, 0).paragraphs[0]
        sig_l.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sig_l.add_run("PHÒNG TÀI CHÍNH KẾ TOÁN\n\n\n\n").font.bold = True
        sig_l.add_run("Trưởng phòng")

        sig_r = sig_table.cell(0, 1).paragraphs[0]
        sig_r.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sig_r.add_run("NGƯỜI LẬP BÁO CÁO\n\n\n\n").font.bold = True
        sig_r.add_run("Chuyên viên tổng hợp")

        doc.save(output_path)
        return output_path

    def generate_excel_report(self, month_key="Thang 09", output_path=None):
        if output_path is None:
            output_path = os.path.join(os.path.dirname(__file__), f"Tong_Hop_Bao_Cao_{month_key.replace(' ', '_')}.xlsx")

        wb = openpyxl.Workbook()
        ws_units = wb.active
        ws_units.title = "Tổng Hợp Điện Lực"

        rankings = self.analytics.get_unit_rankings(month_key)
        bank_info = self.analytics.get_bank_breakdown(month_key, "TOÀN CÔNG TY")
        ov = self.analytics.get_overview(month_key, "TOÀN CÔNG TY")

        # Styles
        font_title = Font(name="Calibri", size=14, bold=True, color="0F4C81")
        font_sub = Font(name="Calibri", size=11, italic=True)
        font_header = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        fill_header = PatternFill(start_color="0F4C81", end_color="0F4C81", fill_type="solid")
        fill_total = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
        font_bold = Font(name="Calibri", size=10, bold=True)
        font_regular = Font(name="Calibri", size=10)

        thin_side = Side(border_style="thin", color="CCCCCC")
        border_all = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        # Title
        ws_units["A1"] = f"BÁO CÁO TỔNG HỢP THU TIỀN ĐIỆN QUA NGÂN HÀNG & TCTG - {month_key.upper()}/2026"
        ws_units["A1"].font = font_title
        ws_units["A2"] = "CÔNG TY ĐIỆN LỰC LÂM ĐỒNG - PHÒNG TÀI CHÍNH KẾ TOÁN"
        ws_units["A2"].font = font_sub

        # Sheet 1 Headers
        u_headers = [
            "STT", "ĐIỆN LỰC", 
            "HĐ UNT", "SỐ TIỀN UNT", 
            "HĐ UNC", "SỐ TIỀN UNC", 
            "HĐ APP/VÍ", "SỐ TIỀN APP/VÍ", 
            "HĐ TẠI QUẦY", "SỐ TIỀN TẠI QUẦY", 
            "TỔNG SỐ HĐ", "TỔNG SỐ TIỀN (VNĐ)", "TỶ LỆ SỐ HÓA (%)"
        ]

        row_idx = 4
        for c_idx, h in enumerate(u_headers, 1):
            cell = ws_units.cell(row_idx, c_idx, h)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border_all

        # Data rows
        m_data = self.analytics.get_month_data(month_key)
        for idx, u in enumerate(rankings, 1):
            row_idx += 1
            u_name = u['unit']
            u_tot = m_data[u_name]['total']

            vals = [
                idx, u_name,
                u_tot['hd_unt'], u_tot['st_unt'],
                u_tot['hd_unc'], u_tot['st_unc'],
                u_tot['hd_app'], u_tot['st_app'],
                u_tot['hd_quay'], u_tot['st_quay'],
                u_tot['hd_tong'], u_tot['st_tong'],
                u['pct_digital_hd'] / 100.0
            ]

            for c_idx, val in enumerate(vals, 1):
                cell = ws_units.cell(row_idx, c_idx, val)
                cell.font = font_regular
                cell.border = border_all
                if c_idx == 1:
                    cell.alignment = Alignment(horizontal="center")
                elif c_idx == 2:
                    cell.alignment = Alignment(horizontal="left")
                elif c_idx == 13:
                    cell.alignment = Alignment(horizontal="right")
                    cell.number_format = '0.0%'
                else:
                    cell.alignment = Alignment(horizontal="right")
                    cell.number_format = '#,##0'

        # Total Row
        row_idx += 1
        tot_all = m_data['TOÀN CÔNG TY']['total']
        tot_vals = [
            "", "TỔNG TOÀN CÔNG TY",
            tot_all['hd_unt'], tot_all['st_unt'],
            tot_all['hd_unc'], tot_all['st_unc'],
            tot_all['hd_app'], tot_all['st_app'],
            tot_all['hd_quay'], tot_all['st_quay'],
            tot_all['hd_tong'], tot_all['st_tong'],
            (tot_all['hd_app'] / (tot_all['hd_tong'] or 1.0))
        ]
        for c_idx, val in enumerate(tot_vals, 1):
            cell = ws_units.cell(row_idx, c_idx, val)
            cell.font = font_bold
            cell.fill = fill_total
            cell.border = border_all
            if c_idx <= 2:
                cell.alignment = Alignment(horizontal="center" if c_idx == 1 else "left")
            elif c_idx == 13:
                cell.alignment = Alignment(horizontal="right")
                cell.number_format = '0.0%'
            else:
                cell.alignment = Alignment(horizontal="right")
                cell.number_format = '#,##0'

        # Adjust column widths
        for c in range(1, 14):
            letter = get_column_letter(c)
            ws_units.column_dimensions[letter].width = 16 if c not in [1, 2] else (6 if c == 1 else 20)

        # Sheet 2: Chi tiết Ngân hàng
        ws_banks = wb.create_sheet("Chi Tiết Ngân Hàng & TCTG")
        ws_banks["A1"] = f"DANH SÁCH THU HỘ THEO NGÂN HÀNG & TỔ CHỨC TRUNG GIAN THANH TOÁN - {month_key.upper()}/2026"
        ws_banks["A1"].font = font_title
        ws_banks["A2"] = "CÔNG TY ĐIỆN LỰC LÂM ĐỒNG - PHÒNG TÀI CHÍNH KẾ TOÁN"
        ws_banks["A2"].font = font_sub

        b_headers = [
            "STT", "TÊN NGÂN HÀNG / TCTG", "TÊN VIẾT TẮT", "PHÂN NHÓM",
            "HĐ UNT", "TIỀN UNT", "HĐ UNC", "TIỀN UNC", 
            "HĐ APP/VÍ", "TIỀN APP/VÍ", "HĐ QUẦY", "TIỀN QUẦY", 
            "TỔNG HĐ", "TỔNG SỐ TIỀN (VNĐ)", "THỊ PHẦN TIỀN (%)"
        ]

        b_row = 4
        for c_idx, h in enumerate(b_headers, 1):
            cell = ws_banks.cell(b_row, c_idx, h)
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = border_all

        for idx, b in enumerate(bank_info['banks'], 1):
            b_row += 1
            b_vals = [
                idx, b['bank_name'], b['bank_short'], b['category'],
                b['hd_unt'], b['st_unt'], b['hd_unc'], b['st_unc'],
                b['hd_app'], b['st_app'], b['hd_quay'], b['st_quay'],
                b['hd_tong'], b['st_tong'], b['share_st'] / 100.0
            ]
            for c_idx, val in enumerate(b_vals, 1):
                cell = ws_banks.cell(b_row, c_idx, val)
                cell.font = font_regular
                cell.border = border_all
                if c_idx == 1:
                    cell.alignment = Alignment(horizontal="center")
                elif c_idx in [2, 3, 4]:
                    cell.alignment = Alignment(horizontal="left")
                elif c_idx == 15:
                    cell.alignment = Alignment(horizontal="right")
                    cell.number_format = '0.00%'
                else:
                    cell.alignment = Alignment(horizontal="right")
                    cell.number_format = '#,##0'

        for c in range(1, 16):
            letter = get_column_letter(c)
            ws_banks.column_dimensions[letter].width = 18 if c > 4 else (6 if c == 1 else 30)

        wb.save(output_path)
        return output_path

if __name__ == "__main__":
    exporter = ExportEngine()
    d_path = exporter.generate_docx_report("Thang 09")
    print("DOCX Exported:", d_path)
    x_path = exporter.generate_excel_report("Thang 09")
    print("Excel Exported:", x_path)
    print("SUCCESS EXPORT ENGINE")
