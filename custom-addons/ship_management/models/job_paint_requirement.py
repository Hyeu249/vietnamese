# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class JobPaintRequirement(models.Model):
    _name = "ship.job.paint.requirement"
    _description = "Job paint requirement records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    required_quantity_liter_m2 = fields.Float(
        "Required quantity liter/m2", tracking=True
    )
    paint_position = fields.Char("Paint position", tracking=True)
    layer_count = fields.Integer("Layer count", tracking=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    paint_id = fields.Many2one("ship.paint", string="Paint", tracking=True)
    job_id = fields.Many2one("ship.job", string="Job", readonly=True, tracking=True)

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.job.paint.requirement"
            )
        return super(JobPaintRequirement, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            paint_name = report.paint_id.name
            paint_position = report.paint_position
            layer_count = report.layer_count
            required_quantity_liter_m2 = report.required_quantity_liter_m2

            name = f"{paint_name} / {paint_position} / {layer_count} / {required_quantity_liter_m2}"

            result.append((report.id, name))
        return result
