# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from . import CONST


class RequiredAllApprovalFlow(models.Model):
    _name = "utilities.required.all.approval.flow"
    _description = "Required all approval flow records"
    _inherit = ["utilities.notification"]

    model_name = fields.Char(string="Model name", tracking=True)
    user_ids = fields.Many2many(
        "res.users",
        string="Users",
        tracking=True,
    )

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_model_name",
            "unique (model_name)",
            "model_name must be unique.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        result = super(RequiredAllApprovalFlow, self).create(vals_list)
        return result
