# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from . import CONST
import logging
from ...utilities.models import CONST as CONST_UTILITIES


class ReviewPlan(models.Model):
    _name = "ship.review.plan"
    _description = "Review plan records"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    review_date = fields.Date("Review date", tracking=True)
    expected_review_date = fields.Date("Expected review date", tracking=True)
    review_approval_date = fields.Date("Review approval date", tracking=True)
    stop_noti_for_prepare = fields.Boolean("stop_noti_for_prepare", tracking=True)
    stop_noti_for_request_date = fields.Boolean(
        "stop_noti_for_request_date", tracking=True
    )

    # relations
    internal_audit_checklist_id = fields.Many2one(
        "ship.internal.audit.checklist",
        default=lambda self: self.env["ship.internal.audit.checklist"].create({}),
        tracking=True,
    )
    internal_mlc_audit_checklist_id = fields.Many2one(
        "ship.internal.mlc.audit.checklist",
        default=lambda self: self.env["ship.internal.mlc.audit.checklist"].create({}),
        tracking=True,
    )
    internal_ism_audit_report_ids = fields.One2many(
        "ship.internal.ism.audit.report",
        "review_plan_id",
        tracking=True,
    )
    list_of_ism_nonconformities_ids = fields.One2many(
        "ship.list.of.ism.nonconformities",
        "review_plan_id",
        tracking=True,
    )
    audit_question_ids = fields.Many2many(
        "ship.checklist.value",
        string="Audit Question",
        compute="_get_audit_questions_are_no",
    )

    @api.depends("internal_audit_checklist_id", "internal_mlc_audit_checklist_id")
    def _get_audit_questions_are_no(self):
        for record in self:
            answer_is_no = (
                lambda self: self.yes_no == CONST.AUDIT_CHECKLIST_NO
                or self.yes_no == CONST.AUDIT_CHECKLIST_NOT_SATISFIED
            )
            checklist_id = record.internal_audit_checklist_id
            mlc_checklist_id = record.internal_mlc_audit_checklist_id

            checklist_question_ids = checklist_id.audit_question_ids.filtered(
                answer_is_no
            )
            mlc_checklist_question_ids = mlc_checklist_id.audit_question_ids.filtered(
                answer_is_no
            )

            record.audit_question_ids = (
                checklist_question_ids.ids + mlc_checklist_question_ids.ids
            )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.review.plan")
        return super(ReviewPlan, self).create(vals_list)

    def write(self, vals):
        self.ensure_one()
        result = super(ReviewPlan, self).write(vals)

        if "approval_status" in vals:
            if self._is_approved():
                self.send_email_to_captain()

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def edit_internal_audit_notice(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "legis.accident.report",
            "view_mode": "form",
            "res_id": self.edit_internal_audit_notice_id.id,
            "target": "current",
            "context": self.env.context,
        }

    def edit_internal_audit_checklist(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "ship.internal.audit.checklist",
            "view_mode": "form",
            "res_id": self.internal_audit_checklist_id.id,
            "target": "current",
            "context": self.env.context,
        }

    def edit_internal_mlc_audit_checklist(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "ship.internal.mlc.audit.checklist",
            "view_mode": "form",
            "res_id": self.internal_mlc_audit_checklist_id.id,
            "target": "current",
            "context": self.env.context,
        }

    def edit_internal_ism_audit_report(self):
        self.ensure_one()
        report_ids = self.internal_ism_audit_report_ids

        if report_ids:
            report_id = report_ids[0]
            return {
                "type": "ir.actions.act_window",
                "res_model": "ship.internal.ism.audit.report",
                "view_mode": "form",
                "res_id": report_id.id,
                "target": "current",
                "context": self.env.context,
            }

    def edit_list_of_ism_nonconformities(self):
        self.ensure_one()
        report_ids = self.list_of_ism_nonconformities_ids
        question_ids = self.audit_question_ids

        if report_ids:
            report_id = report_ids[0]
            if not report_id:
                report_id.create_description_of_objective_evidence_ids(question_ids)
            elif report_id.is_difference_review_plan_audit_question:
                question_ids = report_id.get_difference_questions_from_review_plan()
                report_id.create_description_of_objective_evidence_ids(question_ids)

            return {
                "type": "ir.actions.act_window",
                "res_model": "ship.list.of.ism.nonconformities",
                "view_mode": "form",
                "res_id": report_id.id,
                "target": "current",
                "context": self.env.context,
            }

    def create_internal_ism_audit_report(self):
        self.ensure_one()
        self.internal_ism_audit_report_ids.create({"review_plan_id": self.id})

    def create_list_of_ism_nonconformities(self):
        self.ensure_one()
        self.list_of_ism_nonconformities_ids.create({"review_plan_id": self.id})

    def complete_plan(self):
        self.ensure_one()

        return {
            "name": "Complete Plan Wizard",
            "type": "ir.actions.act_window",
            "res_model": "ship.create.review.plan.wiz",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_review_plan_id": self.id,
            },
        }

    def prepare_review_plan(self):
        company_ids = self.search([]).mapped("company_id")

        for company_id in company_ids:
            record = self.search(
                [
                    ("stop_noti_for_prepare", "=", False),
                    ("review_date", "=", False),
                    ("company_id", "=", company_id.id),
                ]
            )
            if not record:
                return
            if len(record) > 1:
                raise ValidationError(f"Chỉ có 1 kế hoạch chuẩn bị!")

            prepare_date = record.expected_review_date - timedelta(days=60)
            today = fields.Date.today()

            if today >= prepare_date:
                record.noti_to_head_of_legal_for_preparation()

    def request_review_approval_date(self):
        company_ids = self.search([]).mapped("company_id")

        for company_id in company_ids:
            record = self.search(
                [
                    ("stop_noti_for_request_date", "=", False),
                    ("review_date", "=", False),
                    ("company_id", "=", company_id.id),
                ],
            )
            if not record:
                return
            if len(record) > 1:
                raise ValidationError(f"Chỉ có 1 kế hoạch chuẩn bị!")

            prepare_date = record.expected_review_date - timedelta(days=7)
            today = fields.Date.today()

            if today >= prepare_date:
                record.noti_to_head_of_legal_to_fill_in_review_approval_date()

    def noti_to_head_of_legal_for_preparation(self):
        self.ensure_one()
        group_xml_id = "group_ship_head_of_legal"
        subject = f"Chuẩn bị kế hoạch đánh giá!"
        body = f"Bản ghi {self.ref} cần chuẩn bị!"
        company_id = self.company_id

        self._send_notification_by_group_xml_and_company_id(
            group_xml_id, company_id, subject, body
        )
        self.bypass_checks().stop_noti_for_prepare = True

    def noti_to_head_of_legal_to_fill_in_review_approval_date(self):
        self.ensure_one()
        group_xml_id = "group_ship_head_of_legal"
        subject = f"Yêu cầu điền ngày duyệt đánh giá!"
        body = f"Bản ghi {self.ref} cần ngày duyệt đánh giá!"
        company_id = self.company_id

        self._send_notification_by_group_xml_and_company_id(
            group_xml_id, company_id, subject, body
        )
        self.bypass_checks().stop_noti_for_request_date = True

    def _get_email_values(self):
        group = self.env.ref("utilities.group_ship_captain")
        users = group.users.filtered(
            lambda record: self.company_id.id in record.company_ids.ids
            and not record.has_group("utilities.group_ship_admin")
        )

        return {"email_to": users.email}

    def send_email_to_captain(self):
        self.ensure_one()
        try:
            template = self.env.ref("ship_management.email_review_plan_template").id
            email_values = self._get_email_values()
            context = {
                "self": self,
            }

            self._send_email(self.id, template, context, email_values)
        except Exception as e:
            logging.error(e)
            raise e

    def _send_email(self, record_id, template, context, email_values, force_send=False):
        return (
            self.env["mail.template"]
            .browse(template)
            .with_context(context)
            .send_mail(record_id, email_values=email_values, force_send=False)
        )
