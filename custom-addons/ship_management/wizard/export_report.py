# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ..models import CONST
from ...utilities.models import CONST as CONST_UTILITIES
from ..models.material import machinery, boong, tool
from odoo.exceptions import ValidationError


class ExportReportWiz(models.TransientModel):
    _name = "ship.export.report.wiz"
    _description = "Export report wiz records"
    _inherit = ["utilities.notification"]

    report_type = fields.Selection(
        CONST.REPORT_TYPE,
        string="Report type",
        default=CONST.PAINT_HISTORY,
        required=True,
        tracking=True,
    )

    start_date = fields.Date("Start date")
    end_date = fields.Date("end date")
    rendered_html_medicine = fields.Html("Rendered html medicine")

    # relations
    paint_history_ids = fields.Many2many("ship.paint.history", string="Paint history")
    material_ids = fields.Many2many("ship.material", string="Material")
    material_group_id = fields.Many2one(
        "ship.material.group", string="Material Group", tracking=True
    )

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.onchange("report_type", "start_date", "end_date", "material_group_id")
    def _get_page(self):
        if self._is_paint_history_type():
            self._get_paint_history_ids()
        elif self._is_essential_material_type():
            if self.start_date and self.end_date:
                self._get_essential_material_ids()
        elif self._is_material_history_type():
            if self.start_date and self.end_date:
                self._get_material_ids()

        if self._is_lashing_material_type():
            if self.start_date and self.end_date:
                self._get_material_ids_by_material_group_id()

        if self._is_medicine_report_type():
            if self.end_date:
                self._get_medicine_html()
        else:
            self.rendered_html_medicine = False

        if not self._is_lashing_material_type() and not self._is_medicine_report_type():
            self.material_group_id = False

    def _get_paint_history_ids(self):
        paint_history_ids = self.env["ship.paint.history"].search(
            [
                ("occured_at", ">=", self.start_date),
                ("occured_at", "<=", self.end_date),
            ]
        )

        self.paint_history_ids = paint_history_ids

    def _get_essential_material_ids(self):
        material_ids = self.env["ship.material"].search(
            [
                ("is_essential_material", "=", True),
            ]
        )

        self.material_ids = material_ids

    def _get_material_ids(self):
        material_ids = self.env["ship.material"].search([])
        self.material_ids = material_ids

    def _get_material_ids_by_material_group_id(self):
        material_ids = self.env["ship.material"].search(
            [
                ("material_group_id", "=", self.material_group_id.id),
            ]
        )
        self.material_ids = material_ids

    def generate_xlsx(self):
        self.ensure_one()
        if self._is_paint_history_type():
            return self._generate_paint_history_wiz_xlsx()
        elif self._is_essential_material_type():
            return self._generate_essential_material_wiz_xlsx()
        elif self._is_material_history_type():
            return self._generate_material_history_wiz_xlsx()
        elif self._is_lashing_material_type():
            return self._generate_lashing_material_wiz_xlsx()
        elif self._is_medicine_report_type():
            return self._generate_medicine_report()

    def _generate_medicine_report(self):
        return self.env.ref(
            "ship_management.ship_medicine_report_option"
        ).report_action(self)

    def _generate_paint_history_wiz_xlsx(self):
        paint_ids = self.paint_history_ids.mapped("paint_id").ids
        data = {
            "form_data": self.read()[0],
            "paint_ids": paint_ids,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "company_name": self.company_id.name,
        }

        return self.env.ref(
            "ship_management.ship_paint_history_wiz_xlsx_option"
        ).report_action(self, data=data)

    def _generate_essential_material_wiz_xlsx(self):
        material_ids = self.material_ids.ids
        data = {
            "form_data": self.read()[0],
            "material_ids": material_ids,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "company_name": self.company_id.name,
        }

        return self.env.ref(
            "ship_management.ship_essential_material_wiz_xlsx_option"
        ).report_action(self, data=data)

    def _generate_material_history_wiz_xlsx(self):
        machinery_material_ids = self.material_ids.filtered(
            lambda e: e.warehouse == machinery and e.material_type != CONST.SPARE_PART
        )
        machinery_spare_part_ids = self.material_ids.filtered(
            lambda e: e.warehouse == machinery and e.material_type == CONST.SPARE_PART
        )
        boong_material_ids = self.material_ids.filtered(lambda e: e.warehouse == boong)
        tool_material_ids = self.material_ids.filtered(lambda e: e.warehouse == tool)

        data = {
            "form_data": self.read()[0],
            "machinery_material_ids": machinery_material_ids.ids,
            "machinery_spare_part_ids": machinery_spare_part_ids.ids,
            "boong_material_ids": boong_material_ids.ids,
            "tool_material_ids": tool_material_ids.ids,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "company_name": self.company_id.name,
        }

        return self.env.ref(
            "ship_management.ship_material_history_wiz_xlsx_option"
        ).report_action(self, data=data)

    def _generate_lashing_material_wiz_xlsx(self):
        material_ids = self.material_ids

        data = {
            "form_data": self.read()[0],
            "material_ids": material_ids.ids,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "company_name": self.company_id.name,
        }

        return self.env.ref(
            "ship_management.ship_lashing_material_fix_wiz_xlsx_option"
        ).report_action(self, data=data)

    def _get_default_value_model(self):
        model_name = "utilities.default.value"
        default_value_model = self.env[model_name].search([])

        return default_value_model

    def _get_medicine_report_html(self):
        default_value_model = self._get_default_value_model()
        variable_name = CONST_UTILITIES.HTML_EXPORT_REPORT_WIZ_RENDERED_MEDICINE_CONTENT
        return default_value_model._get_default_value_by_variable_name(variable_name)

    def _get_medicine_html(self):
        placeholders = {
            "medicine": self._render_table_html_for_medicine(),
        }

        new_medicine_html = str(self._get_medicine_report_html()).format(**placeholders)

        self.rendered_html_medicine = new_medicine_html

    def _render_table_html_for_medicine(self):
        self.ensure_one()
        return f"""
            <table class="table table-bordered o_table">
                {self._render_thead_table_for_medicine()}
                {self._render_body_table_for_medicine()}
            </table>
        """

    def _render_thead_table_for_medicine(self):
        self.ensure_one()
        return f"""
            <thead>
                <tr class="active">
                    <th class="text-center">
                        {self._get_name_column("STT")}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Loại thuốc")}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Tên hoạt chất")}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Đơn vị tính")}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Nồng độ- Hàm lượng")}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Số lượng")}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("R.O.B")}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Hạn dùng")}
                    </th>
                </tr>
            </thead>
        """

    def _render_body_table_for_medicine(self):
        self.ensure_one()
        records = self.env["ship.material"].search(
            [
                ("material_group_id", "=", self.material_group_id.id),
            ]
        )

        tr = [
            self._get_tr_tag_for_medicine(i, record_id)
            for i, record_id in enumerate(records)
        ]

        return f"""
            <tbody>
                {"".join(tr)}
            </tbody>
        """

    def _get_tr_tag_for_medicine(self, i, record_id):
        stt = i + 1
        type_of_medicine = record_id.type_of_medicine or ""
        name = record_id.name
        unit = record_id.unit
        concentration = record_id.concentration or ""
        min_quantity = record_id.min_quantity
        rob = self._get_ROB_stock(record_id.id)
        expiration_date = record_id.expiration_date or ""

        return f"""
            <tr>
                <td class="text-center">{stt}</td>
                <td>{type_of_medicine}</td>
                <td>{name}</td>
                <td class="text-center">{unit}</td>
                <td>{concentration}</td>
                <td class="text-center">{min_quantity}</td>
                <td class="text-center">{rob}</td>
                <td>{expiration_date}</td>
            </tr>
        """

    def _get_name_column(self, name, font_weight="bold"):
        return f"""<div style="font-weight: {font_weight};">{name}</div>"""

    def _get_ROB_stock(self, material_id):
        result = self.env["ship.material.entity"].read_group(
            [
                ("material_id", "=", material_id),
                ("create_date", "<=", self.end_date),
                ("is_discarded", "=", False),
            ],
            ["quantity:sum"],
            ["material_id"],
        )
        if result:
            history = result[0]
            return history.get("quantity", 0)
        else:
            return 0

    def _is_paint_history_type(self):
        return self.report_type == CONST.PAINT_HISTORY

    def _is_material_history_type(self):
        return self.report_type == CONST.MATERIAL_HISTORY

    def _is_essential_material_type(self):
        return self.report_type == CONST.ESSENTIAL_MATERIAL

    def _is_lashing_material_type(self):
        return self.report_type == CONST.LASHING_MATERIAL

    def _is_medicine_report_type(self):
        return self.report_type == CONST.MEDICINE_REPORT
