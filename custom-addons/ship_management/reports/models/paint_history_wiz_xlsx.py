from odoo import models
import copy
from odoo.exceptions import ValidationError
import logging
from ...models import CONST


class PaintHistoryWizXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_paint_history_wiz_xlsx"
    _inherit = ["report.report_xlsx.abstract", "report.utilities"]

    def generate_xlsx_report(self, workbook, data, record_ids):
        sheet = workbook.add_worksheet("Báo cáo sơn")
        start_date = data["start_date"]
        end_date = data["end_date"]
        paint_ids = data["paint_ids"]
        company_name = data["company_name"]

        self.create_header(workbook, sheet, company_name, start_date, end_date)
        self.create_body(workbook, sheet, paint_ids, start_date, end_date)
        self.create_footer(workbook, sheet, len(paint_ids))
        workbook.close()

    def create_body(
        self, workbook, sheet, paint_ids, start_date, end_date, taken_row=9
    ):
        normal_format = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align=False)
        )
        format_2 = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align="center")
        )

        for i, paint_id in enumerate(paint_ids):
            stt = i + 1
            row_number = taken_row + stt

            paint = self.env["ship.paint"].browse(paint_id)
            add_quantity_liter = self._get_add_quantity_in_month(
                paint_id, start_date, end_date
            )
            minus_quantity_liter = self._get_minus_quantity_in_month(
                paint_id, start_date, end_date
            )
            beginning = self._get_quantity_of_material_history(
                paint_id, start_date, end_date, is_beginning=True
            )
            not_beginning = self._get_quantity_of_material_history(
                paint_id, start_date, end_date, is_beginning=False
            )
            paint_area = self._get_paint_area(paint_id, start_date, end_date)
            paint_position = self._get_paint_position(paint_id, start_date, end_date)

            sheet.write(f"A{row_number}", stt, format_2)
            sheet.write(f"B{row_number}", paint.description or "", format_2)
            sheet.write(f"C{row_number}", paint.name or "", normal_format)
            sheet.write(f"D{row_number}", paint.paint_type_id.name or "", normal_format)
            sheet.write(f"E{row_number}", "lít", format_2)
            sheet.write(f"F{row_number}", beginning, format_2)
            sheet.write(f"G{row_number}", add_quantity_liter, format_2)
            sheet.write(f"H{row_number}", minus_quantity_liter, format_2)
            sheet.write(f"I{row_number}", not_beginning, format_2)
            sheet.write(f"J{row_number}", paint_area, format_2)
            sheet.write(f"K{row_number}", paint_position, normal_format)

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

        # set height column
        height = 40
        sheet.set_row(7, height)

        # set width column
        b_width = 15
        c_width = 30
        d_width = 30
        e_width = 10
        f_width = 10
        g_width = 10
        h_width = 10
        i_width = 10
        j_width = 30
        k_width = 30
        sheet.set_column("B:B", b_width)
        sheet.set_column("C:C", c_width)
        sheet.set_column("D:D", d_width)
        sheet.set_column("E:E", e_width)
        sheet.set_column("F:F", f_width)
        sheet.set_column("G:G", g_width)
        sheet.set_column("H:H", h_width)
        sheet.set_column("I:I", i_width)
        sheet.set_column("J:J", j_width)
        sheet.set_column("K:K", k_width)

        image_path = "/mnt/extra-addons/images/vsico-1.png"
        image_stream = self._get_image_by_path(image_path)
        if image_stream:
            sheet.insert_image("A1", image_path, {"image_data": image_stream})

        name_1 = "BÁO CÁO CHI TIẾT TIÊU THỤ SƠN HÀNG THÁNG"
        sheet.merge_range(f"A1:J1", "CÔNG TY CỔ PHẦN HÀNG HẢI VSICO", bold)
        sheet.merge_range(
            f"A2:J2", "VSICO SHIPPING JOINT STOCK COMPANY", not_bold_italic
        )
        sheet.merge_range(f"A3:J3", name_1, bold)
        sheet.merge_range(
            f"A4:J4", "MONTHLY PAINT CONSUMPTION REPORT", bottom_not_bold_italic
        )

        name_3 = "Control No: VSICO-09-02\nIssued Date: 01/12/2022\nRevision No: 00\nRevised Date;\nPage:     of "
        sheet.merge_range(f"K1:K4", name_3, bottom_right_not_bold_not_center)

        name_4 = f"Từ/ From: {start_date}     Đến/Until: {end_date}"
        sheet.merge_range(f"B6:C6", f"Tên tàu/Vessel: {company_name}", bold_not_center)
        sheet.merge_range(f"B7:C7", name_4, not_bold_not_center)
        sheet.merge_range(f"G7:I7", "Nhà sản xuất/Manufacturer: ", not_bold_not_center)

        # No
        sheet.merge_range(f"A8:A9", "No", border_bold)

        # others
        sheet.write(f"B8", "Mã", border_bold)
        sheet.write(f"B9", "PART No", border_bold)

        sheet.write(f"C8", "Tên gọi", border_bold)
        sheet.write(f"C9", "NAME", border_bold)

        sheet.write(f"D8", "Loại sơn", border_bold)
        sheet.write(f"D9", "", border_bold)

        sheet.write(f"E8", "Đơn vị tính", border_bold)
        sheet.write(f"E9", "UNIT", border_bold)

        sheet.write(f"F8", "SL tồn đầu tháng", border_bold)
        sheet.write(f"F9", "IN STOCK", border_bold)

        sheet.write(f"G8", "SL nhận trong tháng", border_bold)
        sheet.write(f"G9", "REC'D", border_bold)

        sheet.write(f"H8", "SL tiêu thụ trong tháng", border_bold)
        sheet.write(f"H9", "USED", border_bold)

        sheet.write(f"I8", "Sl còn lại cuối tháng", border_bold)
        sheet.write(f"I9", "R.O.B", border_bold)

        sheet.write(f"J8", "Khu vực sơn bản dưỡng", border_bold)
        sheet.write(f"J9", "Maintenance Area", border_bold)

        sheet.write(f"K8", "Diện tích sơn", border_bold)
        sheet.write(f"K9", "", border_bold)

    def create_footer(self, workbook, sheet, record_len=0, taken_row=9):
        normal_format = workbook.add_format(self.get_normal_format(top=1))
        format_2 = workbook.add_format(self.get_normal_format(bold=False))

        footer_row = taken_row + record_len + 1
        sheet.merge_range(f"A{footer_row}:K{footer_row}", "", normal_format)

        footer_row_2 = footer_row + 2
        name_1 = "Đại phó kiểm tra\nCheck by Chief officer"
        sheet.write(f"B{footer_row_2}", name_1, format_2)
        sheet.write(f"D{footer_row_2}", "Thuyền trưởng\nCaptain", format_2)
        sheet.write(f"F{footer_row_2}", "Thủy thủ trưởng\nPrepared by Bosun", format_2)
        sheet.write(f"H{footer_row_2}", "Ngày/ date:", format_2)

    def _get_paint_area(self, paint_id, start_date, end_date):
        result = self.env["ship.area.of.paint.job"].read_group(
            [
                ("paint_id", "=", paint_id),
                ("create_date", ">=", start_date),
                ("create_date", "<=", end_date),
            ],
            ["paint_area_m2:sum"],
            ["paint_id"],
        )
        if result:
            history = result[0]
            return history.get("paint_area_m2", 0)
        else:
            return 0

    def _get_paint_position(self, paint_id, start_date, end_date):
        result = self.env["ship.area.of.paint.job"].search(
            [
                ("paint_id", "=", paint_id),
                ("create_date", ">=", start_date),
                ("create_date", "<=", end_date),
            ],
        )
        if result:
            mapped_paint_position = result.mapped("paint_position")
            if mapped_paint_position:
                return ",".join(mapped_paint_position)
            else:
                return ""
        else:
            return ""

    def _get_quantity_of_material_history(
        self, paint_id, start_date, end_date, is_beginning=True
    ):
        if is_beginning:
            result = self.env["ship.paint.history"].search(
                [
                    ("paint_id", "=", paint_id),
                    ("occured_at", ">=", start_date),
                    ("occured_at", "<=", end_date),
                ],
                order="occured_at asc",
                limit=1,
            )
            if result:
                return result.previous_quantity
            else:
                return ""
        else:
            result = self.env["ship.paint.history"].search(
                [
                    ("paint_id", "=", paint_id),
                    ("occured_at", ">=", start_date),
                    ("occured_at", "<=", end_date),
                ],
                order="occured_at desc",
                limit=1,
            )
            if result:
                if result.action == CONST.MINUS_ACTION:
                    return result.previous_quantity - result.quantity_liter
                if result.action == CONST.ADD_ACTION:
                    return result.previous_quantity + result.quantity_liter
            else:
                return ""

    def _get_add_quantity_in_month(self, paint_id, start_date, end_date):
        result = self.env["ship.paint.history"].read_group(
            [
                ("paint_id", "=", paint_id),
                ("occured_at", ">=", start_date),
                ("occured_at", "<=", end_date),
                ("action", "=", CONST.ADD_ACTION),
            ],
            ["quantity_liter:sum"],
            ["paint_id"],
        )
        if result:
            history = result[0]
            return history.get("quantity_liter", 0)
        else:
            return 0

    def _get_minus_quantity_in_month(self, paint_id, start_date, end_date):
        result = self.env["ship.paint.history"].read_group(
            [
                ("paint_id", "=", paint_id),
                ("occured_at", ">=", start_date),
                ("occured_at", "<=", end_date),
                ("action", "=", CONST.MINUS_ACTION),
            ],
            ["quantity_liter:sum"],
            ["paint_id"],
        )
        if result:
            history = result[0]
            return history.get("quantity_liter", 0)
        else:
            return 0
