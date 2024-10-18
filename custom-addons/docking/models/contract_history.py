# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class ContractHistory(models.Model):
    _name = "docking.contract.history"
    _description = "Contract History records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    html = fields.Html("Html", tracking=True)

    # relations
    contract_id = fields.Many2one(
        "docking.contract",
        string="Contract",
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
            model_name = "docking.contract.history"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        return super(ContractHistory, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            date_format = "%d-%m-%Y %H:%M:%S"
            create_date = report.create_date.strftime(date_format)
            name = create_date or _("New")
            result.append((report.id, name))
        return result
