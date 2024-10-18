# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from .common_utils import generate_token, format_field_date
from . import CONST
import logging


class MaterialSupplierQuote(models.Model):
    _name = "ship.material.supplier.quote"
    _description = "Material supplier quote records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    unit_price = fields.Float("Unit price", tracking=True)
    estimated_delivery_date = fields.Date("Estimated delivery date", tracking=True)
    note = fields.Text("Note", tracking=True)
    is_email_sent = fields.Boolean("Is email sent", default=False)
    is_responded = fields.Boolean("Is the supplier responded", default=False)
    not_allowed_to_see_price = fields.Boolean(
        "Not allow crew",
        related="material_quote_id.material_paint_quotes_request_id.not_allowed_to_see_price",
    )
    quote_date = fields.Date("Quote date", tracking=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    supplier_id = fields.Many2one("ship.supplier", string="Supplier", tracking=True)
    material_quote_id = fields.Many2one(
        "ship.material.quote", string="Material quote", tracking=True
    )
    material_paint_quotes_request_id = fields.Many2one(
        "ship.material.paint.quotes.request",
        related="material_quote_id.material_paint_quotes_request_id",
        string="Material paint quotes request",
        readonly=True,
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # an access_token is a unique string that is automatically generated for each quote.
    access_token = fields.Char("Access Token", default=lambda self: generate_token())

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.user.company_id.currency_id,
    )

    @api.constrains("unit_price")
    def _set_quote_date(self):
        for record in self:
            if record.unit_price > 0:
                record.quote_date = fields.Date().today()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.material.supplier.quote"
            )
        result = super(MaterialSupplierQuote, self).create(vals_list)

        for record in result:
            record.material_quote_id.material_paint_quotes_request_id._check_supplier_quote_status_is_complete()

        return result

    def write(self, vals):
        result = super(MaterialSupplierQuote, self).write(vals)

        for record in self:
            material_paint_quotes_request_id = (
                record.material_quote_id.material_paint_quotes_request_id
            )

            if material_paint_quotes_request_id:
                material_paint_quotes_request_id._check_supplier_quote_status_is_complete()

        return result

    def unlink(self):
        for record in self:
            material_paint_quotes_request_id = (
                record.material_quote_id.material_paint_quotes_request_id
            )
            result = super(MaterialSupplierQuote, record).unlink()

            if material_paint_quotes_request_id:
                material_paint_quotes_request_id._check_supplier_quote_status_is_complete()
        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.supplier_id.name or _("New")

            is_show_unit_price = self.env.context.get("show_unit_price")

            if is_show_unit_price:
                unit_price = str(report.unit_price)
                name = name + " - Đơn giá: " + "(" + unit_price + ")"

            result.append((report.id, name))
        return result

    def get_all_unsent_supplier_quotes(self):
        """
        Get all unsent supplier quotes. Conditions:
        - is_email_sent = False
        - material_quote_id.approval_status = CONST.SUPPLIER
        - material_quote_id.deadline is not set or material_quote_id.deadline >= today
        """
        conditions = [
            ("is_email_sent", "=", False),
            (
                "material_quote_id.approval_status",
                "=",
                CONST.SUPPLIER,
            ),
            "|",
            ("material_quote_id.deadline", "=", False),
            ("material_quote_id.deadline", ">=", fields.Date.today()),
        ]
        return self.search(conditions)

    def action_send_emails_to_all_unsent_supplier_quotes(self):
        for record in self.get_all_unsent_supplier_quotes():
            record.action_send_email()

    def action_send_email(self):
        """For sending email to suppliers"""
        self.ensure_one()
        self.is_email_sent = True
        try:
            # get material info
            material = self.env["ship.material"].search(
                [("id", "=", self.material_quote_id.material_id.id)]
            )
            template = self.env.ref(
                "ship_management.email_template_material_rfq_request"
            ).id
            reply_quote_url = (
                "{base_url}/vendor_rfmq/{ref}?access_token={token}".format(
                    base_url=self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("web.base.url"),
                    ref=self.ref,
                    token=self.access_token,
                )
            )
            context = {
                "supplier_name": self.supplier_id.name,
                "prod_name": material.name,
                "prod_origin": material.origin,
                "prod_description": material.description,
                "unit": "chiếc",
                "quantity": self.material_quote_id.quantity,
                "expected_delivery_date": format_field_date(
                    self.material_quote_id.expected_delivery_date
                ),
                "deadline": format_field_date(self.material_quote_id.deadline),
                "reply_quote_url": reply_quote_url,
            }
            email_values = {
                "email_to": self.supplier_id.email,
            }
            self.env["mail.template"].browse(template).with_context(context).send_mail(
                self.id, email_values=email_values, force_send=False
            )
        except Exception as e:
            self.is_email_sent = False
            logging.error(e)

    def action_inform_selected_email(self):
        """Send email when the supplier is selected"""
        # get material info
        material = self.env["ship.material"].search(
            [("id", "=", self.material_quote_id.material_id.id)]
        )
        template = self.env.ref(
            "ship_management.email_template_material_rfq_mark_done"
        ).id

        supplier_ref = self.supplier_id.ref
        access_token = self.supplier_id.access_token
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        params = f"supplier_ref={supplier_ref}&access_token={access_token}"
        portal_access_url = f"{base_url}/material-supplier-quote/{self.ref}?{params}"

        context = {
            "supplier_name": self.supplier_id.name,
            "prod_name": material.name,
            "prod_origin": material.origin,
            "prod_description": material.description,
            "quote_ref": self.ref,
            "unit": material.unit,
            "quantity": self.material_quote_id.quantity,
            "unit_price": str(self.unit_price).replace(".", ","),
            "currency": self.currency_id.symbol,
            "total_price": str(
                self.unit_price * self.material_quote_id.quantity
            ).replace(".", ","),
            "estimated_delivery_date": format_field_date(self.estimated_delivery_date),
            "portal_access_url": portal_access_url,
        }
        email_values = {
            "email_to": self.supplier_id.email,
        }
        self.env["mail.template"].browse(template).with_context(context).send_mail(
            self.id, email_values=email_values, force_send=False
        )
