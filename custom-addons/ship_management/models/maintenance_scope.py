# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from . import CONST
from datetime import timedelta


class MaintenanceScopeTemplate(models.Model):
    _name = "ship.maintenance.scope.template"
    _description = "Maintenance scope records"
    _inherit = ["utilities.notification"]

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)
    department_in_charge = fields.Selection(
        CONST.DEPARTMENT_IN_CHARGE,
        string="Department in charge",
        default=CONST.MACHINERY,
        tracking=True,
    )

    maintenance_type = fields.Selection(
        CONST.MAINTENANCE_TYPE,
        string="Maintenance Type",
        default=CONST.ARISE,
        required=True,
        tracking=True,
    )

    is_auto_create_allowed = fields.Boolean(
        "Is auto create allowed", default=True, tracking=True
    )

    # maintenance_threshold
    next_maintenance_date = fields.Date(
        "Next maintenance date", default=fields.Date.today, tracking=True
    )
    last_maintenance_date = fields.Date("Last maintenance date", tracking=True)

    maintenance_interval_days = fields.Selection(
        CONST.MAINTENANCE_DAYS_SELECTION,
        string="Maintenance interval days",
        tracking=True,
    )

    maintenance_interval = fields.Selection(
        CONST.MAINTENANCE_INTERVAL_SELECTION,
        string="Maintenance interval",
        tracking=True,
    )

    interval_days = fields.Integer(
        string="Interval days",
        compute="get_interval_days",
        default=0,
        store=True,
        tracking=True,
    )

    @api.depends("maintenance_interval", "last_maintenance_date")
    def get_interval_days(self):
        for record in self:
            if record.maintenance_interval:
                relativedelta = CONST.MAINTENANCE_INTERVAL.get(
                    record.maintenance_interval
                )
                if relativedelta:
                    start_date = record.last_maintenance_date
                    end_date = start_date + relativedelta
                    record.interval_days = (end_date - start_date).days
                    return
            record.interval_days = 0

    def refactor_maintenance_interval_days(self):
        for record in self:
            if not record.maintenance_interval:
                record.maintenance_interval = CONST.MAINTENANCE_INTERVAL_CONVERTER.get(
                    record.maintenance_interval_days
                )

    # maintenance_consumption
    utilization_time = fields.Integer(
        "Utilization time",
        tracking=True,
    )
    allowed_usage_time = fields.Integer(
        "Allowed usage time",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):

        records = super(MaintenanceScopeTemplate, self).create(vals_list)

        for record in records:
            record.set_next_maintenance_date_by_last_maintenance_date_and_interval_days()

        return records

    def write(self, vals):
        self.ensure_one()
        result = super(MaintenanceScopeTemplate, self).write(vals)

        if "last_maintenance_date" in vals or "maintenance_interval" in vals:
            self.set_next_maintenance_date_by_last_maintenance_date_and_interval_days()

        return result

    def set_next_maintenance_date_by_last_maintenance_date_and_interval_days(self):
        self.ensure_one()
        if self.last_maintenance_date and self.maintenance_interval:
            relativedelta = CONST.MAINTENANCE_INTERVAL[self.maintenance_interval]
            self.next_maintenance_date = self.last_maintenance_date + relativedelta


class MaintenanceScope(models.Model):
    _name = "ship.maintenance.scope"
    _description = "Maintenance scope records"
    _inherit = ["ship.maintenance.scope.template"]
    _check_company_auto = True

    is_docking = fields.Boolean("Is docking", tracking=True)

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    equipment_id = fields.Many2one("ship.equipment", string="Equipment", tracking=True)
    job_ids = fields.One2many(
        "ship.job", "maintenance_scope_id", string="Job", tracking=True
    )

    maintenance_scope_report_ids = fields.One2many(
        "ship.maintenance.scope.report",
        "maintenance_scope_id",
        string="Maintenance Scope Report",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.maintenance.scope")

        records = super(MaintenanceScope, self).create(vals_list)

        for record in records:
            record.create_report_for_consumption_if_reach_allowed_usage_time()
        return records

    def write(self, vals):
        self.ensure_one()
        result = super(MaintenanceScope, self).write(vals)

        if "utilization_time" in vals or "allowed_usage_time" in vals:
            self.create_report_for_consumption_if_reach_allowed_usage_time()

        if "is_docking" in vals:
            self.set_docking_state_for_under_maintenance_report_if_in_docking()

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            maintenance_type = report.maintenance_type
            result.append((report.id, f"{name}({maintenance_type})"))
        return result

    def set_docking_state_for_under_maintenance_report_if_in_docking(self):
        self.ensure_one()
        report = self.get_under_maintenance_report()
        if self.is_docking:
            report.set_waiting_for_docking_state()
        else:
            report.set_ref_job_state()

    def create_new_report_if_threshold_maintenance(self):
        self.ensure_one()
        if self.is_maintenance_for_threshold():
            self.unlink_prepare_report_and_create_new_one()

    def create_report_for_consumption_if_reach_allowed_usage_time(self):
        self.ensure_one
        if self.is_maintenance_for_consumption():
            if self.utilization_time and self.allowed_usage_time:
                if self.utilization_time >= self.allowed_usage_time:
                    self.unlink_prepare_report_and_create_new_one()
                    self.utilization_time = 0

    def unlink_prepare_report_and_create_new_one(self):
        self.ensure_one()
        if not self.is_auto_create_allowed:
            return

        self.unlink_prepare_reports()
        self.create_maintenance_scope_report()

    def create_maintenance_scope_report(self):
        self.ensure_one()
        if self.is_maintenance_for_arise() or self.is_maintenance_for_consumption():
            self.next_maintenance_date = fields.Date.today()

        self.env["ship.maintenance.scope.report"].create(
            {
                "maintenance_scope_id": self.id,
            }
        )

    def unlink_prepare_reports(self):
        self.ensure_one()
        reports = self.maintenance_scope_report_ids
        prepare_reports = reports.filtered(lambda e: not e.finished_at)

        prepare_reports.unlink()

    def _is_under_maintenance(self):
        self.ensure_one()
        report = self.maintenance_scope_report_ids
        not_finished_reports = report.filtered(lambda e: not e.finished_at)

        if not_finished_reports:
            return True
        else:
            return False

    def get_under_maintenance_report(self):
        self.ensure_one()
        report = self.maintenance_scope_report_ids
        not_finished_reports = report.filtered(lambda e: not e.finished_at)

        if not_finished_reports:
            return not_finished_reports[0]

    def is_maintenance_for_arise(self):
        return self.maintenance_type == CONST.ARISE

    def is_maintenance_for_threshold(self):
        return self.maintenance_type == CONST.THRESHOLD

    def is_maintenance_for_consumption(self):
        return self.maintenance_type == CONST.CONSUMPTION

    def allow_auto_create_maintenance_scope(self):
        for record in self:
            record.is_auto_create_allowed = True

    def stop_auto_create_maintenance_scope(self):
        for record in self:
            record.is_auto_create_allowed = False

    def create_all_report_for_scope(self):
        for record in self:
            record.unlink_prepare_report_and_create_new_one()
