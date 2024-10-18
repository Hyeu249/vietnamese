from odoo import models
import copy
from ...models import CONST


class FuelECalculatorXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_fuel_e_calculator_xlsx"
    _inherit = ["report.report_xlsx.abstract", "report.utilities"]

    def generate_xlsx_report(self, workbook, data, record_ids):

        for i, record_id in enumerate(record_ids):
            y = i + 1
            sheet = workbook.add_worksheet(f"BẢNG TÍNH CẤP NHIÊN LIỆU {y}")
            self.write_sheet(workbook, sheet, record_id)

        workbook.close()

    def write_sheet(self, workbook, sheet, record_id):
        self.create_header(workbook, sheet, record_id)
        # self.create_body(workbook, sheet, record_id)
        # self.create_footer(workbook, sheet, len(record_id))

    def create_body(
        self, workbook, sheet, sample_record_ids, taken_rows_for_HFO, taken_rows_for_MDO
    ):
        normal_format = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align=False)
        )
        format_2 = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align="center")
        )

        for i, sample_id in enumerate(sample_record_ids):
            stt = i + 1
            row_number = taken_rows_for_HFO + stt

            # HFO
            hfo_date_of_bunker = sample_id.hfo_date_of_bunker
            hfo_location = sample_id.hfo_location
            hfo_bunker_receipt_number = sample_id.hfo_bunker_receipt_number
            hfo_sulphur_declared = sample_id.hfo_sulphur_declared
            hfo_sample_number = sample_id.hfo_sample_number
            hfo_fuel_seal_number = sample_id.hfo_fuel_seal_number
            hfo_analysed_sulphur_content = sample_id.hfo_analysed_sulphur_content

            sheet.write(f"A{row_number}", hfo_date_of_bunker, normal_format)
            sheet.write(f"B{row_number}", hfo_location, format_2)
            sheet.write(f"C{row_number}", hfo_bunker_receipt_number, format_2)
            sheet.write(f"D{row_number}", hfo_sulphur_declared, format_2)
            sheet.write(f"E{row_number}", hfo_sample_number, format_2)
            sheet.write(f"F{row_number}", hfo_fuel_seal_number, format_2)
            sheet.write(f"G{row_number}", hfo_analysed_sulphur_content, format_2)

            # MDO
            row_number_for_MDO = taken_rows_for_MDO + stt

            mdo_date_of_bunker = sample_id.mdo_date_of_bunker
            mdo_location = sample_id.mdo_location
            mdo_bunker_receipt_number = sample_id.mdo_bunker_receipt_number
            mdo_sulphur_declared = sample_id.mdo_sulphur_declared
            mdo_sample_number = sample_id.mdo_sample_number
            mdo_fuel_seal_number = sample_id.mdo_fuel_seal_number
            mdo_analysed_sulphur_content = sample_id.mdo_analysed_sulphur_content

            sheet.write(f"A{row_number_for_MDO}", mdo_date_of_bunker, normal_format)
            sheet.write(f"B{row_number_for_MDO}", mdo_location, format_2)
            sheet.write(f"C{row_number_for_MDO}", mdo_bunker_receipt_number, format_2)
            sheet.write(f"D{row_number_for_MDO}", mdo_sulphur_declared, format_2)
            sheet.write(f"E{row_number_for_MDO}", mdo_sample_number, format_2)
            sheet.write(f"F{row_number_for_MDO}", mdo_fuel_seal_number, format_2)
            sheet.write(
                f"G{row_number_for_MDO}", mdo_analysed_sulphur_content, format_2
            )

    def create_header(self, workbook, sheet, record_id):
        border_not_center = workbook.add_format(
            self.get_normal_format(border=1, align=False)
        )

        border_not_bold_align_right = workbook.add_format(
            self.get_normal_format(border=1, bold=False, align="right")
        )
        border_bold = workbook.add_format(self.get_normal_format(border=1))
        border_not_bold = workbook.add_format(
            self.get_normal_format(border=1, bold=False)
        )
        border_not_bold_not_center = workbook.add_format(
            self.get_normal_format(border=1, bold=False, align=False)
        )
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

        # set height column
        height = 25
        sheet.set_row(6, height)
        sheet.set_row(7, height)
        sheet.set_row(8, height)
        sheet.set_row(9, height)
        sheet.set_row(10, height)

        sheet.set_row(16, height)
        sheet.set_row(17, height)
        sheet.set_row(18, height)
        sheet.set_row(19, height)
        sheet.set_row(20, height)
        sheet.set_row(21, height)
        sheet.set_row(22, height)
        sheet.set_row(23, height)

        sheet.set_row(27, height)
        sheet.set_row(28, height)
        sheet.set_row(29, height)
        sheet.set_row(30, height)
        sheet.set_row(31, height)

        sheet.set_row(34, height)
        sheet.set_row(35, height)

        # set width column
        a_width = 5
        b_width = 25
        c_width = 30
        d_width = 35
        e_width = 25
        sheet.set_column("A:A", a_width)
        sheet.set_column("B:B", b_width)
        sheet.set_column("C:C", c_width)
        sheet.set_column("D:D", d_width)
        sheet.set_column("E:E", e_width)

        image_path = "/mnt/extra-addons/images/vsico-1.png"
        image_stream = self._get_image_by_path(image_path)
        if image_stream:
            sheet.insert_image("A1", image_path, {"image_data": image_stream})

        sheet.merge_range(f"A1:D1", "CÔNG TY CỔ PHẦN HÀNG HẢI VSICO", bold)
        sheet.merge_range(
            f"A2:D2", "VSICO SHIPPING JOINT STOCK COMPANY", not_bold_italic
        )

        name_2 = "FUEL OIL CACULATOR/ BẢNG TÍNH CẤP NHIÊN LIỆU"
        sheet.merge_range(f"A3:E3", name_2, border_not_bold)

        name_3 = "Control No: VSICO-09-04\nIssued Date: 01/12/2022\nRevision No: 00\nRevised Date;\nPage:     of "

        sheet.merge_range(f"E1:E2", name_3, bottom_right_not_bold_not_center)

        company_name = record_id.company_id.name
        create_date = record_id.create_date
        sheet.merge_range(f"A4:C4", f"MV (Tàu): {company_name}", not_bold_not_center)
        sheet.write(f"D4", f"Date (Ngày): {create_date}", not_bold_not_center)
        sheet.write(f"D5", "Order no. (Lần thứ): . . .", not_bold_not_center)

        sheet.merge_range(
            f"A6:C6", "1. Tank Capacity (Dung tích két)", not_bold_not_center
        )

        name_6 = "% Tank Capacity (% Dung tích các két)"
        sheet.merge_range(f"B7:C7", name_6, border_bold)
        sheet.merge_range(f"B8:C8", "100%", border_not_bold)
        sheet.merge_range(f"B9:C9", "90%", border_not_bold)
        sheet.merge_range(f"B10:C10", "85%", border_not_bold)
        sheet.merge_range(f"B11:C11", "80%", border_not_bold)
        sheet.write(f"D7", "F.O", border_bold)
        sheet.write(f"D8", "1066.2 m3", border_not_bold)
        sheet.write(f"D9", "959.58 m3", border_not_bold)
        sheet.write(f"D10", "852.96 m3", border_not_bold)
        sheet.write(f"D11", "852,96m3", border_not_bold)
        sheet.write(f"E7", "D.O", border_bold)
        sheet.write(f"E8", "129. 9 m3", border_not_bold)
        sheet.write(f"E9", "116.91 m3", border_not_bold)
        sheet.write(f"E10", "110,415m3", border_not_bold)
        sheet.write(f"E11", "103,92m3", border_not_bold)

        name_7 = "2. Estimation of Remaining Oil at . . . .hrs, date . . . . . . ."
        name_8 = "(Dự kiến lượng nhiên liệu còn lại trên tàu khi nhận dầu lúc . . . giờ, ngày . . . . . . . . )  đưa ngày giờ dự kiến lúc nhận (dự kiến thôi)"
        sheet.merge_range(f"A13:E13", name_7, not_bold_not_center)
        sheet.merge_range(f"B14:E14", name_8, not_bold_not_center)
        sheet.merge_range(
            f"B15:C15", "Sailing Days (Ngày tàu chạy biển):", not_bold_not_center
        )
        sheet.merge_range(
            f"D15:E15", "Stopping Days (Ngày tàu dừng):", not_bold_not_center
        )

        name_10 = "Remain. Oil/ Date . . . (Ngày . . . . .. . . Lượng nhiên liệu còn)"
        name_11 = "In Sett./Serv. Tank (Trong két lắng/ trực nhật)"
        name_12 = "Remainning Oil in Other Tanks (Trong các két khác)"
        name_13 = "Consumtion to Bunk. Port (Nhiên liệu tiêu thụ tới cảng nhận dầu)"
        name_14 = "Remain. Oil at Bunk. Port (Nhiên liệu còn lại tại cảng nhận dầu)"
        name2_15 = ". . . .16,2 . . Tấn/ngày x . . . . . ngày"
        name2_16 = ". . . 1,5. . . Tấn/ngày x . . . . . ngày"
        name2_17 = ". . . 1,3. . . Tấn/ngày x . . . . . ngày"
        name2_18 = ". . . .1,4 . . Tấn/ngày x . . . . . ngày"
        sheet.merge_range(f"B17:C17", name_10, border_not_center)
        sheet.merge_range(f"B18:C18", name_11, border_not_center)
        sheet.merge_range(f"B19:C19", name_12, border_not_center)
        sheet.merge_range(f"B20:C20", name_13, border_not_center)
        sheet.write(f"B21", "M/E (M/chính):", border_not_center)
        sheet.write(f"C21", name2_15, border_not_bold_not_center)
        sheet.write(f"B22", "Boiler (Nồi hơi):", border_not_center)
        sheet.write(f"C22", name2_16, border_not_bold_not_center)

        sheet.merge_range(f"B23:B24", "G/E (Máy đèn):", border_not_center)
        sheet.write(f"C23", name2_17, border_not_bold_not_center)
        sheet.write(f"C24", name2_18, border_not_bold_not_center)
        sheet.merge_range(f"B25:C25", name_14, border_not_center)
        # value
        remaining_oil_serv_tank_fo = record_id.remaining_oil_serv_tank_fo
        remaining_oil_other_tanks_fo = record_id.remaining_oil_other_tanks_fo
        consumption_to_bunk_port_mt_fo = record_id.consumption_to_bunk_port_mt_fo
        me_consumption_fo = record_id.me_consumption_fo
        boiler_consumption_fo = record_id.boiler_consumption_fo
        ge_consumption_sailing_ship_fo = record_id.ge_consumption_sailing_ship_fo
        ge_consumption_stopping_ship_fo = record_id.ge_consumption_stopping_ship_fo
        remaining_oil_bunk_port_mt_fo = record_id.remaining_oil_bunk_port_mt_fo

        remaining_oil_serv_tank_do = record_id.remaining_oil_serv_tank_do
        remaining_oil_other_tanks_do = record_id.remaining_oil_other_tanks_do
        consumption_to_bunk_port_mt_do = record_id.consumption_to_bunk_port_mt_do
        me_consumption_do = record_id.me_consumption_do
        boiler_consumption_do = record_id.boiler_consumption_do
        ge_consumption_sailing_ship_do = record_id.ge_consumption_sailing_ship_do
        ge_consumption_stopping_ship_do = record_id.ge_consumption_stopping_ship_do
        remaining_oil_bunk_port_mt_do = record_id.remaining_oil_bunk_port_mt_do

        for_name_1 = f"Sailing Ship (Tàu chạy): {ge_consumption_sailing_ship_fo} MT"
        for_name_2 = f"Stopping Ship (Tàu dừng): {ge_consumption_stopping_ship_fo} MT"
        sheet.write(f"D17", "MT", border_not_bold_align_right)
        sheet.write(
            f"D18", f"{remaining_oil_serv_tank_fo} MT", border_not_bold_align_right
        )
        sheet.write(
            f"D19", f"{remaining_oil_other_tanks_fo} MT", border_not_bold_align_right
        )
        sheet.write(
            f"D20", f"{consumption_to_bunk_port_mt_fo} MT", border_not_bold_align_right
        )
        sheet.write(f"D21", f"{me_consumption_fo} MT", border_not_bold_align_right)
        sheet.write(f"D22", f"{boiler_consumption_fo} MT", border_not_bold_align_right)
        sheet.write(f"D23", for_name_1, border_not_bold_not_center)
        sheet.write(f"D24", for_name_2, border_not_bold_not_center)
        sheet.write(
            f"D25", f"{remaining_oil_bunk_port_mt_fo} MT", border_not_bold_align_right
        )

        for_name_3 = f"Tàu chạy: {ge_consumption_sailing_ship_do} MT"
        for_name_4 = f"Tàu dừng: {ge_consumption_stopping_ship_do} MT"
        sheet.write(f"E17", "MT", border_not_bold_align_right)
        sheet.write(
            f"E18", f"{remaining_oil_serv_tank_do} MT", border_not_bold_align_right
        )
        sheet.write(
            f"E19", f"{remaining_oil_other_tanks_do} MT", border_not_bold_align_right
        )
        sheet.write(
            f"E20", f"{consumption_to_bunk_port_mt_do} MT", border_not_bold_align_right
        )
        sheet.write(f"E21", f"{me_consumption_do} MT", border_not_bold_align_right)
        sheet.write(f"E22", f"{boiler_consumption_do} MT", border_not_bold_align_right)
        sheet.write(f"E23", for_name_3, border_not_bold_not_center)
        sheet.write(f"E24", for_name_4, border_not_bold_not_center)
        sheet.write(
            f"E25", f"{remaining_oil_bunk_port_mt_do} MT", border_not_bold_align_right
        )

        name_15 = (
            "3.Estimation of Bunkering Quantity (Dự kiến lượng nhiên liệu cần cấp)"
        )
        name_16 = "In case of 90% Filling (Trong trường hợp 90% két)"
        name_17 = "In case of 85% Filling (Trong trường hợp 85% két)"
        name_18 = "In case of 90% Filling (Trong trường hợp 80% két)"
        sheet.merge_range(f"A27:E27", name_15, not_bold_not_center)
        sheet.merge_range(f"B28:C28", name_16, border_not_center)
        sheet.merge_range(f"B29:C29", name_17, border_not_center)
        sheet.merge_range(f"B30:C30", name_18, border_not_center)
        sheet.merge_range(
            f"B31:C31", "Resonable Quantity (Số lượng hợp lý)", border_not_center
        )
        sheet.merge_range(f"B32:C32", "", border_bold)
        # value
        bunkering_quantity_90_percent_fo = record_id.bunkering_quantity_90_percent_fo
        bunkering_quantity_85_percent_fo = record_id.bunkering_quantity_85_percent_fo
        bunkering_quantity_80_percent_fo = record_id.bunkering_quantity_80_percent_fo
        reasonable_quantity_fo = record_id.reasonable_quantity_fo

        bunkering_quantity_90_percent_do = record_id.bunkering_quantity_90_percent_do
        bunkering_quantity_85_percent_do = record_id.bunkering_quantity_85_percent_do
        bunkering_quantity_80_percent_do = record_id.bunkering_quantity_80_percent_do
        reasonable_quantity_do = record_id.reasonable_quantity_do

        sheet.write(
            f"D28",
            f"{bunkering_quantity_90_percent_fo} m3",
            border_not_bold_align_right,
        )
        sheet.write(
            f"D29",
            f"{bunkering_quantity_85_percent_fo} m3",
            border_not_bold_align_right,
        )
        sheet.write(
            f"D30",
            f"{bunkering_quantity_80_percent_fo} m3",
            border_not_bold_align_right,
        )
        sheet.write(f"D31", f"{reasonable_quantity_fo} m3", border_not_bold_align_right)
        sheet.write(f"D32", "MT", border_not_bold_align_right)

        sheet.write(
            f"E28",
            f"{bunkering_quantity_90_percent_do} m3",
            border_not_bold_align_right,
        )
        sheet.write(
            f"E29",
            f"{bunkering_quantity_85_percent_do} m3",
            border_not_bold_align_right,
        )
        sheet.write(
            f"E30",
            f"{bunkering_quantity_80_percent_do} m3",
            border_not_bold_align_right,
        )
        sheet.write(f"E31", f"{reasonable_quantity_do} m3", border_not_bold_align_right)
        sheet.write(f"E32", "MT", border_not_bold_align_right)

        name_19 = "Bunker Request (SL Nhiên liệu yêu cầu)"
        sheet.merge_range(f"A34:E34", "4.Requisition (Yêu cầu)", not_bold_not_center)
        sheet.merge_range(f"B35:C35", name_19, border_not_center)
        sheet.merge_range(
            f"B36:C36", "Filling Percentage ( % của két)", border_not_center
        )

        sheet.write(f"C38", "CHIEF ENGINEER\nMÁY TRƯỞNG", bold)
        sheet.write(f"E38", "ENGINEER in CHARGE\nSỹ quan máy phụ trách", bold)
        # value
        bunker_request_mt_fo = record_id.bunker_request_mt_fo
        filling_percentage_fo = record_id.filling_percentage_fo

        bunker_request_mt_do = record_id.bunker_request_mt_do
        filling_percentage_do = record_id.filling_percentage_do

        sheet.write(f"D35", f"{bunker_request_mt_fo} MT", border_not_bold_align_right)
        sheet.write(f"D36", f"{filling_percentage_fo} %", border_not_bold_align_right)

        sheet.write(f"E35", f"{bunker_request_mt_do} MT", border_not_bold_align_right)
        sheet.write(f"E36", f"{filling_percentage_do} %", border_not_bold_align_right)

    def create_footer(self, workbook, sheet, taken_rows):
        top = workbook.add_format(self.get_normal_format(top=1))
        not_bold = workbook.add_format(self.get_normal_format(bold=False))

        footer_row = taken_rows + 1
        sheet.merge_range(f"A{footer_row}:G{footer_row}", "", top)

        footer_row_2 = taken_rows + 2
        sheet.write(f"B{footer_row_2}", "CHIEF ENGINEER\nMÁY TRƯỞNG", not_bold)
        sheet.write(f"G{footer_row_2}", "THIRD ENGINEER\nMÁY BA", not_bold)
