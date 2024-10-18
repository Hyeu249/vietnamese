from odoo import api, fields, models, _
from . import CONST
from ...utilities.models import CONST as CONST_UTILITIES
from odoo.exceptions import ValidationError
from datetime import timedelta
from .common_utils import generate_token, format_field_date
import logging
import io
import os
import base64  # Add this import for base64 encoding
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import openpyxl
from datetime import datetime
import tempfile
from odoo.exceptions import UserError
from odoo import _, api, fields, models
from datetime import datetime, timedelta
from openpyxl.styles import Alignment


class FuelExternalReceiving(models.Model):
    _name = "ship.fuel.external.receiving"
    _description = "Kế hoạch nhận nhiên liệu quốc tế"
    _inherit = ["utilities.approval.status"]

    arrival_datetime = fields.Datetime(string="Datetime", default=fields.Datetime.now)
    bunkering_safety_checklist_html = fields.Html(
        string="Bunkering safety checklist html", readonly=True
    )
    voyage_number = fields.Char(string="Voyage Number", compute="_compute_voy")
    order_number = fields.Char(string="Order Number")
    trim = fields.Float(string="Trim (m)", help="Trim ")
    heel = fields.Float(string="Heel (Độ nghiêng)", default=0.0)

    hfo_received = fields.Float(
        string="H.F.O Nhận dự kiến (Tấn)",
        help="Received quantity of H.F.O",
        compute="_compute_fuel_received",
        digits=(10, 3),
    )
    hfo_received_final = fields.Float(
        string="H.F.O nhận cuối cùng (Tấn)",
        help="Final recevied quantity of H.F.O",
        compute="_compute_hfo_final_received",
        digits=(10, 3),
    )
    hfo_volume_received = fields.Float(
        string="H.F.O Volume Received (m3)",
        help="Volume received of H.F.O",
        compute="_compute_hfo_volume_received",
        digits=(10, 3),
    )
    hfo_density = fields.Float(
        string="Density H.F.O (Tỷ trọng 15°C)",
        help="Density of H.F.O at 15°C",
        default=1,
        digits=(10, 4),
    )

    do_received = fields.Float(
        string="D.O/G.O Nhận dự kiến(Tấn) ",
        help="Received quantity of D.O/G.O",
        compute="_compute_fuel_received",
        digits=(10, 3),
    )
    do_received_final = fields.Float(
        string="D.O/G.O nhận cuối cùng (Tấn)",
        help="Final recevied quantity of D.O",
        compute="_compute_do_final_received",
        digits=(10, 3),
    )
    do_volume_received = fields.Float(
        string="D.O/G.O Volume Received (m3)",
        help="Volume received of D.O/G.O",
        compute="_compute_do_volume_received",
        digits=(10, 3),
    )
    do_density = fields.Float(
        string="Density D.O (Tỷ trọng 15°C)",
        help="Density of D.O at 15°C",
        default=1,
        digits=(10, 4),
    )

    temperature = fields.Float(string="At/ (Tại) . . . 0C")

    ref = fields.Char(string="Code", default=lambda self: _("New"))

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    fuel_condition_ids = fields.One2many(
        "ship.fuel.external.oil.tank.condition",
        "fuel_external_receiving_id",
        string="Fuel Oil Tank Conditions",
    )

    fuel_check_ids = fields.One2many(
        "ship.fuel.external.check",
        "fuel_external_receiving_id",
        default=lambda self: self._get_default_fuel_checks(),
        string="Fuel Checks",
    )
    fuel_tank_measurement_ids = fields.One2many(
        "ship.fuel.external.tank.measurement",
        "fuel_external_receiving_id",
        string="Fuel Tank Measurements",
    )

    fuel_oil_sample_record_ids = fields.One2many(
        "ship.fuel.external.oil.sample.record",
        "fuel_external_receiving_id",
        string="Fuel Oil Sample Record",
    )

    bunker_ids = fields.One2many(
        "ship.fuel.external.bunker.barge",
        "fuel_external_receiving_id",
        string="Bunkers Transfer Bagre",
    )
    attachment_file = fields.Image(
        string="Attachment File",
        help="Upload attachment file here.",
        max_width=CONST.MAX_IMAGE_UPLOAD_WIDTH,
        max_height=CONST.MAX_IMAGE_UPLOAD_HEIGHT,
    )

    def _get_default_value_model(self):
        model_name = "utilities.default.value"
        default_value_model = self.env[model_name].search([])

        return default_value_model

    def _get_bunkering_safety_checklist_html(self):
        default_value_model = self._get_default_value_model()
        variable_name = (
            CONST_UTILITIES.HTML_SHIP_FUEL_EXTERNAL_RECEIVING_BUNKERING_SAFETY_CHECKLIST
        )
        return default_value_model._get_default_value_by_variable_name(variable_name)

    def rerender_bunkering_safety_checklist_html(self):
        self.ensure_one()
        placeholders = {
            "for_barge": self._render_table_html_for_barge(),
            "for_ship": self._render_table_html_for_ship(),
            "check_to_berthing": self._render_table_html_for_check_to_berthing(),
            "check_to_transfer": self._render_table_html_for_check_to_transfer(),
            "r_code": self._render_table_html_for_r_code(),
        }

        new_html_contract = str(self._get_bunkering_safety_checklist_html()).format(
            **placeholders
        )

        self.bunkering_safety_checklist_html = new_html_contract

    def _render_table_html_for_r_code(self):
        self.ensure_one()
        return f"""
            <table class="table table-bordered o_table">
                {self._render_thead_table_for_r_code()}
                {self._render_body_table_for_r_code()}
            </table>
        """

    def _render_thead_table_for_r_code(self):
        self.ensure_one()
        return f"""
            <thead>
                <tr class="active">
                    <th class="text-center">
                        {self._get_name_column("Stt")}
                        {self._get_name_column("No.", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Mục kiểm tra")}
                        {self._get_name_column("Checked items", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Ngày/Giờ kiểm tra")}
                        {self._get_name_column("Date(s)/Check time", font_weight=False)}
                    </th>
                </tr>
            </thead>
        """

    def _render_body_table_for_r_code(self):
        self.ensure_one()
        r_code = "R"
        records = self.fuel_check_ids.filtered(lambda e: e.code == r_code)
        tr = [
            self._get_tr_tag_for_r_code(i, record_id)
            for i, record_id in enumerate(records)
        ]

        return f"""
            <tbody>
                {"".join(tr)}
            </tbody>
        """

    def _get_tr_tag_for_r_code(self, i, record_id):
        stt = i + 1
        name = record_id.name

        return f"""
            <tr>
                <td class="text-center">{stt}</td>
                <td>{name}</td>
                <td><br/></td>
            </tr>
        """

    def _render_table_html_for_check_to_transfer(self):
        self.ensure_one()
        return f"""
            <table class="table table-bordered o_table">
                {self._render_thead_table_for_check_to_transfer()}
                {self._render_body_table_for_check_to_transfer()}
            </table>
        """

    def _render_thead_table_for_check_to_transfer(self):
        self.ensure_one()
        return f"""
            <thead>
                <tr class="active">
                    <th class="text-center">
                        {self._get_name_column("Stt")}
                        {self._get_name_column("No.", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Hạng mục kiểm tra")}
                        {self._get_name_column("General", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Tàu")}
                        {self._get_name_column("Ship", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Sà lan")}
                        {self._get_name_column("Barge", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Mã")}
                        {self._get_name_column("Code", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Ghi chú")}
                        {self._get_name_column("Remark", font_weight=False)}
                    </th>
                </tr>
            </thead>
        """

    def _render_body_table_for_check_to_transfer(self):
        self.ensure_one()
        records = self.fuel_check_ids.filtered(
            lambda e: e.check_type == CONST.CHECK_TO_TRANSFER
        )
        tr = [
            self._get_tr_tag_for_check_to_transfer(i, record_id)
            for i, record_id in enumerate(records)
        ]

        return f"""
            <tbody>
                {"".join(tr)}
            </tbody>
        """

    def _get_tr_tag_for_check_to_transfer(self, i, record_id):
        berthing = self.fuel_check_ids.filtered(
            lambda e: e.check_type == CONST.CHECK_TO_BERTHING
        )
        berthing_len = len(berthing)
        stt = berthing_len + i + 1
        name = record_id.name
        is_satisfied_ship = (
            '<ul class="o_checklist"><li id="checkId-1" placeholder="Danh sách" class="o_checked"><br></li></ul>'
            if record_id.is_satisfied_ship
            else '<ul class="o_checklist"><li id="checkId-2" placeholder="Danh sách" class="oe-hint"><br></li></ul>'
        )
        is_satisfied_barge = (
            '<ul class="o_checklist"><li id="checkId-1" placeholder="Danh sách" class="o_checked"><br></li></ul>'
            if record_id.is_satisfied_barge
            else '<ul class="o_checklist"><li id="checkId-2" placeholder="Danh sách" class="oe-hint"><br></li></ul>'
        )
        code = record_id.code or ""
        remark = record_id.remark or ""

        return f"""
            <tr>
                <td class="text-center">{stt}</td>
                <td>{name}</td>
                <td>{is_satisfied_ship}</td>
                <td>{is_satisfied_barge}</td>
                <td>{code}</td>
                <td>{remark}</td>
            </tr>
        """

    def _render_table_html_for_check_to_berthing(self):
        self.ensure_one()
        return f"""
            <table class="table table-bordered o_table">
                {self._render_thead_table_for_check_to_berthing()}
                {self._render_body_table_for_check_to_berthing()}
            </table>
        """

    def _render_thead_table_for_check_to_berthing(self):
        self.ensure_one()
        return f"""
            <thead>
                <tr class="active">
                    <th class="text-center">
                        {self._get_name_column("Stt")}
                        {self._get_name_column("No.", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Hạng mục kiểm tra")}
                        {self._get_name_column("General", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Tàu")}
                        {self._get_name_column("Ship", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Sà lan")}
                        {self._get_name_column("Barge", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Mã")}
                        {self._get_name_column("Code", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Ghi chú")}
                        {self._get_name_column("Remark", font_weight=False)}
                    </th>
                </tr>
            </thead>
        """

    def _render_body_table_for_check_to_berthing(self):
        self.ensure_one()
        records = self.fuel_check_ids.filtered(
            lambda e: e.check_type == CONST.CHECK_TO_BERTHING
        )
        tr = [
            self._get_tr_tag_for_check_to_berthing(i, record_id)
            for i, record_id in enumerate(records)
        ]

        return f"""
            <tbody>
                {"".join(tr)}
            </tbody>
        """

    def _get_tr_tag_for_check_to_berthing(self, i, record_id):
        stt = i + 1
        name = record_id.name
        is_satisfied_ship = (
            '<ul class="o_checklist"><li id="checkId-1" placeholder="Danh sách" class="o_checked"><br></li></ul>'
            if record_id.is_satisfied_ship
            else '<ul class="o_checklist"><li id="checkId-2" placeholder="Danh sách" class="oe-hint"><br></li></ul>'
        )
        is_satisfied_barge = (
            '<ul class="o_checklist"><li id="checkId-1" placeholder="Danh sách" class="o_checked"><br></li></ul>'
            if record_id.is_satisfied_barge
            else '<ul class="o_checklist"><li id="checkId-2" placeholder="Danh sách" class="oe-hint"><br></li></ul>'
        )
        code = record_id.code or ""
        remark = record_id.remark or ""

        return f"""
            <tr>
                <td class="text-center">{stt}</td>
                <td>{name}</td>
                <td>{is_satisfied_ship}</td>
                <td>{is_satisfied_barge}</td>
                <td>{code}</td>
                <td>{remark}</td>
            </tr>
        """

    def _render_table_html_for_barge(self):
        self.ensure_one()
        return f"""
            <table class="table table-bordered o_table">
                {self._render_thead_table_for_barge()}
                {self._render_body_table_for_barge()}
            </table>
        """

    def _render_thead_table_for_barge(self):
        self.ensure_one()
        return f"""
            <thead>
                <tr class="active">
                    <th class="text-center">
                        {self._get_name_column("Loại nhiên liệu")}
                        {self._get_name_column("Grade", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Khối lượng")}
                        {self._get_name_column("Tonnes", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Thể tích dầu tại nhiệt độ nhận")}
                        {self._get_name_column("Vol of oil loading temp", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Nhiệt độ nhận")}
                        {self._get_name_column("Vol of oil loading temp.", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Tốc độ bơm tối đa")}
                        {self._get_name_column("Maximum Transfer rate", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Áp suất tối đa trong đường ống")}
                        {self._get_name_column("Maximum line pressurre", font_weight=False)}
                    </th>
                </tr>
            </thead>
        """

    def _render_body_table_for_barge(self):
        self.ensure_one()
        records = self.bunker_ids
        tr = [self._get_tr_tag_for_barge(bunker_id) for bunker_id in records]

        return f"""
            <tbody>
                {"".join(tr)}
            </tbody>
        """

    def _get_tr_tag_for_barge(self, bunker_id):
        grade = bunker_id.grade
        weight_tonnes = bunker_id.weight_tonnes
        loading_temperature = bunker_id.loading_temperature
        volume_loading_temp = bunker_id.volume_loading_temp
        max_transfer_rate = bunker_id.max_transfer_rate
        max_line_pressure = bunker_id.max_line_pressure

        return f"""
            <tr>
                <td>{grade}</td>
                <td>{weight_tonnes}</td>
                <td>{loading_temperature}</td>
                <td>{volume_loading_temp}</td>
                <td>{max_transfer_rate}</td>
                <td>{max_line_pressure}</td>
            </tr>
        """

    def _render_table_html_for_ship(self):
        self.ensure_one()
        return f"""
            <table class="table table-bordered o_table">
                {self._render_thead_table_for_ship()}
                {self._render_body_table_for_ship()}
            </table>
        """

    def _render_thead_table_for_ship(self):
        self.ensure_one()
        return f"""
            <thead>
                <tr class="active">
                    <th class="text-center">
                        {self._get_name_column("Két")}
                        {self._get_name_column("Tank", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Loại nhiên liệu")}
                        {self._get_name_column("Grade", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Thể tích két")}
                        {self._get_name_column("@............%", font_weight=False)}
                        {self._get_name_column("Volume of tank", font_weight=False)}
                        {self._get_name_column("@............%", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Thể tích dầu trong két trước khi nhận")}
                        {self._get_name_column("Volume of oil in tank beore loading", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Thể tích không gian trống")}
                        {self._get_name_column("Available volume", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Dung lượng sẽ nhận")}
                        {self._get_name_column("Vol. to be loaded", font_weight=False)}
                    </th>
                    <th class="text-center">
                        {self._get_name_column("Tổng dung lượng nhận theo loại")}
                        {self._get_name_column("Total volume grade", font_weight=False)}
                    </th>
                </tr>
            </thead>
        """

    def _render_body_table_for_ship(self):
        self.ensure_one()
        records = [1, 2, 3]
        tr = [self._get_tr_tag_for_ship() for _ in records]

        return f"""
            <tbody>
                {"".join(tr)}
            </tbody>
        """

    def _get_tr_tag_for_ship(self):

        return f"""
            <tr>
                <td><br/></td>
                <td><br/></td>
                <td><br/></td>
                <td><br/></td>
                <td><br/></td>
                <td><br/></td>
                <td><br/></td>
            </tr>
        """

    def _get_name_column(self, name, font_weight="bold"):
        return f"""<div style="font-weight: {font_weight};">{name}</div>"""

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "ship.fuel.external.receiving"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)

        result = super(FuelExternalReceiving, self).create(vals_list)

        for record in result:
            record._create_fuel_tank_conditions()

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def write(self, vals):
        self.ensure_one()
        result = super(FuelExternalReceiving, self).write(vals)

        if "bunkering_safety_checklist_html" not in vals:
            self.rerender_bunkering_safety_checklist_html()
        return result

    @api.depends("arrival_datetime")
    def _compute_fuel_received(self):
        for record in self:
            latest_calculator = self.env["ship.fuel.external.calculator"].search(
                [("order_date", "<=", record.arrival_datetime)],
                order="order_date desc",
                limit=1,
            )
            if latest_calculator:
                record.hfo_received = latest_calculator.bunker_request_mt_fo
                record.do_received = latest_calculator.bunker_request_mt_do
            else:
                record.hfo_received = 0.0
                record.do_received = 0.0

    @api.depends("arrival_datetime")
    def _compute_voy(self):
        for record in self:
            if record.arrival_datetime:
                # Find the latest ShipFuelConsumption record based on tank_datetime
                latest_fuel_consumption = self.env["ship.fuel"].search(
                    [("time", "<=", record.arrival_datetime)],
                    order="time desc",
                    limit=1,
                )
                if latest_fuel_consumption:
                    record.voyage_number = latest_fuel_consumption.voy
                else:
                    record.voyage_number = "Not yet define"
            else:
                record.voyage_number = "Not yet define"

    @api.depends("fuel_tank_measurement_ids", "fuel_condition_ids")
    def _compute_hfo_final_received(self):
        for record in self:
            total_hfo_after = sum(
                record.fuel_condition_ids.filtered(
                    lambda fc: fc.condition == "after"
                ).mapped("total_FO_weight")
            )
            total_hfo_before = sum(
                record.fuel_condition_ids.filtered(
                    lambda fc: fc.condition == "before"
                ).mapped("total_FO_weight")
            )

            if total_hfo_after and total_hfo_before:
                time_diff = 0.0
                condition_before = record.fuel_condition_ids.filtered(
                    lambda fc: fc.condition == "before"
                )
                condition_after = record.fuel_condition_ids.filtered(
                    lambda fc: fc.condition == "after"
                )

                if condition_after and condition_before:
                    time_diff = (
                        condition_after.tank_datetime - condition_before.tank_datetime
                    ).total_seconds() / 3600

                record.hfo_received_final = (
                    total_hfo_after
                    - total_hfo_before
                    + (1.5 / 24) * time_diff
                    + (1.4 / 24) * time_diff
                )
            else:
                record.hfo_received_final = 0.0

    @api.depends("fuel_tank_measurement_ids", "fuel_condition_ids")
    def _compute_do_final_received(self):
        for record in self:
            total_do_after = sum(
                record.fuel_condition_ids.filtered(
                    lambda fc: fc.condition == "after"
                ).mapped("total_DO_weight")
            )
            total_do_before = sum(
                record.fuel_condition_ids.filtered(
                    lambda fc: fc.condition == "before"
                ).mapped("total_DO_weight")
            )

            if total_do_after and total_do_before:
                time_diff = 0.0
                condition_before = record.fuel_condition_ids.filtered(
                    lambda fc: fc.condition == "before"
                )
                condition_after = record.fuel_condition_ids.filtered(
                    lambda fc: fc.condition == "after"
                )

                if condition_after and condition_before:
                    time_diff = (
                        condition_after.tank_datetime - condition_before.tank_datetime
                    ).total_seconds() / 3600

                record.do_received_final = total_do_after - total_do_before
            else:
                record.do_received_final = 0.0

    @api.depends("do_received", "temperature")
    def _compute_do_volume_received(self):
        for record in self:
            temperature_difference = record.temperature - 15
            expansion_factor = 1 - (temperature_difference * 0.00064)
            record.do_volume_received = record.do_received / (
                record.do_density * expansion_factor
            )

    @api.depends("hfo_received", "temperature")
    def _compute_hfo_volume_received(self):
        for record in self:
            temperature_difference = record.temperature - 15
            expansion_factor = 1 - (temperature_difference * 0.00064)
            record.hfo_volume_received = record.hfo_received / (
                record.hfo_density * expansion_factor
            )

    def _create_fuel_tank_conditions(self):
        # Create one before FuelOilTankCondition
        latest_condition = self.env["ship.fuel.external.oil.tank.condition"].search(
            [("condition", "=", "external_calculator")],
            order="tank_datetime desc",
            limit=1,
        )

        if latest_condition:
            latest_condition.write({"fuel_external_receiving_id": self.id})

    def _get_default_fuel_checks(self):
        # default_checks = [
        #     {"name": "Sà lan đã có đủ giấy phép cập mạn"},
        #     {
        #         "name": "Đã kiểm tra các đệm chống va đảm bảo trong tình trạng tốt và không có khả năng tiếp xúc với kim loại?"
        #     },
        #     {
        #         "name": "Các phương tiện cách điện phù hợp đã được bố trí ở các điểm tiếp xúc xà lan-tàu?"
        #     },
        #     {
        #         "name": "Tất cả các rồng cấp nhiên liệu đều trong tình trạng tốt để làm việc?"
        #     },
        #     {"name": "Sà lan đã được buộc chắc chắn vào tàu?"},
        # ]

        default_value_model = self._get_default_value_model()
        variable_name = (
            CONST_UTILITIES.RELATION_SHIP_FUEL_EXTERNAL_RECEIVING_FUEL_CHECKS
        )
        default_checks = default_value_model._get_default_value_by_variable_name(
            variable_name
        )

        if default_checks:
            fuel_check_ids = self.env["ship.fuel.external.check"].create(
                [
                    {
                        "name": check.text_1,
                        "check_type": check.text_2,
                    }
                    for check in default_checks
                ]
            )

            return fuel_check_ids.ids


class FuelExternalOilTankCondition(models.Model):
    _name = "ship.fuel.external.oil.tank.condition"
    _description = "Fuel External Oil Tank Condition"
    CONDITIONS = [
        ("before", "Before"),
        ("after", "After"),
        ("external_calculator", "External Calculator"),
    ]

    fuel_external_receiving_id = fields.Many2one(
        "ship.fuel.external.receiving", string="Fuel External Receiving"
    )
    fuel_external_diary_id = fields.Many2one(
        "ship.fuel.external.diary", string="Fuel External Diary"
    )
    tank_datetime = fields.Datetime(string="Tank Datetime", default=fields.Datetime.now)
    condition = fields.Selection(CONDITIONS, string="Condition")
    trim = fields.Float(string="Trim (m)")
    heel = fields.Float(string="Heel (m)")
    density_hfo = fields.Float(string="Density H.F.O", digits=(10, 4), default=1)
    density_do = fields.Float(string="Density D.O", digits=(10, 4), default=1)
    sea_water_temperature = fields.Float(string="Sea Water Temperature (°C)")
    total_FO_weight = fields.Float(
        string="Total F.O Weight", compute="_compute_total_fo_weight", digits=(10, 3)
    )
    total_DO_weight = fields.Float(
        string="Total D.O Weight", compute="_compute_total_do_weight", digits=(10, 3)
    )
    weight_in_eng_log_FO = fields.Float(
        string="Weight in Eng.Log (MT) FO",
        compute="_compute_weight_in_eng_log_FO",
        digits=(10, 3),
    )
    weight_in_eng_log_DO = fields.Float(
        string="Weight in Eng.Log (MT) DO",
        compute="_compute_weight_in_eng_log_DO",
        digits=(10, 3),
    )
    weight_difference_FO = fields.Float(
        string="Difference (MT) FO",
        compute="_compute_weight_difference_FO",
        digits=(10, 3),
    )
    weight_difference_DO = fields.Float(
        string="Difference (MT) DO",
        compute="_compute_weight_difference_DO",
        digits=(10, 3),
    )
    last_measured_weight_FO = fields.Float(
        string="Last Measured Weight (MT) FO",
        compute="_compute_last_measured_weights",
        digits=(10, 3),
    )
    last_measured_weight_DO = fields.Float(
        string="Last Measured Weight (MT) DO",
        compute="_compute_last_measured_weights",
        digits=(10, 3),
    )
    consumption_between_measurements_FO = fields.Float(
        string="Consumption between two measurements (MT) FO",
        compute="_compute_consumption_between_measurements_FO",
        digits=(10, 3),
    )
    consumption_between_measurements_DO = fields.Float(
        string="Consumption between two measurements (MT) FO",
        compute="_compute_consumption_between_measurements_DO",
        digits=(10, 3),
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    fuel_tank_ids = fields.One2many(
        "ship.fuel.external.tank",
        "fuel_external_oil_tank_condition_id",
        default=lambda self: self.get_default_fuel_tank(),
        string="Fuel Tanks",
    )

    def get_default_fuel_tank(self):
        fuel_tank_ids = []
        for value, _ in CONST.TANK_NAME_SELECTION:
            fuek_tank_id = self.fuel_tank_ids.create(
                {
                    # "fuel_oil_tank_condition_id": self.id,
                    "tank_name": value,
                }
            )
            if fuek_tank_id:
                fuel_tank_ids.append(fuek_tank_id.id)
        return fuel_tank_ids

    @api.depends("tank_datetime")
    def _compute_weight_in_eng_log_FO(self):
        for record in self:
            if record.tank_datetime:
                # Find the latest ShipFuelConsumption record based on tank_datetime
                latest_fuel_consumption = self.env["ship.fuel"].search(
                    [("time", "<=", record.tank_datetime)], order="time desc", limit=1
                )
                if latest_fuel_consumption:
                    record.weight_in_eng_log_FO = latest_fuel_consumption.current_fo
                else:
                    record.weight_in_eng_log_FO = 0.0
            else:
                record.weight_in_eng_log_FO = 0.0

    @api.depends("tank_datetime")
    def _compute_weight_in_eng_log_DO(self):
        for record in self:
            if record.tank_datetime:
                # Find the latest ShipFuelConsumption record based on tank_datetime
                latest_fuel_consumption = self.env["ship.fuel"].search(
                    [("time", "<=", record.tank_datetime)], order="time desc", limit=1
                )
                if latest_fuel_consumption:
                    record.weight_in_eng_log_DO = latest_fuel_consumption.current_do
                else:
                    record.weight_in_eng_log_DO = 0.0
            else:
                record.weight_in_eng_log_DO = 0.0

    @api.depends("condition", "total_FO_weight", "total_DO_weight")
    def _compute_last_measured_weights(self):
        for record in self:
            fuel_external_receiving_id = record.fuel_external_receiving_id
            if record.condition == "external_calculator":
                record.last_measured_weight_FO = record.total_FO_weight
                record.last_measured_weight_DO = record.total_DO_weight
            elif record.condition == "before":
                # Find the last measured weights from the previous condition
                previous_condition = self.env[
                    "ship.fuel.external.oil.tank.condition"
                ].search(
                    [
                        ("condition", "=", "external_calculator"),
                        (
                            "fuel_external_receiving_id",
                            "=",
                            fuel_external_receiving_id.id,
                        ),
                    ],
                    limit=1,
                )
                if previous_condition:
                    record.last_measured_weight_FO = previous_condition.total_FO_weight
                    record.last_measured_weight_DO = previous_condition.total_DO_weight
                else:
                    record.last_measured_weight_FO = 0
                    record.last_measured_weight_DO = 0
            elif record.condition == "after":
                # Find the last measured weights from the previous condition
                previous_condition = self.env[
                    "ship.fuel.external.oil.tank.condition"
                ].search(
                    [
                        ("condition", "=", "before"),
                        (
                            "fuel_external_receiving_id",
                            "=",
                            fuel_external_receiving_id.id,
                        ),
                    ],
                    limit=1,
                )
                if previous_condition:
                    record.last_measured_weight_FO = previous_condition.total_FO_weight
                    record.last_measured_weight_DO = previous_condition.total_DO_weight
                else:
                    record.last_measured_weight_FO = 0
                    record.last_measured_weight_DO = 0

            else:
                record.last_measured_weight_FO = 0
                record.last_measured_weight_DO = 0

    @api.depends("last_measured_weight_DO", "total_DO_weight")
    def _compute_consumption_between_measurements_DO(self):
        for record in self:
            if record.condition == "after":
                record.consumption_between_measurements_DO = (
                    record.last_measured_weight_DO
                    - record.total_DO_weight
                    + record.fuel_external_receiving_id.do_received
                )
            else:
                record.consumption_between_measurements_DO = (
                    record.last_measured_weight_DO - record.total_DO_weight
                )

    @api.depends("last_measured_weight_FO", "total_FO_weight")
    def _compute_consumption_between_measurements_FO(self):
        for record in self:
            if record.condition == "after":
                record.consumption_between_measurements_FO = (
                    record.last_measured_weight_FO
                    - record.total_FO_weight
                    + record.fuel_external_receiving_id.hfo_received
                )
            else:
                record.consumption_between_measurements_FO = (
                    record.last_measured_weight_FO - record.total_FO_weight
                )

    @api.depends("total_FO_weight", "weight_in_eng_log_FO")
    def _compute_weight_difference_FO(self):
        for record in self:
            record.weight_difference_FO = (
                record.total_FO_weight - record.weight_in_eng_log_FO
            )

    @api.depends("total_DO_weight", "weight_in_eng_log_DO")
    def _compute_weight_difference_DO(self):
        for record in self:
            record.weight_difference_DO = (
                record.total_DO_weight - record.weight_in_eng_log_DO
            )

    @api.depends("fuel_tank_ids")
    def _compute_total_fo_weight(self):
        for record in self:
            record.total_FO_weight = sum(
                record.fuel_tank_ids.filtered(
                    lambda tank: tank.fuel_type == "hfo"
                ).mapped("weight")
            )

    @api.depends("fuel_tank_ids")
    def _compute_total_do_weight(self):
        for record in self:
            record.total_DO_weight = sum(
                record.fuel_tank_ids.filtered(
                    lambda tank: tank.fuel_type == "do"
                ).mapped("weight")
            )


class FuelExternalCheck(models.Model):
    _name = "ship.fuel.external.check"
    _description = "Fuel External Checks during Fuel Receiving"

    name = fields.Char(string="Check Name", required=True)
    check_type = fields.Selection(
        CONST.CHECK_TYPE,
        string="Check type",
        default=CONST.CHECK_TO_BERTHING,
        required=True,
    )
    code = fields.Char(string="Mã Code")
    remark = fields.Char(string="Ghi chú Remark")
    is_satisfied_ship = fields.Boolean(string="Ship Check")
    is_satisfied_barge = fields.Boolean(string="Barge Check")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    fuel_external_receiving_id = fields.Many2one(
        "ship.fuel.external.receiving", string="Fuel External Receiving"
    )


class FuelExternalTankMeasurement(models.Model):
    _name = "ship.fuel.external.tank.measurement"
    _description = "Fuel External Tank Measurement"

    TANK_NAME_SELECTION = [
        ("F.O.T NO.2 P", "F.O.T NO.2 P"),
        ("F.O.T NO.2 S", "F.O.T NO.2 S"),
        ("F.O.T NO.1 P", "F.O.T NO.1 P"),
        ("F.O.T NO.1 S", "F.O.T NO.1 S"),
        ("D.O.T NO.1 P", "D.O.T NO.1 P"),
        ("D.O.T NO.1 S", "D.O.T NO.1 S"),
    ]

    tank_name = fields.Selection(
        TANK_NAME_SELECTION, string="Tank Name", default="F.O.T NO.2 P"
    )

    measure_type = fields.Selection(
        [("sound", "Sound"), ("ullage", "Ullage")],
        string="Measure Type",
        compute="_compute_measure_type",
    )
    FUEL_TYPE_SELECTION = [("hfo", "HFO"), ("do", "DO")]
    fuel_type = fields.Selection(FUEL_TYPE_SELECTION, string="Fuel Type")

    tank_measurement_at_100 = fields.Float(
        string="Tanks measurement at 100% m3",
        compute="_compute_tank_measurement_at_100",
        digits=(10, 3),
    )
    tank_measurement_at_85 = fields.Float(
        string="Tanks measurement at 85 m3%",
        compute="_compute_tank_measurement_at_85",
        digits=(10, 3),
    )
    ##remain on board
    measure_adjustment = fields.Float(
        string="Measure/Adjust (m)", compute="_compute_measurement", digits=(10, 3)
    )
    volume_m3 = fields.Float(
        string="Volume - m3", compute="_compute_volume", digits=(10, 3)
    )
    ###Receiving
    receiving_volume = fields.Float(string="Receiving Volume (m3)", digits=(10, 3))

    ##after bunking
    after_bunkering_estimate = fields.Float(
        string="After Bunkering Estimate (m3)",
        compute="_compute_after_bunkering_estimate",
        digits=(10, 3),
    )

    tank_measurement_at_0 = fields.Float(
        string="Tank Measurement (m) when trim is 0.0m",
        compute="_compute_tank_measurement_trim_0",
        digits=(10, 3),
    )
    tank_measurement_at_1 = fields.Float(
        string="Tank Measurement (m) when trim is 1.0 m",
        compute="_compute_tank_measurement_trim_1",
        digits=(10, 3),
    )
    tank_measurement_at_2 = fields.Float(
        string="Tank Measurement (m) when trim is 2.0 m",
        compute="_compute_tank_measurement_trim_2",
        digits=(10, 3),
    )
    tank_measurement_at_3 = fields.Float(
        string="Tank Measurement (m) when trim is 3.0 m",
        compute="_compute_tank_measurement_trim_3",
        digits=(10, 3),
    )
    percentage_fill = fields.Float(
        string="Percentage filling", compute="_compute_percentage_fill", digits=(10, 3)
    )
    fuel_external_receiving_id = fields.Many2one(
        "ship.fuel.external.receiving",
        string="Fuel External Receiving",
        ondelete="cascade",  # Optional: This ensures that if the parent record is deleted, the related records are also deleted
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.depends("tank_name")
    def _compute_tank_measurement_at_100(self):
        for record in self:
            if record.tank_name in ["F.O.T NO.1 P", "F.O.T NO.1 S"]:
                record.tank_measurement_at_100 = 187.1
            elif record.tank_name in ["F.O.T NO.2 P", "F.O.T NO.2 S"]:
                record.tank_measurement_at_100 = 308.8
            elif record.tank_name in ["D.O.T NO.1 P", "D.O.T NO.1 S"]:
                record.tank_measurement_at_100 = 51.1
            else:
                record.tank_measurement_at_100 = 0

    @api.depends("tank_measurement_at_100")
    def _compute_tank_measurement_at_85(self):
        for record in self:
            record.tank_measurement_at_85 = record.tank_measurement_at_100 * 0.85

    @api.depends("after_bunkering_estimate")
    def _compute_tank_measurement_trim_0(self):
        for record in self:

            # Calculate tank measurement at trim 0
            # Initialize total_volume
            trim = 0
            final_sound = 0
            final_ullage = 0
            volume = record.after_bunkering_estimate
            nearest_volume_record_above = False
            nearest_volume_record_below = False

            # Define search criteria based on tank name and measurement type (sound or ullage)
            search_criteria = [("tank_name", "=", record.tank_name)]

            # Search for sounding records based on trim
            search_criteria_trim = search_criteria + [("table_type", "=", "trim")]
            sounding_trim_books = self.env["ship.sounding.book"].search(
                search_criteria_trim
            )
            for sounding_book in sounding_trim_books:
                # Search for sounding records based on provided trim and volume
                sounding_table_records = self.env["ship.sounding.table"].search(
                    [
                        ("sounding_book_id", "=", sounding_book.id),
                        ("volume", "=", volume),
                        ("table_value", "=", trim),
                    ]
                )
                # If exact match found, retrieve volume
                if sounding_table_records:
                    record.tank_measurement_at_0 = sum(
                        sounding_table_records.mapped(record.measure_type)
                    )

                else:
                    # Find the two nearest trim values
                    nearest_volume_records = self.env["ship.sounding.table"].search(
                        [
                            ("sounding_book_id", "=", sounding_book.id),
                            ("table_value", "=", trim),
                        ]
                    )
                    if nearest_volume_records:
                        nearest_volume_records_sorted = nearest_volume_records.sorted(
                            key=lambda r: abs(r.volume - volume)
                        )
                        for measure_record in nearest_volume_records_sorted:
                            if measure_record.volume < volume:
                                nearest_volume_record_below = measure_record
                            elif measure_record.volume > volume:
                                nearest_volume_record_above = measure_record
                            if (
                                nearest_volume_record_above
                                and nearest_volume_record_below
                            ):
                                above_measure_ullage = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_above.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("ullage")
                                )
                                below_measure_ullage = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_below.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("ullage")
                                )
                                above_measure_sound = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_above.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("sound")
                                )
                                below_measure_sound = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_below.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("sound")
                                )
                                if (
                                    nearest_volume_record_above.volume
                                    != nearest_volume_record_below.volume
                                ):
                                    final_ullage = below_measure_ullage + (
                                        volume - nearest_volume_record_below.volume
                                    ) * (
                                        above_measure_ullage - below_measure_ullage
                                    ) / (
                                        nearest_volume_record_above.volume
                                        - nearest_volume_record_below.volume
                                    )
                                    final_sound = below_measure_sound + (
                                        volume - nearest_volume_record_below.volume
                                    ) * (above_measure_sound - below_measure_sound) / (
                                        nearest_volume_record_above.volume
                                        - nearest_volume_record_below.volume
                                    )

            if record.measure_type == "sound":
                record.tank_measurement_at_0 = final_sound
            elif record.measure_type == "ullage":
                record.tank_measurement_at_0 = final_ullage
            else:
                record.tank_measurement_at_0 = 0

    @api.depends("after_bunkering_estimate")
    def _compute_tank_measurement_trim_1(self):
        for record in self:

            # Calculate tank measurement at trim 0
            # Initialize total_volume
            trim = 1
            final_sound = 0
            final_ullage = 0
            volume = record.after_bunkering_estimate
            nearest_volume_record_above = False
            nearest_volume_record_below = False
            # Define search criteria based on tank name and measurement type (sound or ullage)
            search_criteria = [("tank_name", "=", record.tank_name)]

            # Search for sounding records based on trim
            search_criteria_trim = search_criteria + [("table_type", "=", "trim")]
            sounding_trim_books = self.env["ship.sounding.book"].search(
                search_criteria_trim
            )
            for sounding_book in sounding_trim_books:
                # Search for sounding records based on provided trim and volume
                sounding_table_records = self.env["ship.sounding.table"].search(
                    [
                        ("sounding_book_id", "=", sounding_book.id),
                        ("volume", "=", volume),
                        ("table_value", "=", trim),
                    ]
                )
                # If exact match found, retrieve volume
                if sounding_table_records:
                    record.tank_measurement_at_1 = sum(
                        sounding_table_records.mapped(record.measure_type)
                    )

                else:
                    # Find the two nearest trim values
                    nearest_volume_records = self.env["ship.sounding.table"].search(
                        [
                            ("sounding_book_id", "=", sounding_book.id),
                            ("table_value", "=", trim),
                        ]
                    )
                    if nearest_volume_records:
                        nearest_volume_records_sorted = nearest_volume_records.sorted(
                            key=lambda r: abs(r.volume - volume)
                        )
                        for measure_record in nearest_volume_records_sorted:
                            if measure_record.volume < volume:
                                nearest_volume_record_below = measure_record
                            elif measure_record.volume > volume:
                                nearest_volume_record_above = measure_record
                            # Once both above and below records are found, exit the loop
                            if (
                                nearest_volume_record_above
                                and nearest_volume_record_below
                            ):
                                above_measure_ullage = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_above.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("ullage")
                                )
                                below_measure_ullage = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_below.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("ullage")
                                )
                                above_measure_sound = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_above.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("sound")
                                )
                                below_measure_sound = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_below.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("sound")
                                )
                                if (
                                    nearest_volume_record_above.volume
                                    != nearest_volume_record_below.volume
                                ):
                                    final_ullage = below_measure_ullage + (
                                        volume - nearest_volume_record_below.volume
                                    ) * (
                                        above_measure_ullage - below_measure_ullage
                                    ) / (
                                        nearest_volume_record_above.volume
                                        - nearest_volume_record_below.volume
                                    )
                                    final_sound = below_measure_sound + (
                                        volume - nearest_volume_record_below.volume
                                    ) * (above_measure_sound - below_measure_sound) / (
                                        nearest_volume_record_above.volume
                                        - nearest_volume_record_below.volume
                                    )

                                break
            if record.measure_type == "sound":
                record.tank_measurement_at_1 = final_sound
            elif record.measure_type == "ullage":
                record.tank_measurement_at_1 = final_ullage
            else:
                record.tank_measurement_at_1 = 0

    @api.depends("after_bunkering_estimate")
    def _compute_tank_measurement_trim_2(self):
        for record in self:

            # Calculate tank measurement at trim 0
            # Initialize total_volume
            trim = 2
            final_sound = 0
            final_ullage = 0
            volume = record.after_bunkering_estimate
            nearest_volume_record_above = False
            nearest_volume_record_below = False
            # Define search criteria based on tank name and measurement type (sound or ullage)
            search_criteria = [("tank_name", "=", record.tank_name)]

            # Search for sounding records based on trim
            search_criteria_trim = search_criteria + [("table_type", "=", "trim")]
            sounding_trim_books = self.env["ship.sounding.book"].search(
                search_criteria_trim
            )
            for sounding_book in sounding_trim_books:
                # Search for sounding records based on provided trim and volume
                sounding_table_records = self.env["ship.sounding.table"].search(
                    [
                        ("sounding_book_id", "=", sounding_book.id),
                        ("volume", "=", volume),
                        ("table_value", "=", trim),
                    ]
                )
                # If exact match found, retrieve volume
                if sounding_table_records:
                    record.tank_measurement_at_2 = sum(
                        sounding_table_records.mapped(record.measure_type)
                    )

                else:
                    # Find the two nearest trim values
                    nearest_volume_records = self.env["ship.sounding.table"].search(
                        [
                            ("sounding_book_id", "=", sounding_book.id),
                            ("table_value", "=", trim),
                        ]
                    )
                    if nearest_volume_records:
                        nearest_volume_records_sorted = nearest_volume_records.sorted(
                            key=lambda r: abs(r.volume - volume)
                        )
                        for measure_record in nearest_volume_records_sorted:
                            if measure_record.volume < volume:
                                nearest_volume_record_below = measure_record
                            elif measure_record.volume > volume:
                                nearest_volume_record_above = measure_record
                            # Once both above and below records are found, exit the loop
                            if (
                                nearest_volume_record_above
                                and nearest_volume_record_below
                            ):
                                above_measure_ullage = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_above.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("ullage")
                                )
                                below_measure_ullage = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_below.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("ullage")
                                )
                                above_measure_sound = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_above.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("sound")
                                )
                                below_measure_sound = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_below.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("sound")
                                )
                                if (
                                    nearest_volume_record_above.volume
                                    != nearest_volume_record_below.volume
                                ):
                                    final_ullage = below_measure_ullage + (
                                        volume - nearest_volume_record_below.volume
                                    ) * (
                                        above_measure_ullage - below_measure_ullage
                                    ) / (
                                        nearest_volume_record_above.volume
                                        - nearest_volume_record_below.volume
                                    )
                                    final_sound = below_measure_sound + (
                                        volume - nearest_volume_record_below.volume
                                    ) * (above_measure_sound - below_measure_sound) / (
                                        nearest_volume_record_above.volume
                                        - nearest_volume_record_below.volume
                                    )
                                break
            if record.measure_type == "sound":
                record.tank_measurement_at_2 = final_sound
            elif record.measure_type == "ullage":
                record.tank_measurement_at_2 = final_ullage
            else:
                record.tank_measurement_at_2 = 0

    @api.depends("after_bunkering_estimate")
    def _compute_tank_measurement_trim_3(self):
        for record in self:

            # Calculate tank measurement at trim 0
            # Initialize total_volume
            trim = 3
            final_sound = 0
            final_ullage = 0
            volume = record.after_bunkering_estimate
            nearest_volume_record_above = False
            nearest_volume_record_below = False
            # Define search criteria based on tank name and measurement type (sound or ullage)
            search_criteria = [("tank_name", "=", record.tank_name)]

            # Search for sounding records based on trim
            search_criteria_trim = search_criteria + [("table_type", "=", "trim")]
            sounding_trim_books = self.env["ship.sounding.book"].search(
                search_criteria_trim
            )
            for sounding_book in sounding_trim_books:
                # Search for sounding records based on provided trim and volume
                sounding_table_records = self.env["ship.sounding.table"].search(
                    [
                        ("sounding_book_id", "=", sounding_book.id),
                        ("volume", "=", volume),
                        ("table_value", "=", trim),
                    ]
                )
                # If exact match found, retrieve volume
                if sounding_table_records:
                    record.tank_measurement_at_3 = sum(
                        sounding_table_records.mapped(record.measure_type)
                    )

                else:
                    # Find the two nearest trim values
                    nearest_volume_records = self.env["ship.sounding.table"].search(
                        [
                            ("sounding_book_id", "=", sounding_book.id),
                            ("table_value", "=", trim),
                        ]
                    )
                    if nearest_volume_records:
                        nearest_volume_records_sorted = nearest_volume_records.sorted(
                            key=lambda r: abs(r.volume - volume)
                        )
                        for measure_record in nearest_volume_records_sorted:
                            if measure_record.volume < volume:
                                nearest_volume_record_below = measure_record
                            elif measure_record.volume > volume:
                                nearest_volume_record_above = measure_record
                            # Once both above and below records are found, exit the loop
                            if (
                                nearest_volume_record_above
                                and nearest_volume_record_below
                            ):
                                above_measure_ullage = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_above.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("ullage")
                                )
                                below_measure_ullage = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_below.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("ullage")
                                )
                                above_measure_sound = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_above.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("sound")
                                )
                                below_measure_sound = min(
                                    self.env["ship.sounding.table"]
                                    .search(
                                        [
                                            ("sounding_book_id", "=", sounding_book.id),
                                            (
                                                "volume",
                                                "=",
                                                nearest_volume_record_below.volume,
                                            ),
                                            ("table_value", "=", trim),
                                        ]
                                    )
                                    .mapped("sound")
                                )
                                if (
                                    nearest_volume_record_above.volume
                                    != nearest_volume_record_below.volume
                                ):
                                    final_ullage = below_measure_ullage + (
                                        volume - nearest_volume_record_below.volume
                                    ) * (
                                        above_measure_ullage - below_measure_ullage
                                    ) / (
                                        nearest_volume_record_above.volume
                                        - nearest_volume_record_below.volume
                                    )
                                    final_sound = below_measure_sound + (
                                        volume - nearest_volume_record_below.volume
                                    ) * (above_measure_sound - below_measure_sound) / (
                                        nearest_volume_record_above.volume
                                        - nearest_volume_record_below.volume
                                    )
                                break

            if record.measure_type == "sound":
                record.tank_measurement_at_3 = final_sound
            elif record.measure_type == "ullage":
                record.tank_measurement_at_3 = final_ullage
            else:
                record.tank_measurement_at_3 = 0

    @api.depends("tank_name", "fuel_external_receiving_id")
    def _compute_measure_type(self):
        for record in self:
            if record.tank_name:
                fuel_external_receiving_id = record.fuel_external_receiving_id
                if fuel_external_receiving_id:
                    fuel_condition_ids = self.env[
                        "ship.fuel.external.oil.tank.condition"
                    ].search(
                        [
                            ("condition", "=", "before"),
                            (
                                "fuel_external_receiving_id",
                                "=",
                                fuel_external_receiving_id.id,
                            ),
                        ],
                        limit=1,
                    )
                    if fuel_condition_ids:
                        for fuel_condition_id in fuel_condition_ids:
                            fuel_tank = self.env["ship.fuel.external.tank"].search(
                                [
                                    ("tank_name", "=", record.tank_name),
                                    (
                                        "fuel_external_oil_tank_condition_id",
                                        "=",
                                        fuel_condition_id.id,
                                    ),
                                ],
                                limit=1,
                            )
                            if fuel_tank:
                                record.measure_type = fuel_tank.measure_type
                            else:
                                record.measure_type = "sound"
                    else:
                        record.measure_type = "sound"
                else:
                    record.measure_type = "sound"
            else:
                record.measure_type = "sound"

    @api.depends("tank_name", "fuel_external_receiving_id")
    def _compute_measurement(self):
        for record in self:
            if record.tank_name:
                fuel_external_receiving_id = record.fuel_external_receiving_id
                if fuel_external_receiving_id:
                    fuel_condition_ids = self.env[
                        "ship.fuel.external.oil.tank.condition"
                    ].search(
                        [
                            ("condition", "=", "before"),
                            (
                                "fuel_external_receiving_id",
                                "=",
                                fuel_external_receiving_id.id,
                            ),
                        ],
                        limit=1,
                    )
                    if fuel_condition_ids:
                        for fuel_condition_id in fuel_condition_ids:
                            fuel_tank = self.env["ship.fuel.external.tank"].search(
                                [
                                    ("tank_name", "=", record.tank_name),
                                    (
                                        "fuel_external_oil_tank_condition_id",
                                        "=",
                                        fuel_condition_id.id,
                                    ),
                                ],
                                limit=1,
                            )
                            if fuel_tank:
                                record.measure_adjustment = fuel_tank.measurement
                            else:
                                record.measure_adjustment = 0
                    else:
                        record.measure_adjustment = 0
                else:
                    record.measure_adjustment = 0
            else:
                record.measure_adjustment = 0

    @api.depends("tank_name", "fuel_external_receiving_id")
    def _compute_volume(self):
        for record in self:
            if record.tank_name:
                fuel_external_receiving_id = record.fuel_external_receiving_id
                if fuel_external_receiving_id:
                    fuel_condition_ids = self.env[
                        "ship.fuel.external.oil.tank.condition"
                    ].search(
                        [
                            ("condition", "=", "before"),
                            (
                                "fuel_external_receiving_id",
                                "=",
                                fuel_external_receiving_id.id,
                            ),
                        ],
                        limit=1,
                    )
                    if fuel_condition_ids:
                        for fuel_condition_id in fuel_condition_ids:
                            fuel_tank = self.env["ship.fuel.external.tank"].search(
                                [
                                    ("tank_name", "=", record.tank_name),
                                    (
                                        "fuel_external_oil_tank_condition_id",
                                        "=",
                                        fuel_condition_id.id,
                                    ),
                                ],
                                limit=1,
                            )
                            if fuel_tank:
                                record.volume_m3 = fuel_tank.volumetric_capacity
                            else:
                                record.volume_m3 = 0
                    else:
                        record.volume_m3 = 0
                else:
                    record.volume_m3 = 0
            else:
                record.volume_m3 = 0

    @api.depends("receiving_volume", "volume_m3")
    def _compute_after_bunkering_estimate(self):
        for record in self:
            record.after_bunkering_estimate = record.receiving_volume + record.volume_m3

    @api.depends("after_bunkering_estimate", "tank_measurement_at_100")
    def _compute_percentage_fill(self):
        for record in self:
            if record.tank_measurement_at_100 != 0:
                record.percentage_fill = (
                    record.after_bunkering_estimate / record.tank_measurement_at_100
                ) * 100
            else:
                record.percentage_fill = 0  # Handle division by zero case


class FuelExternalTank(models.Model):
    _name = "ship.fuel.external.tank"
    _description = "Fuel External Tank"

    fuel_external_oil_tank_condition_id = fields.Many2one(
        "ship.fuel.external.oil.tank.condition",
        string="Fuel External Oil Tank Condition",
    )
    fuel_type = fields.Selection([("hfo", "HFO"), ("do", "DO")], string="Fuel Type")
    tank_type = fields.Selection(
        [
            ("service", "Service"),
            ("settling", "Settling"),
            ("overflow", "Overflow"),
            ("fuel_oil", "Fuel Oil"),
        ],
        string="Tank Type",
    )

    TANK_NAME_SELECTION = [
        ("F.O.T NO.2 P", "F.O.T NO.2 P"),
        ("F.O.T NO.2 S", "F.O.T NO.2 S"),
        ("F.O.T NO.1 P", "F.O.T NO.1 P"),
        ("F.O.T NO.1 S", "F.O.T NO.1 S"),
        ("D.O.T NO.1 P", "D.O.T NO.1 P"),
        ("D.O.T NO.1 S", "D.O.T NO.1 S"),
    ]

    tank_name = fields.Selection(TANK_NAME_SELECTION, string="Tank Name")
    measure_type = fields.Selection(
        [("sound", "Sound"), ("ullage", "Ullage")], string="Measure Type"
    )
    measurement = fields.Float(string="Measurement / Số đo (m)", digits=(10, 3))
    volumetric_capacity = fields.Float(
        string="Volumetric Capacity / Dung tích (m3)",
        compute="_compute_calculated_volume",
        digits=(10, 3),
    )
    temperature = fields.Float(string="At/ (Tại) . . . 0C")
    expansion_factor = fields.Float(
        string="Factor of Temp. Adjust",
        compute="_compute_expansion_factor",
        digits=(10, 3),
    )
    volumetric_at_150C = fields.Float(
        string="Volumetric at 15°C / Dung tích tại 15°C (m3)",
        compute="_compute_volumetric_at_150c",
        digits=(10, 3),
    )
    weight = fields.Float(
        string="Weight / Trọng lượng (MT)", compute="_compute_weight", digits=(10, 3)
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.depends("measurement", "fuel_external_oil_tank_condition_id")
    def _compute_calculated_volume(self):
        for record in self:
            nearest_above_measure = None
            nearest_below_measure = None
            nearest_below_trim = None
            nearest_above_trim = None
            nearest_below_heel = None
            nearest_above_heel = None
            nearest_above_heel = None

            if record.measurement >= 0 and record.fuel_external_oil_tank_condition_id:
                # Calculate volume based on sounding table values
                fuel_oil_tank_condition = record.fuel_external_oil_tank_condition_id

                # Extract the trim and heel values
                trim = fuel_oil_tank_condition.trim
                heel = fuel_oil_tank_condition.heel

                # Initialize volume
                total_volume = 0.0
                final_trim_volume = 0
                final_heel_volume = 0
                # Define search criteria based on fuel type
                search_criteria = [("tank_name", "=", record.tank_name)]

                # Search for sounding records based on trim
                if record.measure_type == "ullage":
                    search_criteria_trim = search_criteria + [
                        ("table_type", "=", "trim")
                    ]
                    sounding_trim_books = self.env["ship.sounding.book"].search(
                        search_criteria_trim
                    )
                    for sounding_book in sounding_trim_books:
                        sounding_table_records = self.env["ship.sounding.table"].search(
                            [
                                ("sounding_book_id", "=", sounding_book.id),
                                ("ullage", "=", record.measurement),
                                ("table_value", "=", trim),
                            ]
                        )
                        final_trim_volume = sum(sounding_table_records.mapped("volume"))

                        if not sounding_table_records:
                            # If no records found for provided measurement, find the two nearest trim values
                            nearest_measure_records = self.env[
                                "ship.sounding.table"
                            ].search([("sounding_book_id", "=", sounding_book.id)])
                            nearest_measure_records = sorted(
                                nearest_measure_records,
                                key=lambda r: abs(r.ullage - record.measurement),
                            )
                            if nearest_measure_records:
                                exact_measure_record = next(
                                    (
                                        r
                                        for r in nearest_measure_records
                                        if abs(r.ullage - record.measurement) == 0
                                    ),
                                    False,
                                )
                                if exact_measure_record:
                                    nearest_below_measure = exact_measure_record[
                                        0
                                    ].ullage
                                    nearest_above_measure = exact_measure_record[
                                        0
                                    ].ullage
                                else:
                                    nearest_below_measure = None
                                    nearest_above_measure = None
                                    for r in nearest_measure_records:
                                        if r.ullage < record.measurement:
                                            nearest_below_measure = r.ullage
                                        elif r.ullage > record.measurement:
                                            nearest_above_measure = r.ullage
                                        if (
                                            nearest_below_measure
                                            and nearest_above_measure
                                        ):
                                            break

                            nearest_trim_records = self.env[
                                "ship.sounding.table"
                            ].search([("sounding_book_id", "=", sounding_book.id)])
                            nearest_trim_records = sorted(
                                nearest_trim_records,
                                key=lambda r: abs(r.table_value - trim),
                            )

                            if nearest_trim_records:
                                exact_trim_record = self.env[
                                    "ship.sounding.table"
                                ].browse(
                                    [
                                        r.id
                                        for r in nearest_trim_records
                                        if abs(r.table_value - trim) == 0
                                    ]
                                )
                                if exact_trim_record:
                                    nearest_below_trim = exact_trim_record[
                                        0
                                    ].table_value
                                    nearest_above_trim = exact_trim_record[
                                        0
                                    ].table_value
                                else:
                                    nearest_below_trim = None
                                    nearest_above_trim = None
                                    for r in nearest_trim_records:
                                        if r.table_value < trim:
                                            nearest_below_trim = r.table_value
                                        elif r.table_value > trim:
                                            nearest_above_trim = r.table_value
                                        if nearest_below_trim and nearest_above_trim:
                                            break

                            ## find 4 point

                            low_low_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("ullage", "=", nearest_below_measure),
                                        ("table_value", "=", nearest_below_trim),
                                    ]
                                )
                                .volume
                            )
                            high_low_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("ullage", "=", nearest_above_measure),
                                        ("table_value", "=", nearest_below_trim),
                                    ]
                                )
                                .volume
                            )
                            low_high_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("ullage", "=", nearest_below_measure),
                                        ("table_value", "=", nearest_above_trim),
                                    ]
                                )
                                .volume
                            )
                            high_high_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("ullage", "=", nearest_above_measure),
                                        ("table_value", "=", nearest_above_trim),
                                    ]
                                )
                                .volume
                            )
                            try:
                                if nearest_above_measure != nearest_below_measure:
                                    trim_low_volume = low_low_volume + (
                                        record.measurement - nearest_below_measure
                                    ) * (high_low_volume - low_low_volume) / (
                                        nearest_above_measure - nearest_below_measure
                                    )
                                    trim_high_volume = low_high_volume + (
                                        record.measurement - nearest_below_measure
                                    ) * (high_high_volume - low_high_volume) / (
                                        nearest_above_measure - nearest_below_measure
                                    )

                                else:
                                    trim_low_volume = (
                                        low_low_volume + high_low_volume
                                    ) / 2
                                    trim_high_volume = (
                                        low_high_volume + high_high_volume
                                    ) / 2

                                if nearest_above_trim != nearest_below_trim:
                                    final_trim_volume = trim_low_volume + (
                                        trim - nearest_below_trim
                                    ) * (trim_high_volume - trim_low_volume) / (
                                        nearest_above_trim - nearest_below_trim
                                    )
                                else:
                                    final_trim_volume = (
                                        trim_low_volume + trim_high_volume
                                    ) / 2
                            except:
                                final_trim_volume = 0

                    # Search for sounding records based on heel
                    search_criteria_heel = search_criteria + [
                        ("table_type", "=", "heel")
                    ]
                    sounding_heel_books = self.env["ship.sounding.book"].search(
                        search_criteria_heel
                    )
                    for sounding_book in sounding_heel_books:
                        sounding_table_records = self.env["ship.sounding.table"].search(
                            [
                                ("sounding_book_id", "=", sounding_book.id),
                                ("ullage", "=", record.measurement),
                                ("table_value", "=", heel),
                            ]
                        )
                        final_heel_volume = sum(sounding_table_records.mapped("volume"))
                        if not sounding_table_records:
                            # If no records found for provided measurement, find the two nearest heel values
                            nearest_measure_records = self.env[
                                "ship.sounding.table"
                            ].search([("sounding_book_id", "=", sounding_book.id)])
                            nearest_measure_records = sorted(
                                nearest_measure_records,
                                key=lambda r: abs(r.ullage - record.measurement),
                            )

                            if nearest_measure_records:
                                exact_measure_record = next(
                                    (
                                        r
                                        for r in nearest_measure_records
                                        if abs(r.ullage - record.measurement) == 0
                                    ),
                                    False,
                                )
                                if exact_measure_record:
                                    nearest_below_measure = exact_measure_record[
                                        0
                                    ].ullage
                                    nearest_above_measure = exact_measure_record[
                                        0
                                    ].ullage
                                else:
                                    nearest_below_measure = None
                                    nearest_above_measure = None
                                    for r in nearest_measure_records:
                                        if r.ullage < record.measurement:
                                            nearest_below_measure = r.ullage
                                        elif r.ullage > record.measurement:
                                            nearest_above_measure = r.ullage
                                        if (
                                            nearest_above_measure
                                            and nearest_below_measure
                                        ):
                                            break

                            nearest_heel_records = self.env[
                                "ship.sounding.table"
                            ].search([("sounding_book_id", "=", sounding_book.id)])
                            nearest_heel_records = sorted(
                                nearest_heel_records,
                                key=lambda r: abs(r.table_value - heel),
                            )

                            if nearest_heel_records:
                                exact_heel_record = self.env[
                                    "ship.sounding.table"
                                ].browse(
                                    [
                                        r.id
                                        for r in nearest_heel_records
                                        if abs(r.table_value - heel) == 0
                                    ]
                                )
                                if exact_heel_record:
                                    nearest_below_heel = exact_heel_record[
                                        0
                                    ].table_value
                                    nearest_above_heel = exact_heel_record[
                                        0
                                    ].table_value
                                else:
                                    nearest_below_heel = None
                                    nearest_above_heel = None
                                    for r in nearest_heel_records:
                                        if r.table_value < heel:
                                            nearest_below_heel = r.table_value
                                        elif r.table_value > heel:
                                            nearest_above_heel = r.table_value
                                        if nearest_below_heel and nearest_above_heel:
                                            break

                            ## find 4 point

                            low_low_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("ullage", "=", nearest_below_measure),
                                        ("table_value", "=", nearest_below_heel),
                                    ]
                                )
                                .volume
                            )
                            high_low_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("ullage", "=", nearest_above_measure),
                                        ("table_value", "=", nearest_below_heel),
                                    ]
                                )
                                .volume
                            )
                            low_high_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("ullage", "=", nearest_below_measure),
                                        ("table_value", "=", nearest_above_heel),
                                    ]
                                )
                                .volume
                            )
                            high_high_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("ullage", "=", nearest_above_measure),
                                        ("table_value", "=", nearest_above_heel),
                                    ]
                                )
                                .volume
                            )
                            try:
                                if nearest_above_measure != nearest_below_measure:
                                    heel_low_volume = low_low_volume + (
                                        record.measurement - nearest_below_measure
                                    ) * (high_low_volume - low_low_volume) / (
                                        nearest_above_measure - nearest_below_measure
                                    )
                                    heel_high_volume = low_high_volume + (
                                        record.measurement - nearest_below_measure
                                    ) * (high_high_volume - low_high_volume) / (
                                        nearest_above_measure - nearest_below_measure
                                    )
                                else:
                                    heel_low_volume = (
                                        low_low_volume + high_low_volume
                                    ) / 2
                                    heel_high_volume = (
                                        low_high_volume + high_high_volume
                                    ) / 2

                                if nearest_above_heel != nearest_below_heel:
                                    final_heel_volume = heel_low_volume + (
                                        heel - nearest_below_heel
                                    ) * (heel_high_volume - heel_low_volume) / (
                                        nearest_above_heel - nearest_below_heel
                                    )
                                else:
                                    final_heel_volume = (
                                        heel_low_volume + heel_high_volume
                                    ) / 2
                            except:
                                final_heel_volume = 0

                    total_volume = final_heel_volume + final_trim_volume

                else:
                    search_criteria_trim = search_criteria + [
                        ("table_type", "=", "trim")
                    ]
                    sounding_trim_books = self.env["ship.sounding.book"].search(
                        search_criteria_trim
                    )
                    for sounding_book in sounding_trim_books:
                        sounding_table_records = self.env["ship.sounding.table"].search(
                            [
                                ("sounding_book_id", "=", sounding_book.id),
                                ("sound", "=", record.measurement),
                                ("table_value", "=", trim),
                            ]
                        )
                        final_trim_volume = sum(sounding_table_records.mapped("volume"))

                        if not sounding_table_records:
                            # If no records found for provided measurement, find the two nearest trim values
                            nearest_measure_records = self.env[
                                "ship.sounding.table"
                            ].search([("sounding_book_id", "=", sounding_book.id)])
                            nearest_measure_records = sorted(
                                nearest_measure_records,
                                key=lambda r: abs(r.sound - record.measurement),
                            )
                            if nearest_measure_records:
                                exact_measure_record = next(
                                    (
                                        r
                                        for r in nearest_measure_records
                                        if abs(r.sound - record.measurement) == 0
                                    ),
                                    False,
                                )
                                if exact_measure_record:
                                    nearest_below_measure = exact_measure_record[
                                        0
                                    ].sound
                                    nearest_above_measure = exact_measure_record[
                                        0
                                    ].sound
                                else:
                                    nearest_below_measure = None
                                    nearest_above_measure = None
                                    for r in nearest_measure_records:
                                        if r.sound < record.measurement:
                                            nearest_below_measure = r.sound
                                        elif r.sound > record.measurement:
                                            nearest_above_measure = r.sound
                                        if (
                                            nearest_below_measure
                                            and nearest_above_measure
                                        ):
                                            break

                            nearest_trim_records = self.env[
                                "ship.sounding.table"
                            ].search([("sounding_book_id", "=", sounding_book.id)])
                            nearest_trim_records = sorted(
                                nearest_trim_records,
                                key=lambda r: abs(r.table_value - trim),
                            )

                            if nearest_trim_records:
                                exact_trim_record = self.env[
                                    "ship.sounding.table"
                                ].browse(
                                    [
                                        r.id
                                        for r in nearest_trim_records
                                        if abs(r.table_value - trim) == 0
                                    ]
                                )
                                if exact_trim_record:
                                    nearest_below_trim = exact_trim_record[
                                        0
                                    ].table_value
                                    nearest_above_trim = exact_trim_record[
                                        0
                                    ].table_value
                                else:
                                    nearest_below_trim = None
                                    nearest_above_trim = None
                                    for r in nearest_trim_records:
                                        if r.table_value < trim:
                                            nearest_below_trim = r.table_value
                                        elif r.table_value > trim:
                                            nearest_above_trim = r.table_value
                                        if nearest_below_trim and nearest_above_trim:
                                            break

                            ## find 4 point

                            low_low_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("sound", "=", nearest_below_measure),
                                        ("table_value", "=", nearest_below_trim),
                                    ]
                                )
                                .volume
                            )
                            high_low_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("sound", "=", nearest_above_measure),
                                        ("table_value", "=", nearest_below_trim),
                                    ]
                                )
                                .volume
                            )
                            low_high_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("sound", "=", nearest_below_measure),
                                        ("table_value", "=", nearest_above_trim),
                                    ]
                                )
                                .volume
                            )
                            high_high_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("sound", "=", nearest_above_measure),
                                        ("table_value", "=", nearest_above_trim),
                                    ]
                                )
                                .volume
                            )
                            try:
                                if nearest_above_measure != nearest_below_measure:
                                    trim_low_volume = low_low_volume + (
                                        record.measurement - nearest_below_measure
                                    ) * (high_low_volume - low_low_volume) / (
                                        nearest_above_measure - nearest_below_measure
                                    )
                                    trim_high_volume = low_high_volume + (
                                        record.measurement - nearest_below_measure
                                    ) * (high_high_volume - low_high_volume) / (
                                        nearest_above_measure - nearest_below_measure
                                    )

                                else:
                                    trim_low_volume = (
                                        low_low_volume + high_low_volume
                                    ) / 2
                                    trim_high_volume = (
                                        low_high_volume + high_high_volume
                                    ) / 2

                                if nearest_above_trim != nearest_below_trim:
                                    final_trim_volume = trim_low_volume + (
                                        trim - nearest_below_trim
                                    ) * (trim_high_volume - trim_low_volume) / (
                                        nearest_above_trim - nearest_below_trim
                                    )
                                else:
                                    final_trim_volume = (
                                        trim_low_volume + trim_high_volume
                                    ) / 2
                            except:
                                final_trim_volume = 0

                    # Search for sounding records based on heel
                    search_criteria_heel = search_criteria + [
                        ("table_type", "=", "heel")
                    ]
                    sounding_heel_books = self.env["ship.sounding.book"].search(
                        search_criteria_heel
                    )
                    for sounding_book in sounding_heel_books:
                        sounding_table_records = self.env["ship.sounding.table"].search(
                            [
                                ("sounding_book_id", "=", sounding_book.id),
                                ("sound", "=", record.measurement),
                                ("table_value", "=", heel),
                            ]
                        )
                        final_heel_volume = sum(sounding_table_records.mapped("volume"))
                        if not sounding_table_records:
                            # If no records found for provided measurement, find the two nearest heel values
                            nearest_measure_records = self.env[
                                "ship.sounding.table"
                            ].search([("sounding_book_id", "=", sounding_book.id)])
                            nearest_measure_records = sorted(
                                nearest_measure_records,
                                key=lambda r: abs(r.sound - record.measurement),
                            )

                            if nearest_measure_records:
                                exact_measure_record = next(
                                    (
                                        r
                                        for r in nearest_measure_records
                                        if abs(r.sound - record.measurement) == 0
                                    ),
                                    False,
                                )
                                if exact_measure_record:
                                    nearest_below_measure = exact_measure_record[
                                        0
                                    ].sound
                                    nearest_above_measure = exact_measure_record[
                                        0
                                    ].sound
                                else:
                                    nearest_below_measure = None
                                    nearest_above_measure = None
                                    for r in nearest_measure_records:
                                        if r.sound < record.measurement:
                                            nearest_below_measure = r.sound
                                        elif r.sound > record.measurement:
                                            nearest_above_measure = r.sound
                                        if (
                                            nearest_above_measure
                                            and nearest_below_measure
                                        ):
                                            break

                            nearest_heel_records = self.env[
                                "ship.sounding.table"
                            ].search([("sounding_book_id", "=", sounding_book.id)])
                            nearest_heel_records = sorted(
                                nearest_heel_records,
                                key=lambda r: abs(r.table_value - heel),
                            )

                            if nearest_heel_records:
                                exact_heel_record = self.env[
                                    "ship.sounding.table"
                                ].browse(
                                    [
                                        r.id
                                        for r in nearest_heel_records
                                        if abs(r.table_value - heel) == 0
                                    ]
                                )
                                if exact_heel_record:
                                    nearest_below_heel = exact_heel_record[
                                        0
                                    ].table_value
                                    nearest_above_heel = exact_heel_record[
                                        0
                                    ].table_value
                                else:
                                    nearest_below_heel = None
                                    nearest_above_heel = None
                                    for r in nearest_heel_records:
                                        if r.table_value < heel:
                                            nearest_below_heel = r.table_value
                                        elif r.table_value > heel:
                                            nearest_above_heel = r.table_value
                                        if nearest_below_heel and nearest_above_heel:
                                            break

                            ## find 4 point

                            low_low_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("sound", "=", nearest_below_measure),
                                        ("table_value", "=", nearest_below_heel),
                                    ]
                                )
                                .volume
                            )
                            high_low_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("sound", "=", nearest_above_measure),
                                        ("table_value", "=", nearest_below_heel),
                                    ]
                                )
                                .volume
                            )
                            low_high_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("sound", "=", nearest_below_measure),
                                        ("table_value", "=", nearest_above_heel),
                                    ]
                                )
                                .volume
                            )
                            high_high_volume = (
                                self.env["ship.sounding.table"]
                                .search(
                                    [
                                        ("sounding_book_id", "=", sounding_book.id),
                                        ("sound", "=", nearest_above_measure),
                                        ("table_value", "=", nearest_above_heel),
                                    ]
                                )
                                .volume
                            )
                            try:
                                if nearest_above_measure != nearest_below_measure:
                                    heel_low_volume = low_low_volume + (
                                        record.measurement - nearest_below_measure
                                    ) * (high_low_volume - low_low_volume) / (
                                        nearest_above_measure - nearest_below_measure
                                    )
                                    heel_high_volume = low_high_volume + (
                                        record.measurement - nearest_below_measure
                                    ) * (high_high_volume - low_high_volume) / (
                                        nearest_above_measure - nearest_below_measure
                                    )
                                else:
                                    heel_low_volume = (
                                        low_low_volume + high_low_volume
                                    ) / 2
                                    heel_high_volume = (
                                        low_high_volume + high_high_volume
                                    ) / 2

                                if nearest_above_heel != nearest_below_heel:
                                    print(nearest_below_heel)
                                    print(nearest_above_heel)
                                    final_heel_volume = heel_low_volume + (
                                        heel - nearest_below_heel
                                    ) * (heel_high_volume - heel_low_volume) / (
                                        nearest_above_heel - nearest_below_heel
                                    )
                                else:
                                    final_heel_volume = (
                                        heel_low_volume + heel_high_volume
                                    ) / 2
                            except:
                                final_heel_volume = 0

                    total_volume = final_heel_volume + final_trim_volume

                record.volumetric_capacity = total_volume

            else:
                record.volumetric_capacity = 0.0

    @api.depends("temperature", "volumetric_capacity")
    def _compute_volumetric_at_150c(self):
        for record in self:
            if record.temperature >= 0 and record.volumetric_capacity:
                temperature_difference = record.temperature - 15
                expansion_factor = 1 - (temperature_difference * 0.00064)
                record.volumetric_at_150C = (
                    record.volumetric_capacity * expansion_factor
                )
            else:
                record.volumetric_at_150C = 0.0

    @api.depends("temperature")
    def _compute_expansion_factor(self):
        for record in self:
            temperature_difference = record.temperature - 15
            record.expansion_factor = 1 - (temperature_difference * 0.00064)

    @api.depends("volumetric_at_150C", "fuel_external_oil_tank_condition_id")
    def _compute_weight(self):
        for record in self:
            if record.volumetric_at_150C >= 0 and record.fuel_type:
                if (
                    record.fuel_type == "hfo"
                    and record.fuel_external_oil_tank_condition_id
                    and record.fuel_external_oil_tank_condition_id.density_hfo
                ):
                    record.weight = (
                        record.volumetric_at_150C
                        * record.fuel_external_oil_tank_condition_id.density_hfo
                    )
                elif (
                    record.fuel_type == "do"
                    and record.fuel_external_oil_tank_condition_id
                    and record.fuel_external_oil_tank_condition_id.density_do
                ):
                    record.weight = (
                        record.volumetric_at_150C
                        * record.fuel_external_oil_tank_condition_id.density_do
                    )
                else:
                    record.weight = 0.0
            else:
                record.weight = 0.0


class FuelOilSampleRecord(models.Model):
    _name = "ship.fuel.external.oil.sample.record"
    _description = "Fuel Oil Sample Record"

    # Additional fields
    datetime = fields.Datetime(string="Datetime", default=fields.Datetime.now)
    voyage_number = fields.Char(string="Voyage Number")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    fuel_oil_sample_locker_location = fields.Char(
        string="Fuel Oil Sample Locker Location"
    )
    vessel_flag = fields.Char(string="Vessel Flag")
    fuel_oil_analysis_company = fields.Char(string="Fuel Oil Analysis Company")
    fuel_external_receiving_id = fields.Many2one(
        "ship.fuel.external.receiving", string="Fuel External Receiving"
    )

    # Fields related to HFO
    hfo_date_of_bunker = fields.Date(string="Date of Bunker")
    hfo_location = fields.Char(string="Location")
    hfo_bunker_receipt_number = fields.Char(string="Bunker Delivery Receipt Number")
    hfo_sulphur_declared = fields.Float(string="Sulphur % Declared")
    hfo_sample_number = fields.Char(string="Fuel Oil Sample Number")
    hfo_fuel_seal_number = fields.Char(string="Fuel Seal Number")
    hfo_analysed_sulphur_content = fields.Float(string="Analysed Sulphur Content %")

    # Fields related to MDO
    mdo_date_of_bunker = fields.Date(string="Date of Bunker")
    mdo_location = fields.Char(string="Location")
    mdo_bunker_receipt_number = fields.Char(string="Bunker Delivery Receipt Number")
    mdo_sulphur_declared = fields.Float(string="Sulphur % Declared")
    mdo_sample_number = fields.Char(string="Fuel Oil Sample Number")
    mdo_fuel_seal_number = fields.Char(string="Fuel Seal Number")
    mdo_analysed_sulphur_content = fields.Float(string="Analysed Sulphur Content %")


class Bunker(models.Model):
    _name = "ship.fuel.external.bunker.barge"
    _description = "Bunker Transfer Barge"

    fuel_type = fields.Selection([("HFO", "HFO"), ("MDO", "MDO")], string="Fuel Type")

    grade = fields.Char(string="Grade")

    weight_tonnes = fields.Float(string="Weight (Tonnes)")

    volume_loading_temp = fields.Float(string="Volume of Oil at Loading Temperature")

    loading_temperature = fields.Float(string="Loading Temperature")

    max_transfer_rate = fields.Float(string="Maximum Transfer Rate")

    max_line_pressure = fields.Float(string="Maximum Line Pressure")

    fuel_external_receiving_id = fields.Many2one(
        "ship.fuel.external.receiving", string="Fuel External Receiving"
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
