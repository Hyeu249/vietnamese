# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class ErtRoleModel(models.Model):
    _name = "legis.ert.role.meta"
    _description = "Ert role meta records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    # relations
    user_id = fields.Many2one(
        "res.users",
        string="User",
        tracking=True,
    )
    handbook_section_id = fields.Many2one(
        "legis.handbook.section",
        string="Handbook section",
        tracking=True,
    )
    ert_role_task_meta_ids = fields.One2many(
        "legis.ert.role.task.meta",
        "ert_role_meta_id",
        string="Ert role task meta",
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
            model_name = "legis.ert.role.meta"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(ErtRoleModel, self).create(vals_list)

        return result

    def name_get(self):
        result = []
        for report in self:
            group_name = report.user_id.name
            name = group_name + "(" + report.ref + ")" if group_name else _("New")
            result.append((report.id, name))
        return result
