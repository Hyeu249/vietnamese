# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MaterialUsageType(models.Model):
    _name = "ship.material.usage.type"
    _description = "Material usage type records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)
    min_life_span_hours = fields.Integer("Min life span in hours", tracking=True)
    max_life_span_hours = fields.Integer("Max life span in hours", tracking=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.material.usage.type"
            )
        return super(MaterialUsageType, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
