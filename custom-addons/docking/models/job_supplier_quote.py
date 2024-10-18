# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class JobSupplierQuote(models.Model):
    _name = "docking.job.supplier.quote"
    _description = "Job supplier quote records"
    _inherit = ["ship.job.supplier.quote.template"]
    _check_company_auto = True

    # relations
    supplier_id = fields.Many2one("docking.supplier", string="Supplier", tracking=True)
    job_quote_id = fields.Many2one(
        "docking.job.quote", string="Job quote", tracking=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.user.company_id.currency_id,
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
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "docking.job.supplier.quote"
            )
        result = super(JobSupplierQuote, self).create(vals_list)

        for record in result:
            template = "docking.quote_email_in_docking_job_supplier_quote"
            path_segment = "docking/job-supplier-quote"
            record.send_email_to_supplier_for_quote(template, path_segment)

        return result

    def name_get(self):
        result = []
        for report in self:
            ref = report.ref
            supplier_name = report.supplier_id.name
            labor_cost = report.labor_cost
            name = f"{ref}({supplier_name}). Đơn giá: {labor_cost}"
            result.append((report.id, name))
        return result
