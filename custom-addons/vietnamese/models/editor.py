# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class Editor(models.Model):
    _name = "vietnamese.editor"
    _description = "Editor records"
    _inherit = ["mail.thread"]

    def add_sequence(self, record):
        record.x_ref = self.env["ir.sequence"].next_by_code(record._name)
