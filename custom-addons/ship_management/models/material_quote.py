# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
import logging
from datetime import timedelta
from odoo.exceptions import ValidationError

MAX_APPROVAL_STATUS_INDEX_TO_EDIT_QUANTITY = 1


class MaterialQuote(models.Model):
    _name = "ship.material.quote"
    _description = "Material quote records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    quantity = fields.Float("Quantity", tracking=True)
    preapproved_quantity = fields.Float("QLT pre-approved quantity", tracking=True)
    delivered_quantity = fields.Float("Delivered quantity", tracking=True)
    unit = fields.Char("Unit", related="material_id.unit", tracking=True)
    expected_delivery_date = fields.Date(
        "Expected delivery date",
        related="material_paint_quotes_request_id.expected_delivery_date",
        store=True,
        tracking=True,
    )
    deadline = fields.Date(
        "Deadline",
        related="material_paint_quotes_request_id.deadline",
        tracking=True,
    )
    delivered_at = fields.Datetime(
        "Delivered at",
        readonly=lambda self: not self.user.has_group("utilities.group_ship_admin"),
        tracking=True,
    )
    note = fields.Char("Note", tracking=True)
    unit_price = fields.Float("Unit price", compute="_get_unit_price", tracking=True)
    total_price = fields.Float("Total price", compute="_get_total_price", tracking=True)
    lowest_total_price = fields.Float(
        "Lowest total price", compute="_get_lowest_total_price", tracking=True
    )
    currency = fields.Char(
        "Currency",
        compute="_get_currency",
    )
    preselected_supplier = fields.Char(
        "Pre-selected supplier", compute="_get_preselected_supplier", tracking=True
    )
    average_quote_price = fields.Float(
        "Average quote price", compute="_calc_average_quote_price", tracking=True
    )
    is_selected_supplier_informed = fields.Boolean(
        "Is selected supplier informed", readonly=True
    )
    added_to_warehouse = fields.Boolean(
        "Are material entities added to warehouse",
        readonly=lambda self: not self.user.has_group("utilities.group_ship_admin"),
    )
    not_allowed_to_see_price = fields.Boolean(
        "Not allow crew",
        related="material_paint_quotes_request_id.not_allowed_to_see_price",
    )
    is_system_create = fields.Boolean(
        "is_system_create",
        readonly=lambda self: not self.user.has_group("utilities.group_ship_admin"),
    )
    is_quantity_readonly = fields.Boolean(
        "Is quantity readonly",
        compute="_get_is_quantity_readonly",
        store=False)
    is_preapproved_quantity_readonly = fields.Boolean(
        "Is approved quantity readonly",
        compute="_get_is_preapproved_quantity_readonly",
        store=False)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relation field
    approval_status = fields.Selection(
        related="material_paint_quotes_request_id.approval_status",
        string="Approval status",
        store=True,
    )

    quote_state = fields.Selection(
        CONST.QUOTE_STATE,
        default=CONST.NORMAL,
        string="Quote state",
        required=True,
        tracking=True,
    )

    material_type = fields.Selection(
        related="material_id.material_type",
        string="Material Type",
        tracking=True,
    )

    material_group = fields.Char(
        related="material_id.material_group_id.name",
        string="Material Group",
        store=True,
        tracking=True,
    )
    spare_part_no = fields.Char(
        "Spare part no", related="material_id.spare_part_no", tracking=True
    )

    internal_code = fields.Char(
        "Internal code", related="material_id.internal_code", tracking=True
    )
    available_quantity = fields.Float(
        "Available quantity",
        related="material_id.available_quantity",
    )

    # relations
    material_id = fields.Many2one("ship.material", string="Material", tracking=True)
    material_supplier_quote_id = fields.Many2one(
        "ship.material.supplier.quote",
        domain="[('material_quote_id', '=', id)]",
        string="Selected Material supplier",
        tracking=True,
    )
    material_supplier_quote_ids = fields.One2many(
        "ship.material.supplier.quote",
        "material_quote_id",
        string="Material supplier quote",
        tracking=True,
    )
    material_paint_quotes_request_id = fields.Many2one(
        "ship.material.paint.quotes.request",
        string="Material paint quotes request",
        readonly=True,
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_material_supplier_quote_id",
            "unique (material_supplier_quote_id)",
            "material_supplier_quote_id must be unique.",
        ),
    ]

    @api.constrains("material_id", "is_system_create")
    def only_1_system_quote_for_1_material(self):
        for record in self:
            quotes = self.search(
                [
                    ("material_id", "=", record.material_id.id),
                    ("company_id", "=", self.company_id.id),
                    ("approval_status", "!=", CONST.APPROVED),
                    ("approval_status", "!=", CONST.REJECTED),
                    ("is_system_create", "=", True),
                ]
            )
            message = "Báo giá vật tư được tạo 2 lần bởi system, trên 1 vật tư!!"
            if len(quotes) > 1:
                raise ValidationError(message)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.material.quote")
        return super(MaterialQuote, self).create(vals_list)

    def write(self, vals):
        self._post_chatter_message_to_related_model_on_write(
            vals,
            "material_paint_quotes_request_id",
            tracking_fields=["quantity", "preapproved_quantity", "material_supplier_quote_id"],
        )
        result = super(MaterialQuote, self).write(vals)
        for record in self:
            current_approval_status_index = record.\
                material_paint_quotes_request_id.\
                _get_index_of_current_approval_status()
            if "quantity" in vals and current_approval_status_index <= MAX_APPROVAL_STATUS_INDEX_TO_EDIT_QUANTITY:
                message = "Không được sửa số lượng dành cho cấp duyệt chuyên viên kỹ thuật trở lên, khi đang ở cấp duyệt thấp hơn chuyên viên kỹ thuật!"
                raise ValidationError(message)
            if "preapproved_quantity" in vals and current_approval_status_index > MAX_APPROVAL_STATUS_INDEX_TO_EDIT_QUANTITY:
                message = "Không được sửa số lượng mong muốn khi đã gửi duyệt lên chuyên viên kỹ thuật (hoặc cấp cao hơn)!"
                raise ValidationError(message)
            if "quantity" in vals and record.approval_status == CONST.APPROVED:
                message = "Không được sửa số lượng khi đã đơn đã được duyệt!"
                raise ValidationError(message)
            if "preapproved_quantity" in vals and record.approval_status == CONST.APPROVED:
                message = "Không được sửa số lượng đã duyệt!"
                raise ValidationError(message)

        return result

    def _get_is_quantity_readonly(self):
        for record in self:
            if record.approval_status == CONST.APPROVED:
                record.is_quantity_readonly = True
                return
            current_approval_status_index = record.\
                material_paint_quotes_request_id.\
                _get_index_of_current_approval_status()
            if current_approval_status_index <= MAX_APPROVAL_STATUS_INDEX_TO_EDIT_QUANTITY:
                record.is_quantity_readonly = True
                return
            record.is_quantity_readonly = False

    def _get_is_preapproved_quantity_readonly(self):
        for record in self:
            if record.approval_status == CONST.APPROVED:
                record.is_preapproved_quantity_readonly = True
                return
            current_approval_status_index = record.\
                material_paint_quotes_request_id.\
                _get_index_of_current_approval_status()
            if current_approval_status_index > MAX_APPROVAL_STATUS_INDEX_TO_EDIT_QUANTITY:
                record.is_preapproved_quantity_readonly = True
                return
            record.is_preapproved_quantity_readonly = False

    def _get_chatter_message_on_write(self, old_values, vals):
        """
        Get the chatter message on write.
        Args:
            old_values: a dict of old values of changed fields
            vals: the vals of the write method
        """
        material_type = (
            "phụ tùng" if self.material_type == CONST.SPARE_PART else "vật tư"
        )
        message_text = f"Báo giá {material_type} {self.material_id.name} (mã: \
            <b>{self.ref}</b>) đã được cập nhật với các thông tin sau: <br/>"
        for field in old_values:
            if old_values[field] != vals[field]:
                if field == "quantity":
                    message_text += (
                        f"Số lượng QLT duyệt: {old_values[field]} -> {vals[field]} <br/>"
                    )
                elif field == "preapproved_quantity":
                    message_text += (
                        f"Số lượng yêu cầu: {old_values[field]} -> {vals[field]} <br/>"
                    )
                elif field == "material_supplier_quote_id":
                    new_supplier_quote = (
                        self.env["ship.material.supplier.quote"].browse(vals[field])
                        if vals[field]
                        else None
                    )
                    new_supplier_quote_name = (
                        f"{new_supplier_quote.supplier_id.name} (Đơn giá: {new_supplier_quote.unit_price})"
                        if new_supplier_quote
                        else "Trống"
                    )

                    old_supplier_quote_name = (
                        f"{old_values[field].supplier_id.name} (Đơn giá: {old_values[field].unit_price})"
                        if old_values[field]
                        else "Trống"
                    )
                    message_text += f"Nhà cung cấp: {old_supplier_quote_name} -> {new_supplier_quote_name} <br/>"
                else:
                    message_text += (
                        f"{field}: {old_values[field]} -> {vals[field]} <br/>"
                    )

        return message_text

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _get_lowest_material_supplier_price(self):
        self.ensure_one()
        lowest_price = None
        lowest_supplier_quote = None

        for supplier_quote in self.material_supplier_quote_ids:
            supplier_price = supplier_quote.unit_price
            if lowest_price is None or supplier_price < lowest_price:
                if supplier_price != 0:
                    lowest_price = supplier_quote.unit_price
                    lowest_supplier_quote = supplier_quote

        self.material_supplier_quote_id = lowest_supplier_quote

    def _are_all_suppliers_have_priced(self):
        self.ensure_one()
        prices = [quote.unit_price for quote in self.material_supplier_quote_ids]
        is_all_have_price = all(price > 0 for price in prices)
        return is_all_have_price

    def _create_material_supplier_quotes(self):
        self.ensure_one()
        supplier_ids = self.material_id.supplier_ids
        for supplier in supplier_ids:
            self.env["ship.material.supplier.quote"].create(
                {
                    "unit_price": 0,
                    "material_quote_id": self.id,
                    "supplier_id": supplier.id,
                }
            )

    def action_send_email_batch(self):
        """For sending email to suppliers"""
        self.ensure_one()
        for supplier_quote in self.material_supplier_quote_ids:
            supplier_quote.action_send_email()

    def send_email_to_selected_provider(self):
        self.ensure_one()
        if self.material_supplier_quote_id:
            self.is_selected_supplier_informed = True
            try:
                self.material_supplier_quote_id.action_inform_selected_email()
            except Exception as e:
                self.is_selected_supplier_informed = False
                raise e

    def get_all_uninformed_quotes(self):
        """
        Get all quotes that are not informed to selected suppliers. Conditions:
        - is_selected_supplier_informed = False
        - delivered_at is False
        - approval_status = CONST.APPROVED
        """
        conditions = [
            ("is_selected_supplier_informed", "=", False),
            ("delivered_at", "=", False),
            ("approval_status", "=", CONST.APPROVED),
            ("quote_state", "=", CONST.NORMAL),
        ]
        return self.search(conditions)

    def _is_quote_approved(self):
        self.ensure_one()
        if self.approval_status == CONST.APPROVED and self.quote_state == CONST.NORMAL:
            return True
        else:
            return False

    def _is_not_informed(self):
        self.ensure_one()
        if self.is_selected_supplier_informed == False and self.delivered_at == False:
            return True
        else:
            return False

    def action_send_emails_to_all_uninformed_quotes(self):
        """
        Send email to all selected suppliers who are not informed yet.
        """
        for record in self.get_all_uninformed_quotes():
            record.send_email_to_selected_provider()

    def _add_material_entities_to_warehouse(self):
        self.ensure_one()
        quantity = self.delivered_quantity
        material_supplier_quote_id = self.material_supplier_quote_id
        material_id = self.material_id

        material_id._create_material_entities(quantity, material_supplier_quote_id.id)
        self.added_to_warehouse = True

    def action_confirm_delivered(self, delivered_quantity=None):
        """
        When user click on button "Delivered", automatically create new material entities
        """
        self.ensure_one()
        if self.approval_status != CONST.APPROVED:
            raise ValidationError("Material quote is not approved yet.")
        if self.delivered_at:
            raise ValidationError("Material quote is already marked as delivered.")
        if delivered_quantity and delivered_quantity != 0:
            self.delivered_quantity = delivered_quantity

        if not self.delivered_quantity:
            raise ValidationError("Không có số lượng thực tế!")

        self.delivered_at = fields.Datetime.now()
        self._add_material_entities_to_warehouse()

    def confirm_delivered_via_ref_code(self, ref_code):
        """
        When user enter ref code, automatically confirm delivered if a material quote with such ref code exists.
        """
        # get material quote with ref code
        material_quote = self.search([("ref", "=", ref_code)])
        if material_quote:
            material_quote.action_confirm_delivered()
        else:
            raise ValidationError("Material quote with such ref code does not exist.")

    @api.depends("material_supplier_quote_id")
    def _calc_average_quote_price(self):
        for record in self:
            if record.expected_delivery_date:
                last_3_times = self.env["ship.material.quote"].search(
                    [
                        ("approval_status", "=", CONST.APPROVED),
                        ("quote_state", "=", CONST.NORMAL),
                        ("material_id", "=", record.material_id.id),
                        ("expected_delivery_date", "<", record.expected_delivery_date),
                    ],
                    limit=3,
                )

                count = len(last_3_times)

                if count == 0:
                    record.average_quote_price = 0
                    return

                average_unit_prices = sum(last_3_times.mapped("unit_price")) / count
                quantities = sum(last_3_times.mapped("quantity"))

                if average_unit_prices and quantities:
                    average_price = average_unit_prices * quantities
                    record.average_quote_price = average_price
                else:
                    record.average_quote_price = 0
            else:
                record.average_quote_price = 0

    @api.depends("material_supplier_quote_id")
    def _get_unit_price(self):
        for record in self:
            if record.material_supplier_quote_id:
                record.unit_price = record.material_supplier_quote_id.unit_price
            else:
                record.unit_price = 0

    @api.depends("material_supplier_quote_id")
    def _get_currency(self):
        for record in self:
            if record.material_supplier_quote_id:
                record.currency = record.material_supplier_quote_id.currency_id.name
            else:
                record.currency = ""

    @api.depends("unit_price", "delivered_quantity", "quantity")
    def _get_total_price(self):
        for record in self:
            if record.delivered_quantity:
                record.total_price = record.unit_price * record.delivered_quantity
            else:
                record.total_price = record.unit_price * record.quantity

    @api.depends("approval_status", "quantity", "material_supplier_quote_ids")
    def _get_lowest_total_price(self):
        for record in self:
            unit_prices = record.material_supplier_quote_ids.mapped("unit_price")
            unit_prices = [x for x in unit_prices if x != 0]
            if unit_prices:
                unit_prices.sort()
                unit_price = unit_prices[0]
                record.lowest_total_price = unit_price * record.quantity
            else:
                record.lowest_total_price = 0

    def _get_preselected_supplier(self):
        for record in self:
            if record.expected_delivery_date:
                material_quote_id = self.env["ship.material.quote"].search(
                    [
                        ("approval_status", "=", CONST.APPROVED),
                        ("material_id", "=", record.material_id.id),
                        ("expected_delivery_date", "<", record.expected_delivery_date),
                    ],
                    order="expected_delivery_date desc",
                    limit=1,
                )

                supplier_id = material_quote_id.material_supplier_quote_id.supplier_id

                if supplier_id:
                    record.preselected_supplier = (
                        f"{supplier_id.name}({material_quote_id.total_price})"
                    )
                else:
                    record.preselected_supplier = ""

            else:
                record.preselected_supplier = ""

    def _get_emails(self):
        emails = [
            supplier_quote.supplier_id.email
            for supplier_quote in self.material_supplier_quote_ids
        ]
        return emails

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
