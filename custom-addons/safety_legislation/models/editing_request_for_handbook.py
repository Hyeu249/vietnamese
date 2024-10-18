# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
import logging
from ...utilities.models import CONST as UTILITIES_CONST


class EditingRequestForHandbook(models.Model):
    _name = "legis.editing.request.for.handbook"
    _description = "Phát hiện sự không phù hợp trong sổ tay"
    _inherit = ["utilities.notification"]

    request_date = fields.Date(string="Request date", tracking=True)
    request_type = fields.Selection(
        CONST.EDITING_REQUEST_FOR_HANDBOOK_TYPE,
        string="Request type",
        default=CONST.UNEXPECT,
        required=True,
        tracking=True,
    )
    note = fields.Text(string="Note", tracking=True)
    help = fields.Char(
        "Help",
        readonly=True,
        tracking=True,
        help="""
        1.Phần mềm thông báo định kỳ kiểm tra sổ tay
        2.Nếu có bât thường, đội tàu có thể yêu cầu sửa đổi, hoặc hủy bỏ theo form 0102
        ------------------------------
        Định kỳ:
        1.Phần mềm tự động tạo thông báo cho đội tàu kiểm tra
        ------------------------------
        Bất thường:
        1.Đội tàu chọn loại yêu cầu là bất thường
        2.Sau đó tiến hành chỉnh sửa sổ tay
        3.Sau khi chỉnh sửa sổ tay, người dùng tiến hành tạo form 0102
        4.Sau khi tạo form 0102, người dùng báo cáo cho DPA(người phụ trách)
        5.DPA kiểm tra phần sửa đổi sổ tay(ở form 0102)
        6.Sau khi kiểm tra, DPA trình duyệt BLĐ để duyệt đồng thời
        7.Sau khi duyệt chốt sửa đổi, DPA lập biên bản form 0103 và cập nhật bản mới của sổ tay   
    """,
    )
    # relations

    handbook_revision_report_id = fields.Many2one(
        "legis.handbook.revision.report",
        string="Handbook revision report",
        default=lambda self: self.env["legis.handbook.revision.report"].create({}),
        tracking=True,
    )
    safety_management_handbook_id = fields.Many2one(
        "legis.safety.management.handbook",
        string="Safety management handbook",
        tracking=True,
    )
    requisition_for_handbook_revision_ids = fields.One2many(
        "legis.requisition.for.handbook.revision",
        "editing_request_for_handbook_id",
        string="Requisition for handbook revision",
        tracking=True,
    )

    revision_approval_status = fields.Char(
        compute="_get_revision_approval_status",
    )

    @api.depends("requisition_for_handbook_revision_ids")
    def _get_revision_approval_status(self):
        for record in self:
            revision_ids = record.requisition_for_handbook_revision_ids
            if revision_ids:
                revision_id = revision_ids[0]
                record.revision_approval_status = (
                    revision_id.approval_status_for_all_approval
                )
            else:
                record.revision_approval_status = False

    @api.constrains("requisition_for_handbook_revision_ids")
    def only_1_requisition_for_handbook_revision(self):
        for record in self:
            if len(record.requisition_for_handbook_revision_ids) > 1:
                message = "Chỉ có 1 bản sửa đổi!"
                raise ValidationError(message)

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.editing.request.for.handbook"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(EditingRequestForHandbook, self).create(vals_list)

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(EditingRequestForHandbook, self).write(vals)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def create_new_handbook(self):
        self.ensure_one()
        return self.env["legis.safety.management.handbook"].create({})

    def create_new_handbook_based_on_request(self):
        self.ensure_one()

        revision_id = self.get_requisition_for_handbook_revision_id()

        if not revision_id._is_all_approved():
            raise ValidationError("Yêu cầu chưa được duyệt, vui lòng kiểm tra lại!")

        old_handbook_id = self.safety_management_handbook_id
        new_handbook_id = self.create_new_handbook()

        for section in old_handbook_id.handbook_section_ids:
            section.recursive_action(
                self.copy_or_create_new_handbook_section,
                (CONST.SECTION_FOR_HANDBOOK, new_handbook_id.id),
            )

    def copy_or_create_new_handbook_section(self, section_id, return_result=False):
        self.ensure_one()
        if return_result:
            first_value = return_result[0]
            second_value = return_result[1]
            modified_section_id = section_id.modified_section_version_id

            control_number = section_id.control_number
            title = section_id.title
            content = section_id.content

            if modified_section_id:
                approved_section = self.check_revision_state_of_current_section(
                    section_id
                )

                if approved_section:
                    control_number = modified_section_id.control_number
                    title = modified_section_id.title
                    content = modified_section_id.content

            if first_value == CONST.SECTION_FOR_HANDBOOK:
                new_section_id = self.create_handbook_section(
                    control_number, title, content, handbook_id=second_value
                )
                if section_id.are_need_metas:
                    new_section_id.are_need_metas = section_id.are_need_metas
                    section_id.set_ert_role_meta_ids_to_new_section(new_section_id)
                    section_id.set_incidence_type_meta_ids_to_new_section(
                        new_section_id
                    )
                return (CONST.SECTION_FOR_PARENT_SECTION, new_section_id.id)
            if first_value == CONST.SECTION_FOR_PARENT_SECTION:
                new_section_id = self.create_handbook_section(
                    control_number, title, content, parent_section_id=second_value
                )
                if section_id.are_need_metas:
                    new_section_id.are_need_metas = section_id.are_need_metas
                    section_id.set_ert_role_meta_ids_to_new_section(new_section_id)
                    section_id.set_incidence_type_meta_ids_to_new_section(
                        new_section_id
                    )
                return (CONST.SECTION_FOR_PARENT_SECTION, new_section_id.id)

    def create_handbook_section(
        self, control_number, title, content, handbook_id=False, parent_section_id=False
    ):
        self.ensure_one()

        result = {
            "control_number": control_number,
            "title": title,
            "content": content,
            "safety_management_handbook_id": handbook_id,
            "handbook_parent_section_id": parent_section_id,
        }
        return self.env["legis.handbook.section"].create(result)

    def get_requisition_for_handbook_revision_id(self):
        self.ensure_one()
        if self.requisition_for_handbook_revision_ids:
            return self.requisition_for_handbook_revision_ids[0]
        else:
            return False

    def check_revision_state_of_current_section(self, current_section_id):
        self.ensure_one()
        revision_id = self.get_requisition_for_handbook_revision_id()
        changed_content = revision_id.changed_content_of_handbook_ids.filtered(
            lambda e: e.existing_handbook_section_content_id == current_section_id
        )

        if changed_content.revision_state == CONST.APPROVED_HANDBOOK_SECTION_VERSION:
            return True
        else:
            return False

    def create_requisition_for_handbook_revision(self):
        self.ensure_one()
        self.env["legis.requisition.for.handbook.revision"].create(
            {"editing_request_for_handbook_id": self.id}
        )

    def edit_handbook(self):
        self.ensure_one()
        handbook_id = self.safety_management_handbook_id

        if handbook_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "legis.safety.management.handbook",
                "view_mode": "form",
                "res_id": handbook_id.id,
                "target": "current",
                "context": self.env.context,
            }

    def edit_requisition_for_handbook_revision(self):
        self.ensure_one()
        revision_ids = self.requisition_for_handbook_revision_ids

        if revision_ids:
            revision_id = revision_ids[0]
            return {
                "type": "ir.actions.act_window",
                "res_model": "legis.requisition.for.handbook.revision",
                "view_mode": "form",
                "res_id": revision_id.id,
                "target": "current",
                "context": self.env.context,
            }

    def edit_handbook_revision_report(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "legis.handbook.revision.report",
            "view_mode": "form",
            "res_id": self.handbook_revision_report_id.id,
            "target": "current",
            "context": self.env.context,
        }

    def notify_DPA(self):
        self.ensure_one()
        group_xml_id = "group_ship_head_of_legal"
        subject = f"Yêu cầu kiểm tra, sửa đổi sổ tay!"
        body = f"Bản ghi {self.ref} cần yêu cầu sửa đổi sổ tay!"
        company_id = self.company_id

        self._send_notification_by_group_xml_and_company_id(
            group_xml_id, company_id, subject, body
        )

    def _get_default_value_model(self):
        model_name = "utilities.default.value"
        default_value_model = self.env[model_name].search([])

        return default_value_model

    def notify_for_periodic_handbook_check(self):
        record = self.create({"request_type": CONST.PERIODIC})
        default_value_model = self._get_default_value_model()
        variable_name = (
            UTILITIES_CONST.USERS_LEGIS_EDITING_REQUEST_FOR_HANDBOOK_PERIODIC_NOTIFY
        )
        user_ids = default_value_model._get_default_value_by_variable_name(
            variable_name
        )

        subject = "Thông báo kiểm tra sổ tay định kỳ!!"
        message = f"Thông báo kiểm tra sổ tay định kỳ!!"

        for user in user_ids:
            record._send_notification_by_user(user, subject, message)
