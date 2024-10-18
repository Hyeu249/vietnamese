# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
import logging
from .paint_history import ADD_ACTION, MINUS_ACTION
from datetime import timedelta
from odoo.exceptions import ValidationError

MAX_APPROVAL_STATUS_INDEX_TO_EDIT_QUANTITY_LITER = 1


class PaintQuote(models.Model):
    _name = "ship.paint.quote"
    _description = "PaintQuote records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    preapproved_quantity_liter = fields.Float("QLT pre-approved quantity liter", tracking=True)
    quantity_liter = fields.Float("Quantity liter", tracking=True)
    delivered_quantity_liter = fields.Float("Delivered quantity liter", tracking=True)
    expected_delivery_date = fields.Date(
        "Expected delivery date",
        related="material_paint_quotes_request_id.expected_delivery_date",
        tracking=True,
    )
    note = fields.Char("Note", tracking=True)
    deadline = fields.Date(
        "Deadline", related="material_paint_quotes_request_id.deadline", tracking=True
    )
    is_selected_supplier_informed = fields.Boolean(
        "Is selected supplier informed", readonly=True
    )
    delivered_at = fields.Datetime("Delivered at", readonly=True, tracking=True)
    added_to_warehouse = fields.Boolean(
        "Is paint added to the warehouse", readonly=True
    )
    unit_price = fields.Float("Unit price", compute="_get_unit_price", tracking=True)
    lowest_total_price = fields.Float(
        "Total price", compute="_get_lowest_total_price", tracking=True
    )

    average_quote_price = fields.Float(
        "Average quote price", compute="_calc_average_quote_price", tracking=True
    )
    currency = fields.Char(
        "Currency",
        compute="_get_currency",
    )
    quote_state = fields.Selection(
        CONST.QUOTE_STATE,
        default=CONST.NORMAL,
        string="Quote state",
        required=True,
        tracking=True,
    )
    not_allowed_to_see_price = fields.Boolean(
        "Not allow crew",
        related="material_paint_quotes_request_id.not_allowed_to_see_price",
    )
    is_quantity_liter_readonly = fields.Boolean(
        "Is quantity liter readonly",
        compute="_get_is_quantity_liter_readonly",
        store=False)
    is_preapproved_quantity_liter_readonly = fields.Boolean(
        "Is approved quantity liter readonly",
        compute="_get_is_preapproved_quantity_liter_readonly",
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

    # relations
    paint_id = fields.Many2one("ship.paint", string="Paint")
    paint_supplier_quote_id = fields.Many2one(
        "ship.paint.supplier.quote",
        domain="[('paint_quote_id', '=', id)]",
        string="Selected Paint supplier",
        tracking=True,
    )
    paint_supplier_quote_ids = fields.One2many(
        "ship.paint.supplier.quote",
        "paint_quote_id",
        string="Paint supplier quote",
        readonly=True,
        tracking=True,
    )
    material_paint_quotes_request_id = fields.Many2many(
        "ship.material.paint.quotes.request",
        "ship_paint_quote_ship_material_paint_quotes_request_rel",
        "paint_quote_id",
        "material_paint_quotes_request_id",
        string="Material paint quotes request",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.paint.quote")
        return super(PaintQuote, self).create(vals_list)

    def write(self, vals):
        self._post_chatter_message_to_related_model_on_write(
            vals,
            "material_paint_quotes_request_id",
            tracking_fields=["quantity_liter", "preapproved_quantity_liter", "paint_supplier_quote_id"],
        )
        result = super(PaintQuote, self).write(vals)

        for record in self:
            current_approval_status_index = record.\
                material_paint_quotes_request_id.\
                _get_index_of_current_approval_status()
            if "quantity_liter" in vals and current_approval_status_index <= MAX_APPROVAL_STATUS_INDEX_TO_EDIT_QUANTITY_LITER:
                message = "Không được sửa khối lượng dành cho cấp duyệt chuyên viên kỹ thuật trở lên, khi đang ở cấp duyệt thấp hơn chuyên viên kỹ thuật!"
                raise ValidationError(message)
            if "preapproved_quantity_liter" in vals and current_approval_status_index > MAX_APPROVAL_STATUS_INDEX_TO_EDIT_QUANTITY_LITER:
                message = "Không được sửa khối lượng (lít) mong muốn khi đã gửi duyệt lên chuyên viên kỹ thuật (hoặc cấp cao hơn)!"
                raise ValidationError(message)
            if "quantity_liter" in vals:
                record._not_allow_editing_quantity_once_the_quote_has_been_sent_to_ncc()

        return result

    def _get_is_quantity_liter_readonly(self):
        for record in self:
            if record.approval_status == CONST.APPROVED:
                record.is_quantity_liter_readonly = True
                return
            current_approval_status_index = record.\
                material_paint_quotes_request_id.\
                _get_index_of_current_approval_status()
            if current_approval_status_index <= MAX_APPROVAL_STATUS_INDEX_TO_EDIT_QUANTITY_LITER:
                record.is_quantity_liter_readonly = True
                return
            record.is_quantity_liter_readonly = False

    def _get_is_preapproved_quantity_liter_readonly(self):
        for record in self:
            if record.approval_status == CONST.APPROVED:
                record.is_preapproved_quantity_liter_readonly = True
                return
            current_approval_status_index = record.\
                material_paint_quotes_request_id.\
                _get_index_of_current_approval_status()
            if current_approval_status_index > MAX_APPROVAL_STATUS_INDEX_TO_EDIT_QUANTITY_LITER:
                record.is_preapproved_quantity_liter_readonly = True
                return
            record.is_preapproved_quantity_liter_readonly = False

    def _get_chatter_message_on_write(self, old_values, vals):
        """
        Get the chatter message on write.
        Args:
            old_values: a dict of old values of changed fields
            vals: the vals of the write method
        """
        message_text = f"Báo giá sơn {self.paint_id.name} (mã: \
            <b>{self.ref}</b>) đã được cập nhật với các thông tin sau: <br/>"
        for field in old_values:
            if old_values[field] != vals[field]:
                if field == "quantity_liter":
                    message_text += (
                        f"Khối lượng QLT duyệt (lít) : {old_values[field]} -> {vals[field]} <br/>"
                    )
                elif field == "preapproved_quantity_liter":
                    message_text += (
                        f"Khối lượng yêu cầu (lít): {old_values[field]} -> {vals[field]} <br/>"
                    )
                elif field == "paint_supplier_quote_id":
                    new_supplier_quote = (
                        self.env["ship.paint.supplier.quote"].browse(vals[field])
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

    def _get_lowest_paint_supplier_price(self):
        self.ensure_one()
        lowest_price = None
        lowest_supplier_quote = None

        for supplier_quote in self.paint_supplier_quote_ids:
            supplier_price = supplier_quote.unit_price
            if lowest_price is None or supplier_price < lowest_price:
                if supplier_price != 0:
                    lowest_price = supplier_quote.unit_price
                    lowest_supplier_quote = supplier_quote

        self.paint_supplier_quote_id = lowest_supplier_quote

    def _are_all_suppliers_have_priced(self):
        self.ensure_one()
        prices = [quote.unit_price for quote in self.paint_supplier_quote_ids]
        is_all_have_price = all(price > 0 for price in prices)
        return is_all_have_price

    def _create_paint_supplier_quotes(self):
        self.ensure_one()
        supplier_ids = self.paint_id.supplier_ids
        for supplier in supplier_ids:
            self.env["ship.paint.supplier.quote"].create(
                {
                    "unit_price": 0,
                    "paint_quote_id": self.id,
                    "supplier_id": supplier.id,
                }
            )

    def action_send_email_batch(self):
        """For sending email to suppliers"""
        self.ensure_one()
        for supplier_quote in self.paint_supplier_quote_ids:
            supplier_quote.action_send_email()

    def send_email_to_selected_provider(self):
        self.ensure_one()
        if self.paint_supplier_quote_id:
            self.is_selected_supplier_informed = True
            try:
                self.paint_supplier_quote_id.action_inform_selected_email()
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

    def action_send_emails_to_all_uninformed_quotes(self):
        """
        Send email to all selected suppliers who are not informed yet.
        """
        for record in self.get_all_uninformed_quotes():
            record.send_email_to_selected_provider()

    def _add_paint_to_warehouse(self):
        self.ensure_one()
        new_paint_history_event = {
            "paint_id": self.paint_id.id,
            "action": ADD_ACTION,
            "quantity_liter": self.delivered_quantity_liter,
            "occured_at": fields.Datetime.now(),
        }
        # if there is a selected supplier, add it to the history event
        if self.paint_supplier_quote_id:
            new_paint_history_event["paint_supplier_quote_id"] = (
                self.paint_supplier_quote_id.id
            )
        self.env["ship.paint.history"].create([new_paint_history_event])
        self.added_to_warehouse = True

    def action_confirm_delivered(self, delivered_quantity=None):
        """
        When user click on button "Delivered", automatically create new paint history event.
        """
        self.ensure_one()
        if self.approval_status != CONST.APPROVED:
            raise ValidationError("Paint quote is not approved yet.")
        if self.delivered_at:
            raise ValidationError("Paint quote is already marked as delivered.")
        if delivered_quantity and delivered_quantity != 0:
            self.delivered_quantity_liter = delivered_quantity
        self.delivered_at = fields.Datetime.now()
        self._add_paint_to_warehouse()

    def confirm_delivered_via_ref_code(self, ref_code):
        """
        When user enter ref code, automatically confirm delivered if a oaint quote with such ref code exists.
        """
        paint_quote = self.search([("ref", "=", ref_code)])
        if paint_quote:
            paint_quote.action_confirm_delivered()
        else:
            raise ValidationError("Paint quote with such ref code does not exist.")

    @api.depends("paint_supplier_quote_id")
    def _get_currency(self):
        for record in self:
            if record.paint_supplier_quote_id:
                record.currency = record.paint_supplier_quote_id.currency_id.name
            else:
                record.currency = ""

    @api.depends("paint_supplier_quote_id")
    def _calc_average_quote_price(self):
        for record in self:
            if record.expected_delivery_date:
                last_3_times = self.env["ship.paint.quote"].search(
                    [
                        ("approval_status", "=", CONST.APPROVED),
                        ("quote_state", "=", CONST.NORMAL),
                        ("paint_id", "=", record.paint_id.id),
                        ("expected_delivery_date", "<", record.expected_delivery_date),
                    ],
                    limit=3,
                )
                prices = [
                    quote.paint_supplier_quote_id.unit_price for quote in last_3_times
                ]

                total = sum(prices)
                count = len(prices)
                if total and count:
                    average_price = total / count
                    record.average_quote_price = average_price
                else:
                    record.average_quote_price = 0
            else:
                record.average_quote_price = 0

    @api.depends("paint_supplier_quote_id")
    def _get_unit_price(self):
        for record in self:
            if record.paint_supplier_quote_id:
                record.unit_price = record.paint_supplier_quote_id.unit_price
            else:
                record.unit_price = 0

    @api.depends("approval_status", "paint_supplier_quote_ids")
    def _get_lowest_total_price(self):
        for record in self:
            unit_prices = record.paint_supplier_quote_ids.mapped("unit_price")
            unit_prices = [x for x in unit_prices if x != 0]
            if unit_prices:
                unit_prices.sort()
                unit_price = unit_prices[0]
                record.lowest_total_price = unit_price
            else:
                record.lowest_total_price = 0

    def _get_emails(self):
        emails = [
            supplier_quote.supplier_id.email
            for supplier_quote in self.paint_supplier_quote_ids
        ]
        return emails

    def _not_allow_editing_quantity_once_the_quote_has_been_sent_to_ncc(self):
        self.ensure_one()
        if self.approval_status in CONST.REQUEST_STATES_THAT_NOT_ALLOW_EDIT_THE_PRICE:
            raise ValidationError("Không được sửa số lượng khi đã gửi nhà cung cấp!")

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
