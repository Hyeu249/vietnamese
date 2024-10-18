# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class Classify(models.Model):
    _name = "ship.classify"
    _description = "Classify records"
    _inherit = ["mail.thread"]

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_name",
            "unique (name)",
            "name must be unique.",
        ),
    ]

    # relations
    supplier_ids = fields.Many2many("ship.supplier", string="Supplier", tracking=True)

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.classify")
        return super(Classify, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
