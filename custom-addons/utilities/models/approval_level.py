# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ApprovalLevel(models.Model):
    _name = "utilities.approval.level"
    _description = "Approval level records"
    _inherit = ["utilities.notification"]

    name = fields.Char("Name", tracking=True)
    user_group = fields.Many2one(
        "res.groups",
        string="User Group",
        required=True,
        tracking=True,
        domain="[('category_id.name', '=', \"Ship Roles\")]",
    )
    group_xml_id = fields.Char("group_xml_id", tracking=True)
    second_time = fields.Boolean("Second time", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        result = super(ApprovalLevel, self).create(vals_list)

        for record in result:
            if record.user_group:
                record.group_xml_id = record._get_group_xml_id()

        return result

    def write(self, vals):
        result = super(ApprovalLevel, self).write(vals)

        for record in self:
            if "user_group" in vals:
                record.group_xml_id = record._get_group_xml_id()

        return result

    def _get_group_xml_id(self):
        self.ensure_one()

        group_xml_id = list(self.user_group.ensure_one().get_xml_id().values())[0]
        return group_xml_id
