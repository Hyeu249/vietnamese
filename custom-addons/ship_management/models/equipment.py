# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class Equipment(models.Model):
    _name = "ship.equipment"
    _description = "Equipment records"
    _inherit = ["ship.date", "utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)

    calculate_consumption_by = fields.Selection(
        CONST.TIME_TYPE,
        default=CONST.NONE,
        string="Calculate consumption by",
        required=True,
        tracking=True,
    )
    last_recording_date = fields.Date("Last recording date", tracking=True)
    total_utilization_time = fields.Integer(
        "Total utilization time", compute="_calc_total_utilization_time", tracking=True
    )
    is_for_consumption = fields.Boolean("Is for consumption", tracking=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # relations
    maintenance_scope_ids = fields.One2many(
        "ship.maintenance.scope",
        "equipment_id",
        string="Maintenance Scope",
        tracking=True,
    )

    utilization_time_ids = fields.One2many(
        "ship.utilization.time",
        "equipment_id",
        string="Utilization time",
        tracking=True,
    )

    @api.depends("utilization_time_ids")
    def _calc_total_utilization_time(self):
        for record in self:
            total = sum(record.utilization_time_ids.mapped("utilization_time"))
            record.total_utilization_time = total

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.equipment")
        return super(Equipment, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
