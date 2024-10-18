# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MaterialConsumptionReportBatch(models.Model):
    _name = "ship.material.consumption.report.batch"
    _description = "Material Consumption Report Batch"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name")
    date_start = fields.Date("Date From", required=True)
    date_end = fields.Date("Date To", required=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    line_ids = fields.One2many(
        "ship.material.consumption.report", "batch_id", string="Report Lines"
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals["name"]:
                model_code = "ship.material.consumption.report.batch"
                vals["name"] = self.env["ir.sequence"].next_by_code(model_code)
        return super(MaterialConsumptionReportBatch, self).create(vals_list)

    def generate_report(self):
        self.ensure_one()
        if self.line_ids:
            self.line_ids.unlink()

        model_name = "ship.material.assignment"

        result = self.env[model_name].read_group(
            [
                ("start_time_of_use", ">=", self.date_start),
                ("end_time_of_use", "<=", self.date_end),
            ],
            ["total_hours:sum", "start_time_of_use:min"],
            ["material_id"],
        )

        data = [
            {
                "batch_id": self.id,
                "material_id": record.get("material_id", 0)[0],
                "date": record.get("start_time_of_use"),
                "consumption": record.get("total_hours"),
                "remark": "",
            }
            for record in result
        ]

        self.env["ship.material.consumption.report"].create(data)


class MaterialConsumptionReport(models.Model):
    _name = "ship.material.consumption.report"
    _description = "Material Consumption Report"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    date = fields.Date(string="Date", tracking=True, readonly=True)
    remark = fields.Char("Remark", tracking=True)
    consumption = fields.Float(string="Total Consumption", tracking=True, readonly=True)
    added = fields.Float(
        string="Total Recevied", compute="_get_added", store=True, tracking=True
    )

    # related
    spare_part_no = fields.Char(
        "Spare part no", related="material_id.spare_part_no", tracking=True
    )
    unit = fields.Char("Unit", related="material_id.unit", tracking=True)
    rob = fields.Float("ROB", related="material_id.available_quantity", tracking=True)

    # relations
    material_id = fields.Many2one("ship.material", string="Material")
    batch_id = fields.Many2one(
        "ship.material.consumption.report.batch", string="Batch", readonly=True
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.depends("material_id", "batch_id")
    def _get_added(self):
        for record in self:
            batch_id = record.batch_id
            material_id = record.material_id
            model_name = "ship.material.assignment"
            assignment_count = self.env[model_name].search_count(
                [
                    ("material_id", "=", material_id.id),
                    ("start_time_of_use", ">=", batch_id.date_start),
                    ("end_time_of_use", "<=", batch_id.date_end),
                ]
            )
            record.added = assignment_count
