# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from ...utilities.models import CONST as CONST_UTILITIES
from odoo.exceptions import ValidationError


class InspectionEvent(models.Model):
    _name = "docking.inspection.event"
    _description = "Inspection event records"
    _inherit = ["ship.date", "utilities.notification"]
    _check_company_auto = True

    name = fields.Char(
        "Name", related="inspection_event_metadata_id.name", tracking=True
    )
    description = fields.Html(
        "Description", related="inspection_event_metadata_id.description", tracking=True
    )
    is_confirmed = fields.Boolean("Is confirmed", tracking=True)
    inspection_date = fields.Date("Inspection date", tracking=True)

    # relations
    docking_plan_id = fields.Many2one(
        "docking.docking.plan",
        string="Docking plan",
        required=True,
        tracking=True,
    )
    inspection_event_metadata_id = fields.Many2one(
        "docking.inspection.event.metadata",
        string="Inspection event metadata",
        required=True,
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
            model_name = "docking.inspection.event"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(InspectionEvent, self).create(vals_list)

        return result

    def write(self, vals):
        result = super(InspectionEvent, self).write(vals)

        if "inspection_date" in vals:
            current_user = self.env.user
            message = f"Lịch đăng kiểm {self.name} đã thay đổi ngày đăng kiểm bởi {current_user.name}"
            self._changing_inspection_date_notification(message)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result

    def confirm_inspection(self):
        self.ensure_one()
        self.is_confirmed = True

    def confirm_inspection_date_notification(self):
        today = fields.Date.today()
        today_plus_1 = self._plus_date(today, 1)

        inspection_event_ids = self.search(
            [("is_confirmed", "=", False), ("inspection_date", "<=", today_plus_1)]
        )

        for inspection_event_id in inspection_event_ids:
            inspection_event_id._send_confirm_inspection_date_notification()

    def _send_confirm_inspection_date_notification(self):
        self.ensure_one()
        default_value_model = self._get_default_value_model()
        variable_name = CONST_UTILITIES.USERS_DOCKING_INSPECTION_EVENT_CONFIRM_INSPECTION_DATE
        user_ids = default_value_model._get_default_value_by_variable_name(
            variable_name
        )

        classes = "title_inspection_event_color"
        subject = f"Thông báo xác nhận đăng kiểm cho {self.name}"
        message = f"{self.description}"

        for user in user_ids:
            self._send_notification_by_user(user, subject, message, classes)

    def _get_default_value_model(self):
        model_name = "utilities.default.value"
        default_value_model = self.env[model_name].search([])

        return default_value_model

    def _changing_inspection_date_notification(self, message):
        self.ensure_one()
        default_value_model = self._get_default_value_model()
        variable_name = CONST_UTILITIES.USERS_DOCKING_INSPECTION_EVENT_CHANGING_INSPECTION_DATE
        user_ids = default_value_model._get_default_value_by_variable_name(
            variable_name
        )

        classes = "title_docking_date_color"
        subject = "Thay đổi ngày đăng kiểm!"

        for user in user_ids:
            self._send_notification_by_user(user, subject, message, classes)
