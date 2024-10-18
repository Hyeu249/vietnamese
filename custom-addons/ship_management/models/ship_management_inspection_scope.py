# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class ShipManagementInspectionScope(models.Model):
    _name = "ship.ship.management.inspection.scope"
    _description = "Ship management inspection scope records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char(
        "Name",
        related="ship_management_inspection_scope_metadata_id.name",
        tracking=True,
    )
    description = fields.Char("Description", tracking=True)
    status = fields.Selection(
        CONST.INSPECTION_STATUS, string="Status", compute="_get_status"
    )

    @api.depends("ship_management_inspection_task_ids")
    def _get_status(self):
        for record in self:
            statuses = record.ship_management_inspection_task_ids.mapped("status")

            if CONST.NEED_REVIEW in statuses:
                record.status = CONST.NEED_REVIEW

            elif CONST.UNSATISFIED in statuses:
                record.status = CONST.UNSATISFIED

            elif CONST.PENDING in statuses:
                record.status = CONST.PENDING
            else:
                record.status = CONST.SATISFIED

    # relations
    inspection_plan_id = fields.Many2one(
        "ship.inspection.plan",
        string="Inspection plan",
        tracking=True,
    )
    ship_management_inspection_task_ids = fields.One2many(
        "ship.ship.management.inspection.task",
        "ship_management_inspection_scope_id",
        string="Ship management inspection task",
        tracking=True,
    )
    ship_management_inspection_scope_metadata_id = fields.Many2one(
        "ship.ship.management.inspection.scope.metadata",
        string="Ship management inspection scope metadata",
        tracking=True,
    )

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_inspection_plan_id_ship_management_inspection_scope_metadata_id",
            "unique (inspection_plan_id, ship_management_inspection_scope_metadata_id)",
            "inspection_plan_id and ship_management_inspection_scope_metadata_id must be unique.",
        ),
    ]

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "ship.ship.management.inspection.scope"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(ShipManagementInspectionScope, self).create(vals_list)

        for record in result:
            record._create_default_ship_management_inspection_tasks()

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result

    def _create_default_ship_management_inspection_tasks(self):
        self.ensure_one()
        last_inspection_plan = self.inspection_plan_id._get_last_month_inspection_plan(
            self.company_id
        )

        scope_metadata_id = self.ship_management_inspection_scope_metadata_id
        task_metadata_ids = (
            scope_metadata_id.ship_management_inspection_task_metadata_ids
        )

        for task_metadata in task_metadata_ids:
            last_inspection_plan_task_ids = (
                last_inspection_plan.ship_management_inspection_scope_ids.ship_management_inspection_task_ids
            )
            appropriate_task_id = last_inspection_plan_task_ids.filtered(
                lambda e: e.ship_management_inspection_scope_id.ship_management_inspection_scope_metadata_id
                == scope_metadata_id
                and e.ship_management_inspection_task_metadata_id == task_metadata
            )
            status = CONST.PENDING
            task_type = CONST.NEW
            if appropriate_task_id.task_type == CONST.BACKLOGGED:
                status = CONST.UNSATISFIED
                task_type = CONST.LAST_MONTH_BACKLOG

            new_task = self._create_ship_management_inspection_task(
                task_metadata, status, task_type
            )

            if appropriate_task_id.image_ids:
                new_task.image_ids = [(6, 0, appropriate_task_id.image_ids.ids)]

    def _create_ship_management_inspection_task(
        self, metadata, status=CONST.PENDING, task_type=CONST.NEW
    ):
        self.ensure_one()
        return self.env["ship.ship.management.inspection.task"].create(
            {
                "ship_management_inspection_scope_id": self.id,
                "ship_management_inspection_task_metadata_id": metadata.id,
                "status": status,
                "task_type": task_type,
            }
        )
