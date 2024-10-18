from odoo import models
import copy
from ...models import CONST


class EssentialMaterialWizXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_essential_material_wiz_xlsx"
    _inherit = [
        "report.report_xlsx.abstract",
        "report.cacl.material.quantity",
        "report.utilities",
    ]

    def generate_xlsx_report(self, workbook, data, record_ids):
        sheet = workbook.add_worksheet("Báo cáo thông kê và sử dụng vật tư")
        start_date = data["start_date"]
        end_date = data["end_date"]
        material_ids = data["material_ids"]
        company_name = data["company_name"]

        self.create_header(workbook, sheet, company_name, start_date, end_date)
        self.create_body(workbook, sheet, material_ids, start_date, end_date)
        self.create_footer(workbook, sheet, len(material_ids))
        workbook.close()

    def create_body(
        self, workbook, sheet, material_ids, start_date, end_date, taken_row=5
    ):
        normal_format = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align=False)
        )
        format_2 = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align="center")
        )

        for i, material_id in enumerate(material_ids):
            stt = i + 1
            row_number = taken_row + stt

            material = self.env["ship.material"].browse(material_id)

            beginning = self._get_begining_stock(material_id, start_date)
            receiving_in_month = self._get_receiving_in_month(
                material_id, start_date, end_date
            )
            total_consumed = self._get_total_consumed(material_id, start_date, end_date)
            ROB = self._get_ROB_stock(material_id, start_date, end_date)

            sheet.write(f"A{row_number}", material.name or "", normal_format)
            sheet.write(f"B{row_number}", material.spare_part_no or "", format_2)
            sheet.write(f"C{row_number}", material.min_quantity or "", format_2)
            sheet.write(f"D{row_number}", beginning, format_2)
            sheet.write(f"E{row_number}", receiving_in_month, format_2)
            sheet.write(f"F{row_number}", total_consumed, format_2)
            sheet.write(f"G{row_number}", ROB, format_2)
            sheet.write(f"H{row_number}", material.warehouse, format_2)

    def create_header(self, workbook, sheet, company_name, start_date, end_date):
        border_bold = workbook.add_format(self.get_normal_format(border=1))
        bold = workbook.add_format(self.get_normal_format())
        border = workbook.add_format(self.get_normal_format(border=1))
        not_bold_not_center = workbook.add_format(
            self.get_normal_format(bold=False, align=False)
        )
        border_not_bold_not_center = workbook.add_format(
            self.get_normal_format(border=1, bold=False, align=False)
        )
        not_bold_italic = workbook.add_format(
            self.get_normal_format(bold=False, italic=True)
        )

        # set height column
        height = 40
        sheet.set_row(4, height)
        sheet.set_row(2, height)

        # set width column
        a_width = 45
        b_width = 15
        c_width = 10
        d_width = 10
        e_width = 10
        f_width = 10
        g_width = 10
        h_width = 25
        sheet.set_column("A:A", a_width)
        sheet.set_column("B:B", b_width)
        sheet.set_column("C:C", c_width)
        sheet.set_column("D:D", d_width)
        sheet.set_column("E:E", e_width)
        sheet.set_column("F:F", f_width)
        sheet.set_column("G:G", g_width)
        sheet.set_column("H:H", h_width)

        image_path = "/mnt/extra-addons/images/vsico-1.png"
        image_stream = self._get_image_by_path(image_path)
        if image_stream:
            sheet.insert_image("A1", image_path, {"image_data": image_stream})

        sheet.merge_range(f"A1:G1", "CÔNG TY CỔ PHẦN HÀNG HẢI VSICO", bold)
        sheet.merge_range(
            f"A2:G2", "VSICO SHIPPING JOINT STOCK COMPANY", not_bold_italic
        )

        name_1 = "DANH MỤC PHỤ TÙNG VẬT TƯ THIẾT YẾU TRÊN TÀU"
        sheet.merge_range(f"A3:G3", name_1, bold)

        name_3 = "Control No: VSICO-09-04\nIssued Date: 01/12/2022\nRevision No: 00\nRevised Date;\nPage:     of "
        sheet.merge_range(f"H1:H3", name_3, not_bold_not_center)

        sheet.write(f"A4", f"MV (Tên tàu): {company_name}", border_not_bold_not_center)
        sheet.write(f"B4", "", border)
        sheet.merge_range(
            f"C4:E4", f"Date (Ngày): {end_date}", border_not_bold_not_center
        )
        sheet.write(f"F4", "", border)
        sheet.write(f"G4", "", border)
        sheet.write(f"H4", "", border)

        # No
        sheet.write(f"A5", "Description\nMô tả", border_bold)

        # others
        sheet.write(f"B5", "Spare Part No.\nSố phụ tùng", border_bold)
        sheet.write(f"C5", "Mini-mum", border_bold)

        sheet.write(f"D5", "Begin-ing stock", border_bold)
        sheet.write(f"E5", "Rcvd. in month", border_bold)
        sheet.write(f"F5", "Total cons-umped", border_bold)

        sheet.write(f"G5", "R.O.B\nHiệncó", border_bold)
        sheet.write(f"H5", "Location\nVị trí", border_bold)

        # below
        # sheet.write(f"A8", "Tên vật tư", format_4)
        # sheet.write(f"B8", "Số hiệu phụ tùng", format_4)
        # sheet.write(f"C8", "Cố định(trong phần mềm để khác)", format_4)
        # sheet.write(f"D8", "Đầu tháng mùng 1", format_4)
        # sheet.write(f"E8", "Nhận trong tháng", format_4)
        # sheet.write(f"F8", "Lượng sử dụng", format_4)
        # sheet.write(f"G8", "Còn lại", format_4)
        # sheet.write(f"H8", "Kho", format_4)

    def create_footer(self, workbook, sheet, record_len=0, taken_row=5):
        normal_format = workbook.add_format(self.get_normal_format(top=1))
        format_2 = workbook.add_format(self.get_normal_format(bold=False))

        footer_row = taken_row + record_len + 1
        sheet.merge_range(f"A{footer_row}:H{footer_row}", "", normal_format)

        footer_row_2 = footer_row + 2
        footer_row_3 = footer_row + 3
        footer_row_5 = footer_row + 5
        name_1 = "Prepared by - Chief Engineer / Chief Officer"
        sheet.write(f"B{footer_row_2}", name_1, format_2)
        sheet.write(f"B{footer_row_3}", "Người lập danh mục:", format_2)
        sheet.write(f"B{footer_row_5}", "Thuyền trưởng\nCaptain", format_2)

        sheet.write(f"H{footer_row_2}", "Signed:     Date:", format_2)
