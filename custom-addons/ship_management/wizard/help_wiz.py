# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ..models import CONST
from odoo.exceptions import ValidationError


class HelpWiz(models.TransientModel):
    _name = "ship.help.wiz"
    _description = "Help wiz records"
    _inherit = ["utilities.notification"]

    help = fields.Text(string="Help", readonly=True, tracking=True)

    # relations
    default_value_ids = fields.Many2many(
        "utilities.default.value", string="Default value"
    )
    cron_ids = fields.Many2many("ir.cron", readonly=True, string="Cron")
