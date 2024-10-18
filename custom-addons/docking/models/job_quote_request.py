# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
from ...ship_management.models import CONST as SHIP_CONST


class JobQuoteRequest(models.Model):
    _name = "docking.job.quote.request"
    _description = "Yêu cầu báo giá công việc-docking"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    comment = fields.Char("Comment", tracking=True)
    survey_type = fields.Selection(
        CONST.ARISE_SELECTION,
        string="Survey type",
        default=CONST.NORMAL,
        required=True,
        tracking=True,
    )
    deadline = fields.Date("Deadline", tracking=True)

    # related
    name_for_noti = fields.Char(
        related="docking_plan_id.name",
        string="Docking name",
    )

    # compute
    is_consistent_status = fields.Boolean(
        "Is consistent status", compute="get_is_consistent_status"
    )

    @api.depends("job_quote_ids")
    def get_is_consistent_status(self):
        for record in self:
            request_status = record._get_approval_status()
            unique_status = record.job_quote_ids.mapped_unique_status()

            record.is_consistent_status = request_status == unique_status

    # relations
    docking_plan_id = fields.Many2one(
        "docking.docking.plan",
        string="Docking plan",
        tracking=True,
    )

    job_quote_ids = fields.One2many(
        "docking.job.quote",
        "job_quote_request_id",
        string="Job Quote",
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
            model_name = "docking.job.quote.request"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)

        result = super(JobQuoteRequest, self).create(vals_list)
        return result

    def write(self, vals):
        old_job_quote_ids = self.job_quote_ids.ids
        old_job_qs = {quote.id: quote.name_for_noti for quote in self.job_quote_ids}

        if "approval_status" in vals:
            message = "Trạng thái các báo giá không nhất quán, vui lòng kiểm tra lại"
            if not self.is_consistent_status:
                raise ValidationError(f"{message}")

        result = super(JobQuoteRequest, self).write(vals)

        new_job_quote_ids = self.job_quote_ids.ids

        if old_job_quote_ids != new_job_quote_ids:
            added_quotes = list(set(new_job_quote_ids) - set(old_job_quote_ids))
            removed_quotes = list(set(old_job_quote_ids) - set(new_job_quote_ids))
            removed_names = self.get_removed_quote_name(removed_quotes, old_job_qs)

            self._log_quote_changes_to_chatter(added_quotes, removed_names)

        if "approval_status" in vals:
            docking_plan_id = self.docking_plan_id
            all_approved = docking_plan_id._are_all_equipment_survey_datas_approved()
            message = "Báo cáo chưa đủ điều kiện để tham gia luồng duyệt, vui lòng liên hệ quản trị viên!"

            if not all_approved:
                raise ValidationError(message)

        if "approval_status" in vals:
            for job_quote in self.job_quote_ids:
                job_quote._set_approval_status(self._get_approval_status())

        return result

    def get_removed_quote_name(self, removed_ids, quotes):
        removed_name = []

        for id, name in quotes.items():
            if id in removed_ids:
                removed_name.append(name)

        return removed_name

    def _log_quote_changes_to_chatter(self, added_quotes, removed_names):
        message = ""
        if added_quotes:
            added_names = (
                self.env["docking.job.quote"]
                .browse(added_quotes)
                .mapped("name_for_noti")
            )
            message += "<li>Added quotes: {}</li>".format(", ".join(added_names))

        if removed_names:
            message += "<li>Removed quotes: {}</li>".format(", ".join(removed_names))

        if message:
            full_message = "<ul>{}</ul>".format(message)
            self.message_post(body=full_message)

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def get_new_job_quote_ids(self):
        self.ensure_one()
        job_quote_ids = self._get_job_quote_ids()
        self.job_quote_ids = [(6, 0, job_quote_ids)]

    def _get_job_quote_ids(self):
        survey_ids = self.docking_plan_id.equipment_survey_data_ids
        get_survey_type = lambda e: e.survey_type == self.survey_type
        equipment_survey_data_ids = survey_ids.filtered(get_survey_type)
        job_quote_ids = [
            quote.id
            for survey in equipment_survey_data_ids
            for report in survey.maintenance_scope_report_ids
            for quote in report.job_quote_ids
            if not quote.is_for_crew and quote._arise_or_approved_survey()
        ]
        return job_quote_ids

    def _check_are_all_quotes_have_prices(self):
        self.ensure_one()
        all_quotes_have_price = self._are_all_job_quotes_priced()

        if all_quotes_have_price and self.is_at_this_approval_level(CONST.SUPPLIER):
            self.action_propose()

    def _are_all_job_quotes_priced(self):
        for job_quote in self.job_quote_ids:
            are_have_priced = job_quote._are_all_job_supplier_quotes_priced()

            if not are_have_priced:
                return False
        return True

    def open_record(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
            "context": self.env.context,
        }

    def run_job_quote_request_daily_cronjobs(self):
        self._propose_to_head_department_when_reaching_deadline()

    def _propose_to_head_department_when_reaching_deadline(self):
        today = fields.Date.today()
        supplier_id = self._get_supplier_group_id()

        conditions = [
            ("deadline", "=", today),
            ("approval_status", "=", supplier_id.id),
        ]
        due_requests = self.search(conditions)

        for request in due_requests:
            request.action_propose()
