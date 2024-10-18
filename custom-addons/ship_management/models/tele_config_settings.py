# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError

CONFIG_PARAM_1 = "ship_management.bot_token"
CONFIG_PARAM_2 = "ship_management.is_active_telegram"
default_token = "7216628327:AAHPUtZJFDbsXY57rcrRC7HTmaxd3I55F9E"


class TeleConfigSettings(models.TransientModel):
    _inherit = ["res.config.settings"]

    bot_token = fields.Char(
        "Token", required=True, default=default_token, config_parameter=CONFIG_PARAM_1
    )
    is_active_telegram = fields.Boolean(
        string="Is active?",
        default=False,
        config_parameter=CONFIG_PARAM_2,
    )

    def move_to_setting_tele_groups(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Telegram setting groups",
            "res_model": "ship.tele.group.settings",
            "view_type": "form",
            "view_mode": "tree,form",
            "target": "current",
            "context": self.env.context,
        }


class TeleGroupSettings(models.Model):
    _name = "ship.tele.group.settings"
    _description = "Telegram setting groups records"
    _inherit = ["utilities.notification"]

    chat_id = fields.Char("chat_id", required=True, tracking=True)
    token = fields.Char(
        "Token", required=True, compute="get_telegram_bot_token", tracking=True
    )
    is_active = fields.Boolean(
        "is_active", compute="get_is_active", default=False, tracking=True
    )

    # relations
    company_ids = fields.Many2many("res.company", tracking=True)

    @api.depends("company_ids")
    def get_is_active(self):
        for record in self:
            is_active_telegram = record.get_is_allow_send_tele_message()
            if is_active_telegram and record.is_allow_current_company():
                record.is_active = True
            else:
                record.is_active = False

    @api.depends("chat_id")
    def get_telegram_bot_token(self):
        for record in self:
            token = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_param(CONFIG_PARAM_1, default=False)
            )

            record.token = token

    def get_is_allow_send_tele_message(self):
        is_allowed = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(CONFIG_PARAM_2, default=False)
        )

        if is_allowed == "True":
            return True
        elif is_allowed == True:
            return True
        else:
            return False

    def get_token_and_chat_id_based_on_company(self):
        record = self.sudo().search(
            [
                ("company_ids", "=", self.env.company.id),
            ],
            limit=1,
        )
        if record:
            return {
                "chat_id": record.chat_id,
                "token": record.token,
            }
        else:
            return {}

    def get_tele_token(self):
        token = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(CONFIG_PARAM_1, default=False)
        )

        return token

    def is_allow_current_company(self):
        self.ensure_one()
        current_company_id = self.env.company.id
        if current_company_id in self.company_ids.ids:
            return True
        else:
            return False
