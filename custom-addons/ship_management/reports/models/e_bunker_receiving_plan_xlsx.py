from odoo import models
import copy
from ...models import CONST
from odoo.exceptions import ValidationError


class BunkerReceivingPlanXlsx(models.AbstractModel):
    _name = "report.ship_bunker_receiving_plan_xlsx"
    _inherit = ["report.utilities"]

    def _generate_xlsx_report(self, workbook, data, record_ids):
        for record_id in record_ids:
            sheet = workbook.add_worksheet("KẾ HOẠCH NHẬN NHIÊN LIỆU")
            measurement_ids = record_id.fuel_tank_measurement_ids
            HFO_measurement_ids = measurement_ids.filtered(
                lambda e: e.fuel_type == "hfo"
            )
            DO_measurement_ids = measurement_ids.filtered(lambda e: e.fuel_type == "do")
            taken_rows = 11
            measurement_len = len(measurement_ids)

            self.create_header(workbook, sheet, record_id)
            self.create_body(
                workbook, sheet, HFO_measurement_ids, DO_measurement_ids, taken_rows
            )
            self.create_footer(workbook, sheet, taken_rows, measurement_len)

        workbook.close()

    def create_body(
        self,
        workbook,
        sheet,
        HFO_measurement_ids,
        DO_measurement_ids,
        taken_rows,
    ):
        normal_format = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align=False)
        )
        format_2 = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align="center")
        )
        format_3 = workbook.add_format(self.get_normal_format(right=1, align="center"))

        for i, measurement_id in enumerate(HFO_measurement_ids):
            stt = i + 1
            row_number = taken_rows + stt

            tank_measurement_at_100 = measurement_id.tank_measurement_at_100
            tank_measurement_at_85 = measurement_id.tank_measurement_at_85
            after_bunkering_estimate = measurement_id.after_bunkering_estimate

            tank_measurement_at_0 = measurement_id.tank_measurement_at_0
            tank_measurement_at_1 = measurement_id.tank_measurement_at_1
            tank_measurement_at_2 = measurement_id.tank_measurement_at_2
            tank_measurement_at_3 = measurement_id.tank_measurement_at_3

            # HFO
            sheet.write(f"A{row_number}", measurement_id.tank_name, normal_format)
            sheet.write(f"B{row_number}", measurement_id.measure_type, normal_format)
            sheet.write(f"C{row_number}", tank_measurement_at_100, format_2)
            sheet.write(f"D{row_number}", tank_measurement_at_85, format_2)
            sheet.write(f"E{row_number}", measurement_id.measure_adjustment, format_2)
            sheet.write(f"F{row_number}", measurement_id.volume_m3, format_2)
            sheet.write(f"G{row_number}", measurement_id.receiving_volume, format_2)
            sheet.write(f"H{row_number}", after_bunkering_estimate, format_2)
            sheet.write(f"I{row_number}", tank_measurement_at_0, format_2)
            sheet.write(f"J{row_number}", tank_measurement_at_1, format_2)
            sheet.write(f"K{row_number}", tank_measurement_at_2, format_2)
            sheet.write(f"L{row_number}", tank_measurement_at_3, format_2)
            sheet.write(f"M{row_number}", measurement_id.percentage_fill, format_2)

        HFO_len = len(HFO_measurement_ids)
        total_HFO_row_number = taken_rows + HFO_len + 1
        sheet.write(f"A{total_HFO_row_number}", "", format_3)
        sheet.write(f"B{total_HFO_row_number}", "TOTAL (TỔNG SỐ) HFO", format_3)
        sheet.write(f"C{total_HFO_row_number}", "", format_3)
        sheet.write(f"D{total_HFO_row_number}", "", format_3)
        sheet.write(f"E{total_HFO_row_number}", "", format_3)
        sheet.write(f"F{total_HFO_row_number}", "", format_3)
        sheet.write(f"G{total_HFO_row_number}", "", format_3)
        sheet.write(f"H{total_HFO_row_number}", "", format_3)
        sheet.write(f"I{total_HFO_row_number}", "", format_3)
        sheet.write(f"J{total_HFO_row_number}", "", format_3)
        sheet.write(f"K{total_HFO_row_number}", "", format_3)
        sheet.write(f"L{total_HFO_row_number}", "", format_3)
        sheet.write(f"M{total_HFO_row_number}", "", format_3)

        for i, measurement_id in enumerate(DO_measurement_ids):
            stt = i + 1
            row_number = total_HFO_row_number + stt

            # DO
            tank_measurement_at_100 = measurement_id.tank_measurement_at_100
            tank_measurement_at_85 = measurement_id.tank_measurement_at_85
            after_bunkering_estimate = measurement_id.after_bunkering_estimate

            tank_measurement_at_0 = measurement_id.tank_measurement_at_0
            tank_measurement_at_1 = measurement_id.tank_measurement_at_1
            tank_measurement_at_2 = measurement_id.tank_measurement_at_2
            tank_measurement_at_3 = measurement_id.tank_measurement_at_3

            # HFO
            sheet.write(f"A{row_number}", measurement_id.tank_name, normal_format)
            sheet.write(f"B{row_number}", measurement_id.measure_type, normal_format)
            sheet.write(f"C{row_number}", tank_measurement_at_100, format_2)
            sheet.write(f"D{row_number}", tank_measurement_at_85, format_2)
            sheet.write(f"E{row_number}", measurement_id.measure_adjustment, format_2)
            sheet.write(f"F{row_number}", measurement_id.volume_m3, format_2)
            sheet.write(f"G{row_number}", measurement_id.receiving_volume, format_2)
            sheet.write(f"H{row_number}", after_bunkering_estimate, format_2)
            sheet.write(f"I{row_number}", tank_measurement_at_0, format_2)
            sheet.write(f"J{row_number}", tank_measurement_at_1, format_2)
            sheet.write(f"K{row_number}", tank_measurement_at_2, format_2)
            sheet.write(f"L{row_number}", tank_measurement_at_3, format_2)
            sheet.write(f"M{row_number}", measurement_id.percentage_fill, format_2)

        DO_len = len(DO_measurement_ids)
        total_DO_row_number = total_HFO_row_number + DO_len + 1
        sheet.write(f"A{total_DO_row_number}", "", format_3)
        sheet.write(f"B{total_DO_row_number}", "TOTAL (TỔNG SỐ) DO", format_3)
        sheet.write(f"C{total_DO_row_number}", "", format_3)
        sheet.write(f"D{total_DO_row_number}", "", format_3)
        sheet.write(f"E{total_DO_row_number}", "", format_3)
        sheet.write(f"F{total_DO_row_number}", "", format_3)
        sheet.write(f"G{total_DO_row_number}", "", format_3)
        sheet.write(f"H{total_DO_row_number}", "", format_3)
        sheet.write(f"I{total_DO_row_number}", "", format_3)
        sheet.write(f"J{total_DO_row_number}", "", format_3)
        sheet.write(f"K{total_DO_row_number}", "", format_3)
        sheet.write(f"L{total_DO_row_number}", "", format_3)
        sheet.write(f"M{total_DO_row_number}", "", format_3)

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
        a_width = 15
        b_width = 18
        c_width = 17
        d_width = 17
        e_width = 25
        f_width = 15
        g_width = 15
        h_width = 15
        i_width = 8
        j_width = 8
        k_width = 8
        l_width = 8
        m_width = 10
        sheet.set_column("A:A", a_width)
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
        sheet.set_column("L:L", l_width)
        sheet.set_column("M:M", m_width)

        image_path = "/mnt/extra-addons/images/vsico-1.png"
        image_stream = self._get_image_by_path(image_path)
        if image_stream:
            sheet.insert_image("A1", image_path, {"image_data": image_stream})

        sheet.merge_range(f"A1:L1", "CÔNG TY CỔ PHẦN HÀNG HẢI VSICO", bold)
        sheet.merge_range(
            f"A2:L2", "VSICO SHIPPING JOINT STOCK COMPANY", not_bold_italic
        )

        sheet.merge_range(f"A3:L3", "BUNKER RECEIVING PLAN", bold)
        sheet.merge_range(f"A4:L4", "KẾ HOẠCH NHẬN NHIÊN LIỆU", bottom_not_bold_italic)

        name_3 = "Control No: VSICO-09-04\nIssued Date: 01/12/2022\nRevision No: 00\nRevised Date;\nPage:     of "
        sheet.merge_range(f"M1:M4", name_3, bottom_right_not_bold_not_center)

        datetime = record_id.arrival_datetime
        company_name = record_id.company_id.name
        sheet.merge_range(f"A5:B5", f"MV (Tàu): {company_name}", not_bold_not_center)
        sheet.merge_range(f"C5:D5", f"Date (T/gian): {datetime}", not_bold_not_center)
        sheet.merge_range(
            f"J5:L5", f"Order no. (Lần thứ):      /20__", not_bold_not_center
        )

        name_5 = "When arrive port/ anchorage area (Khi tới cảng/khu neo) . . ."
        sheet.merge_range(f"A6:C6", name_5, not_bold_not_center)
        sheet.merge_range(
            f"D6:F6",
            "C5 / (tỷ trọng15C* (1- [ {T-15} x 0.00064]) )",
            not_bold_not_center,
        )
        sheet.merge_range(f"J6:L6", "Heel (Độ nghiêng): . . .", not_bold_not_center)

        sheet.write(f"A7", "Receive (Nhận):", not_bold_not_center)
        sheet.write(f"B7", "H.F.O", not_bold_not_center)
        sheet.write(
            f"C7", "… tấn ( bắt từ order dầu dòng 32 form 1204)", not_bold_not_center
        )
        sheet.write(f"E7", "at . . .C", not_bold_not_center)
        sheet.write(f"F7", "điền", not_bold_not_center)
        sheet.write(f"G7", "Density FO  (Tỷ trọng 15C): . . .", not_bold_not_center)
        sheet.write(f"I7", "điền", not_bold_not_center)
        sheet.merge_range(f"J7:K7", "Trim:. . . m", not_bold_not_center)
        sheet.write(f"M7", "điền", not_bold_not_center)

        sheet.write(f"B8", "D.O/G.O .", not_bold_not_center)
        sheet.write(f"C8", "… tấn", not_bold_not_center)
        sheet.write(f"D8", "...m3", not_bold_not_center)
        sheet.write(f"E8", "at. . .C", not_bold_not_center)
        sheet.write(f"G8", "Density DO (Tỷ trọng15C): . . .", not_bold_not_center)
        sheet.merge_range(
            f"J8:M8", "(Chênh lệch mớn nước mũi lái)", not_bold_not_center
        )

        # header

        name_7 = "Measure in Sound or Space/\nĐo theo Độ sâu/Khoảng không"
        name_8 = "Tanks measurement/ capacity/\nSố đo (m)/Dung tích két (m3)"
        name_9 = "Remain on Board/\nCòn lại trên tàu"
        name_10 = "After bunkering (Estimate)/\nSau khi nhân dầu (Dự tính)"
        name_11 = "Tank Measurement (m) when trim is/\nSố đo két (m) khi chênh lệch mũi lái là"
        sheet.merge_range(f"A9:A11", "Tank No.", border_bold)
        sheet.merge_range(f"B9:B11", name_7, border_bold)
        sheet.merge_range(f"C9:D10", name_8, border_bold)
        sheet.write(f"C11", "at 100%", border_bold)
        sheet.write(f"D11", "at 85%", border_bold)
        sheet.merge_range(f"E9:F9", name_9, border_bold)
        sheet.merge_range(f"E10:E11", "Mearure/Adjust/Số đo/Hiệu chỉnh(m)", border_bold)
        sheet.write(f"F10", "Volume - m3 At / (Tại) . . . 0C", border_bold)
        sheet.write(f"F11", "(1)", border_bold)
        sheet.write(f"G9", "Receiving - m3/\nNhận thêm- m3", border_bold)
        sheet.write(f"G10", "At (Tại) . . . 0C", border_bold)
        sheet.write(f"G11", "(2)", border_bold)
        sheet.merge_range(f"H9:M9", name_10, border_bold)
        sheet.write(f"H10", "Volume - m3/\nAt (Tại) . . . 0C", border_bold)
        sheet.write(f"H11", "(3) = (1) + (2)", border_bold)
        sheet.merge_range(f"I10:L10", name_11, border_bold)
        sheet.write(f"I11", "0.0 m", border_bold)
        sheet.write(f"J11", "1.0 m", border_bold)
        sheet.write(f"K11", "2.0 m", border_bold)
        sheet.write(f"L11", "3.0 m", border_bold)
        sheet.merge_range(f"M10:M11", "%", border_bold)

    def create_footer(self, workbook, sheet, taken_rows, record_len):
        normal_format = workbook.add_format(self.get_normal_format(top=1))
        format_2 = workbook.add_format(self.get_normal_format(bold=False))

        total_row_len = 2
        footer_row = taken_rows + record_len + total_row_len

        row_1 = footer_row + 1
        sheet.merge_range(f"A{row_1}:M{row_1}", "", normal_format)

        row_2 = footer_row + 2
        sheet.write(f"A{row_2}", "3rd Engineer\nMáy ba", format_2)
        sheet.write(f"C{row_2}", "CHIEF ENGINEER\nMáy trưởng", format_2)
        sheet.write(f"E{row_2}", "CHIEF OFFICER\nĐại phó", format_2)
        sheet.write(f"G{row_2}", "MASTER\nThuyền trưởng", format_2)
        sheet.write(f"I{row_2}", "BUNKER SUPPLIER\nNgười cấp dầu", format_2)


class EBunkerReceivingPlanXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_e_bunker_receiving_plan_xlsx"
    _inherit = [
        "report.report_xlsx.abstract",
        "report.ship_bunker_receiving_plan_xlsx",
    ]

    def generate_xlsx_report(self, workbook, data, record_ids):
        self._generate_xlsx_report(workbook, data, record_ids)


class IBunkerReceivingPlanXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_i_bunker_receiving_plan_xlsx"
    _inherit = [
        "report.report_xlsx.abstract",
        "report.ship_bunker_receiving_plan_xlsx",
    ]

    def generate_xlsx_report(self, workbook, data, record_ids):
        self._generate_xlsx_report(workbook, data, record_ids)
