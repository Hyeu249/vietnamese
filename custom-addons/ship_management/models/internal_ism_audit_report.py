# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from . import CONST


class InternalISMAuditReport(models.Model):
    _name = "ship.internal.ism.audit.report"
    _description = "Internal ism audit report records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    lead_auditor_id = fields.Many2one("res.users", string="Auditor", tracking=True)
    audit_open_at = fields.Date("Audit open", tracking=True)
    audit_close_at = fields.Date("Audit close", tracking=True)
    scope = fields.Text("Scope", tracking=True)

    is_major_NC = fields.Boolean("Is major N.C", tracking=True)
    is_NC = fields.Boolean("Is N.C", tracking=True)
    are_previous_NC_cleared = fields.Boolean("All previous N.C. cleared", tracking=True)
    is_additional_assessment_required = fields.Boolean(
        "Additional assessment required", tracking=True
    )
    are_major_NC_cleared = fields.Boolean("Major NC cleared", tracking=True)
    comment = fields.Text("Comment", tracking=True)

    # relations
    internal_auditor_ids = fields.Many2many(
        "res.users",
        string="Internal auditor(s)",
    )
    review_plan_id = fields.Many2one("ship.review.plan", tracking=True)
    audit_question_ids = fields.Many2many(
        "ship.checklist.value",
        string="Audit Question",
        related="review_plan_id.audit_question_ids",
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
                "ship.internal.ism.audit.report"
            )
        return super(InternalISMAuditReport, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
