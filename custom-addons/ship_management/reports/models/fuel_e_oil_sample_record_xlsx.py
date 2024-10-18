from odoo import models
import copy
from ...models import CONST


class FuelOilSampleRecordXlsx(models.AbstractModel):
    _name = "report.ship_fuel_oil_sample_record_xlsx"
    _inherit = ["report.utilities"]

    def _generate_xlsx_report(self, workbook, data, record_ids):
        for record_id in record_ids:
            sheet = workbook.add_worksheet("BẢN GHI MẪU NHIÊN LIỆU")
            sample_record_ids = record_id.fuel_oil_sample_record_ids
            sample_len = len(sample_record_ids)
            taken_rows_for_HFO = 10
            taken_rows_for_MDO = 12 + sample_len
            taken_rows = taken_rows_for_MDO + sample_len
            self.create_header(workbook, sheet, taken_rows_for_MDO, record_id)
            self.create_body(
                workbook,
                sheet,
                sample_record_ids,
                taken_rows_for_HFO,
                taken_rows_for_MDO,
            )
            self.create_footer(workbook, sheet, taken_rows)

        workbook.close()

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

    def create_header(self, workbook, sheet, taken_rows_for_MDO, record_id):
        border_not_center = workbook.add_format(
            self.get_normal_format(border=1, align=False)
        )
        not_bold = workbook.add_format(
            self.get_normal_format(bold=False, align="center")
        )
        border_bold = workbook.add_format(self.get_normal_format(border=1))
        border_not_bold = workbook.add_format(
            self.get_normal_format(border=1, bold=False)
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
        twenty_five_height = 25
        sixty_five_height = 70
        thirty_height = 30
        sheet.set_row(8, twenty_five_height)
        sheet.set_row(9, sixty_five_height)
        # sheet.set_row(10, thirty_height)

        # set width column
        a_width = 8
        b_width = 18
        c_width = 15
        d_width = 15
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

        sheet.merge_range(f"C1:F1", "CÔNG TY CỔ PHẦN HÀNG HẢI VSICO", bold)
        sheet.merge_range(
            f"C2:F2", "VSICO SHIPPING JOINT STOCK COMPANY", not_bold_italic
        )

        name_2 = "BẢN GHI MẪU NHIÊN LIỆU/ 2"
        sheet.merge_range(f"A3:G3", name_2, border_not_bold)

        name_3 = "Control No: VSICO-09-04\nIssued Date: 01/12/2022\nRevision No: 00\nRevised Date;\nPage:     of "

        sheet.merge_range(f"G1:G2", name_3, bottom_right_not_bold_not_center)

        company_name = record_id.company_id.name
        sheet.merge_range(
            f"A4:B4", f"MV (Tên tàu): {company_name}", not_bold_not_center
        )
        sheet.merge_range(f"D4:E4", "Time/Date (T/gian): . . .", not_bold_not_center)
        sheet.merge_range(f"F4:G4", "Voy. No. (Chuyến số): . . .", not_bold_not_center)

        sheet.merge_range(f"A5:D5", "Vessel name", not_bold)
        sheet.merge_range(f"A6:D6", "Tên tàu", not_bold_italic)

        sheet.merge_range(f"E5:G5", "Fuel oil sample locker location", not_bold)
        sheet.merge_range(f"E6:G6", "Vị trí lưu giữ mẫu nhiên liệu:", not_bold_italic)

        sheet.merge_range(f"A7:D7", "Vessel flag", not_bold)
        sheet.merge_range(f"A8:D8", "Quốc gia tàu mang cờ:", not_bold_italic)

        sheet.merge_range(f"E7:G7", "Fuel oil analysis company", not_bold)
        sheet.merge_range(
            f"E8:G8", "Công ty phân tích mẫu nhiên liệu:", not_bold_italic
        )

        # HFO
        name_7 = "Bunker delivery receipt number\nSố phiếu cung ứng nhiên liệu"
        name_8 = "Sulphur % declared\nHàm lượng % lưu huỳnh công bố"
        name_9 = "Fuel oil sample number\nSố mẫu nhiên liệu"
        name_10 = "Fuel seal number\nSố niêm phong nhiên liệu"
        name_11 = "Analysed sulphur content %\nHàm lượng % lưu huỳnh sau khi phân tích "

        sheet.merge_range(f"A9:G9", "HFO", border_not_center)
        sheet.write(f"A10", "Date of bunker\nNgày cung ứng nhiên liệu", border_bold)
        sheet.write(f"B10", "Location\nVị trí", border_bold)
        sheet.write(f"C10", name_7, border_bold)

        sheet.write(f"D10", name_8, border_bold)
        sheet.write(f"E10", name_9, border_bold)
        sheet.write(f"F10", name_10, border_bold)
        sheet.write(f"G10", name_11, border_bold)

        # MDO
        name_12 = "Date of bunker\nNgày cung ứng nhiên liệu"
        mdo_row = taken_rows_for_MDO - 1
        mdo_f_row = taken_rows_for_MDO

        sheet.set_row(mdo_row - 1, twenty_five_height)
        sheet.set_row(mdo_f_row - 1, sixty_five_height)

        sheet.merge_range(f"A{mdo_row}:G{mdo_row}", "MDO", border_not_center)
        sheet.write(f"A{mdo_f_row}", name_12, border_bold)
        sheet.write(f"B{mdo_f_row}", "Location\nVị trí", border_bold)
        sheet.write(f"C{mdo_f_row}", name_7, border_bold)

        sheet.write(f"D{mdo_f_row}", name_8, border_bold)
        sheet.write(f"E{mdo_f_row}", name_9, border_bold)
        sheet.write(f"F{mdo_f_row}", name_10, border_bold)
        sheet.write(f"G{mdo_f_row}", name_11, border_bold)

    def create_footer(self, workbook, sheet, taken_rows):
        normal_format = workbook.add_format(self.get_normal_format(top=1))
        format_2 = workbook.add_format(self.get_normal_format(bold=False))

        footer_row = taken_rows + 1
        sheet.merge_range(f"A{footer_row}:G{footer_row}", "", normal_format)

        footer_row_2 = taken_rows + 2
        sheet.write(f"B{footer_row_2}", "CHIEF ENGINEER\nMÁY TRƯỞNG", format_2)
        sheet.write(f"G{footer_row_2}", "THIRD ENGINEER\nMÁY BA", format_2)


class FuelEOilSampleRecordXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_fuel_e_oil_sample_record_xlsx"
    _inherit = [
        "report.report_xlsx.abstract",
        "report.ship_fuel_oil_sample_record_xlsx",
    ]

    def generate_xlsx_report(self, workbook, data, record_ids):
        self._generate_xlsx_report(workbook, data, record_ids)


class FuelIOilSampleRecordXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_fuel_i_oil_sample_record_xlsx"
    _inherit = [
        "report.report_xlsx.abstract",
        "report.ship_fuel_oil_sample_record_xlsx",
    ]

    def generate_xlsx_report(self, workbook, data, record_ids):
        self._generate_xlsx_report(workbook, data, record_ids)
