# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class MaterialSupplierQuote(models.Model):
    _name = "docking.material.supplier.quote"
    _description = "Material supplier quote records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    unit_price = fields.Integer("Unit price", tracking=True)
    estimated_delivery_date = fields.Date("Estimated delivery date", tracking=True)
    note = fields.Char("Note", tracking=True)
    is_responded = fields.Boolean("Is Responded", tracking=True)
    material_type = fields.Selection(
        CONST.MATERIAL_TYPE,
        related="material_quote_id.material_survey_data_id.material_survey_metadata_id.material_type",
        string="Material Type",
        tracking=True,
    )
    is_email_sent = fields.Boolean("Is email sent", default=False)

    # relations
    material_quote_id = fields.Many2one(
        "docking.material.quote", string="Material quote", tracking=True
    )
    supplier_id = fields.Many2one("docking.supplier", string="Supplier", tracking=True)
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
                "docking.material.supplier.quote"
            )
        return super(MaterialSupplierQuote, self).create(vals_list)

    def write(self, vals):
        self.ensure_one()
        old_unit_price = self.unit_price
        result = super(MaterialSupplierQuote, self).write(vals)
        new_unit_price = self.unit_price

        if "unit_price" in vals:
            if old_unit_price != new_unit_price:
                request = self.material_quote_id.material_quote_request_id
                request._check_supplier_quote_status_is_complete()

        return result

    def name_get(self):
        result = []
        for report in self:
            supplier_name = report.supplier_id.name
            ref_name = report.ref or _("New")
            code = f"{ref_name}({supplier_name})"
            name = code if supplier_name else ref_name
            name = f"{name}. Đơn giá: {report.unit_price}"
            result.append((report.id, name))
        return result

    def send_mail_to_supplier(self):
        self.is_email_sent = True
        docking_plan_id = self.material_quote_id.material_survey_data_id.docking_plan_id
        self.supplier_id.send_material_quote_for_supplier_email(docking_plan_id.ref)

    def get_all_unsent_supplier_quotes(self):
        supplier_group = self.material_quote_id._get_supplier_group_id()
        material_quote_flow = "material_quote_id.approval_status"
        conditions = [
            ("is_email_sent", "=", False),
            (material_quote_flow, "=", supplier_group.id),
        ]
        return self.search(conditions)

    def action_send_emails_to_all_unsent_supplier_quotes(self):
        for record in self.get_all_unsent_supplier_quotes():
            record.send_mail_to_supplier()
