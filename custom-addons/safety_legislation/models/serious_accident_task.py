# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class SeriousAccidentTask(models.Model):
    _name = "legis.serious.accident.task"
    _description = "Serious accident task records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char(string="Name", tracking=True)
    description = fields.Char(string="Description", tracking=True)
    is_completed = fields.Boolean("Is completed", tracking=True)

    # related
    user_id = fields.Many2one(
        "res.users", related="serious_accident_team_id.user_id", store=True
    )
    serious_accident_report_id = fields.Many2one(
        "legis.serious.accident.report",
        string="Serious accident report",
        related="serious_accident_team_id.serious_accident_report_id",
        store=True,
        tracking=True,
    )

    # relations
    serious_accident_team_id = fields.Many2one(
        "legis.serious.accident.team",
        string="Serious accident team",
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
            model_name = "legis.serious.accident.task"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(SeriousAccidentTask, self).create(vals_list)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

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

    def complete_task(self):
        self.ensure_one()
        self.is_completed = True

    def uncomplete_task(self):
        self.ensure_one()
        self.is_completed = False
