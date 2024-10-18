# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class NonconformityReport(models.Model):
    _name = "ship.nonconformity.report"
    _description = "Nonconformity report records"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    report_date = fields.Char("Report date", tracking=True)
    NCR_no = fields.Char("NCR No.", tracking=True)
    department = fields.Char("Department", tracking=True)
    ism_code = fields.Char("ism code", tracking=True)
    sms_procedure = fields.Char("sms procedure", tracking=True)
    description = fields.Text(
        "Discription of Non-conformit",
        related="description_of_objective_evidence_id.audit_question_id.name",
        tracking=True,
    )
    cause = fields.Char("Root cause", tracking=True)
    corrective_action = fields.Char("Corrective actions", tracking=True)
    preventive_action = fields.Char("Preventive actions", tracking=True)
    proposed_date_of_completion = fields.Char(
        "Proposed date of completion", tracking=True
    )
    complete_date = fields.Char("Completion date", tracking=True)
    the_NC_cleared_on = fields.Char("The NC cleared on", tracking=True)
    signature = fields.Char("Department", tracking=True)
    master_head_of_department_sign = fields.Char(
        "Master/ Head of Department signs", tracking=True
    )
    deadline = fields.Date(
        "Deadline",
        related="description_of_objective_evidence_id.deadline",
        tracking=True,
    )
    is_overdue = fields.Boolean("Is_overdue", compute="get_is_overdue")

    @api.depends("deadline")
    def get_is_overdue(self):
        today = fields.Date.today()
        for record in self:
            if record.deadline and record.deadline <= today:
                record.is_overdue = True
            else:
                record.is_overdue = False

    # relations
    list_of_ism_nonconformities_id = fields.Many2one(
        "ship.list.of.ism.nonconformities", tracking=True
    )
    description_of_objective_evidence_id = fields.Many2one(
        "ship.description.of.objective.evidence", tracking=True
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
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.nonconformity.report"
            )
        return super(NonconformityReport, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
