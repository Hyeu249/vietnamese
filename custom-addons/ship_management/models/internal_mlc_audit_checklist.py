# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ...utilities.models import CONST as CONST_UTILITIES
from . import CONST


class InternalMCLAuditChecklist(models.Model):
    _name = "ship.internal.mlc.audit.checklist"
    _description = "Internal mlc audit checklist records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    audit_date = fields.Date("Audit date", tracking=True)
    audit_no = fields.Char("Audit no", tracking=True)
    port = fields.Char("Port", tracking=True)

    captain_id = fields.Many2one("res.users", string="Captain", tracking=True)
    auditor_id = fields.Many2one("res.users", string="Auditor", tracking=True)

    # relations
    audit_question_ids = fields.Many2many(
        "ship.checklist.value",
        string="Audit Question",
        default=lambda self: self.get_audit_question_ids(),
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
                "ship.internal.mlc.audit.checklist"
            )
        return super(InternalMCLAuditChecklist, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _get_default_value_model(self):
        model_name = "utilities.default.value"
        default_value_model = self.env[model_name].search([])

        return default_value_model

    def get_audit_question_ids(self):
        default_value_model = self._get_default_value_model()
        variable_name = (
            CONST_UTILITIES.RELATION_SHIP_INTERNAL_MLC_AUDIT_CHECKLIST_CHECKLIST
        )
        auditQuestions = default_value_model._get_default_value_by_variable_name(
            variable_name
        )
        questions = [{"name": question.text_1} for question in auditQuestions]
        question_ids = self.env["ship.checklist.value"].create(questions)
        return question_ids.ids
