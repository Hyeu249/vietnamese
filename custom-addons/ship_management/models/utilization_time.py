# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class UtilizationTime(models.Model):
    _name = "ship.utilization.time"
    _description = "UtilizationTime records"
    _inherit = ["ship.date", "utilities.notification"]
    _check_company_auto = True

    utilization_time = fields.Integer("Utilization time", default=0, tracking=True)
    note = fields.Char("Note", tracking=True)
    recording_date = fields.Date(
        "Recording date", default=fields.Date.today, required=True, tracking=True
    )
    total_utilization_time = fields.Integer(
        "Total utilization time",
        related="equipment_id.total_utilization_time",
        tracking=True,
    )

    # related
    calculate_consumption_by = fields.Selection(
        CONST.TIME_TYPE,
        default=CONST.NONE,
        string="Calculate consumption by",
        required=True,
        tracking=True,
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    equipment_id = fields.Many2one(
        "ship.equipment",
        string="Equipment",
        required=True,
        readonly=True,
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    _order = "recording_date DESC"

    @api.constrains("equipment_id", "recording_date")
    def _unique_recording_date_for_equipment(self):
        for record in self:
            duplicate = self.search(
                [
                    ("id", "!=", record.id),
                    ("equipment_id", "=", record.equipment_id.id),
                    ("recording_date", "=", record.recording_date),
                ]
            )
            message = "Không thể ghi nhận 2 lần trong 1 ngày cho thiết bị!"
            if duplicate:
                raise ValidationError(message)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.utilization.time")

        result = super(UtilizationTime, self).create(vals_list)

        for record in result:
            record.add_utilization_time_for_all_maintenance_scopes_for_consumption()

        return result

    def write(self, vals):
        self.ensure_one()
        self.not_allow_change_utilization_time_if_there_is(vals)

        result = super(UtilizationTime, self).write(vals)

        if self.utilization_time and "utilization_time" in vals:
            self.add_utilization_time_for_all_maintenance_scopes_for_consumption()

        return result

    def unlink(self):
        for record in self:
            record.remove_utilization_time_for_all_maintenance_scopes_for_consumption()

        return super(UtilizationTime, self).unlink()

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def add_utilization_time_for_all_maintenance_scopes_for_consumption(self):
        self.ensure_one
        mcs_for_consumption = self.get_mcs_for_consumption_by_equipment_id()

        for maintenance_scope_id in mcs_for_consumption:
            if not maintenance_scope_id._is_under_maintenance():
                maintenance_scope_id.utilization_time += self.utilization_time

    def remove_utilization_time_for_all_maintenance_scopes_for_consumption(self):
        self.ensure_one
        mcs_for_consumption = self.get_mcs_for_consumption_by_equipment_id()

        for maintenance_scope_id in mcs_for_consumption:
            if not maintenance_scope_id._is_under_maintenance():
                maintenance_scope_id.utilization_time -= self.utilization_time

    def get_mcs_for_consumption_by_equipment_id(self):
        self.ensure_one()
        mc_ids = self.equipment_id.maintenance_scope_ids

        return mc_ids.filtered(lambda e: e.maintenance_type == CONST.CONSUMPTION)

    def not_allow_change_utilization_time_if_there_is(self, vals):
        self.ensure_one()
        old_utilization_time = self.utilization_time
        new_utilization_time = vals["utilization_time"]
        message = "Không cho phép chỉnh sửa thời gian sử dụng, khi đã có!"

        if "utilization_time" in vals:
            if old_utilization_time and new_utilization_time != old_utilization_time:
                raise ValidationError(message)
