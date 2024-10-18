# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class Help(models.Model):
    _name = "utilities.help"
    _description = "Help records"
    _inherit = ["utilities.notification"]

    model = fields.Char(string="Model", tracking=True)
    help = fields.Text(string="Help", tracking=True)

    @api.constrains("model")
    def _unique_model(self):
        for record in self:
            duplicate = self.search(
                [
                    ("id", "!=", record.id),
                    ("model", "=", record.model),
                ]
            )
            message = "Tên model là duy nhất!"
            if duplicate:
                raise ValidationError(message)
