# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
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


_logger = logging.getLogger(__name__)


class FuelInternalCalculator(models.Model):
    _name = "ship.fuel.internal.calculator"
    _description = "Bảng tính cấp nhiên liệu nội địa"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    order_date = fields.Datetime("Order date", tracking=True)
    hfo_density = fields.Float(
        string="Density H.F.O (Tỷ trọng 15°C)",
        help="Density of H.F.O at 15°C",
        default=1,
        digits=(10, 4),
    )
    do_density = fields.Float(
        string="Density D.O (Tỷ trọng 15°C)",
        help="Density of D.O at 15°C",
        default=1,
        digits=(10, 4),
    )

    sailing_days = fields.Integer(string="Sailing Days")
    stopping_days = fields.Integer(string="Stopping Days")

    # Tank Capacity Levels for Fuel Oil (F.O)
    tank_capacity_fo_100 = fields.Float(
        string="F.O Tank Capacity (100%) (m3)",
        default=1066.2,
        readonly=True,
        digits=(10, 3),
    )
    tank_capacity_fo_90 = fields.Float(
        string="F.O Tank Capacity (90%) (m3)",
        default=959.6,
        readonly=True,
        digits=(10, 3),
    )
    tank_capacity_fo_85 = fields.Float(
        string="F.O Tank Capacity (85%) (m3)",
        default=906.3,
        readonly=True,
        digits=(10, 3),
    )
    tank_capacity_fo_80 = fields.Float(
        string="F.O Tank Capacity (80%) (m3)",
        default=852.9,
        readonly=True,
        digits=(10, 3),
    )

    # Tank Capacity Levels for Diesel Oil (D.O)
    tank_capacity_do_100 = fields.Float(
        string="D.O Tank Capacity (100%) (m3)",
        default=129.9,
        readonly=True,
        digits=(10, 3),
    )
    tank_capacity_do_90 = fields.Float(
        string="D.O Tank Capacity (90%) (m3)",
        default=116.9,
        readonly=True,
        digits=(10, 3),
    )
    tank_capacity_do_85 = fields.Float(
        string="D.O Tank Capacity (85%) (m3)",
        default=110.4,
        readonly=True,
        digits=(10, 3),
    )
    tank_capacity_do_80 = fields.Float(
        string="D.O Tank Capacity (80%) (m3)",
        default=103.9,
        readonly=True,
        digits=(10, 3),
    )

    sailing_days = fields.Integer(string="Sailing Days")
    stopping_days = fields.Integer(string="Stopping Days")

    # Estimation of Remaining Oil for Fuel Oil (F.O)
    expected_arrival_date = fields.Date(string="Expected Arrival Date")
    remaining_oil_serv_tank_fo = fields.Float(
        string="Remaining F.O Oil in Sett./Serv. Tank (MT)", digits=(10, 3)
    )
    remaining_oil_serv_tank_do = fields.Float(
        string="Remaining D.O Oil in Sett./Serv. Tank (MT)", digits=(10, 3)
    )

    # Estimation of Remaining Oil in Other Tanks for Fuel Oil (F.O)
    remaining_oil_other_tanks_fo = fields.Float(
        string="Remaining F.O Oil in Other Tanks (MT)", digits=(10, 3)
    )
    remaining_oil_other_tanks_do = fields.Float(
        string="Remaining D.O Oil in Other Tanks (MT)", digits=(10, 3)
    )

    # #Consumtiton to Bunk Port
    consumption_to_bunk_port_mt_fo = fields.Float(
        string="Consumption to Bunkering Port F.O (MT)",
        compute="_compute_consumption_to_bunk_port_mt_fo",
        digits=(10, 3),
    )
    consumption_to_bunk_port_mt_do = fields.Float(
        string="Consumption to Bunkering Port D.O (MT)",
        compute="_compute_consumption_to_bunk_port_mt_do",
        digits=(10, 3),
    )

    me_consumption_fo = fields.Float(
        string="M/E Consumption F.O (MT/Day)",
        compute="_compute_me_consumption_fo",
        digits=(10, 3),
    )
    me_consumption_do = fields.Float(
        string="M/E Consumption D.O (MT/Day)", default=0, digits=(10, 3)
    )

    boiler_consumption_fo = fields.Float(
        string="Boiler Consumption F.O (MT/Day)",
        compute="_compute_boiler_consumption_fo",
        digits=(10, 3),
    )
    boiler_consumption_do = fields.Float(
        string="Boiler Consumption D.O (MT/Day)", default=0, digits=(10, 3)
    )

    ge_consumption_sailing_ship_fo = fields.Float(
        string="G/E Consumption - Sailing Ship F.O (MT/Day)",
        compute="_compute_ge_consumption_sailing_ship_fo",
        digits=(10, 3),
    )
    ge_consumption_stopping_ship_fo = fields.Float(
        string="G/E Consumption - Stopping Ship F.O (MT/Day)",
        compute="_compute_ge_consumption_stopping_ship_fo",
        digits=(10, 3),
    )

    ge_consumption_sailing_ship_do = fields.Float(
        string="G/E Consumption - Sailing Ship D.O (MT/Day)", default=0, digits=(10, 3)
    )
    ge_consumption_stopping_ship_do = fields.Float(
        string="G/E Consumption - Stopping Ship D.O (MT/Day)", default=0, digits=(10, 3)
    )

    remaining_oil_bunk_port_mt_fo = fields.Float(
        string="Remaining Oil at Bunkering Port F.O (MT)",
        compute="_compute_remaining_oil_bunk_port_mt_fo",
        digits=(10, 3),
    )
    remaining_oil_bunk_port_mt_do = fields.Float(
        string="Remaining Oil at Bunkering Port D.O (MT)",
        compute="_compute_remaining_oil_bunk_port_mt_do",
        digits=(10, 3),
    )

    # Estimation of Bunkering Quantity
    bunkering_quantity_90_percent_fo = fields.Float(
        string="Bunkering Quantity (90% Filling) F.O (m3)",
        compute="_compute_bunkering_quantity_90_percent_fo",
        digits=(10, 3),
    )
    bunkering_quantity_85_percent_fo = fields.Float(
        string="Bunkering Quantity (85% Filling) F.O (m3)",
        compute="_compute_bunkering_quantity_85_percent_fo",
        digits=(10, 3),
    )
    bunkering_quantity_80_percent_fo = fields.Float(
        string="Bunkering Quantity (80% Filling) F.O (m3)",
        compute="_compute_bunkering_quantity_80_percent_fo",
        digits=(10, 3),
    )
    reasonable_quantity_fo = fields.Float(
        string="Reasonable Quantity F.O (MT)",
        compute="_compute_reasonable_quantity_fo",
        digits=(10, 3),
    )

    bunkering_quantity_90_percent_do = fields.Float(
        string="Bunkering Quantity (90% Filling) D.O (m3)",
        compute="_compute_bunkering_quantity_90_percent_do",
        digits=(10, 3),
    )
    bunkering_quantity_85_percent_do = fields.Float(
        string="Bunkering Quantity (85% Filling) D.O (m3)",
        compute="_compute_bunkering_quantity_85_percent_do",
        digits=(10, 3),
    )
    bunkering_quantity_80_percent_do = fields.Float(
        string="Bunkering Quantity (80% Filling) D.O (m3)",
        compute="_compute_bunkering_quantity_80_percent_do",
        digits=(10, 3),
    )
    reasonable_quantity_do = fields.Float(
        string="Reasonable Quantity D.O (MT)",
        compute="_compute_reasonable_quantity_do",
        digits=(10, 3),
    )

    # Requisition

    # Bunker Request and Filling Percentage for Fuel Oil (F.O)
    bunker_request_mt_fo = fields.Float(
        string="Bunker Request F.O (MT)", digits=(10, 3)
    )
    filling_percentage_fo = fields.Float(
        string="Filling Percentage F.O (%)",
        compute="_compute_filling_percentage_fo",
        digits=(10, 3),
    )

    # Bunker Request and Filling Percentage for Diesel Oil (D.O)
    bunker_request_mt_do = fields.Float(
        string="Bunker Request D.O (MT)", digits=(10, 3)
    )
    filling_percentage_do = fields.Float(
        string="Filling Percentage D.O (%)",
        compute="_compute_filling_percentage_do",
        digits=(10, 3),
    )

    ref = fields.Char(string="Code", default=lambda self: _("New"))

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    def find_or_create_fuel_request(self):
        self.ensure_one()
        fuel_request_id = self._find_or_create_fuel_request()
        return {
            "type": "ir.actions.act_window",
            "res_model": "ship.fuel.quotes.request",
            "view_mode": "form",
            "res_id": fuel_request_id.id,
            "target": "current",
            "context": self.env.context,
        }

    def _find_or_create_fuel_request(self):
        self.ensure_one()
        request_env = self.env["ship.fuel.quotes.request"]
        request = request_env.search(
            [("fuel_internal_calculator_id", "=", self.id)], limit=1
        )

        if request:
            return request
        else:
            return self.env["ship.fuel.quotes.request"].create(
                {"fuel_internal_calculator_id": self.id}
            )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "ship.fuel.internal.calculator"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)

        return super(FuelInternalCalculator, self).create(vals_list)

    def name_get(self):
        # Your name_get logic here
        return super(FuelInternalCalculator, self).name_get()

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def write(self, vals):
        # Your write logic here
        result = super(FuelInternalCalculator, self).write(vals)

        if "approval_status" in vals:
            if self.is_at_this_approval_level(CONST.CAPTAIN):
                # Send notification to captain
                self.send_notification_threshold(
                    fuel_type="HFO", current_value=self.bunker_request_mt_fo
                )
                self.send_notification_threshold(
                    fuel_type="DO", current_value=self.bunker_request_mt_do
                )

        return result

    @api.depends("sailing_days")
    def _compute_me_consumption_fo(self):
        for record in self:
            record.me_consumption_fo = 16.2 * record.sailing_days

    @api.depends("stopping_days")
    def _compute_boiler_consumption_fo(self):
        for record in self:
            record.boiler_consumption_fo = 1.5 * record.stopping_days

    @api.depends("sailing_days")
    def _compute_ge_consumption_sailing_ship_fo(self):
        for record in self:
            record.ge_consumption_sailing_ship_fo = 1.3 * record.sailing_days

    @api.depends("stopping_days")
    def _compute_ge_consumption_stopping_ship_fo(self):
        for record in self:
            record.ge_consumption_stopping_ship_fo = 1.4 * record.stopping_days

    @api.depends(
        "me_consumption_fo",
        "boiler_consumption_fo",
        "ge_consumption_sailing_ship_fo",
        "ge_consumption_stopping_ship_fo",
    )
    def _compute_consumption_to_bunk_port_mt_fo(self):
        for record in self:
            record.consumption_to_bunk_port_mt_fo = (
                record.me_consumption_fo
                + record.boiler_consumption_fo
                + record.ge_consumption_sailing_ship_fo
                + record.ge_consumption_stopping_ship_fo
            )

    @api.depends(
        "remaining_oil_serv_tank_fo",
        "remaining_oil_other_tanks_fo",
        "consumption_to_bunk_port_mt_fo",
    )
    def _compute_remaining_oil_bunk_port_mt_fo(self):
        for record in self:
            record.remaining_oil_bunk_port_mt_fo = (
                record.remaining_oil_serv_tank_fo
                + record.remaining_oil_other_tanks_fo
                - record.consumption_to_bunk_port_mt_fo
            )

    @api.depends(
        "me_consumption_do",
        "boiler_consumption_do",
        "ge_consumption_sailing_ship_do",
        "ge_consumption_stopping_ship_do",
    )
    def _compute_consumption_to_bunk_port_mt_do(self):
        for record in self:
            record.consumption_to_bunk_port_mt_do = (
                record.me_consumption_do
                + record.boiler_consumption_do
                + record.ge_consumption_sailing_ship_do
                + record.ge_consumption_stopping_ship_do
            )

    @api.depends(
        "remaining_oil_serv_tank_do",
        "remaining_oil_other_tanks_do",
        "consumption_to_bunk_port_mt_do",
    )
    def _compute_remaining_oil_bunk_port_mt_do(self):
        for record in self:
            record.remaining_oil_bunk_port_mt_do = (
                record.remaining_oil_serv_tank_do
                + record.remaining_oil_other_tanks_do
                - record.consumption_to_bunk_port_mt_do
            )

    @api.depends("remaining_oil_bunk_port_mt_fo", "hfo_density")
    def _compute_bunkering_quantity_90_percent_fo(self):
        for record in self:
            bunkering_quantity_90_percent_fo = (
                record.tank_capacity_fo_90
                - record.remaining_oil_bunk_port_mt_fo / record.hfo_density
            )
            record.bunkering_quantity_90_percent_fo = bunkering_quantity_90_percent_fo

    @api.depends("remaining_oil_bunk_port_mt_fo", "hfo_density")
    def _compute_bunkering_quantity_85_percent_fo(self):
        for record in self:
            bunkering_quantity_85_percent_fo = (
                record.tank_capacity_fo_85
                - record.remaining_oil_bunk_port_mt_fo / record.hfo_density
            )
            record.bunkering_quantity_85_percent_fo = bunkering_quantity_85_percent_fo

    @api.depends("remaining_oil_bunk_port_mt_fo", "hfo_density")
    def _compute_bunkering_quantity_80_percent_fo(self):
        for record in self:
            bunkering_quantity_80_percent_fo = (
                record.tank_capacity_fo_80
                - record.remaining_oil_bunk_port_mt_fo / record.hfo_density
            )
            record.bunkering_quantity_80_percent_fo = bunkering_quantity_80_percent_fo

    @api.depends("remaining_oil_bunk_port_mt_do")
    def _compute_bunkering_quantity_90_percent_do(self):
        for record in self:
            bunkering_quantity_90_percent_do = (
                record.tank_capacity_do_90
                - record.remaining_oil_bunk_port_mt_do / record.do_density
            )
            record.bunkering_quantity_90_percent_do = bunkering_quantity_90_percent_do

    @api.depends("remaining_oil_bunk_port_mt_do")
    def _compute_bunkering_quantity_85_percent_do(self):
        for record in self:
            bunkering_quantity_85_percent_do = (
                record.tank_capacity_do_85
                - record.remaining_oil_bunk_port_mt_do / record.do_density
            )
            record.bunkering_quantity_85_percent_do = bunkering_quantity_85_percent_do

    @api.depends("remaining_oil_bunk_port_mt_do")
    def _compute_bunkering_quantity_80_percent_do(self):
        for record in self:
            bunkering_quantity_80_percent_do = (
                record.tank_capacity_do_80
                - record.remaining_oil_bunk_port_mt_do / record.do_density
            )
            record.bunkering_quantity_80_percent_do = bunkering_quantity_80_percent_do

    @api.depends("bunkering_quantity_85_percent_fo", "hfo_density")
    def _compute_reasonable_quantity_fo(self):
        for record in self:
            reasonable_quantity_fo = (
                record.bunkering_quantity_85_percent_fo * record.hfo_density
            )
            record.reasonable_quantity_fo = reasonable_quantity_fo

    @api.depends("bunkering_quantity_85_percent_do", "do_density")
    def _compute_reasonable_quantity_do(self):
        for record in self:
            reasonable_quantity_do = (
                record.bunkering_quantity_85_percent_do * record.do_density
            )
            record.reasonable_quantity_do = reasonable_quantity_do

    @api.depends("bunker_request_mt_fo", "hfo_density", "tank_capacity_fo_100")
    def _compute_filling_percentage_fo(self):
        for record in self:
            if record.hfo_density != 0 and record.tank_capacity_fo_100 != 0:
                filling_percentage_fo = (
                    (record.bunker_request_mt_fo / record.hfo_density)
                    / record.tank_capacity_fo_100
                    * 100
                )
                record.filling_percentage_fo = filling_percentage_fo
            else:
                record.filling_percentage_fo = 0.0

    @api.depends("bunker_request_mt_do", "do_density", "tank_capacity_do_100")
    def _compute_filling_percentage_do(self):
        for record in self:
            if record.do_density != 0 and record.tank_capacity_do_100 != 0:
                filling_percentage_do = (
                    (record.bunker_request_mt_do / record.do_density)
                    / record.tank_capacity_do_100
                    * 100
                )
                record.filling_percentage_do = filling_percentage_do
            else:
                record.filling_percentage_do = 0.0

    def send_notification_threshold(self, fuel_type="current_fo", current_value=100):
        channel = self.env["mail.channel"].search(
            [("name", "=", "Fuel Notifications")], limit=1
        )
        if channel:
            self._console_log(f"Channel found: {channel.name}")
            try:
                single_channel = channel[0]
                subject = "Fuel Threshold Alert"
                message = f"Nhiên liệu {fuel_type} cần được đặt thêm. Giá trị đề xuất: {current_value} MT"
                # Post a message in the channel
                single_channel.message_post(
                    body=message,
                    subject=subject,
                    message_type="comment",
                    subtype_xmlid="mail.mt_comment",
                )
                self._console_log(f"Sent")
            except:
                self._console_log(f"Fail")
        else:
            self._console_log("Channel not found")
            channel = self.env["mail.channel"].create(
                {
                    "name": "Fuel Notifications",
                    "description": "Notifications for Monthly Fuel Orders",
                    "channel_type": "channel",
                }
            )
            subject = "Fuel Threshold Alert"
            message = f"Nhiên liệu {fuel_type} cần được đặt thêm. Giá trị đề xuất: {current_value} MT "
            # Post a message in the channel
            channel.message_post(
                body=message,
                subject=subject,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )
