# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class SeriousAccident(models.Model):
    _name = "legis.serious.accident"
    _description = "Serious accident records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char(string="Name", tracking=True)
    description = fields.Html("Description", tracking=True)

    # relations

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.serious.accident"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(SeriousAccident, self).create(vals_list)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
