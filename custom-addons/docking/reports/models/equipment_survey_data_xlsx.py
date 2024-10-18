from odoo import models
import copy


class EquipmentSurveyDataXlsx(models.AbstractModel):
    _name = "report.docking.docking_equipment_survey_data_xlsx_report"
    _inherit = ["report.report_xlsx.abstract"]

    def generate_xlsx_report(self, workbook, data, surveys):
        sheet = workbook.add_worksheet("Khảo sát thiết bị")

        reports = surveys.mapped(lambda e: e.maintenance_scope_report_ids)

        job_quotes = reports.mapped(lambda e: e.job_quote_ids)

        self.create_header(workbook, sheet)
        self.create_body(workbook, sheet, job_quotes)
        self.create_footer(workbook, sheet, len(job_quotes))
        workbook.close()

    def create_body(self, workbook, sheet, job_quotes, taken_row=2):
        normal_format = workbook.add_format(
            self.get_normal_format(right=1, bold=False, align=False)
        )

        for i, record in enumerate(job_quotes):
            stt = i + 1
            row_number = taken_row + stt

            report = record.maintenance_scope_report_id
            job_name = record.job_id.name
            survey = report.equipment_survey_data_id
            metadata = survey.equipment_survey_metadata_id

            equipment_survey_group = metadata.equipment_survey_group_id.name
            maintenance_scope = report.maintenance_scope_id.name

            length = record.length
            width = record.width
            height = record.height
            weight = record.weight
            unit = record.unit
            quantity = record.quantity
            note = record.note
            is_for_crew = record.is_for_crew
            job_supplier_quote_id = record.job_supplier_quote_id
            supplier_id = job_supplier_quote_id.supplier_id
            construction_worker = "Thuyền viên" if is_for_crew else supplier_id.name

            sheet.write(f"A{row_number}", stt, normal_format)
            sheet.write(f"B{row_number}", equipment_survey_group, normal_format)
            sheet.write(f"C{row_number}", maintenance_scope, normal_format)
            sheet.write(f"D{row_number}", job_name, normal_format)
            sheet.write(f"E{row_number}", "", normal_format)
            sheet.write(f"F{row_number}", "", normal_format)
            sheet.write(f"G{row_number}", "", normal_format)
            sheet.write(f"H{row_number}", "", normal_format)
            sheet.write(f"I{row_number}", "", normal_format)
            sheet.write(f"J{row_number}", length, normal_format)
            sheet.write(f"K{row_number}", width, normal_format)
            sheet.write(f"L{row_number}", height, normal_format)
            sheet.write(f"M{row_number}", weight, normal_format)
            sheet.write(f"N{row_number}", unit, normal_format)
            sheet.write(f"O{row_number}", quantity, normal_format)
            sheet.write(f"P{row_number}", construction_worker, normal_format)
            sheet.write(f"Q{row_number}", note, normal_format)

    def create_header(self, workbook, sheet):
        normal_format = workbook.add_format(self.get_normal_format(border=1))

        green_bg_obj = self.get_normal_format(bg_color="#92d050", border=1)
        green_bg = workbook.add_format(green_bg_obj)

        yellow_bg_obj = self.get_normal_format(bg_color="yellow", border=1)
        yellow_bg = workbook.add_format(yellow_bg_obj)

        # set height column
        height = 25
        sheet.set_row(1, height)

        # set width column
        b_width = 25
        c_width = 25
        d_width = 25
        e_width = 25
        f_width = 25
        g_width = 25
        h_width = 12
        i_width = 12
        j_width = 12
        k_width = 12
        l_width = 12
        m_width = 12
        n_width = 12
        o_width = 12
        p_width = 25
        q_width = 12
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
        sheet.set_column("N:N", n_width)
        sheet.set_column("O:O", o_width)
        sheet.set_column("P:P", p_width)
        sheet.set_column("Q:Q", q_width)

        # stt
        sheet.merge_range(f"A1:A2", "STT", normal_format)
        # maintenance scope
        sheet.merge_range(f"B1:F1", "HẠNG MỤC CÔNG VIỆC", normal_format)
        sheet.write(f"B2", "Nhóm hạng mục/thiết bị", green_bg)
        sheet.write(f"C2", "Hạng mục", green_bg)
        sheet.write(f"D2", "Mô tả công việc", green_bg)
        sheet.write(f"E2", "Hạng mục đăng kiểm", green_bg)
        sheet.write(f"F2", "Hạn đăng kiểm", green_bg)

        # specifications
        sheet.merge_range(f"G1:I1", "MÔ TẢ THÔNG SỐ KỸ THUẬT", normal_format)
        sheet.write(f"G2", "Tiêu chuẩn/vật liệu", yellow_bg)
        sheet.write(f"H2", "Tên gọi", yellow_bg)
        sheet.write(f"I2", "Kỹ hiệu KT", yellow_bg)

        # sizes
        sheet.merge_range(f"J1:L1", "KÍCH THƯỚC", normal_format)
        sheet.write(f"J2", "Dài", yellow_bg)
        sheet.write(f"K2", "Rộng", yellow_bg)
        sheet.write(f"L2", "Cao", yellow_bg)

        # others
        sheet.merge_range(f"M1:M2", "Khối lượng", normal_format)
        sheet.merge_range(f"N1:N2", "DVT", normal_format)
        sheet.merge_range(f"O1:O2", "Số lượng", normal_format)
        sheet.merge_range(f"P1:P2", "Đơn vị thi công", normal_format)
        sheet.merge_range(f"Q1:Q2", "Ghi chú", normal_format)

    def create_footer(self, workbook, sheet, survey_len=0, taken_row=2):
        normal_format = workbook.add_format(self.get_normal_format(top=1))

        footer_row = taken_row + survey_len + 1
        sheet.merge_range(f"A{footer_row}:Q{footer_row}", "", normal_format)

    def get_normal_format(
        self,
        bold=True,
        align="center",
        bg_color=False,
        border=False,
        right=False,
        top=False,
    ):
        base_format = {
            "font_name": "Arial",
            "font_size": 10,
            "valign": "vcenter",
            "bold": bold,
        }

        if bg_color:
            base_format["bg_color"] = bg_color

        if border:
            base_format["border"] = border

        if right:
            base_format["right"] = right

        if top:
            base_format["top"] = top

        if align != False:
            base_format["align"] = align

        return base_format
