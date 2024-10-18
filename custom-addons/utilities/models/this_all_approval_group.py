# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from . import CONST


class ThisAllApprovalGroup(models.Model):
    _name = "utilities.this.all.approval.group"
    _description = "This all approval group records"
    _inherit = ["utilities.notification"]

    model_name = fields.Char(string="Name", tracking=True)
    # relations
    required_all_approval_group_ids = fields.One2many(
        "utilities.required.all.approval.group",
        "this_all_approval_group_id",
        string="Required all approval group",
        readonly=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "utilities.this.all.approval.group"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        return super(ThisAllApprovalGroup, self).create(vals_list)

    def unlink(self):
        for record in self:
            record.required_all_approval_group_ids.unlink()
        return super(ThisAllApprovalGroup, self).unlink()

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def implement_approval_flow(self, notification, record):
        self.ensure_one()
        approval_flow_condition = [("model_name", "=", self.model_name)]
        approval_flow_name = "utilities.required.all.approval.flow"
        approval_group_name = "utilities.required.all.approval.group"
        approval_flow_id = self.env[approval_flow_name].search(approval_flow_condition)

        self.required_all_approval_group_ids.unlink()
        for user_id in approval_flow_id.user_ids:
            self.env[approval_group_name].create(
                {
                    "this_all_approval_group_id": self.id,
                    "user_id": user_id.id,
                }
            )

            if notification:
                subject = "Duyệt đồng thời"
                body = f"Cần duyệt {record._description}"
                record._send_notification_by_user(user_id, subject, body)

    def not_implement_approval_flow(self):
        self.ensure_one()
        self.required_all_approval_group_ids.unlink()
