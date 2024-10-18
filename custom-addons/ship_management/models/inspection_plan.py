# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from ...utilities.models import CONST as UTILITIES_CONST
from datetime import timedelta
from odoo.exceptions import ValidationError
import logging


class InspectionPlan(models.Model):
    _name = "ship.inspection.plan"
    _description = "Kế hoạch kiểm tra"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True
    _edit_field_permissions_list = {
        "ship_management_inspection_scope_ids": [],
        "technical_inspection_scope_ids": [],
    }

    real_date = fields.Date("Real date", tracking=True)
    expected_date = fields.Date("Expected date", tracking=True)
    real_or_expected_date = fields.Date("Real or expected date")
    is_have_real_date = fields.Boolean(
        "Is have real date", compute="_is_have_real_date"
    )
    general_prenoti_days = fields.Integer(
        "General prenoti days",
        default=lambda self: self._get_default_general_prenoti_days(),
        required=True,
        tracking=True,
    )
    speciallist_prenoti_days = fields.Integer(
        "Speciallist prenoti days",
        default=lambda self: self._get_default_speciallist_prenoti_days(),
        required=True,
        tracking=True,
    )
    stop_notification_for_prepare = fields.Boolean(
        "Stop notification for prepare", tracking=True
    )
    ship_management_report_date = fields.Date(
        "Ship management report date", tracking=True
    )
    technical_report_date = fields.Date("Technical report date", tracking=True)

    # relations
    ship_management_inspection_scope_ids = fields.One2many(
        "ship.ship.management.inspection.scope",
        "inspection_plan_id",
        string="Ship management inspection scope",
        tracking=True,
    )
    technical_inspection_scope_ids = fields.One2many(
        "ship.technical.inspection.scope",
        "inspection_plan_id",
        string="Technical inspection scope",
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
            model_name = "ship.inspection.plan"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)

            real_or_expected_date = vals.get("real_or_expected_date")
            expected_date = vals.get("expected_date")

            if not expected_date and real_or_expected_date:
                vals["expected_date"] = real_or_expected_date

        result = super(InspectionPlan, self).create(vals_list)

        for record in result:
            record._get_real_or_expected_date()

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(InspectionPlan, self).write(vals)

        if "real_date" in vals:
            self._stop_noti_for_prepare_base_on_real_date()

        if "real_date" in vals or "expected_date" in vals:
            self._get_real_or_expected_date()

        if "approval_status" in vals:
            if self._is_approved() and not self.real_date:
                raise ValidationError(
                    "Không thể chấp thuận đơn này, khi chưa có ngày thực tế!"
                )

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def create_default_ship_management_inspection_scopes(self):
        self.ensure_one()

        if self.ship_management_inspection_scope_ids:
            return

        last_inspection_plan = self._get_last_month_inspection_plan(self.company_id)
        last_inspection_plan._backlog_all_unsatisfy_ship_management_tasks()

        model_name = "ship.ship.management.inspection.scope.metadata"
        metadata_ids = self.env[model_name].search(
            [
                ("company_id", "=", self.company_id.id),
            ]
        )

        for metadata in metadata_ids:
            self._create_ship_management_inspection_scope(metadata)

    def _create_ship_management_inspection_scope(self, metadata):
        self.ensure_one()
        return self.env["ship.ship.management.inspection.scope"].create(
            {
                "inspection_plan_id": self.id,
                "ship_management_inspection_scope_metadata_id": metadata.id,
                "company_id": self.company_id.id,
            }
        )

    def create_default_technical_inspection_scopes(self):
        self.ensure_one()

        if self.technical_inspection_scope_ids:
            return

        last_inspection_plan = self._get_last_month_inspection_plan(self.company_id)
        last_inspection_plan._backlog_all_unsatisfy_technical_tasks()

        model_name = "ship.technical.inspection.scope.metadata"
        metadata_ids = self.env[model_name].search(
            [
                ("company_id", "=", self.company_id.id),
            ]
        )

        for metadata in metadata_ids:
            self._create_technical_inspection_scope(metadata)

    def _create_technical_inspection_scope(self, metadata):
        self.ensure_one()
        return self.env["ship.technical.inspection.scope"].create(
            {
                "inspection_plan_id": self.id,
                "technical_inspection_scope_metadata_id": metadata.id,
                "company_id": self.company_id.id,
            }
        )

    def _get_default_general_prenoti_days(self):
        default_value_model = self._get_default_value_model()
        variable_name = UTILITIES_CONST.INTEGER_SHIP_INSPECTION_PLAN_GENERAL_PRENOTI_DAYS
        return default_value_model._get_default_value_by_variable_name(variable_name)

    def _get_default_speciallist_prenoti_days(self):
        default_value_model = self._get_default_value_model()
        variable_name = UTILITIES_CONST.INTEGER_SHIP_INSPECTION_PLAN_SPECIALLIST_PRENOTI_DAYS
        return default_value_model._get_default_value_by_variable_name(variable_name)

    def _prepare_for_inspection_date(self):
        company_ids = self.search([]).mapped("company_id")

        for company_id in company_ids:
            record = self.search(
                [
                    ("stop_notification_for_prepare", "=", False),
                    ("real_date", "=", False),
                    ("company_id", "=", company_id.id),
                ],
                order="expected_date asc",
                limit=1,
            )

            if record:
                general_prenoti_days = record.general_prenoti_days
                prenoti_date = record.expected_date - timedelta(
                    days=general_prenoti_days
                )
                today = fields.Date.today()

                if prenoti_date <= today:

                    record.create_default_ship_management_inspection_scopes()
                    record.create_default_technical_inspection_scopes()
                    record._send_noti_for_people_need_to_prepare_inspection_plan()

    def _need_real_date_for_inspection_plan(self):
        result = self.search([("real_date", "=", False)])

        for record in result:
            prenoti_days = record.speciallist_prenoti_days
            prenoti_date = record.expected_date - timedelta(days=prenoti_days)
            today = fields.Date.today()

            if prenoti_date <= today:
                record._send_noti_for_people_need_to_fill_in_real_date()

    def _send_noti_for_people_need_to_prepare_inspection_plan(self):
        self.ensure_one()
        default_value_model = self._get_default_value_model()
        variable_name = UTILITIES_CONST.USERS_SHIP_INSPECTION_PLAN_NEED_PREPARE
        user_ids = default_value_model._get_default_value_by_variable_name(
            variable_name
        )

        classes = "title_inspection_plan_color"
        subject = "Cần chuẩn bị cho đợt kiểm tra tàu hàng tháng!!"
        message = f"Ngày dự kiến rơi vào {self.expected_date}!!"

        for user in user_ids:
            self._send_notification_by_user(user, subject, message, classes)

    def _send_noti_for_people_need_to_fill_in_real_date(self):
        self.ensure_one()
        default_value_model = self._get_default_value_model()
        variable_name = UTILITIES_CONST.USERS_SHIP_INSPECTION_PLAN_NEED_REAL_DATE
        user_ids = default_value_model._get_default_value_by_variable_name(
            variable_name
        )

        classes = "title_inspection_plan_color"
        subject = "Cần điền ngày kiểm tra thực tế cho kế hoạch kiểm tra tàu hằng tháng"
        message = f"Ngày dự kiến rơi vào {self.expected_date}!!"

        for user in user_ids:
            self._send_notification_by_user(user, subject, message, classes)

    def _get_real_or_expected_date(self):
        self.ensure_one()
        self.bypass_checks().write(
            {"real_or_expected_date": self.real_date or self.expected_date}
        )

    @api.depends("real_date")
    def _is_have_real_date(self):
        for record in self:
            if record.real_date:
                record.is_have_real_date = True
            else:
                record.is_have_real_date = False

    def _get_last_month_inspection_plan(self, company_id):
        model_name = "ship.inspection.plan"
        record = self.env[model_name].search(
            [
                ("approval_status", "=", CONST.APPROVED),
                ("real_date", "!=", False),
                ("company_id", "=", company_id.id),
            ],
            order="real_date desc",
            limit=1,
        )
        return record

    def _backlog_all_unsatisfy_tasks(self):
        self.ensure_one()
        self._backlog_all_unsatisfy_technical_tasks()
        self._backlog_all_unsatisfy_ship_management_tasks()

    def _backlog_all_unsatisfy_technical_tasks(self):
        self.ensure_one()
        technical_inspection_task_ids = (
            self.technical_inspection_scope_ids.technical_inspection_task_ids.filtered(
                lambda e: e.status == CONST.UNSATISFIED
                or e.task_type == CONST.LAST_MONTH_BACKLOG
            )
        )

        for task in technical_inspection_task_ids:
            task.task_type = CONST.BACKLOGGED

    def _backlog_all_unsatisfy_ship_management_tasks(self):
        self.ensure_one()
        ship_management_inspection_task_ids = self.ship_management_inspection_scope_ids.ship_management_inspection_task_ids.filtered(
            lambda e: e.status == CONST.UNSATISFIED
            or e.task_type == CONST.LAST_MONTH_BACKLOG
        )

        for task in ship_management_inspection_task_ids:
            task.task_type = CONST.BACKLOGGED

    def _stop_noti_for_prepare_base_on_real_date(self):
        self.ensure_one()
        if self.real_date:
            self.stop_notification_for_prepare = True
        else:
            self.stop_notification_for_prepare = False

    def reset_real_date(self):
        self.ensure_one()
        self.real_date = False
        self.approval_status = UTILITIES_CONST.REJECTED
