# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class ContractPaymentInstalment(models.Model):
    _name = "docking.contract.payment.instalment"
    _description = "Contract payment instalment records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    status = fields.Selection(
        CONST.PAYMENT_STATUS,
        string="Status",
        default=CONST.PENDING,
        tracking=True,
    )
    sequence = fields.Integer("Sequence", tracking=True)
    percentage = fields.Float("Percentage", tracking=True)
    amount = fields.Float("Amount", compute="_get_amount", tracking=True)
    paid_at = fields.Date("Paid at", tracking=True)
    attachment = fields.Binary("Attachment", tracking=True)

    _order = "sequence ASC"

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
            model_name = "docking.contract.payment.instalment"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        return super(ContractPaymentInstalment, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    @api.depends("percentage", "contract_id")
    def _get_amount(self):
        for record in self:
            record.amount = (record.percentage / 100) * record.contract_id.total_price

    def _is_paid(self):
        self.ensure_one()
        return self.status == CONST.COMPLETED
