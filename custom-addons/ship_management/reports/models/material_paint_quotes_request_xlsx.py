from odoo import models
import copy
from odoo.exceptions import ValidationError


class MaterialPaintQuotesRequestXlsx(models.AbstractModel):
    _name = "report.ship_management.ship_material_paint_quotes_request_xlsx"
    _inherit = ["report.report_xlsx.abstract"]

    def generate_xlsx_report(self, workbook, data, request_ids):

        supplier_ids, material_quote_ids = self.get_supplier_ids_from_requests(
            request_ids
        )

        for supplier_id in supplier_ids:
            supplier = self.env["ship.supplier"].browse(supplier_id)
            sheet = workbook.add_worksheet(f"Form order vật tư của {supplier.name}")
            self.write_sheet(workbook, sheet, material_quote_ids, supplier_id)

        workbook.close()

    def write_sheet(self, workbook, sheet, material_quote_ids, supplier_id):
        material_quote_ids = material_quote_ids.filtered(
            lambda e: e.material_supplier_quote_id.supplier_id.id == supplier_id
        )
        material_groups = list(set(material_quote_ids.mapped("material_group")))
        taken_rows = len(material_quote_ids) + len(material_groups) + 2

        self.create_header(workbook, sheet)
        self.create_body(workbook, sheet, material_quote_ids, material_groups)
        self.create_footer(workbook, sheet, taken_rows)

    def create_body(
        self, workbook, sheet, material_quote_ids, material_groups, taken_rows=2
    ):
        format_1 = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align=False)
        )
        format_2 = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align="center")
        )
        format_3 = workbook.add_format(self.get_normal_format(right=1, align="center"))

        previous_quotes_len = 0
        for y, material_group in enumerate(material_groups):
            new_material_quote_ids = material_quote_ids.filtered(
                lambda e: e.material_group == material_group
            )
            y_is_one = y + 1
            row_number_for_group = taken_rows + y_is_one + previous_quotes_len

            sheet.write(f"A{row_number_for_group}", "", format_2)
            sheet.write(f"B{row_number_for_group}", "", format_2)
            sheet.write(
                f"C{row_number_for_group}", material_group.upper().strip(), format_3
            )
            sheet.write(f"D{row_number_for_group}", "", format_2)
            sheet.write(f"E{row_number_for_group}", "", format_2)
            sheet.write(f"F{row_number_for_group}", "", format_2)
            sheet.write(f"G{row_number_for_group}", "", format_2)
            sheet.write(f"H{row_number_for_group}", "", format_2)

            for i, record in enumerate(new_material_quote_ids):
                i_is_one = i + 1
                stt = i_is_one + previous_quotes_len
                row_number = row_number_for_group + i_is_one

                ref = record.ref
                material_name = record.material_id.name
                unit = record.unit
                quantity = record.quantity
                unit_price = record.unit_price
                total_price = record.total_price
                note = record.note if record.note else ""

                sheet.write(f"A{row_number}", stt, format_2)
                sheet.write(f"B{row_number}", ref, format_2)
                sheet.write(f"C{row_number}", material_name, format_1)
                sheet.write(f"D{row_number}", unit, format_2)
                sheet.write(f"E{row_number}", quantity, format_2)
                sheet.write(f"F{row_number}", unit_price, format_2)
                sheet.write(f"G{row_number}", total_price, format_2)
                sheet.write(f"H{row_number}", note, format_1)

            quotes_len = len(material_quote_ids)
            groups_len = len(material_groups)
            total_row = taken_rows + quotes_len + groups_len + 1
            total_prices = sum(material_quote_ids.mapped("total_price"))
            sheet.write(f"A{total_row}", "", format_1)
            sheet.write(f"B{total_row}", "", format_1)
            sheet.write(f"C{total_row}", "", format_1)
            sheet.write(f"D{total_row}", "", format_1)
            sheet.write(f"E{total_row}", "", format_1)
            sheet.write(f"F{total_row}", "Tổng cộng", format_3)
            sheet.write(f"G{total_row}", total_prices, format_1)
            sheet.write(f"H{total_row}", "", format_1)

            previous_quotes_len = previous_quotes_len + len(new_material_quote_ids)

    def create_header(self, workbook, sheet):
        format_1 = workbook.add_format(self.get_normal_format(border=1))
        format_2 = workbook.add_format(
            self.get_normal_format(font_size=16, font_name="Times New Roman")
        )

        # set width column
        b_width = 25
        c_width = 70
        d_width = 20
        e_width = 20
        f_width = 20
        g_width = 20
        h_width = 20
        sheet.set_column("B:B", b_width)
        sheet.set_column("C:C", c_width)
        sheet.set_column("D:D", d_width)
        sheet.set_column("E:E", e_width)
        sheet.set_column("F:F", f_width)
        sheet.set_column("G:G", g_width)
        sheet.set_column("H:H", h_width)

        name = "DANH MỤC VẬT TƯ ĐƯỢC DUYỆT CUNG CẤP"
        sheet.merge_range(f"A1:H1", name, format_2)

        # stt
        sheet.write(f"A2", "STT", format_1)

        # others
        sheet.write(f"B2", "MÃ HÀNG", format_1)
        sheet.write(f"C2", "NỘI DUNG", format_1)

        sheet.write(f"D2", "ĐVT", format_1)
        sheet.write(f"E2", "S/LG", format_1)
        sheet.write(f"F2", "ĐƠN GIÁ", format_1)

        sheet.write(f"G2", "THÀNH TIỀN", format_1)
        sheet.write(f"H2", "GHI CHÚ", format_1)

    def create_footer(self, workbook, sheet, taken_rows=0):
        normal_format = workbook.add_format(self.get_normal_format(top=1))

        total_price_row = 1
        footer_row = taken_rows + total_price_row + 1
        sheet.merge_range(f"A{footer_row}:H{footer_row}", "", normal_format)

    def get_normal_format(
        self,
        bold=True,
        align="center",
        font_name="Arial",
        font_size=False,
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

        if font_size != False:
            base_format["font_size"] = font_size

        return base_format

    def get_supplier_ids_from_requests(self, request_ids):
        material_quote_ids = request_ids.mapped("material_quote_ids").filtered(
            lambda e: e._is_quote_approved()
        )
        spare_part_quote_ids = request_ids.mapped("spare_part_quote_ids").filtered(
            lambda e: e._is_quote_approved()
        )

        supplier_ids_from_material_quotes = [
            material_quote_id.material_supplier_quote_id.supplier_id.id
            for material_quote_id in material_quote_ids
            if material_quote_id.material_supplier_quote_id.supplier_id
        ]
        supplier_ids_from_spare_part_quotes = [
            spare_part_quote_id.material_supplier_quote_id.supplier_id.id
            for spare_part_quote_id in spare_part_quote_ids
            if spare_part_quote_id.material_supplier_quote_id.supplier_id
        ]

        supplier_ids = list(
            set(supplier_ids_from_material_quotes + supplier_ids_from_spare_part_quotes)
        )

        new_material_quote_ids = material_quote_ids + spare_part_quote_ids

        return (supplier_ids, new_material_quote_ids)
