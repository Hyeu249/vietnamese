from odoo import models
import copy


class MaterialConsumptionReportBatchXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_material_consumption_xlsx_report"
    _inherit = ["report.report_xlsx.abstract"]

    def generate_xlsx_report(self, workbook, data, batch_ids):
        sheet = workbook.add_worksheet("Báo cáo thông kê và sử dụng vật tư")

        line_ids = batch_ids.mapped(lambda e: e.line_ids)

        self.create_header(workbook, sheet)
        self.create_body(workbook, sheet, line_ids)
        self.create_footer(workbook, sheet, len(line_ids))
        workbook.close()

    def create_body(self, workbook, sheet, line_ids, taken_row=6):
        normal_format = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align=False)
        )
        format_2 = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align="center")
        )

        for i, record in enumerate(line_ids):
            stt = i + 1
            row_number = taken_row + stt

            date = record.date
            material_name = record.material_id.name
            spare_part_no = record.spare_part_no
            unit = record.unit
            rob = record.rob
            consumption = record.consumption
            added = record.added
            remark = record.remark

            sheet.write(f"A{row_number}", stt, normal_format)
            sheet.write(f"B{row_number}", date.strftime("%d-%m-%Y"), format_2)
            sheet.write(f"C{row_number}", material_name, normal_format)
            sheet.write(f"D{row_number}", spare_part_no, normal_format)
            sheet.write(f"E{row_number}", unit, format_2)
            sheet.write(f"F{row_number}", rob, format_2)
            sheet.write(f"G{row_number}", consumption, format_2)
            sheet.write(f"H{row_number}", added, format_2)
            sheet.write(f"I{row_number}", remark, normal_format)

    def create_header(self, workbook, sheet):
        normal_format = workbook.add_format(self.get_normal_format())
        format_2 = workbook.add_format(self.get_normal_format(bottom=1))
        format_3 = workbook.add_format(
            self.get_normal_format(bottom=1, right=1, align=False)
        )
        format_4 = workbook.add_format(self.get_normal_format(border=1))

        # set height column
        height = 40
        sheet.set_row(5, height)

        # set width column
        b_width = 25
        c_width = 25
        d_width = 25
        e_width = 25
        f_width = 25
        g_width = 20
        h_width = 20
        i_width = 25
        sheet.set_column("B:B", b_width)
        sheet.set_column("C:C", c_width)
        sheet.set_column("D:D", d_width)
        sheet.set_column("E:E", e_width)
        sheet.set_column("F:F", f_width)
        sheet.set_column("G:G", g_width)
        sheet.set_column("H:H", h_width)
        sheet.set_column("I:I", i_width)

        name_1 = "CÔNG TY CỔ PHẦN HÀNG HẢI VSICO\nVSICO SHIPPING JOINT STOCK COMPANY"
        sheet.merge_range(f"A1:H1", name_1, normal_format)

        name_2 = "BÁO CÁO THÔNG KÊ SỬ DỤNG VẬT TƯ\nSTATISTICAL REPORT ON MATERIAL USE"
        sheet.merge_range(f"A2:H2", name_2, format_2)

        name_3 = "Control No:\nIssued Date:\nRevision No:\nRevised Date:\nPage:     of"
        sheet.merge_range(f"I1:I2", name_3, format_3)

        # stt
        sheet.merge_range(f"A5:A6", "STT", format_4)

        # others
        sheet.merge_range(f"B5:B6", "Ngày sử dụng", format_4)
        sheet.merge_range(f"C5:F5", "Vật tư", format_4)

        sheet.write(f"C6", "Tên vật tư", format_4)
        sheet.write(f"D6", "Số hiệu phụ tùng", format_4)
        sheet.write(f"E6", "Đơn vị", format_4)
        sheet.write(f"F6", "R.O.B", format_4)

        sheet.merge_range(f"G5:H5", "Tiêu thụ", format_4)
        sheet.write(f"G6", "Tổng lần tiêu thụ", format_4)
        sheet.write(f"H6", "Tổng lần sử dụng", format_4)
        sheet.merge_range(f"I5:I6", "Remarks (Ghi chú)", format_4)

    def create_footer(self, workbook, sheet, record_len=0, taken_row=6):
        normal_format = workbook.add_format(self.get_normal_format(top=1))

        footer_row = taken_row + record_len + 1
        sheet.merge_range(f"A{footer_row}:I{footer_row}", "", normal_format)

    def get_normal_format(
        self,
        bold=True,
        align="center",
        font_name="Arial",
        italic=False,
        bg_color=False,
        border=False,
        right=False,
        left=False,
        bottom=False,
        top=False,
    ):
        base_format = {
            "font_name": font_name,
            "font_size": 10,
            "valign": "vcenter",
            "bold": bold,
            "italic": italic,
        }

        if bg_color:
            base_format["bg_color"] = bg_color

        if border:
            base_format["border"] = border

        if right:
            base_format["right"] = right

        if top:
            base_format["top"] = top

        if left:
            base_format["left"] = left

        if bottom:
            base_format["bottom"] = bottom

        if align != False:
            base_format["align"] = align

        return base_format
