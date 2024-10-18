# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class LiquidationMinute(models.Model):
    _name = "ship.liquidation.minute"
    _description = "Liquidation minute records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    proposed_liquidation_id = fields.Many2one(
        "ship.proposed.liquidation",
        string="Proposed liquidation",
        tracking=True,
    )
    material_ids = fields.Many2many(
        "ship.material",
        string="Material",
        tracking=True,
    )

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_proposed_liquidation_id",
            "unique (proposed_liquidation_id)",
            "proposed_liquidation_id must be unique.",
        ),
    ]

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "ship.liquidation.minute"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(LiquidationMinute, self).create(vals_list)

        for record in result:
            record.get_materials()

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def get_materials(self):
        self.ensure_one()
        if self.proposed_liquidation_id:
            self.material_ids = self.proposed_liquidation_id.material_ids
