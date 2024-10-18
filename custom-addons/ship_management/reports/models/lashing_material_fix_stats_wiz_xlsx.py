from odoo import models
import copy
from ...models import CONST


class LashingMaterialFixStatsWizXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_lashing_material_fix_wiz_xlsx"
    _inherit = ["report.report_xlsx.abstract", "report.utilities"]

    def generate_xlsx_report(self, workbook, data, record_ids):
        sheet = workbook.add_worksheet("Báo cáo dụng cụ chằng buộc")
        start_date = data["start_date"]
        end_date = data["end_date"]
        material_ids = data["material_ids"]
        company_name = data["company_name"]

        self.create_header(workbook, sheet, company_name, start_date, end_date)
        self.create_body(workbook, sheet, material_ids, start_date, end_date)
        self.create_footer(workbook, sheet, len(material_ids))
        workbook.close()

    def _get_repaired_quantity(self, material_id, start_date, end_date):
        result = self.env["ship.lashing.material.fix.stats"].read_group(
            [
                ("material_id", "=", material_id),
                ("update_date", ">=", start_date),
                ("update_date", "<=", end_date),
            ],
            ["repaired:sum"],
            ["material_id"],
        )
        if result:
            history = result[0]
            return history.get("repaired", 0)
        else:
            return 0

    def _get_not_repaired_quantity(self, material_id, start_date, end_date):
        result = self.env["ship.lashing.material.fix.stats"].read_group(
            [
                ("material_id", "=", material_id),
                ("update_date", ">=", start_date),
                ("update_date", "<=", end_date),
            ],
            ["not_repaired:sum"],
            ["material_id"],
        )
        if result:
            history = result[0]
            return history.get("not_repaired", 0)
        else:
            return 0

    def _get_repairable_quantity(self, material_id, start_date, end_date):
        result = self.env["ship.lashing.material.fix.stats"].read_group(
            [
                ("material_id", "=", material_id),
                ("update_date", ">=", start_date),
                ("update_date", "<=", end_date),
            ],
            ["repairable:sum"],
            ["material_id"],
        )
        if result:
            history = result[0]
            return history.get("repairable", 0)
        else:
            return 0

    def _get_unrepairable_quantity(self, material_id, start_date, end_date):
        result = self.env["ship.lashing.material.fix.stats"].read_group(
            [
                ("material_id", "=", material_id),
                ("update_date", ">=", start_date),
                ("update_date", "<=", end_date),
            ],
            ["unrepairable:sum"],
            ["material_id"],
        )
        if result:
            history = result[0]
            return history.get("unrepairable", 0)
        else:
            return 0

    def _get_receiving_in_month(self, material_id, start_date, end_date):
        result = self.env["ship.material.entity"].read_group(
            [
                ("material_id", "=", material_id),
                ("create_date", ">=", start_date),
                ("create_date", "<=", end_date),
            ],
            ["quantity:sum"],
            ["material_id"],
        )
        if result:
            history = result[0]
            return history.get("quantity", 0)
        else:
            return 0

    def _get_total_stock(self, material_id, start_date, end_date):
        repaired = self._get_repaired_quantity(material_id, start_date, end_date)
        notrepaired = self._get_not_repaired_quantity(material_id, start_date, end_date)
        receiving = self._get_receiving_in_month(material_id, start_date, end_date)

        return repaired + notrepaired + receiving

    def _get_short_of_minimum(self, material_id, start_date, end_date):
        material = self.env["ship.material"].browse(material_id)

        repaired = self._get_repaired_quantity(material_id, start_date, end_date)
        notrepaired = self._get_not_repaired_quantity(material_id, start_date, end_date)
        min_quantity = material.min_quantity

        return min_quantity - repaired - notrepaired

    def create_body(
        self, workbook, sheet, material_ids, start_date, end_date, taken_row=8
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

            repaired = self._get_repaired_quantity(material_id, start_date, end_date)
            notrepaired = self._get_not_repaired_quantity(
                material_id, start_date, end_date
            )
            repairable = self._get_repairable_quantity(
                material_id, start_date, end_date
            )
            unrepairable = self._get_unrepairable_quantity(
                material_id, start_date, end_date
            )
            receiving = self._get_receiving_in_month(material_id, start_date, end_date)
            total_stock = self._get_total_stock(material_id, start_date, end_date)
            short_of_minimum = self._get_short_of_minimum(
                material_id, start_date, end_date
            )

            sheet.write(f"A{row_number}", stt, format_2)
            sheet.write(f"B{row_number}", material.name or "", normal_format)
            sheet.write(f"C{row_number}", material.spare_part_no or "", format_2)
            sheet.write(f"D{row_number}", material.min_quantity or "", format_2)
            sheet.write(f"E{row_number}", material.note or "", normal_format)
            sheet.write(f"F{row_number}", repaired, format_2)
            sheet.write(f"G{row_number}", notrepaired, format_2)
            sheet.write(f"H{row_number}", repairable, format_2)
            sheet.write(f"I{row_number}", unrepairable, format_2)
            sheet.write(f"J{row_number}", receiving, format_2)
            sheet.write(f"K{row_number}", total_stock, format_2)
            sheet.write(f"L{row_number}", short_of_minimum, format_2)
            sheet.write(f"M{row_number}", "", format_2)

    def create_header(self, workbook, sheet, company_name, start_date, end_date):
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
        a_width = 10
        b_width = 35
        c_width = 20
        d_width = 13
        e_width = 13
        f_width = 13
        g_width = 13
        h_width = 13
        i_width = 13
        j_width = 13
        k_width = 13
        l_width = 13
        m_width = 10
        # sheet.set_column("A:A", a_width)
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

        sheet.merge_range(f"A3:L3", "BÁO CÁO DỤNG CỤ CHẰNG BUỘC CONTAINER", bold)
        sheet.merge_range(f"A4:L4", "LASHING GEAR RECORD", bottom_not_bold_italic)

        name_3 = "Control No: VSICO-09-08\nIssued Date: 01/12/2022\nRevision No: 00\nRevised Date;\nPage:     of "
        sheet.merge_range(f"M1:M4", name_3, bottom_right_not_bold_not_center)

        name_4 = f"Ship's Name (Tên tàu): {company_name} Port (Cảng): . . ."
        sheet.merge_range(f"A5:B5", name_4, not_bold_not_center)
        sheet.merge_range(f"D5:F5", "Voyage No.(Chuyến):. . .", not_bold_not_center)
        sheet.merge_range(f"J5:L5", f"Date (Ngày): {end_date}", not_bold_not_center)

        # No
        sheet.merge_range(f"A6:A8", "No\nStt.", border_bold)

        # others
        name_5 = "TYPE OF FITTING GEAR\nDụng cụ chằng buộc"
        sheet.merge_range(f"B6:B8", name_5, border_bold)
        sheet.merge_range(f"C6:C8", "PART NO. / MARK\nKý hiệu", border_bold)

        sheet.write(f"D6", "Minimum Quantity for FullLoad\nSL.tối thiểu", border_bold)
        sheet.merge_range(f"D7:D8", "1", border_bold)
        sheet.write(f"E6", "Standard Out-fitting\nTrang bị chuẩn", border_bold)
        sheet.merge_range(f"E7:E8", "2", border_bold)
        sheet.merge_range(f"F6:G6", "In Order\nCòn sử dụng được", border_bold)
        sheet.write(f"F7", "3a", border_bold)
        sheet.write(f"F8", "Đã sửa chữa", border_bold)
        sheet.write(f"G7", "3b", border_bold)
        sheet.write(f"G8", "Chưa sửa chữa", border_bold)

        sheet.merge_range(f"H6:I6", "Out of Order\nBị hỏng", border_bold)
        sheet.write(f"H7", "4a", border_bold)
        sheet.write(f"H8", "Có thể sửa chữa", border_bold)
        sheet.write(f"I7", "4b", border_bold)
        sheet.merge_range(f"I8:J8", "Không thể sửa chữa\n(Thanh lý)", border_bold)

        sheet.write(f"J6", "Supply\nCấp bổ sung", border_bold)
        sheet.write(f"J7", "5", border_bold)
        # sheet.write(f"J8", "", border_bold)

        sheet.write(f"K6", "Total Stock\nToàn bộ có trên tàu", border_bold)
        sheet.merge_range(f"K7:K8", "6=(3a+3b+5)", border_bold)

        sheet.write(f"L6", "Short of Minimum Qtty\nSL. Thiếu bổ sung", border_bold)
        sheet.merge_range(f"L7:L8", "7=(1-3a-3b)", border_bold)

        sheet.write(f"M6", "ORDER\nYêu cầu", border_bold)
        sheet.merge_range(f"M7:M8", "8", border_bold)

    def create_footer(self, workbook, sheet, record_len=0, taken_row=8):
        normal_format = workbook.add_format(self.get_normal_format(top=1))
        format_2 = workbook.add_format(self.get_normal_format(bold=False))

        footer_row = taken_row + record_len + 1
        sheet.merge_range(f"A{footer_row}:M{footer_row}", "", normal_format)

        footer_row_2 = footer_row + 2
        sheet.write(f"B{footer_row_2}", "BOSUN\nThủy thủ trưởng", format_2)
        sheet.write(f"C{footer_row_2}", "CHIEF OFFICER\nĐại phó", format_2)
        sheet.write(f"F{footer_row_2}", "CAPTAIN\nThuyền trưởng", format_2)
