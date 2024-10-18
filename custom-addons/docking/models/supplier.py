# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from ...ship_management.models.common_utils import generate_token, format_field_date
import logging
from odoo.exceptions import ValidationError


class Supplier(models.Model):
    _name = "docking.supplier"
    _description = "Supplier records"
    _inherit = ["utilities.notification"]

    name = fields.Char("Name", required=True, tracking=True)
    email = fields.Char("Email", required=True, tracking=True)
    address = fields.Char("Address", tracking=True)
    access_token = fields.Char(
        "Access Token for supplier quote portal", default=lambda self: generate_token()
    )

    # relations
    material_survey_metadata_ids = fields.Many2many(
        "docking.material.survey.metadata",
        string="Material survey metadata",
        tracking=True,
    )
    job_ids = fields.Many2many("docking.job", string="Job", tracking=True)
    material_supplier_quote_ids = fields.One2many(
        "docking.material.supplier.quote",
        "supplier_id",
        string="Material supplier quote",
        tracking=True,
    )
    job_supplier_quote_ids = fields.One2many(
        "docking.job.supplier.quote",
        "supplier_id",
        string="Job supplier quote",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("docking.supplier")
        return super(Supplier, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.email or _("New")
            result.append((report.id, name))
        return result

    def send_material_quote_for_supplier_email(self, quote_ref):
        self.ensure_one()
        try:
            path = f"docking/docking-plan/{quote_ref}"
            template = self.env.ref("docking.material_quote_for_supplier_template").id
            portal_access_url = self._get_portal_access_url(path)
            email_values = self._get_email_values()

            context = {
                "supplier_name": self.name,
                "portal_access_url": portal_access_url,
            }

            self._send_email(self.id, template, context, email_values)
        except Exception as e:
            logging.error(e)
            raise e

    def send_job_quote_for_supplier_email(self, job_supplier_quote):
        self.ensure_one()
        try:
            job_id = job_supplier_quote.job_quote_id.job_id
            path = f"docking/job-supplier-quote/{job_supplier_quote.ref}"
            template = self.env.ref("docking.job_quote_for_supplier_template").id
            reply_quote_url = self._get_portal_access_url(path)
            email_values = self._get_email_values()

            context = {
                "supplier_name": self.name,
                "job_name": job_id.name,
                "job_description": job_id.description,
                "expected_delivery_date": format_field_date(
                    job_supplier_quote.job_quote_id.expected_delivery_date
                ),
                "deadline": format_field_date(job_supplier_quote.job_quote_id.deadline),
                "reply_quote_url": reply_quote_url,
            }

            self._send_email(self.id, template, context, email_values)

        except Exception as e:
            raise e

    def send_selected_material_supplier_email(self, material_supplier_quote):
        material_id = (
            material_supplier_quote.material_quote_id.material_survey_data_id.material_survey_metadata_id
        )
        path = f"docking/material-supplier-quote/{material_supplier_quote.ref}"
        template_xml_id = "docking.material_quote_for_supplier_mark_done_template"
        template = self.env.ref(template_xml_id).id
        portal_access_url = self._get_portal_access_url(path)
        email_values = self._get_email_values()

        material_quote_id = material_supplier_quote.material_quote_id
        context = {
            "supplier_name": self.name,
            "prod_name": material_id.name,
            "prod_origin": material_id.origin,
            "prod_description": material_id.description,
            "quote_ref": material_quote_id.ref,
            "unit": "chiếc",
            "quantity": material_quote_id.quantity,
            "unit_price": str(material_supplier_quote.unit_price).replace(".", ","),
            "currency": material_supplier_quote.currency_id.symbol,
            "total_price": str(
                material_supplier_quote.unit_price * material_quote_id.quantity
            ).replace(".", ","),
            "estimated_delivery_date": format_field_date(
                material_supplier_quote.estimated_delivery_date
            ),
            "portal_access_url": portal_access_url,
        }

        self._send_email(self.id, template, context, email_values)

    def send_selected_job_supplier_email(self, job_supplier_quote):
        job_id = job_supplier_quote.job_quote_id.job_id
        template = self.env.ref("docking.job_quote_for_supplier_mark_done_template").id
        email_values = self._get_email_values()

        context = {
            "supplier_name": self.name,
            "job_name": job_id.name,
            "job_description": job_id.description,
            "quote_ref": job_supplier_quote.ref,
            "labor_cost": str(job_supplier_quote.labor_cost).replace(".", ","),
            "currency": job_supplier_quote.currency_id.symbol,
            "estimated_delivery_date": format_field_date(
                job_supplier_quote.estimated_delivery_date
            ),
        }

        self._send_email(self.id, template, context, email_values)

    def _get_email_values(self):
        return {
            "email_to": self.email,
        }

    def _get_portal_access_url(self, path):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        params = f"supplier_ref={self.ref}&access_token={self.access_token}"
        portal_access_url = f"{base_url}/{path}?{params}"

        return portal_access_url

    def _send_email(self, record_id, template, context, email_values, force_send=False):
        return (
            self.env["mail.template"]
            .browse(template)
            .with_context(context)
            .send_mail(record_id, email_values=email_values, force_send=False)
        )

    def refresh_single_supplier_quote_portal_access_token(self):
        self.ensure_one()
        self.access_token = generate_token()

    def send_email_response_portal_request_access(self, route_request):
        self.ensure_one()
        self.refresh_single_supplier_quote_portal_access_token()
        try:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            template = self.env.ref(
                "docking.docking_email_access_supplier_quote_portal_response"
            ).id
            portal_access_url = f"{base_url}{route_request}?supplier_ref={self.ref}&access_token={self.access_token}".format(
                base_url=self.env["ir.config_parameter"]
                .sudo()
                .get_param("web.base.url"),
                ref=self.ref,
                token=self.access_token,
            )
            context = {
                "supplier_name": self.name,
                "portal_access_url": portal_access_url,
            }
            email_values = {
                "email_to": self.email,
            }
            self.env["mail.template"].browse(template).with_context(context).send_mail(
                self.id, email_values=email_values, force_send=False
            )
        except Exception as e:
            logging.error(e)
            raise e
