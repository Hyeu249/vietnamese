# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class LashingMaterialFixStats(models.Model):
    _name = "ship.lashing.material.fix.stats"
    _description = "Lashing material fix stats records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    update_date = fields.Char(
        "Update date", default=lambda e: fields.Date.today(), tracking=True
    )
    repaired = fields.Integer("Repaired", tracking=True)
    not_repaired = fields.Integer("Not repaired", tracking=True)
    repairable = fields.Integer("Repairable", tracking=True)
    unrepairable = fields.Integer("Unrepairable", tracking=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    material_id = fields.Many2one("ship.material", string="Material", tracking=True)

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "ship.lashing.material.fix.stats"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        return super(LashingMaterialFixStats, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
