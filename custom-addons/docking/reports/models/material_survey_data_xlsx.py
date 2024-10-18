from odoo import models
import copy


class MaterialSurveyDataXlsx(models.AbstractModel):
    _name = "report.docking.docking_material_survey_data_xlsx_report"
    _inherit = ["report.report_xlsx.abstract"]

    def generate_xlsx_report(self, workbook, data, surveys):
        sheet = workbook.add_worksheet("Khảo sát vật tư")

        material_quotes = surveys.mapped(lambda e: e.material_quote_ids)

        self.create_header(workbook, sheet)
        self.create_body(workbook, sheet, material_quotes)
        self.create_footer(workbook, sheet, len(material_quotes))
        workbook.close()

    def create_body(self, workbook, sheet, material_quotes, taken_row=6):
        normal_format = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align=False)
        )
        format_2 = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align="center")
        )

        for i, record in enumerate(material_quotes):
            stt = i + 1
            row_number = taken_row + stt

            survey = record.material_survey_data_id
            meta = survey.material_survey_metadata_id
            name = meta.name
            description = meta.description
            spare_part_no = meta.spare_part_no
            unit = meta.unit
            quantity = record.quantity
            note = record.note

            sheet.write(f"A{row_number}", stt, normal_format)
            sheet.write(f"B{row_number}", description, normal_format)
            sheet.write(f"C{row_number}", spare_part_no, normal_format)
            sheet.write(f"D{row_number}", name, normal_format)
            sheet.write(f"E{row_number}", unit, format_2)
            sheet.write(f"F{row_number}", "", normal_format)
            sheet.write(f"G{row_number}", quantity, format_2)
            sheet.write(f"H{row_number}", note, normal_format)

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
        f_width = 15
        g_width = 15
        h_width = 25
        sheet.set_column("B:B", b_width)
        sheet.set_column("C:C", c_width)
        sheet.set_column("D:D", d_width)
        sheet.set_column("E:E", e_width)
        sheet.set_column("F:F", f_width)
        sheet.set_column("G:G", g_width)
        sheet.set_column("H:H", h_width)

        name_1 = "CÔNG TY CỔ PHẦN HÀNG HẢI VSICO\nVSICO SHIPPING JOINT STOCK COMPANY"
        sheet.merge_range(f"A1:G1", name_1, normal_format)

        name_2 = "YÊU CẦU VẬT TƯ\nORDER SPARE PART"
        sheet.merge_range(f"A2:G2", name_2, format_2)

        name_3 = "Control No:\nIssued Date:\nRevision No:\nRevised Date:\nPage:     of"
        sheet.merge_range(f"H1:H2", name_3, format_3)

        # stt
        sheet.merge_range(f"A5:A6", "STT", format_4)

        # others
        sheet.merge_range(f"B5:B6", "Description/Engine type\nMô tả", format_4)
        name_4 = "Eng. No./ Drwg.No.\nSố máy/ Số bản vẽ"
        sheet.merge_range(f"C5:C6", name_4, format_4)
        name_5 = "Part no.;Page no./Item no.\nSố v.tư; Số trang/mục"
        sheet.merge_range(f"D5:D6", name_5, format_4)
        sheet.merge_range(f"E5:E6", "Unit\nĐơn vị", format_4)
        sheet.merge_range(f"F5:G5", "Qty. (S.lượng)", format_4)
        sheet.merge_range(f"F5:G5", "Qty. (S.lượng)", format_4)
        sheet.write(f"F6", "R.O.B", format_4)
        sheet.write(f"G6", "Req. dự kiến", format_4)
        sheet.merge_range(f"H5:H6", "Remarks (Ghi chú)", format_4)

    def create_footer(self, workbook, sheet, quote_len=0, taken_row=6):
        normal_format = workbook.add_format(self.get_normal_format(top=1))

        footer_row = taken_row + quote_len + 1
        sheet.merge_range(f"A{footer_row}:H{footer_row}", "", normal_format)

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
