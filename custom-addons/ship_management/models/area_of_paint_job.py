# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from .paint_history import MINUS_ACTION, ADD_ACTION
from odoo.exceptions import ValidationError


class AreaOfPaintJob(models.Model):
    _name = "ship.area.of.paint.job"
    _description = "Area of paint job records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    paint_area_m2 = fields.Float("Paint Area")

    # related
    required_quantity_liter_m2 = fields.Float(
        "Required quantity liter/m2",
        related="job_paint_requirement_id.required_quantity_liter_m2",
    )
    paint_position = fields.Char(
        "Paint position", related="job_paint_requirement_id.paint_position"
    )
    layer_count = fields.Integer(
        "Layer count", related="job_paint_requirement_id.layer_count"
    )
    paint_id = fields.Many2one(
        "ship.paint",
        related="job_paint_requirement_id.paint_id",
        string="Paint",
        tracking=True,
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    job_paint_requirement_id = fields.Many2one(
        "ship.job.paint.requirement",
        string="Job Paint Requirement",
        tracking=True,
    )
    job_quote_id = fields.Many2one(
        "ship.job.quote",
        string="Job Quote",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        new_paint_history_event_list = []
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.area.of.paint.job")
            # get job paint requirement
            job_paint_requirement = self.env["ship.job.paint.requirement"].browse(
                vals["job_paint_requirement_id"]
            )
            # get paint from job_paint_requirement
            paint_id = job_paint_requirement.paint_id.id

            quantity_liter = (
                vals["paint_area_m2"] * job_paint_requirement.required_quantity_liter_m2
            )
            # create new paint history event
            new_paint_history_event = {
                "paint_id": paint_id,
                "action": MINUS_ACTION,
                "occured_at": fields.Datetime.now(),
                "quantity_liter": quantity_liter,
                "job_quote_id": vals["job_quote_id"],
            }
            new_paint_history_event_list.append(new_paint_history_event)

        self.env["ship.paint.history"].create(new_paint_history_event_list)

        return super(AreaOfPaintJob, self).create(vals_list)

    def unlink(self):
        # create new paint history event
        new_paint_history_event_list = []
        for record in self:
            # get job paint requirement
            job_paint_requirement = self.env["ship.job.paint.requirement"].browse(
                record.job_paint_requirement_id.id
            )
            # get paint from job_paint_requirement
            paint_id = job_paint_requirement.paint_id.id

            quantity_liter = (
                record.paint_area_m2 * job_paint_requirement.required_quantity_liter_m2
            )
            # create new paint history event
            new_paint_history_event = {
                "paint_id": paint_id,
                "action": ADD_ACTION,
                "occured_at": fields.Datetime.now(),
                "quantity_liter": quantity_liter,
                "job_quote_id": record.job_quote_id.id,
                "note": "Area of paint job is deleted. Restore paint quantity.",
            }
            new_paint_history_event_list.append(new_paint_history_event)

        self.env["ship.paint.history"].create(new_paint_history_event_list)
        return super(AreaOfPaintJob, self).unlink()

    def write(self, vals):
        # do not allow update
        raise ValidationError("Update is not allowed.")

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
