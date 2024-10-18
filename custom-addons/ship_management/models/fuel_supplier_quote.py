# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from .common_utils import generate_token, format_field_date
from . import CONST
import logging


class FuelSupplierQuote(models.Model):
    _name = "ship.fuel.supplier.quote"
    _description = "Fuel supplier quote records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    unit_price = fields.Float("Unit price", tracking=True)
    estimated_delivery_date = fields.Date("Estimated delivery date", tracking=True)
    note = fields.Text("Note", tracking=True)
    is_email_sent = fields.Boolean("Is email sent", default=False)
    is_responded = fields.Boolean("Is the supplier responded", default=False)
    quote_date = fields.Date("Quote date", tracking=True)
    port=fields.Char("Port", tracking=True)
    arrival_time= fields.Datetime(string='Arrival Time')
    departure_time= fields.Datetime(string='Departure Time')

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    # relations
    supplier_id = fields.Many2one("ship.supplier", string="Supplier", tracking=True)
    fuel_quote_id = fields.Many2one(
        "ship.fuel.quote", string="Fuel quote", tracking=True
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # an access_token is a unique string that is automatically generated for each quote.
    access_token = fields.Char("Access Token", default=lambda self: generate_token())

    @api.constrains("unit_price")
    def _set_quote_date(self):
        for record in self:
            if record.unit_price > 0:
                record.quote_date = fields.Date().today()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.fuel.supplier.quote"
            )
        result = super(FuelSupplierQuote, self).create(vals_list)


        return result

    def write(self, vals):
        result = super(FuelSupplierQuote, self).write(vals)

        for record in self:
            fuel_quote_request_id = (
                record.fuel_quote_id.fuel_quote_request_id
            )

        return result

    def unlink(self):
        for record in self:
            fuel_quote_request_id = (
                record.fuel_quote_id.fuel_quote_request_id
            )
            result = super(FuelSupplierQuote, record).unlink()
        return result

    def name_get(self):
        result = []
        for report in self:
            name = f"{report.ref}({report.supplier_id.name})" or _("New")
            result.append((report.id, name))
        return result


class GreaseSupplierQuote(models.Model):
    _name = "ship.fuel.supplier.quote.grease"
    _description = "Grease supplier quote records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    unit_price = fields.Float("Unit price", tracking=True)
    estimated_delivery_date = fields.Date("Estimated delivery date", tracking=True)
    note = fields.Text("Note", tracking=True)
    is_email_sent = fields.Boolean("Is email sent", default=False)
    is_responded = fields.Boolean("Is the supplier responded", default=False)
    quote_date = fields.Date("Quote date", tracking=True)
    port = fields.Char("Port", tracking=True)
    arrival_time = fields.Datetime(string='Arrival Time')
    departure_time = fields.Datetime(string='Departure Time')

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    # relations
    supplier_id = fields.Many2one("ship.supplier", string="Supplier", tracking=True)
    grease_quote_id = fields.Many2one(
        "ship.fuel.quote.grease", string="Grease quote", tracking=True
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # an access_token is a unique string that is automatically generated for each quote.
    access_token = fields.Char("Access Token", default=lambda self: generate_token())

    @api.constrains("unit_price")
    def _set_quote_date(self):
        for record in self:
            if record.unit_price > 0:
                record.quote_date = fields.Date().today()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.fuel.supplier.quote.grease"
            )
        result = super(GreaseSupplierQuote, self).create(vals_list)
        return result

    def write(self, vals):
        result = super(GreaseSupplierQuote, self).write(vals)
        for record in self:
            grease_quote_request_id = record.grease_quote_id.fuel_quote_request_id
        return result

    def unlink(self):
        for record in self:
            grease_quote_request_id = record.grease_quote_id.fuel_quote_request_id
            result = super(GreaseSupplierQuote, record).unlink()
        return True

    def name_get(self):
        result = []
        for report in self:
            name = f"{report.ref}({report.supplier_id.name})" or _("New")
            result.append((report.id, name))
        return result


  