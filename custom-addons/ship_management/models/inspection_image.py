# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class InspectionImage(models.Model):
    _name = "ship.inspection.image"
    _description = "Inspection image records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    image = fields.Image("Image", tracking=True,
                         max_width=CONST.MAX_IMAGE_UPLOAD_WIDTH,
                         max_height=CONST.MAX_IMAGE_UPLOAD_HEIGHT)
    description = fields.Char("Description", tracking=True)

    # relations
    ship_management_inspection_task_ids = fields.Many2many(
        "ship.ship.management.inspection.task",
        string="Ship management inspection task",
        tracking=True,
    )
    technical_inspection_task_ids = fields.Many2many(
        "ship.technical.inspection.task",
        string="Technical inspection task",
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
            model_name = "ship.inspection.image"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        return super(InspectionImage, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
