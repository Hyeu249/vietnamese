# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class ErtRoleTaskModel(models.Model):
    _name = "legis.ert.role.task.meta"
    _description = "Ert role task meta records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)

    # relations
    ert_role_meta_id = fields.Many2one(
        "legis.ert.role.meta",
        string="Ert role meta",
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
            model_name = "legis.ert.role.task.meta"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(ErtRoleTaskModel, self).create(vals_list)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
