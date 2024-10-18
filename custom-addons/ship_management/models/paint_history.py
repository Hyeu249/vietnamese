# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


ADD_ACTION = "add"
MINUS_ACTION = "minus"
ACTIONS = [
    (ADD_ACTION, "Add"),
    (MINUS_ACTION, "Minus"),
]


class PaintHistory(models.Model):
    _name = "ship.paint.history"
    _description = "Paint history records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    previous_quantity = fields.Float(string="Previous quantity", tracking=True)
    action = fields.Selection(ACTIONS, string="Action", default="add", tracking=True)
    occured_at = fields.Datetime(
        "Occured at", default=lambda self: fields.Datetime.now(), tracking=True
    )
    quantity_liter = fields.Float("Quantity liter", tracking=True)
    note = fields.Text("Note", tracking=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    paint_id = fields.Many2one(
        "ship.paint", string="Paint", required=True, tracking=True
    )
    job_quote_id = fields.Many2one(
        "ship.job.quote",
        string="Job Quote",
        tracking=True,
    )
    paint_supplier_quote_id = fields.Many2one(
        "ship.paint.supplier.quote", string="Paint supplier quote", tracking=True
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_paint_supplier_quote_id",
            "unique (paint_supplier_quote_id)",
            "paint_supplier_quote_id must be unique.",
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        record_len = len(vals_list)
        message = "Hãy tạo từng lịch sử sơn một, không cho phép tạo nhiều lịch sử sơn cùng 1 lúc!"
        if record_len >= 2:
            raise ValidationError(message)

        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.paint.history")
            paint_id = vals.get("paint_id")
            if vals.get("paint_id"):
                paint = self.env["ship.paint"].browse(paint_id)
                vals["previous_quantity"] = paint.available_quantity_liter
        result = super(PaintHistory, self).create(vals_list)
        for record in result:
            record.paint_id.compute_single_paint_available_quantity()
            if record.action == MINUS_ACTION:
                if record.quantity_liter > record.previous_quantity:
                    raise ValidationError("Số lượng sơn trong kho không đủ để lấy!")
        return result

    def write(self, vals):
        # do not allow update
        raise ValidationError("Update is not allowed.")

    def unlink(self):
        paint_list = []
        for record in self:
            paint_list.append(record.paint_id)
        result = super(PaintHistory, self).unlink()
        # recompute paint available quantity
        for paint in paint_list:
            paint.compute_single_paint_available_quantity()
        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
