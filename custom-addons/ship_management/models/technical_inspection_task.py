# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from ...utilities.models import CONST as CONST_2
from odoo.exceptions import ValidationError


class TechnicalInspectionTask(models.Model):
    _name = "ship.technical.inspection.task"
    _description = "Technical inspection task records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    # related
    task_name = fields.Char(
        "Task name", related="technical_inspection_task_metadata_id.name", tracking=True
    )
    task_description = fields.Char(
        "Task description",
        related="technical_inspection_task_metadata_id.description",
        tracking=True,
    )

    status = fields.Selection(
        CONST.INSPECTION_STATUS,
        string="Status",
        default=CONST.PENDING,
        tracking=True,
    )
    task_type = fields.Selection(
        CONST.TASK_TYPE,
        string="Task type",
        default=CONST.NEW,
        required=True,
        tracking=True,
    )
    inspection_date = fields.Date("Inspection date", tracking=True)
    expected_fix_date = fields.Date("Expected fix date", tracking=True)
    real_fix_date = fields.Date("Real fix date", tracking=True)
    deadline = fields.Date("Deal line", tracking=True)
    backlog = fields.Char("Back log", tracking=True)
    fix_plan = fields.Char("Fix plan", tracking=True)
    comment = fields.Html("Director comment", tracking=True)
    fix_content = fields.Char("Fix content", tracking=True)
    is_severe = fields.Boolean("Is severe", tracking=True)
    is_ceo = fields.Boolean("is ceo", compute="_is_in_ceo_group")
    is_approved_inspection_plan = fields.Boolean(
        "Is approved inspection plan", compute="_is_approved_inspection_plan"
    )
    is_user_allow_for_editing = fields.Boolean(
        "Is user allow for editing", compute="_is_user_allow_for_editing"
    )

    # relations
    user_ids = fields.Many2many("res.users", string="Inspectors")
    image_ids = fields.Many2many("ship.inspection.image", string="Image", tracking=True)
    technical_inspection_task_metadata_id = fields.Many2one(
        "ship.technical.inspection.task.metadata",
        string="Technical inspection task metadata",
        tracking=True,
    )
    technical_inspection_scope_id = fields.Many2one(
        "ship.technical.inspection.scope",
        string="Technical inspection scope",
        tracking=True,
    )
    inspection_plan_id = fields.Many2one(
        "ship.inspection.plan",
        related="technical_inspection_scope_id.inspection_plan_id",
        string="Inspection plan",
        tracking=True,
    )

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_technical_inspection_scope_id_technical_inspection_task_metadata_id",
            "unique (technical_inspection_scope_id, technical_inspection_task_metadata_id)",
            "technical_inspection_scope_id and technical_inspection_task_metadata_id must be unique.",
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
            model_name = "ship.technical.inspection.task"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)

        result = super(TechnicalInspectionTask, self).create(vals_list)
        return result

    def write(self, vals):
        self.ensure_one()

        if "image_ids" not in vals:
            self.check_permission()

        result = super(TechnicalInspectionTask, self).write(vals)

        if "status" in vals:
            if self.status == CONST.UNSATISFIED:
                self._send_noti_to_people_need_to_fix_the_task()

        return result

    def check_permission(self):
        self.ensure_one()
        admin_group = self.env.user.has_group("utilities.group_ship_admin")
        cvkt_group = self.env.user.has_group("utilities.group_ship_technical_expert")
        ceo_group = self.env.user.has_group("utilities.group_ship_ceo")
        message = "Người dùng không có quyền chỉnh sửa ở đây, vui lòng quay trở lại!"
        local_sudo_field = self.env.context.get("local_sudo_field")

        if (
            not local_sudo_field
            and not admin_group
            and not cvkt_group
            and not ceo_group
        ):

            raise ValidationError(message)

    def _is_user_allow_for_editing(self):
        user_id = self.env.user.id

        for record in self:
            record.is_user_allow_for_editing = user_id in self.user_ids.ids

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def add_inspector(self):
        self.ensure_one()
        current_user = self.env.user
        user_ids = self.user_ids.ids
        user_ids.append(current_user.id)

        self.user_ids = [(6, 0, list(set(user_ids)))]

    def _is_in_ceo_group(self):
        for record in self:
            record.is_ceo = self.env.user.has_group("utilities.group_ship_ceo")

    def _is_approved_inspection_plan(self):
        for record in self:
            is_approved = record.inspection_plan_id._is_approved()
            record.is_approved_inspection_plan = is_approved

    def complete_the_fix(self):
        self.ensure_one()
        self.sudo().local_sudo_field().status = CONST.NEED_REVIEW
        self.sudo()._send_noti_to_technical_expert_to_confirm_the_task()

    def local_sudo_field(self):
        self.ensure_one()
        return self.with_context({"local_sudo_field": True})

    def _send_noti_to_people_need_to_fix_the_task(self):
        self.ensure_one()
        group_xml_ids = ["group_ship_captain", "group_ship_ship_crew"]
        company_id = self.company_id

        for group_xml_id in group_xml_ids:
            classes = "title_inspection_plan_color"
            subject = f"Chưa thỏa mãn nội dung của BCTT kỹ thuật"
            body = f"Bản ghi {self.ref}({self.task_name}) chưa thỏa mãn!"

            self._send_notification_by_group_xml_and_company_id(
                group_xml_id, company_id, subject, body, classes
            )

    def _send_noti_to_technical_expert_to_confirm_the_task(self):
        self.ensure_one()
        group_xml_id = "group_ship_technical_expert"
        company_id = self.company_id

        classes = "title_inspection_plan_color"
        subject = f"Cần xác nhận sửa chữa từ nội dung của BBTT kỹ thuật"
        body = f"Bản ghi {self.ref}({self.task_name}) cần xác nhận!"

        self._send_notification_by_group_xml_and_company_id(
            group_xml_id, company_id, subject, body, classes
        )
