# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from . import CONST


class RequiredAllApproval(models.Model):
    _name = "utilities.required.all.approval"
    _description = "Required all approval records"
    _inherit = ["utilities.notification"]

    approval_status_for_all_approval = fields.Selection(
        CONST.APPROVAL_STATES,
        string="All approval status",
        compute="_get_approval_status_for_all_approval",
        tracking=True,
    )
    is_user_allow_to_approvel = fields.Boolean(
        "Is user allow to approve",
        compute="_get_is_user_allow_to_approvel",
        tracking=True,
    )
    is_off_all_approval = fields.Boolean("Is off all approval", default=False)

    @api.depends("this_all_approval_group_id")
    def _get_approval_status_for_all_approval(self):
        for record in self:
            record.approval_status_for_all_approval = CONST.PENDING
            groups = self.this_all_approval_group_id.required_all_approval_group_ids

            groups_len = len(groups)
            are_all_approved = sum([1 for group in groups if group.color == 10])
            is_one_rejected = record.some_function(
                [True for group in groups if group.color == 9], lambda x: x == True
            )

            if groups_len == are_all_approved and groups_len != 0:
                record.approval_status_for_all_approval = CONST.APPROVED

            if is_one_rejected and groups_len != 0:
                record.approval_status_for_all_approval = CONST.REJECTED

    def some_function(self, iterable, condition):
        for item in iterable:
            if condition(item):
                return True
        return False

    # relations
    this_all_approval_group_id = fields.Many2one(
        "utilities.this.all.approval.group",
        string="This all approval group",
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        result = super(RequiredAllApproval, self).create(vals_list)
        return result

    def write(self, vals):
        self.ensure_one()
        result = super(RequiredAllApproval, self).write(vals)

        if self.is_off_all_approval:
            return result

        return result

    def unlink(self):
        for record in self:
            record.this_all_approval_group_id.unlink()
        return super(RequiredAllApproval, self).unlink()

    def implement_approval_flow(self, notification=True):
        self.ensure_one()
        self.this_all_approval_group_id.implement_approval_flow(notification, self)

    def not_implement_approval_flow(self):
        self.ensure_one()
        self.this_all_approval_group_id.not_implement_approval_flow()

    def _create_this_all_approval_group(self, and_implement=False, notification=True):
        self.ensure_one()
        this_group = self.env["utilities.this.all.approval.group"].create(
            {"model_name": self._name}
        )
        self.this_all_approval_group_id = this_group
        if and_implement:
            self.implement_approval_flow(notification)

    @api.depends("this_all_approval_group_id")
    def _get_is_user_allow_to_approvel(self):
        for record in self:
            groups = record.this_all_approval_group_id.required_all_approval_group_ids
            for group in groups:
                current_user = self.env.user
                if group.user_id == current_user:
                    record.is_user_allow_to_approvel = True
                    return

            record.is_user_allow_to_approvel = False
            return

    def user_approve(self):
        self.ensure_one()
        if not self.is_user_allow_to_approvel:
            return

        current_user = self.env.user
        groups = self.this_all_approval_group_id.required_all_approval_group_ids
        group = groups.filtered(lambda e: e.user_id == current_user)

        group.color = 10

    def user_unapprove(self):
        self.ensure_one()
        if not self.is_user_allow_to_approvel:
            return

        current_user = self.env.user
        groups = self.this_all_approval_group_id.required_all_approval_group_ids
        group = groups.filtered(lambda e: e.user_id == current_user)

        group.color = 9

    def _off_all_approval(self):
        self.is_off_all_approval = True

    def _on_all_approval(self):
        self.is_off_all_approval = False

    def _is_all_approved(self):
        self.ensure_one()
        if self.approval_status_for_all_approval == CONST.APPROVED:
            return True
        else:
            return False
