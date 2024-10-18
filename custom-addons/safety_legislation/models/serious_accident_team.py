# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class MaintenanceScopeReport(models.Model):
    _inherit = "ship.maintenance.scope.report"

    serious_accident_team_id = fields.Many2one("legis.serious.accident.team")


class MaterialPaintQuotesRequest(models.Model):
    _inherit = "ship.material.paint.quotes.request"

    serious_accident_team_id = fields.Many2one("legis.serious.accident.team")


class SeriousAccidentTeam(models.Model):
    _name = "legis.serious.accident.team"
    _description = "Serious accident team records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    # related
    user_id = fields.Many2one("res.users", related="ert_role_meta_id.user_id")
    login = fields.Char("Email", related="user_id.login")
    phone = fields.Char("Phone", related="user_id.phone")
    mobile = fields.Char("Mobile", related="user_id.mobile")
    avatar_128 = fields.Image("avatar_128", related="user_id.avatar_128",
                              max_width=CONST.MAX_IMAGE_UPLOAD_WIDTH,
                              max_height=CONST.MAX_IMAGE_UPLOAD_HEIGHT)
    # relations
    ert_role_meta_id = fields.Many2one(
        "legis.ert.role.meta",
        string="Rrt role meta",
        tracking=True,
    )
    serious_accident_task_ids = fields.One2many(
        "legis.serious.accident.task",
        "serious_accident_team_id",
        string="Serious Accident Task",
        default=lambda self: self.get_default_tasks(),
        tracking=True,
    )
    serious_accident_report_id = fields.Many2one(
        "legis.serious.accident.report",
        string="Serious accident report",
        tracking=True,
    )

    maintenance_scope_report_ids = fields.One2many(
        "ship.maintenance.scope.report",
        "serious_accident_team_id",
        string="Maintenance scope report",
        tracking=True,
    )

    material_paint_quotes_request_ids = fields.One2many(
        "ship.material.paint.quotes.request",
        "serious_accident_team_id",
        string="Material paint quotes request",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.serious.accident.team"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(SeriousAccidentTeam, self).create(vals_list)

        for record in result:
            record.notification_for_ert_team()

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def get_default_tasks(self):
        default_tasks_by_ert_id = self.env.context.get("default_tasks_by_ert_id")

        if default_tasks_by_ert_id:
            ert_id = self.env["legis.ert.role.meta"].browse(default_tasks_by_ert_id)
            tasks = [
                {
                    "name": task.name,
                    "description": task.description,
                }
                for task in ert_id.ert_role_task_meta_ids
            ]
            task_ids = self.serious_accident_task_ids.create(tasks)
            return task_ids.ids
        else:
            return []

    @api.onchange("ert_role_meta_id")
    def get_tasks_by_ert_id(self):
        for record in self:
            if record.ert_role_meta_id and not record.serious_accident_task_ids:
                tasks = [
                    {
                        "name": task.name,
                        "description": task.description,
                    }
                    for task in self.ert_role_meta_id.ert_role_task_meta_ids
                ]
                task_ids = self.serious_accident_task_ids.create(tasks)
                record.serious_accident_task_ids = task_ids.ids

    def notification_for_ert_team(self):
        self.ensure_one
        subject = "Đội sự cố ERT"
        body = "Yêu cầu hoàn thành nhiệm vụ từ đội sự cố"
        self._send_notification_by_user(self.user_id, subject, body)
