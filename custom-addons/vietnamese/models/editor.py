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

    def set_default_value_for_one2many(self, table_id):
        self.env["base.automation"].create(
            {
                "name": "Set sequence for model",
                "trigger": "on_create",
                "state": "code",
                "code": """
                        for record in records:
                            if not record.x_ref or record.x_ref == 'New':
                                record["x_ref"] = env["ir.sequence"].next_by_code(record._name)
                        """,
                "filter_pre_domain": "[]",
            }
        )

        table_id = self.env["vietnamese.table"].browse(table_id)
        action_id = table_id.menu_id.action
        context = {}

        for field in self.field_ids:
            default_name = f"default_{field.name}"
            context[default_name] = field.get_default_value()

        action_id.context = context
