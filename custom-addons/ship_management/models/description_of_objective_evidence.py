# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class DescriptionOfObjectiveEvidence(models.Model):
    _name = "ship.description.of.objective.evidence"
    _description = "Material group records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    name = fields.Text("Name", related="audit_question_id.name", tracking=True)
    grading = fields.Char("Grading", tracking=True)
    ism_code = fields.Char("ism code", tracking=True)
    status = fields.Char("Status", tracking=True)
    deadline = fields.Date("Deadline", tracking=True)

    # relations
    list_of_ism_nonconformities_id = fields.Many2one(
        "ship.list.of.ism.nonconformities", tracking=True
    )
    audit_question_id = fields.Many2one("ship.checklist.value", tracking=True)

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
                "ship.description.of.objective.evidence"
            )
        return super(DescriptionOfObjectiveEvidence, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
