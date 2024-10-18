# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from .common_utils import generate_token
import logging
from . import CONST


class Supplier(models.Model):
    _name = "ship.supplier"
    _description = "Supplier records"
    _inherit = ["utilities.notification"]

    name = fields.Char("Name", required=True, tracking=True)
    email = fields.Char("Email", required=True, tracking=True)
    address = fields.Char("Address", tracking=True)
    phone = fields.Char("Phone", tracking=True)
    classified_for_material = fields.Boolean(
        "For material",
        compute="_calc_classified_for_material",
        store=True,
        tracking=True,
    )
    classified_for_paint = fields.Boolean(
        "For paint",
        compute="_calc_classified_for_paint",
        store=True,
        tracking=True,
    )
    classified_for_job = fields.Boolean(
        "For job",
        compute="_calc_classified_for_job",
        store=True,
        tracking=True,
    )
    access_token = fields.Char(
        "Access Token for supplier quote portal", default=lambda self: generate_token()
    )

    # relations
    classify_ids = fields.Many2many("ship.classify", string="Classified", tracking=True)
    material_ids = fields.Many2many("ship.material", string="Material", tracking=True)
    job_ids = fields.Many2many("ship.job", string="Job", tracking=True)
    paint_ids = fields.Many2many("ship.paint", string="Paint", tracking=True)
    port_ids = fields.One2many("ship.port", "supplier_id", string="Job", tracking=True)

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.supplier")
        return super(Supplier, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result

    def write(self, vals):
        old_classified_for_material = self.classified_for_material
        old_classified_for_paint = self.classified_for_paint
        old_classified_for_job = self.classified_for_job
        result = super(Supplier, self).write(vals)
        new_classified_for_material = self.classified_for_material
        new_classified_for_paint = self.classified_for_paint
        new_classified_for_job = self.classified_for_job

        if old_classified_for_material == True:
            if new_classified_for_material == False:
                self.write({"material_ids": [(5, 0, 0)]})

        if old_classified_for_paint == True:
            if new_classified_for_paint == False:
                self.write({"paint_ids": [(5, 0, 0)]})

        if old_classified_for_job == True:
            if new_classified_for_job == False:
                self.write({"job_ids": [(5, 0, 0)]})

        return result

    def action_refresh_all_supplier_quote_portal_access_token(self):
        for record in self.search([]):
            record.access_token = generate_token()

    def refresh_single_supplier_quote_portal_access_token(self):
        self.ensure_one()
        self.access_token = generate_token()

    def send_email_response_portal_request_access(self, route_request):
        self.ensure_one()
        self.refresh_single_supplier_quote_portal_access_token()
        try:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            template = self.env.ref(
                "ship_management.email_access_supplier_quote_portal_response"
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

    def send_email_notify_quote_portal_change(self, quote_req_ref, quote_req_deadline):
        self.ensure_one()
        try:
            template = self.env.ref(
                "ship_management.email_notify_supplier_quote_portal_change"
            ).id

            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            params = f"supplier_ref={self.ref}&access_token={self.access_token}"
            portal_access_url = (
                f"{base_url}/material-paint-quotes/{quote_req_ref}?{params}"
            )

            context = {
                "supplier_name": self.name,
                "quote_req_deadline": quote_req_deadline,
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

    # def send_email_notify_fuel_quote_portal_change(self):
    #     self.ensure_one()
    #     try:
    #         template = self.env.ref(
    #             "ship_management.email_notify_supplier_quote_portal_change"
    #         ).id
    #         portal_access_url = (
    #             "{base_url}/vendor_rfuq/{ref}?access_token={token}".format(
    #                 base_url=self.env["ir.config_parameter"]
    #                 .sudo()
    #                 .get_param("web.base.url"),
    #                 ref=self.ref,
    #                 token=self.access_token,
    #             )
    #         )
    #         context = {
    #             "supplier_name": self.name,
    #             "portal_access_url": portal_access_url,
    #         }
    #         email_values = {
    #             "email_to": self.email,
    #         }
    #         self.env["mail.template"].browse(template).with_context(context).send_mail(
    #             self.id, email_values=email_values, force_send=False
    #         )
    #     except Exception as e:
    #         logging.error(e)
    #         raise e

    @api.depends("classify_ids")
    def _calc_classified_for_material(self):
        for record in self:
            material = lambda c: c.name == CONST.VAT_TU

            if record.classify_ids.filtered(material):
                record.classified_for_material = True
            else:
                record.classified_for_material = False

    @api.depends("classify_ids")
    def _calc_classified_for_paint(self):
        for record in self:
            paint = lambda c: c.name == CONST.SON
            if record.classify_ids.filtered(paint):
                record.classified_for_paint = True
            else:
                record.classified_for_paint = False

    @api.depends("classify_ids")
    def _calc_classified_for_job(self):
        for record in self:
            job = lambda c: c.name == CONST.CONG_VIEC
            if record.classify_ids.filtered(job):
                record.classified_for_job = True
            else:
                record.classified_for_job = False
