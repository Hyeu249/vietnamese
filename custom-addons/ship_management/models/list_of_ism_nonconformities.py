# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from . import CONST


class ListOfISMNonconformities(models.Model):
    _name = "ship.list.of.ism.nonconformities"
    _description = "List of ism nonconformities records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    deadline = fields.Date("Deadline", tracking=True)
    is_difference_review_plan_audit_question = fields.Boolean(
        "Is difference review plan audit question",
        compute="get_is_difference_review_plan_audit_question",
    )

    def get_is_difference_review_plan_audit_question(self):
        for record in self:
            review_plan_question_ids = record.review_plan_id.audit_question_ids
            question_ids = record.description_of_objective_evidence_ids.mapped(
                "audit_question_id"
            )

            record.is_difference_review_plan_audit_question = set(
                review_plan_question_ids.ids
            ) != set(question_ids.ids)

    def get_difference_questions_from_review_plan(self):
        for record in self:
            difference_questions = []
            question_ids = record.description_of_objective_evidence_ids.mapped(
                "audit_question_id"
            )

            for question in record.review_plan_id.audit_question_ids:
                if question.id not in question_ids.ids:
                    difference_questions.append(question.id)

            return difference_questions

    # relations
    review_plan_id = fields.Many2one("ship.review.plan", tracking=True)
    description_of_objective_evidence_ids = fields.One2many(
        "ship.description.of.objective.evidence",
        "list_of_ism_nonconformities_id",
        tracking=True,
    )
    nonconformity_report_ids = fields.One2many(
        "ship.nonconformity.report",
        "list_of_ism_nonconformities_id",
        tracking=True,
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.constrains("review_plan_id")
    def _unique_review_plan_id(self):
        for record in self:
            duplicate = self.search(
                [
                    ("id", "!=", record.id),
                    ("review_plan_id", "=", record.review_plan_id.id),
                ]
            )
            message = "Duplicate review_plan_id!"
            if duplicate:
                raise ValidationError(message)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.list.of.ism.nonconformities"
            )
        result = super(ListOfISMNonconformities, self).create(vals_list)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def create_description_of_objective_evidence_ids(self, audit_question_ids):
        self.ensure_one()
        package = [
            {
                "audit_question_id": question,
                "list_of_ism_nonconformities_id": self.id,
            }
            for question in audit_question_ids
        ]

        if audit_question_ids:
            self.description_of_objective_evidence_ids.create(package)

    def create_nonconformity_reports(self):
        self.ensure_one()
        report_ids = [
            {
                "description_of_objective_evidence_id": evidence.id,
                "list_of_ism_nonconformities_id": self.id,
            }
            for evidence in self.description_of_objective_evidence_ids
        ]

        self.nonconformity_report_ids.create(report_ids)
