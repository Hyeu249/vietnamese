# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from .paint_history import ADD_ACTION, MINUS_ACTION
from odoo.exceptions import ValidationError


class Paint(models.Model):
    _name = "ship.paint"
    _description = "Paint records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    spare_part_no = fields.Char("Spare part no", tracking=True)
    internal_code = fields.Char("Internal code", tracking=True)
    description = fields.Char("Description", tracking=True)
    min_quantity_liter = fields.Float("Min quantity liter", tracking=True)
    available_quantity_liter = fields.Float("Available quantity", readonly=True)
    origin = fields.Char("Origin", tracking=True)
    is_quantity_low = fields.Boolean("Is quantity low", default=False, readonly=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    paint_type_id = fields.Many2one(
        "ship.paint.type", string="Paint Type", tracking=True
    )
    supplier_ids = fields.Many2many(
        "ship.supplier",
        string="Supplier",
        domain="[('classified_for_paint', '=', True)]",
        tracking=True,
    )
    paint_history_ids = fields.One2many(
        "ship.paint.history",
        inverse_name="paint_id",
        string="Paint History",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.paint")
        result = super(Paint, self).create(vals_list)
        self.compute_all_paints_available_quantity()
        return result

    def unlink(self):
        for paint in self:
            if paint._has_in_progress_paint_quote():
                raise ValidationError(
                    "You cannot delete paint that has in progress paint quote."
                )
            paint.paint_history_ids.unlink()
        result = super(Paint, self).unlink()

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result

    def _has_in_progress_paint_quote(self):
        count = self.env["ship.paint.quote"].search_count(
            [
                ("paint_id", "=", self.id),
                ("approval_status", "!=", CONST.APPROVED),
                ("approval_status", "!=", CONST.REJECTED),
            ]
        )
        return count > 0

    def compute_all_paints_available_quantity(self):
        all_paint = self.search([])
        for paint in all_paint:
            paint.compute_single_paint_available_quantity()

    def compute_single_paint_available_quantity(self):
        self.ensure_one()
        count = 0.0
        for record in self.paint_history_ids:
            if record.action == ADD_ACTION:
                count += record.quantity_liter
            elif record.action == MINUS_ACTION:
                count -= record.quantity_liter
        self.available_quantity_liter = count
        if count < self.min_quantity_liter:
            self.is_quantity_low = True
        else:
            self.is_quantity_low = False

    def _get_paints_below_minimum_quantity(self):
        # update available quantity first
        self.compute_all_paints_available_quantity()
        return self.search([("is_quantity_low", "=", True)])

    def action_create_paint_quote_when_min(self):
        paints = self._get_paints_below_minimum_quantity()
        new_paint_quotes = []
        for paint in paints:
            # check if paint has in progress quotes
            if not paint._has_in_progress_paint_quote():
                new_paint_quotes.append(
                    {
                        "paint_id": paint.id,
                        "quantity_liter": paint.min_quantity_liter
                        - paint.available_quantity_liter,
                    }
                )
        self.env["ship.paint.quote"].create(new_paint_quotes)
