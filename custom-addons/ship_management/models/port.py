# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class Port(models.Model):
    _name = "ship.port"
    _description = "port records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)
    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    assigned_group = fields.Char("Assigned group", tracking=True)

    # relations
    supplier_id = fields.Many2one(
        "ship.supplier",
        string="Supplier",
        tracking=True,
    )
    fuel_quote_request_id = fields.One2many(
        "ship.fuel.quotes.request", "port_id", string="Fuel Quote Request"
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.port")
        return super(Port, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
