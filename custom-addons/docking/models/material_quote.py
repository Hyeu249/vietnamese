# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
from ...supplier_portal.help_func import generate_qr_code_base64


class MaterialQuote(models.Model):
    _name = "docking.material.quote"
    _description = "Báo giá vật tư-docking"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    note = fields.Char("Note", tracking=True)
    expected_delivery_date = fields.Date("Expected delivery date", tracking=True)
    deadline = fields.Date("Deadline", tracking=True)
    delivered_at = fields.Date("Delivered at", tracking=True)
    is_selected_supplier_informed = fields.Boolean(
        "Is selected supplier informed", default=False
    )
    added_to_warehouse = fields.Boolean("added to warehouse")
    qr_code = fields.Image("QR code", compute="_get_qr_code", tracking=True,
                           max_width=CONST.MAX_IMAGE_UPLOAD_WIDTH,
                           max_height=CONST.MAX_IMAGE_UPLOAD_HEIGHT)
    total_price = fields.Float(
        "Total price",
        compute="_get_total_price",
        tracking=True,
    )

    # related
    material_name = fields.Char(
        "Material name",
        related="material_survey_data_id.material_survey_metadata_id.name",
        store=True,
        tracking=True,
    )
    selected_supplier_name = fields.Char(
        "Selected supplier name",
        related="material_supplier_quote_id.supplier_id.name",
        store=True,
        tracking=True,
    )
    unit_price = fields.Integer(
        "Unit price",
        related="material_supplier_quote_id.unit_price",
        store=True,
        tracking=True,
    )

    quantity = fields.Float(
        "Quantity",
        related="material_survey_data_id.quantity",
        store=True,
        tracking=True,
    )
    delivered_quantity = fields.Float(
        "Delivered quantity",
        tracking=True,
    )
    name_for_noti = fields.Char(
        "Name for noti",
        related="material_survey_data_id.material_survey_metadata_id.name",
        store=True,
        tracking=True,
    )
    docking_plan_id = fields.Many2one(
        "docking.docking.plan",
        related="material_survey_data_id.docking_plan_id",
        string="Docking plan",
        tracking=True,
    )

    # relations
    material_supplier_quote_id = fields.Many2one(
        "docking.material.supplier.quote",
        domain="[('material_quote_id', '=', id)]",
        string="Selected material supplier quote",
        tracking=True,
    )
    material_supplier_quote_ids = fields.One2many(
        "docking.material.supplier.quote",
        "material_quote_id",
        string="Material supplier quotes",
        tracking=True,
    )
    material_survey_data_id = fields.Many2one(
        "docking.material.survey.data",
        string="Material survey data",
        tracking=True,
    )
    expected_cost_report_id = fields.Many2one(
        "docking.expected.cost.report",
        string="Expected cost report",
        tracking=True,
    )
    cost_settlement_report_id = fields.Many2one(
        "docking.cost.settlement.report",
        string="Cost Settlement Report",
        tracking=True,
    )
    material_quote_request_id = fields.Many2one(
        "docking.material.quote.request",
        string="Material quote request",
        tracking=True,
    )

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_material_survey_data_id",
            "unique (material_survey_data_id)",
            "material_survey_data_id must be unique.",
        ),
    ]

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("docking.material.quote")

        results = super(MaterialQuote, self).create(vals_list)
        return results

    def write(self, vals):
        if not self.are_only_approval_fields_changed(vals):
            # post chatter message to expected cost report
            self._post_chatter_message_to_related_model_on_write(
                vals,
                "expected_cost_report_id",
            )

            # post chatter message to material quote request
            self._post_chatter_message_to_related_model_on_write(
                vals,
                "material_quote_request_id",
                tracking_fields=[
                    "material_supplier_quote_id",
                    "quantity",
                    "unit_price",
                ],
            )

        result = super(MaterialQuote, self).write(vals)

        if "approval_status" in vals:
            if self.is_at_this_approval_level(CONST.SUPPLIER):
                if not self.material_supplier_quote_ids:
                    self._create_material_supplier_quotes()
            if self.is_at_this_approval_level(CONST.MATERIAL_EXPERT):
                if self.is_second_time_level():
                    self._set_material_supplier_by_lowest_price()

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _create_material_supplier_quotes(self):
        self.ensure_one()
        supplier_ids = (
            self.material_survey_data_id.material_survey_metadata_id.supplier_ids
        )
        for supplier in supplier_ids:
            self.env["docking.material.supplier.quote"].create(
                {
                    "unit_price": 0,
                    "material_quote_id": self.id,
                    "supplier_id": supplier.id,
                }
            )

    def send_mail_to_suppliers(self):
        docking_plan_id = self.material_survey_data_id.docking_plan_id
        for supplier_quote_id in self.material_supplier_quote_ids:
            supplier_id = supplier_quote_id.supplier_id
            supplier_id.send_material_quote_for_supplier_email(docking_plan_id.ref)

    def send_mail_to_selected_supplier(self):
        material_supplier_quote = self.material_supplier_quote_id
        if material_supplier_quote:
            supplier_id = self.material_supplier_quote_id.supplier_id
            supplier_id.send_selected_material_supplier_email(material_supplier_quote)

    def get_all_uninformed_quotes(self):
        expected_cost_report_approval_status = "expected_cost_report_id.approval_status"
        conditions = [
            ("is_selected_supplier_informed", "=", False),
            ("delivered_at", "=", False),
            ("approval_status", "=", CONST.APPROVED),
            (expected_cost_report_approval_status, "=", CONST.APPROVED),
        ]
        return self.search(conditions)

    def action_send_emails_to_all_uninformed_quotes(self):
        for record in self.get_all_uninformed_quotes():
            record.is_selected_supplier_informed = True
            record.send_mail_to_selected_supplier()

    def _set_material_supplier_by_lowest_price(self):
        self.ensure_one()
        lowest_price = None
        lowest_supplier_quote = None

        for supplier_quote in self.material_supplier_quote_ids:
            if lowest_price is None or supplier_quote.unit_price < lowest_price:
                lowest_price = supplier_quote.unit_price
                lowest_supplier_quote = supplier_quote

        if lowest_supplier_quote:
            self.material_supplier_quote_id = lowest_supplier_quote

    def action_confirm_delivered(self, delivered_quantity=None):
        self.ensure_one()
        if self.approval_status != CONST.APPROVED:
            raise ValidationError("Material quote is not approved yet.")
        if self.delivered_at:
            raise ValidationError("Material quote is already marked as delivered.")
        if delivered_quantity and delivered_quantity != 0:
            self.delivered_quantity = delivered_quantity
        self.delivered_at = fields.Datetime.now()
        self.added_to_warehouse = True

    @api.depends("ref")
    def _get_qr_code(self):
        for record in self:
            record.qr_code = generate_qr_code_base64(record.ref)

    @api.depends("unit_price", "quantity")
    def _get_total_price(self):
        for record in self:
            if record.unit_price and record.quantity:
                record.total_price = record.unit_price * record.quantity
            else:
                record.total_price = 0

    def _arise_or_approved_survey(self):
        self.ensure_one()
        survey = self.material_survey_data_id

        if survey._is_arise() or survey._is_approved():
            return True

        return False

    def _is_valid_quote(self):
        self.ensure_one()
        survey = self.material_survey_data_id

        if survey._is_arise() and self._is_approved():
            return True
        if not survey._is_arise() and survey._is_approved() and self._is_approved():
            return True

        return False

    def _get_chatter_message_on_write(self, old_values, vals):
        """
        Get the chatter message on write.
        Args:
            old_values: a dict of old values of changed fields
            vals: the vals of the write method
        """
        message_text = f"Báo giá vật tư {self.material_name} (mã: \
            <b>{self.ref}</b>) đã được cập nhật với các thông tin sau: <br/>"
        for field in old_values:
            if old_values[field] != vals[field]:
                if field == "material_supplier_quote_id":
                    # get supplier
                    model_name = "docking.material.supplier.quote"
                    material_supplier = self.env[model_name].browse(vals[field])
                    if material_supplier:
                        supplier = material_supplier.supplier_id
                        message_text += f"Nhà cung cấp: {old_values[field].supplier_id.name} -> {supplier.name} <br/>"
                else:
                    message_text += (
                        f"{field}: {old_values[field]} -> {vals[field]} <br/>"
                    )
        return message_text

    def _are_all_suppliers_have_priced(self):
        self.ensure_one()
        prices = [quote.unit_price for quote in self.material_supplier_quote_ids]
        is_all_have_price = all(price > 0 for price in prices)
        return is_all_have_price

    def open_record(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
            "context": self.env.context,
        }
