from odoo import models
import copy
from odoo.exceptions import ValidationError


class MaterialHistoryWizXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_material_history_wiz_xlsx"
    _inherit = [
        "report.report_xlsx.abstract",
        "report.cacl.material.quantity",
        "report.utilities",
    ]

    def generate_xlsx_report(self, workbook, data, record_ids):
        machinery_material_sheet = workbook.add_worksheet("Danh mục vật tư máy")
        machinery_spare_part_sheet = workbook.add_worksheet("Danh mục phụ tùng máy")
        boong_sheet = workbook.add_worksheet("Danh mục vật tư boong")
        tool_sheet = workbook.add_worksheet("Danh mục dụng cụ")
        start_date = data["start_date"]
        end_date = data["end_date"]
        machinery_material_ids = data["machinery_material_ids"]
        machinery_spare_part_ids = data["machinery_spare_part_ids"]
        boong_material_ids = data["boong_material_ids"]
        tool_material_ids = data["tool_material_ids"]
        company_name = data["company_name"]

        self.write_sheet(
            workbook,
            machinery_material_sheet,
            machinery_material_ids,
            company_name,
            start_date,
            end_date,
        )
        self.write_sheet(
            workbook,
            machinery_spare_part_sheet,
            machinery_spare_part_ids,
            company_name,
            start_date,
            end_date,
        )
        self.write_sheet(
            workbook,
            boong_sheet,
            boong_material_ids,
            company_name,
            start_date,
            end_date,
        )
        self.write_sheet(
            workbook,
            tool_sheet,
            tool_material_ids,
            company_name,
            start_date,
            end_date,
        )

        workbook.close()

    def write_sheet(
        self, workbook, sheet, record_ids, company_name, start_date, end_date
    ):

        self.create_header(workbook, sheet, company_name, start_date, end_date)
        self.create_body(workbook, sheet, record_ids, start_date, end_date)
        self.create_footer(workbook, sheet, len(record_ids))

    def create_body(
        self, workbook, sheet, record_ids, start_date, end_date, taken_row=10
    ):
        normal_format = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align=False)
        )
        format_2 = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align="center")
        )

        for i, material_id in enumerate(record_ids):
            stt = i + 1
            row_number = taken_row + stt

            material = self.env["ship.material"].browse(material_id)

            beginning = self._get_begining_stock(material_id, start_date)
            receiving_in_month = self._get_receiving_in_month(
                material_id, start_date, end_date
            )
            total_consumed = self._get_total_consumed(material_id, start_date, end_date)
            ROB = self._get_ROB_stock(material_id, start_date, end_date)

            sheet.write(f"A{row_number}", stt, format_2)
            sheet.write(f"B{row_number}", material.name or "", normal_format)
            sheet.write(f"C{row_number}", material.spare_part_no or "", normal_format)
            sheet.write(f"D{row_number}", beginning, format_2)
            sheet.write(f"E{row_number}", receiving_in_month, format_2)
            sheet.write(f"F{row_number}", total_consumed, format_2)
            sheet.write(f"G{row_number}", ROB, format_2)
            sheet.write(f"H{row_number}", material.warehouse, format_2)
            sheet.write(f"I{row_number}", material.note or "", normal_format)

    def create_header(self, workbook, sheet, company_name, start_date, end_date):
        border_bold = workbook.add_format(self.get_normal_format(border=1))
        bold = workbook.add_format(self.get_normal_format())
        bold_not_center = workbook.add_format(self.get_normal_format(align=False))
        not_bold_not_center = workbook.add_format(
            self.get_normal_format(bold=False, align=False)
        )
        not_bold_italic = workbook.add_format(
            self.get_normal_format(bold=False, italic=True)
        )
        bottom_right_not_bold_not_center = workbook.add_format(
            self.get_normal_format(bold=False, align=False, bottom=1, right=1)
        )
        bottom_not_bold_italic = workbook.add_format(
            self.get_normal_format(bold=False, bottom=1, italic=True)
        )

        # set width column
        b_width = 20
        c_width = 15
        d_width = 10
        e_width = 10
        f_width = 10
        g_width = 10
        h_width = 15
        i_width = 25
        sheet.set_column("B:B", b_width)
        sheet.set_column("C:C", c_width)
        sheet.set_column("D:D", d_width)
        sheet.set_column("E:E", e_width)
        sheet.set_column("F:F", f_width)
        sheet.set_column("G:G", g_width)
        sheet.set_column("H:H", h_width)
        sheet.set_column("I:I", i_width)

        image_path = "/mnt/extra-addons/images/vsico-1.png"
        image_stream = self._get_image_by_path(image_path)
        if image_stream:
            sheet.insert_image("A1", image_path, {"image_data": image_stream})

        sheet.merge_range(f"A1:H1", "CÔNG TY CỔ PHẦN HÀNG HẢI VSICO", bold)
        sheet.merge_range(
            f"A2:H2", "VSICO SHIPPING JOINT STOCK COMPANY", not_bold_italic
        )

        sheet.merge_range(f"A3:H3", "DANH MỤC VẬT TƯ TRÊN TÀU", bold)
        sheet.merge_range(f"A4:H4", "INVENTORY", bottom_not_bold_italic)

        name_3 = "Control No: VSICO-09-06\nIssued Date: 01/12/2022\nRevision No: 00\nRevised Date;\nPage:     of "
        sheet.merge_range(f"I1:I4", name_3, bottom_right_not_bold_not_center)

        sheet.merge_range(f"A5:C5", f"Tên tàu/Vessel: {company_name}", bold_not_center)
        sheet.merge_range(
            f"E5:G5", "Department / Bộ phận : __________", not_bold_not_center
        )

        sheet.merge_range(
            f"A6:C6", "Name of Equipment/ Tên thiết bị:", not_bold_not_center
        )
        sheet.merge_range(
            f"E6:G6", "Model, Type / Kiểu loại:_________", not_bold_not_center
        )

        sheet.merge_range(
            f"A7:C7", "Serial No./Số sơ ri : _________", not_bold_not_center
        )
        sheet.merge_range(f"E7:G7", "Maker / Nhà.SX :_________", not_bold_not_center)

        sheet.merge_range(f"A8:C8", f"From/ Từ ngày: {start_date}", not_bold_not_center)
        sheet.merge_range(
            f"E8:G8", f"Until / Đến ngày: {end_date}", not_bold_not_center
        )

        # No
        sheet.merge_range(f"A9:A10", "No.\nstt", border_bold)

        # others
        sheet.merge_range(f"B9:B10", "Description\nTên chi tiết", border_bold)
        sheet.merge_range(f"C9:C10", "Part No.\nSố chi tiết", border_bold)

        sheet.merge_range(f"D9:G9", "Quantity/Số lượng", border_bold)
        sheet.write(f"D10", "In stock\nTồn ban đầu", border_bold)
        sheet.write(f"E10", "Rec`d\nNhận thêm", border_bold)
        sheet.write(f"F10", "Used\nĐã dùng", border_bold)
        sheet.write(f"G10", "ROB\nCòn lại", border_bold)

        sheet.merge_range(f"H9:H10", "Location\nVị trí để", border_bold)
        sheet.merge_range(f"I9:I10", "Remark\nGhi chú ", border_bold)

        # bellow
        # sheet.write(f"A12", "", format_4)
        # sheet.write(f"B12", "Tên chi tiết", format_4)
        # sheet.write(f"C12", "Số hiệu phụ tùng", format_4)
        # sheet.write(f"D12", "Tồn trước cái ngày bắt đầu", format_4)
        # sheet.write(f"E12", "Trong khoảng thời gian đó nhận thêm bao nhiêu", format_4)
        # sheet.write(f"F12", "Dùng bao nhiêu", format_4)
        # sheet.write(f"G12", "Tồn + nhận đã dùng", format_4)
        # sheet.write(f"H12", "Kho", format_4)
        # sheet.write(f"I12", "", format_4)

        # sheet.merge_range(f"H10:H11", "Location\nVị trí để", format_4)
        # sheet.merge_range(f"I10:I11", "Remark\nGhi chú ", format_4)

    def create_footer(self, workbook, sheet, record_len=0, taken_row=10):
        normal_format = workbook.add_format(self.get_normal_format(top=1))
        format_2 = workbook.add_format(self.get_normal_format(bold=False))

        footer_row = taken_row + record_len + 1
        sheet.merge_range(f"A{footer_row}:I{footer_row}", "", normal_format)

        footer_row_2 = footer_row + 2
        footer_row_3 = footer_row + 3
        footer_row_5 = footer_row + 5
        name_1 = "Prepared by - Chief Engineer / Chief Officer"
        sheet.write(f"B{footer_row_2}", name_1, format_2)
        sheet.write(f"B{footer_row_3}", "Người lập danh mục:", format_2)
        sheet.write(f"B{footer_row_5}", "Thuyền trưởng\nCaptain", format_2)

        sheet.write(f"H{footer_row_2}", "Signed:     Date:", format_2)
