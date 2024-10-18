# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class ChecklistValue(models.Model):
    _name = "ship.checklist.value"
    _description = "Check box records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    name = fields.Text("Name", tracking=True)
    yes_no = fields.Selection(
        CONST.CHECKLIST_YES_NO,
        string="yes/no",
        tracking=True,
    )
    answer = fields.Text("Answer", tracking=True)
    attachment = fields.Binary("Attachment", tracking=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.checklist.value")
        return super(ChecklistValue, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
