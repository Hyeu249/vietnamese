# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
import logging
from datetime import timedelta
from odoo.exceptions import ValidationError

    
class FuelQuote(models.Model):
    _name = "ship.fuel.quote"
    _description = "Fuel Quote"
    FUEL_TYPES = [
        ('fo', 'FO'),
        ('do', 'DO'),]
    name = fields.Selection(
        selection=FUEL_TYPES,
        string="Fuel Name",
        required=True
    )
    description = fields.Char("Description", tracking=True)

    quantity = fields.Float("Quantity")
    unit = fields.Selection(selection=[
        ('LÍT','LÍT'),('MT','MT'),('KG','KG')
    ],string="Unit", required=True)
    price_per_unit = fields.Float("Price per Unit")

    fuel_quote_request_id = fields.Many2one(
        "ship.fuel.quotes.request", 
        string="Fuel Quote Request"    )
        
    fuel_supplier_quote_ids = fields.One2many(
        "ship.fuel.supplier.quote",
        "fuel_quote_id",
        string="Fuel supplier quote",
        readonly=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    quantity_received = fields.Float("Quantity Received",tracking=True)

    @api.depends('name')
    def _compute_full_name(self):
            for record in self:
                # Find the full name in the FUEL_TYPES list by the key
                full_name = dict(self.FUEL_TYPES).get(record.name, '')
                record.full_name = full_name

    full_name = fields.Char(compute='_compute_full_name', string="Full Fuel Name", store=True)

    def unlink(self):
        if self.fuel_supplier_quote_ids:
            for record in self:
                self.env['ship.fuel.supplier.quote'].search([('fuel_quote_id', '=', record.id)]).unlink()
        return super(FuelQuote, self).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.fuel.quote"
            )
        result = super(FuelQuote, self).create(vals_list)
        return result
    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _create_fuel_supplier_quotes(self):
        self.ensure_one()

        port_id = self.fuel_quote_request_id.port_id
        self.env["ship.fuel.supplier.quote"].create(
            {
                "unit_price": 0,
                "fuel_quote_id": self.id,
                "supplier_id": port_id.supplier_id.id,
            }
        )


class FuelQuoteGrease(models.Model):
    _name = "ship.fuel.quote.grease"
    _description = "Fuel Quote Grease"

    FUEL_TYPES = [
        ('texmarine_700_sae_50', 'Texmarine 700 SAE 50'),
        ('texmarine_60_sae_30', 'Texmarine 60 SAE 30'),
        ('texmarine_300_sae_40', 'Texmarine 300 SAE 40'),
        ('texas_texfrige_as68', 'Texas Texfrige AS68'),
        ('texas_turbine_t_series', 'Texas Turbine T Series'),
        ('texas_texgear_100', 'Texas Texgear 100'),
        ('texas_texgear_220', 'Texas Texgear 220'),
        ('texas_compressor', 'Texas Compressor'),
        ('texas_hydraulic_hs68', 'Texas Hydraulic HS68'),
        ('ep_lithium_complex_grease_nlgi2', 'EP Lithium Complex Grease NLGI2'),
        ('turbine_t68','TURBINE T68'),
        ('texmarine_300_sae_30','TEXMARINE 300 SAE 30'),
        ('turbine_t_68','TURBINE T 68'),
        ('compressor_100','COMPRESSOR 100'),
        ('texgear_150','TEXTGEAR 150'),
        ('texgear_220','TEXTGEAR 220'),
        ('texgear_100','TEXTGEAR 100'),
        ('hydraulic_hs_68','HYDRAULIC HS68'),
        ('hydraulic_hs_46','HYDRAULIC HS46'),
        ('textfrige_68','TEXFRIGE 68'),
        ('textfrige_32','TEXFRIGE 32'),]
    name = fields.Selection(
        selection=FUEL_TYPES,
        string="Fuel Name",
        required=True
    )

    quantity = fields.Float("Quantity")
    unit = fields.Selection(selection=[
        ('LÍT','LÍT'),('MT','MT'),('KG','KG')
    ],string="Unit", required=True)
    price_per_unit = fields.Float("Price per Unit")

    fuel_quote_request_id = fields.Many2one(
        "ship.fuel.quotes.request", 
        string="Fuel Quote Request"    
    )
        
    grease_supplier_quote_ids = fields.One2many(
        "ship.fuel.supplier.quote.grease",
        "grease_quote_id",
        string="Grease supplier quote",
        readonly=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    quantity_received = fields.Float("Quantity Received",tracking=True)

    @api.depends('name')
    def _compute_full_name(self):
            for record in self:
                # Find the full name in the FUEL_TYPES list by the key
                full_name = dict(self.FUEL_TYPES).get(record.name, '')
                record.full_name = full_name

    full_name = fields.Char(compute='_compute_full_name', string="Full Fuel Name", store=True)

    def unlink(self):
        for record in self:
            # Delete all related fuel_supplier_quote records
            self.env['ship.fuel.supplier.quote.grease'].search([('grease_quote_id', '=', record.id)]).unlink()
        return super(FuelQuoteGrease, self).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.fuel.quote.grease"
            )
        result = super(FuelQuoteGrease, self).create(vals_list)
        return result
    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _create_fuel_supplier_quotes(self):
        self.ensure_one()

        port_id = self.fuel_quote_request_id.port_id
        self.env["ship.fuel.supplier.quote.grease"].create(
            {
                "unit_price": 0,
                "grease_quote_id": self.id,
                "supplier_id": port_id.supplier_id.id,
            }
        )