# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from . import CONST


class RequiredAllApprovalGroup(models.Model):
    _name = "utilities.required.all.approval.group"
    _description = "Required all approval group records"
    _inherit = ["utilities.notification"]

    user_id = fields.Many2one(
        "res.users",
        string="User",
        tracking=True,
    )
    color = fields.Integer(string="Color", tracking=True)

    # relations
    this_all_approval_group_id = fields.Many2one(
        "utilities.this.all.approval.group",
        string="This all approval group",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        result = super(RequiredAllApprovalGroup, self).create(vals_list)
        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.user_id.name or _("New")
            result.append((report.id, name))
        return result
