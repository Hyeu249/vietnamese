# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from .common_utils import generate_token, format_field_date
from . import CONST
import logging


class PaintSupplierQuote(models.Model):
    _name = "ship.paint.supplier.quote"
    _description = "Paint supplier quote records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    unit_price = fields.Float("Unit price", tracking=True)
    estimated_delivery_date = fields.Date("Estimated delivery date", tracking=True)
    note = fields.Char("Note", tracking=True)
    is_email_sent = fields.Boolean("Is email sent", default=False)
    is_responded = fields.Boolean("Is the supplier responded", default=False)
    not_allowed_to_see_price = fields.Boolean(
        "Not allow crew",
        related="paint_quote_id.material_paint_quotes_request_id.not_allowed_to_see_price",
    )
    quote_date = fields.Date("Quote date", tracking=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    supplier_id = fields.Many2one("ship.supplier", string="Supplier", tracking=True)
    paint_quote_id = fields.Many2one(
        "ship.paint.quote", string="Paint quote", tracking=True
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
                "ship.paint.supplier.quote"
            )
        result = super(PaintSupplierQuote, self).create(vals_list)

        for record in result:
            record.paint_quote_id.material_paint_quotes_request_id._check_supplier_quote_status_is_complete()

        return result

    def write(self, vals):
        result = super(PaintSupplierQuote, self).write(vals)

        for record in self:
            material_paint_quotes_request_id = (
                record.paint_quote_id.material_paint_quotes_request_id
            )

            if material_paint_quotes_request_id:
                material_paint_quotes_request_id._check_supplier_quote_status_is_complete()

        return result

    def unlink(self):
        for record in self:
            material_paint_quotes_request_id = (
                record.paint_quote_id.material_paint_quotes_request_id
            )
            result = super(PaintSupplierQuote, record).unlink()

            if material_paint_quotes_request_id:
                material_paint_quotes_request_id._check_supplier_quote_status_is_complete()
        return result

    def name_get(self):
        result = []
        for report in self:
            name = (
                f"{report.ref}({report.supplier_id.name}). Đơn giá: {report.unit_price}"
                or _("New")
            )
            result.append((report.id, name))
        return result

    def get_all_unsent_supplier_quotes(self):
        """
        Get all unsent supplier quotes. Conditions:
        - is_email_sent = False
        - paint_quote_id.approval_status = CONST.SUPPLIER
        - paint_quote_id.deadline is not set or paint_quote_id.deadline >= today
        """
        conditions = [
            ("is_email_sent", "=", False),
            (
                "paint_quote_id.approval_status",
                "=",
                CONST.SUPPLIER,
            ),
            "|",
            ("paint_quote_id.deadline", "=", False),
            ("paint_quote_id.deadline", ">=", fields.Date.today()),
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
            # get paint info
            paint = self.env["ship.paint"].search(
                [("id", "=", self.paint_quote_id.paint_id.id)]
            )
            template = self.env.ref(
                "ship_management.email_template_paint_rfq_request"
            ).id
            reply_quote_url = (
                "{base_url}/vendor_rfpq/{ref}?access_token={token}".format(
                    base_url=self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("web.base.url"),
                    ref=self.ref,
                    token=self.access_token,
                )
            )
            context = {
                "supplier_name": self.supplier_id.name,
                "prod_name": paint.name,
                "prod_origin": paint.origin,
                "prod_description": paint.description,
                "unit": "lít",
                "quantity": self.paint_quote_id.quantity_liter,
                "expected_delivery_date": format_field_date(
                    self.paint_quote_id.expected_delivery_date
                ),
                "deadline": format_field_date(self.paint_quote_id.deadline),
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
        # get paint info
        paint = self.env["ship.paint"].search(
            [("id", "=", self.paint_quote_id.paint_id.id)]
        )
        template = self.env.ref("ship_management.email_template_paint_rfq_mark_done").id

        supplier_ref = self.supplier_id.ref
        access_token = self.supplier_id.access_token
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        params = f"supplier_ref={supplier_ref}&access_token={access_token}"
        portal_access_url = f"{base_url}/paint-supplier-quote/{self.ref}?{params}"

        context = {
            "supplier_name": self.supplier_id.name,
            "prod_name": paint.name,
            "prod_origin": paint.origin,
            "prod_description": paint.description,
            "quote_ref": self.ref,
            "unit": "lít",
            "quantity": self.paint_quote_id.quantity_liter,
            "unit_price": str(self.unit_price).replace(".", ","),
            "currency": self.currency_id.symbol,
            "total_price": str(
                self.unit_price * self.paint_quote_id.quantity_liter
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
