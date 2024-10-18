from odoo import models
import copy


class JobReportXlsx(models.AbstractModel):
    _name = "report.safety_legislation.legis_job_report_report"
    _inherit = ["report.report_xlsx.abstract"]

    def generate_xlsx_report(self, workbook, data, technical_incident_ids):
        sheet = workbook.add_worksheet("Báo cáo công việc")

        incident_job_ids = technical_incident_ids.mapped(
            lambda e: e.technical_incident_job_ids
        )
        records_len = 0
        for incident_job_id in incident_job_ids:
            materials_len = len(incident_job_id.material_assignment_ids)
            records_len = (
                records_len + materials_len if materials_len else records_len + 1
            )
        ship_name = self._get_company_name(technical_incident_ids)

        self.create_header(workbook, sheet, ship_name)
        self.create_body(workbook, sheet, incident_job_ids)
        self.create_footer(workbook, sheet, records_len)
        workbook.close()

    def _get_company_name(self, technical_incident_ids):
        for technical_incident_id in technical_incident_ids:
            if technical_incident_id.company_id:
                return technical_incident_id.company_id.name

    def create_body(self, workbook, sheet, incident_job_ids, taken_row=4):
        normal_format = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align=False)
        )
        format_2 = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align="center")
        )

        row_number = taken_row

        for record in incident_job_ids:
            row_number = row_number + 1

            finished_at = (
                record.finished_at.strftime("%d-%m-%Y") if record.finished_at else ""
            )
            name = record.name
            bs = "S"

            sheet.write(f"A{row_number}", finished_at, format_2)
            sheet.write(f"B{row_number}", name, normal_format)
            sheet.write(f"C{row_number}", bs, format_2)

            for i, assignment_id in enumerate(record.material_assignment_ids):
                if assignment_id:
                    row_number = row_number + i
                    material_name = assignment_id.material_entity_id.material_id.name
                    quantity = assignment_id.quantity
                    unit = assignment_id.unit
                    second_material = i > 0

                    if second_material:
                        sheet.write(f"A{row_number}", "", normal_format)
                        sheet.write(f"B{row_number}", "", normal_format)
                        sheet.write(f"C{row_number}", "", normal_format)
                    sheet.write(f"D{row_number}", material_name, normal_format)
                    sheet.write(f"E{row_number}", quantity, format_2)
                    sheet.write(f"F{row_number}", unit, format_2)
                else:
                    sheet.write(f"D{row_number}", "", format_2)
                    sheet.write(f"E{row_number}", "", format_2)
                    sheet.write(f"F{row_number}", "", format_2)

    def create_header(self, workbook, sheet, ship_name):
        normal_format = workbook.add_format(self.get_normal_format())
        format_2 = workbook.add_format(self.get_normal_format(bottom=1))
        format_3 = workbook.add_format(self.get_normal_format(align=False))
        format_4 = workbook.add_format(self.get_normal_format(border=1))
        format_5 = workbook.add_format(
            self.get_normal_format(align=False, bottom=1, right=1)
        )

        # set height column
        height = 25
        sheet.set_row(2, height)

        height = 40
        sheet.set_row(3, height)

        # set width column
        a_width = 15
        b_width = 60
        c_width = 15
        d_width = 60
        e_width = 15
        f_width = 15
        sheet.set_column("A:A", a_width)
        sheet.set_column("B:B", b_width)
        sheet.set_column("C:C", c_width)
        sheet.set_column("D:D", d_width)
        sheet.set_column("E:E", e_width)
        sheet.set_column("F:F", f_width)

        name_1 = "CÔNG TY CỔ PHẦN HÀNG HẢI VSICO\nVSICO SHIPPING JOINT STOCK COMPANY"
        sheet.merge_range(f"A1:E1", name_1, normal_format)

        name_2 = "YÊU CẦU VẬT TƯ\nORDER SPARE PART"
        sheet.merge_range(f"A2:E2", name_2, format_2)

        name_3 = f"Control No: VSICO-10-06\nIssued Date: 01/12/2022\nRevision No: 00\nRevised Date\nPage:     of"
        sheet.merge_range(f"F1:F2", name_3, format_5)

        # company name
        sheet.merge_range(f"A3:B3", f"Ship's Name(Tên tàu): {ship_name}", format_3)

        # date
        sheet.write(f"A4", "Date\nNgày", format_4)

        # others
        sheet.write(f"B4", "Description of work done\nMô tả công việc", format_4)
        sheet.write(f"C4", "B/S", format_4)
        name_4 = "Spare parts/Materials used A\nPhụ tùng/Vật tư sử dụng (cho phép chọn nhiều)"
        sheet.write(f"D4", name_4, format_4)
        sheet.write(f"E4", "Số lượng", format_4)
        sheet.write(f"F4", "Đơn vị", format_4)

    def create_footer(self, workbook, sheet, record_len=0, taken_row=4):
        format_1 = workbook.add_format(self.get_normal_format(top=1))
        format_2 = workbook.add_format(self.get_normal_format(bold=False))

        footer_row = taken_row + record_len + 1
        footer_row_2 = taken_row + record_len + 2
        footer_row_3 = taken_row + record_len + 4
        sheet.merge_range(f"A{footer_row}:F{footer_row}", "", format_1)

        name_1 = 'Note: in B/S column: "B"-maintenance work, "S"- other works (Ghi chú: Cột B/S: ghi "B"khi là công việc bảo dưỡng định kỳ, ghi "S" khi là công việc đột xuất)'
        sheet.merge_range(f"A{footer_row_2}:F{footer_row_2}", name_1, format_2)
        sheet.write(f"B{footer_row_3}", "CAPTAIN\nThuyền trưởng", format_2)
        name_2 = "CHIEF OFFICER/CHIEF ENGINEER\nThuyền phó nhất/Máy trưởng"
        sheet.write(f"D{footer_row_3}", name_2, format_2)

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
