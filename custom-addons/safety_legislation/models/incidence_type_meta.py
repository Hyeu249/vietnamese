# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class Incidence_type_meta(models.Model):
    _name = "legis.incidence.type.meta"
    _description = "Incidence type meta records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    content = fields.Html("Content", tracking=True)

    # relations
    handbook_section_id = fields.Many2one(
        "legis.handbook.section",
        string="Handbook section",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.incidence.type.meta"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(Incidence_type_meta, self).create(vals_list)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
