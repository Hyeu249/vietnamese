# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import logging


class ApprovalLevelOrdering(models.Model):
    _name = "utilities.approval.level.ordering"
    _description = "Approval level ordering records"
    ordering = fields.Integer("Ordering")

    # relations
    approval_level_id = fields.Many2one(
        "utilities.approval.level",
    )
    approval_flow_id = fields.Many2one(
        "utilities.approval.flow", string="Approval flow"
    )

    _order = "ordering ASC"
