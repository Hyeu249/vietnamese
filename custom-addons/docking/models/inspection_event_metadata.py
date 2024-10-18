# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class InspectionEventMetadata(models.Model):
    _name = "docking.inspection.event.metadata"
    _description = "Inspection event metadata records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Html("Description", tracking=True)
    days_after_real_docking_start_date = fields.Integer(
        "Days after real docking start date", tracking=True
    )

    # relations
    inspection_event_ids = fields.One2many(
        "docking.inspection.event",
        "inspection_event_metadata_id",
        string="Inspection event",
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
            model_name = "docking.inspection.event.metadata"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        return super(InspectionEventMetadata, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
