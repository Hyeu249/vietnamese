from odoo import models
import copy
from ...models import CONST
from odoo.exceptions import ValidationError


class FuelOilTankConditionXlsx(models.AbstractModel):
    _name = "report.ship_fuel_oil_tank_condition_xlsx"
    _inherit = ["report.utilities"]

    def _generate_xlsx_report(self, workbook, data, record_ids):

        for record_id in record_ids:
            sheet = workbook.add_worksheet("TÌNH TRẠNG KÉT DẦU")
            fuel_condition_ids = record_id.fuel_condition_ids
            tank_ids = fuel_condition_ids.mapped("fuel_tank_ids")
            HFO_tank_ids = tank_ids.filtered(lambda e: e.fuel_type == "hfo")
            DO_tank_ids = tank_ids.filtered(lambda e: e.fuel_type == "do")
            taken_rows = 8
            tank_len = len(tank_ids)

            self.create_header(workbook, sheet, record_id)
            self.create_body(
                workbook,
                sheet,
                HFO_tank_ids,
                DO_tank_ids,
                taken_rows,
            )
            self.create_footer(workbook, sheet, taken_rows, tank_len)

        workbook.close()

    def create_body(
        self,
        workbook,
        sheet,
        HFO_tank_ids,
        DO_tank_ids,
        taken_rows,
    ):
        normal_format = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align=False)
        )
        format_2 = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align="center")
        )
        format_3 = workbook.add_format(self.get_normal_format(right=1, align="center"))

        for i, tank_id in enumerate(HFO_tank_ids):
            stt = i + 1
            row_number = taken_rows + stt

            # HFO
            sheet.write(f"B{row_number}", tank_id.tank_name, normal_format)
            sheet.write(f"C{row_number}", tank_id.measurement, format_2)
            sheet.write(f"D{row_number}", tank_id.volumetric_capacity, format_2)
            sheet.write(f"E{row_number}", tank_id.expansion_factor, format_2)
            sheet.write(f"F{row_number}", tank_id.volumetric_at_150C, format_2)
            sheet.write(f"G{row_number}", tank_id.weight, format_2)

        HFO_tank_len = len(HFO_tank_ids)
        total_HFO_row_number = taken_rows + HFO_tank_len + 1
        sheet.write(f"A{total_HFO_row_number}", "", format_3)
        sheet.write(f"B{total_HFO_row_number}", "TOTAL (TỔNG SỐ) HFO", format_3)
        sheet.write(f"C{total_HFO_row_number}", "", format_3)
        sheet.write(f"D{total_HFO_row_number}", "", format_3)
        sheet.write(f"E{total_HFO_row_number}", "", format_3)
        sheet.write(f"F{total_HFO_row_number}", "", format_3)
        sheet.write(f"G{total_HFO_row_number}", "", format_3)

        for i, tank_id in enumerate(DO_tank_ids):
            stt = i + 1
            row_number = total_HFO_row_number + stt

            # DO
            sheet.write(f"B{row_number}", tank_id.tank_name, normal_format)
            sheet.write(f"C{row_number}", tank_id.measurement, format_2)
            sheet.write(f"D{row_number}", tank_id.volumetric_capacity, format_2)
            sheet.write(f"E{row_number}", tank_id.expansion_factor, format_2)
            sheet.write(f"F{row_number}", tank_id.volumetric_at_150C, format_2)
            sheet.write(f"G{row_number}", tank_id.weight, format_2)

        DO_tank_len = len(DO_tank_ids)
        total_DO_row_number = total_HFO_row_number + DO_tank_len + 1
        sheet.write(f"A{total_DO_row_number}", "", format_3)
        sheet.write(f"B{total_DO_row_number}", "TOTAL (TỔNG SỐ) DO", format_3)
        sheet.write(f"C{total_DO_row_number}", "", format_3)
        sheet.write(f"D{total_DO_row_number}", "", format_3)
        sheet.write(f"E{total_DO_row_number}", "", format_3)
        sheet.write(f"F{total_DO_row_number}", "", format_3)
        sheet.write(f"G{total_DO_row_number}", "", format_3)

    def create_header(self, workbook, sheet, record_id):
        border_bold = workbook.add_format(self.get_normal_format(border=1))
        bold = workbook.add_format(self.get_normal_format())
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
        a_width = 8
        b_width = 20
        c_width = 15
        d_width = 20
        e_width = 15
        f_width = 15
        g_width = 15
        sheet.set_column("A:A", a_width)
        sheet.set_column("B:B", b_width)
        sheet.set_column("C:C", c_width)
        sheet.set_column("D:D", d_width)
        sheet.set_column("E:E", e_width)
        sheet.set_column("F:F", f_width)
        sheet.set_column("G:G", g_width)

        image_path = "/mnt/extra-addons/images/vsico-1.png"
        image_stream = self._get_image_by_path(image_path)
        if image_stream:
            sheet.insert_image("A1", image_path, {"image_data": image_stream})

        sheet.merge_range(f"A1:F1", "CÔNG TY CỔ PHẦN HÀNG HẢI VSICO", bold)
        sheet.merge_range(
            f"A2:F2", "VSICO SHIPPING JOINT STOCK COMPANY", not_bold_italic
        )

        sheet.merge_range(f"A3:F3", "TÌNH TRẠNG KÉT DẦU", bold)
        sheet.merge_range(f"A4:F4", "FUEL OIL TANKS CONDITION", bottom_not_bold_italic)

        name_3 = "Control No: VSICO-09-04\nIssued Date: 01/12/2022\nRevision No: 00\nRevised Date;\nPage:     of "
        sheet.merge_range(f"G1:G4", name_3, bottom_right_not_bold_not_center)

        company_name = record_id.company_id.name
        sheet.merge_range(f"A5:C5", f"MV (Tàu): {company_name}", not_bold_not_center)
        sheet.merge_range(f"D5:E5", "Time/Date (T/gian): . . .", not_bold_not_center)
        sheet.merge_range(f"F5:G5", "Voy. No. (Chuyến số): . . .", not_bold_not_center)

        sheet.merge_range(
            f"A6:C6", "Trim (Chênh lệnh mũi lái): . . . (m)", not_bold_not_center
        )
        sheet.merge_range(f"D6:E6", "Heel (Độ nghiêng): .1,2", not_bold_not_center)
        sheet.merge_range(
            f"F6:G6", "Order no. (Lần thứ):. . . /201_", not_bold_not_center
        )

        sheet.merge_range(
            f"A7:C7", "Density (Tỷ trọng) H.F.O:  . . .", not_bold_not_center
        )
        sheet.merge_range(
            f"D7:E7", "Density (Tỷ trọng) D.O: . . .", not_bold_not_center
        )
        sheet.merge_range(
            f"F7:G7", "S.W.Temp.(N/độ n/biển): . .0C", not_bold_not_center
        )

        name_7 = "Factor of Temp. Adjust.\nHệ số hiệu\nchỉnh nhiệt độ"
        name_8 = "Volumetric at150C\nDung tích\nTại 150C (m3)"
        sheet.write(f"A8", "Type\nLoại\nN/liệu", border_bold)
        sheet.write(f"B8", "Tank Name/No.\nTên/ Số két", border_bold)
        sheet.write(f"C8", "Measurement\nSố đo\n(m)", border_bold)
        sheet.write(f"D8", "Volumetric\nDung tích\n(m3)", border_bold)
        sheet.write(f"E8", name_7, border_bold)
        sheet.write(f"F8", name_8, border_bold)
        sheet.write(f"G8", "Weight\nTrọng lượng\n(MT)", border_bold)

    def create_footer(self, workbook, sheet, taken_rows, tank_len):
        format_2 = workbook.add_format(self.get_normal_format(bold=False))
        format_3 = workbook.add_format(self.get_normal_format(border=1, bold=False))
        format_5 = workbook.add_format(
            self.get_normal_format(border=1, bold=False, align=False)
        )

        total_row_len = 2
        footer_row = taken_rows + tank_len + total_row_len

        row_1 = footer_row + 1
        row_2 = footer_row + 2
        sheet.merge_range(
            f"A{row_1}:C{row_1}", "Actual Weight (Tổng số thực tế): (1)", format_5
        )
        sheet.write(f"D{row_1}", " H.F.O:. . . G18 . . . MT", format_3)
        sheet.merge_range(f"E{row_1}:G{row_1}", "D.O: . . . G24 . . . MT", format_3)

        sheet.merge_range(
            f"A{row_2}:C{row_2}", "Weight in Eng.Log (T/số theo sổ sách) (2)", format_5
        )
        sheet.write(f"D{row_2}", "H.F.O:. . . bắt theo logbook. . .MT", format_3)
        sheet.merge_range(
            f"E{row_2}:G{row_2}", "D.O:. . . bắt theo logbook. . .MT", format_3
        )

        row_3 = footer_row + 3
        row_4 = footer_row + 4
        row_5 = footer_row + 5
        name_3 = "Difference (Chênh lệch)        (3) = (1) - (2)   H.F.O:. . .MT"
        name_4 = "Last measured Weight (Lần đo trước)   (4)"
        name_5 = "Consumption between two measurements (Tiêu thụ giữa 2 lần đo) (5)=(4)-(1)+(SL nhận)"
        sheet.merge_range(f"A{row_3}:C{row_3}", name_3, format_5)
        sheet.write(f"D{row_3}", "H.F.O: . . . . . . . MT", format_3)
        sheet.merge_range(f"E{row_3}:G{row_3}", "D.O: . . . . . . . MT", format_3)

        sheet.merge_range(f"A{row_4}:C{row_4}", name_4, format_5)
        sheet.write(f"D{row_4}", "H.F.O: . . . . . . . MT", format_3)
        sheet.merge_range(f"E{row_4}:G{row_4}", "D.O: . . . . . . . MT", format_3)

        sheet.merge_range(f"A{row_5}:C{row_5}", name_5, format_5)
        sheet.write(f"D{row_5}", "H.F.O: . . . . . . . MT", format_3)
        sheet.merge_range(f"E{row_5}:G{row_5}", "D.O: . . . . . . . MT", format_3)

        row_6 = footer_row + 7
        name_6 = "ENGINEER in CHARGE\nSỹ quan máy phụ trách"
        name_7 = "Deck officer duty\nS.quan boong đi ca"
        name_8 = "Master or SUPERINTENDENT\nThuyền trưởng hoặc Đại diện Công ty"
        sheet.merge_range(f"A{row_6}:B{row_6}", name_6, format_2)
        sheet.merge_range(f"C{row_6}:D{row_6}", "CHIEF ENGINEER\nMáy trưởng", format_2)
        sheet.merge_range(f"E{row_6}:F{row_6}", name_7, format_2)
        sheet.merge_range(f"G{row_6}:H{row_6}", name_8, format_2)


class FuelEOilTankConditionXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_fuel_e_oil_tank_condition_xlsx"
    _inherit = [
        "report.report_xlsx.abstract",
        "report.ship_fuel_oil_tank_condition_xlsx",
    ]

    def generate_xlsx_report(self, workbook, data, record_ids):
        self._generate_xlsx_report(workbook, data, record_ids)


class FuelIOilTankConditionXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_fuel_i_oil_tank_condition_xlsx"
    _inherit = [
        "report.report_xlsx.abstract",
        "report.ship_fuel_oil_tank_condition_xlsx",
    ]

    def generate_xlsx_report(self, workbook, data, record_ids):
        self._generate_xlsx_report(workbook, data, record_ids)
