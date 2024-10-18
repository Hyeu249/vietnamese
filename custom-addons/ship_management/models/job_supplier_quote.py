# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from .common_utils import generate_token, format_field_date
from . import CONST
import logging
from odoo.exceptions import ValidationError
from . import listen


class JobSupplierQuoteTemplate(models.Model):
    _name = "ship.job.supplier.quote.template"
    _description = "Job supplier quote records"
    _inherit = ["mail.thread"]

    labor_cost = fields.Float("Labor cost", tracking=True)
    estimated_delivery_date = fields.Date("Estimated delivery date", tracking=True)
    note = fields.Char("Note", tracking=True)
    is_email_sent = fields.Boolean("Is email sent", default=False)
    is_responded = fields.Boolean("Is the supplier responded", default=False)
    # an access_token is a unique string that is automatically generated for each quote.
    access_token = fields.Char("Access Token", default=lambda self: generate_token())

    # compute fields
    not_allow_crew = fields.Boolean("Not allow crew", compute="_get_not_allow_crew")

    # relations
    supplier_id = None
    job_quote_id = None
    currency_id = None

    @api.depends("labor_cost")
    def _get_not_allow_crew(self):
        for record in self:
            group_xml_id = f"utilities.group_ship_ship_crew"
            record.not_allow_crew = self.env.user.has_group(group_xml_id)

    @api.model_create_multi
    def create(self, vals_list):
        result = super(JobSupplierQuoteTemplate, self).create(vals_list)
        listen.job_supplier_quote.call_on_create(self)

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(JobSupplierQuoteTemplate, self).write(vals)
        listen.job_supplier_quote.call_on_write(self, vals)

        return result

    def unlink(self):
        funcs = listen.job_supplier_quote.get_funcs_to_call_after_unlink(self)
        result = super(JobSupplierQuoteTemplate, self).unlink()

        for func in funcs:
            func()
        return result

    def send_email_to_supplier_for_quote(
        self,
        template="ship_management.quote_email_in_job_supplier_quote",
        path_segment="job-supplier-quote",
    ):
        self.ensure_one()
        """For sending email to suppliers"""
        self.ensure_one()
        email_template = self.env.ref(template)

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        params = f"supplier_ref={self.supplier_id.ref}&access_token={self.supplier_id.access_token}"
        reply_quote_url = f"{base_url}/{path_segment}/{self.ref}?{params}"

        context = {
            "self": self,
            "reply_quote_url": reply_quote_url,
        }

        email_template.email_from = self.get_smtp_user()
        email_template.with_context(context).send_mail(
            self.supplier_id.id, force_send=False
        )

    def send_email_to_supplier_to_notify_successed_quote(
        self, template="ship_management.selected_quote_email_in_job_supplier_quote"
    ):
        self.ensure_one()
        """Send email when the supplier is selected"""
        email_template = self.env.ref(template)

        context = {
            "self": self,
        }

        email_template.email_from = self.get_smtp_user()
        email_template.with_context(context).send_mail(
            self.supplier_id.id, force_send=False
        )

    def get_smtp_user(self):
        query = """
            SELECT * 
            FROM ir_mail_server 
        """
        self.env.cr.execute(query)
        outgoing_mail_servers = self.env.cr.fetchall()

        if outgoing_mail_servers:
            mail_server = outgoing_mail_servers[0]
            smtp_user = mail_server[9]

            return smtp_user


class JobSupplierQuote(models.Model):
    _name = "ship.job.supplier.quote"
    _description = "Job supplier quote records"
    _inherit = ["ship.job.supplier.quote.template"]
    _check_company_auto = True

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    supplier_id = fields.Many2one(
        "ship.supplier", string="Supplier", required=True, tracking=True
    )
    job_quote_id = fields.Many2one(
        "ship.job.quote", string="Job quote", required=True, tracking=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        required=True,
        default=lambda self: self.env.user.company_id.currency_id,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.job.supplier.quote"
            )
        result = super(JobSupplierQuote, self).create(vals_list)

        for record in result:
            record.send_email_to_supplier_for_quote()

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(JobSupplierQuote, self).write(vals)

        return result

    def unlink(self):
        for record in self:
            result = super(JobSupplierQuote, record).unlink()
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
