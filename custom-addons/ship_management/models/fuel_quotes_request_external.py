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


class FuelQuotesRequestExternal(models.Model):
    _name = "ship.fuel.quotes.request.external"
    _description = "Yêu cầu dầu quốc tế"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    order_date = fields.Date("Order date", tracking=True)
    expected_delivery_date = fields.Date("Expected delivery date", tracking=True)
    deadline = fields.Date("Deadline", tracking=True)

    fuel_external_calculator_id = fields.Many2one(
        "ship.fuel.external.calculator", string="Fuel external calculator"
    )
    external_bunker_request_mt_fo = fields.Float(
        string="External Bunker Request F.O (MT)",
        related="fuel_external_calculator_id.bunker_request_mt_fo",
    )
    external_bunker_request_mt_do = fields.Float(
        string="External Bunker Request D.O (MT)",
        related="fuel_external_calculator_id.bunker_request_mt_do",
    )
    external_order_remaining_mt_fo=fields.Float(
        string="External Bunker Remaining F.O (MT) At Order",
        compute="_compute_external_order_remaining_mt_fo"
        
    )
    external_order_remaining_mt_do=fields.Float(
        string="External Bunker Remaining D.O (MT) At Order",
        compute="_compute_external_order_remaining_mt_do"
    )

    external_bunker_remaining_mt_fo=fields.Float(
        string="External Bunker Remaining F.O (MT) At Bunkering Port",
        related="fuel_external_calculator_id.remaining_oil_bunk_port_mt_fo",
    )
    external_bunker_remaining_mt_do=fields.Float(
        string="External Bunker Remaining D.O (MT) At Bunkering Port",
        related="fuel_external_calculator_id.remaining_oil_bunk_port_mt_do",
    )

    port_id = fields.Many2one("ship.port", string="Port")
    fuel_quote_external_ids = fields.One2many(
        "ship.fuel.quote.external",
        "fuel_quote_request_external_id",
        string="Fuel Quote External",
    )

    arrival_time = fields.Datetime(string="Arrival Time")
    departure_time = fields.Datetime(string="Departure Time")

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))
    receipt = fields.Image("Receipt", tracking=True,
                           max_width=CONST.MAX_IMAGE_UPLOAD_WIDTH,
                           max_height=CONST.MAX_IMAGE_UPLOAD_HEIGHT)



    @api.depends('fuel_external_calculator_id.remaining_oil_serv_tank_fo', 
             'fuel_external_calculator_id.remaining_oil_other_tanks_fo')
    def _compute_external_order_remaining_mt_fo(self):
        for record in self:
            if record.fuel_external_calculator_id:
                record.external_order_remaining_mt_fo = (
                    record.fuel_external_calculator_id.remaining_oil_serv_tank_fo +
                    record.fuel_external_calculator_id.remaining_oil_other_tanks_fo
                )
            else:
                record.external_order_remaining_mt_fo = 0.0
    @api.depends('fuel_external_calculator_id.remaining_oil_serv_tank_do', 
             'fuel_external_calculator_id.remaining_oil_other_tanks_do')
    def _compute_external_order_remaining_mt_do(self):
        for record in self:
            if record.fuel_external_calculator_id:
                record.external_order_remaining_mt_do = (
                    record.fuel_external_calculator_id.remaining_oil_serv_tank_do +
                    record.fuel_external_calculator_id.remaining_oil_other_tanks_do
                )
            else:
                record.external_order_remaining_mt_do = 0.0



    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "ship.fuel.quotes.request.external"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(FuelQuotesRequestExternal, self).create(vals_list)
        for record in result:
            external_fo = record.external_bunker_request_mt_fo
            external_do = record.external_bunker_request_mt_do
            if external_fo and external_do:
                record._create_fuel_quote("fo", external_fo)
                record._create_fuel_quote("do", external_do)
        return result

    def _create_fuel_quote(self, name, quantity):
        self.ensure_one()
        self.env["ship.fuel.quote.external"].create(
            {
                "name": name,
                "quantity": quantity,
                "unit": "MT",
                "fuel_quote_request_external_id": self.id,
            }
        )

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def write(self, vals):
        self.ensure_one()
        result = super(FuelQuotesRequestExternal, self).write(vals)
        return result

    def _handle_removed_fuel_quotes_external(self, removed_ids):
        self.ensure_one()
        for id in removed_ids:
            fuel_quote_external_id = self.fuel_quote_external_ids.browse(id)
            fuel_quote_external_id.fuel_quote_request_external_id = False

    def _handle_added_fuel_quotes_external(self, added_ids):
        self.ensure_one()
        for id in added_ids:
            fuel_quote_external_id = self.fuel_quote_external_ids.browse(id)
            fuel_quote_external_id.fuel_quote_request_external_id = self.id


class FuelQuoteExternal(models.Model):
    _name = "ship.fuel.quote.external"
    _description = "Fuel Quote External"
    FUEL_TYPES = [
        ("fo", "FO"),
        ("do", "DO"),
        ("texmarine_700_sae_50", "Texmarine 700 SAE 50"),
        ("texmarine_60_sae_30", "Texmarine 60 SAE 30"),
        ("texmarine_300_sae_40", "Texmarine 300 SAE 40"),
        ("texas_texfrige_as68", "Texas Texfrige AS68"),
        ("texas_turbine_t_series", "Texas Turbine T Series"),
        ("texas_texgear_100", "Texas Texgear 100"),
        ("texas_texgear_220", "Texas Texgear 220"),
        ("texas_compressor", "Texas Compressor"),
        ("texas_hydraulic_hs68", "Texas Hydraulic HS68"),
        ("ep_lithium_complex_grease_nlgi2", "EP Lithium Complex Grease NLGI2"),
    ]
    description = fields.Char("Description", tracking=True)
    name = fields.Selection(selection=FUEL_TYPES, string="Fuel Name", required=True)

    quantity = fields.Float("Quantity")
    unit = fields.Selection(
        selection=[("LÍT", "LÍT"), ("MT", "MT"), ("KG", "KG")],
        string="Unit",
        required=True,
    )
    price_per_unit = fields.Float("Price per Unit")

    fuel_quote_request_external_id = fields.Many2one(
        "ship.fuel.quotes.request.external", string="Fuel Quote Request External"
    )

    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    quantity_received = fields.Float("Quantity Received", tracking=True)

    @api.depends("name")
    def _compute_full_name(self):
        for record in self:
            # Find the full name in the FUEL_TYPES list by the key
            full_name = dict(self.FUEL_TYPES).get(record.name, "")
            record.full_name = full_name

    full_name = fields.Char(
        compute="_compute_full_name", string="Full Fuel Name", store=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.fuel.quote.external"
            )
        result = super(FuelQuoteExternal, self).create(vals_list)
        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
