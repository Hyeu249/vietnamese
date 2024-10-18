# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ..models import CONST
from odoo.exceptions import ValidationError


class CreateUtilizationTimeWiz(models.TransientModel):
    _name = "ship.create.utilization.time.wiz"
    _description = "Create utilization time wiz records"
    _inherit = ["utilities.notification"]

    date = fields.Date(string="Date", default=fields.Date.today(), tracking=True)

    # relations
    utilization_time_ids = fields.Many2many(
        "ship.utilization.time", string="Utilization Times"
    )

    def action_confirm(self):
        return {"type": "ir.actions.act_window_close"}

    @api.onchange("date")
    def create_or_get_utilization_time_ids_by_date(self):
        for record in self:
            record._create_utilization_times_for_consumption_equipments_if_not_found()
            record._set_utilization_time_ids_by_date()

    def _create_utilization_times_for_consumption_equipments_if_not_found(self):
        equipment_ids = self._get_consumption_equipment()

        for equipment_id in equipment_ids:
            utilization_time_id = self._get_utilization_time_id_of_equipment_by_date(
                equipment_id
            )
            if not utilization_time_id:
                self._create_utilization_time_for_equipment_by_date(equipment_id)

    def _set_utilization_time_ids_by_date(self):
        utilization_time_ids = self.env["ship.utilization.time"].search(
            [("recording_date", "=", self.date)]
        )
        self.utilization_time_ids = [(6, 0, utilization_time_ids.ids)]

    def _get_consumption_equipment(self):
        return self.env["ship.equipment"].search([("is_for_consumption", "=", True)])

    def _create_utilization_time_for_equipment_by_date(self, equipment_id):
        return self.env["ship.utilization.time"].create(
            {
                "equipment_id": equipment_id.id,
                "recording_date": self.date,
            }
        )

    def _get_utilization_time_id_of_equipment_by_date(self, equipment_id):
        return self.env["ship.utilization.time"].search(
            [
                ("equipment_id", "=", equipment_id.id),
                ("recording_date", "=", self.date),
            ],
            limit=1,
        )
