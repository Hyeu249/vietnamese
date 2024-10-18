# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class TechnicalIncidentInsurance(models.Model):
    _name = "legis.technical.incident.insurance"
    _description = "Technical incident insurance records"
    _inherit = ["utilities.required.all.approval"]
    _check_company_auto = True

    total_price = fields.Float(
        "Total price", related="technical_incident_id.total_price", tracking=True
    )
    insurance_deductible_cost = fields.Float(
        "Insurance deductible cost",
        related="technical_incident_id.insurance_deductible_cost",
        tracking=True,
    )
    document = fields.Binary("Upload Document", tracking=True)
    is_completed = fields.Boolean("Is completed", tracking=True)

    # relations
    technical_incident_id = fields.Many2one(
        "legis.technical.incident",
        string="Technical incident",
        tracking=True,
    )

    required_all_approval_group_ids = fields.Many2many(
        "utilities.required.all.approval.group",
        compute="get_required_all_approval_group_ids",
    )

    @api.depends("this_all_approval_group_id")
    def get_required_all_approval_group_ids(self):
        for record in self:
            group_id = record.this_all_approval_group_id
            record.required_all_approval_group_ids = (
                group_id.required_all_approval_group_ids.ids
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
            model_name = "legis.technical.incident.insurance"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(TechnicalIncidentInsurance, self).create(vals_list)

        for record in result:
            record._create_this_all_approval_group(and_implement=True)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
