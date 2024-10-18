# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from ...ship_management.models import CONST as SHIP_CONST

from odoo.exceptions import ValidationError
import logging
from datetime import timedelta, datetime
import pyshorteners

SUPER_ADMIN_GROUP_EXTERN_ID = "utilities.group_ship_admin"


class ApprovalStatusReminderSender(models.Model):
    _name = "utilities.approval.status.reminder.sender"
    _description = "Approval status reminder sender records"
    _inherit = ["utilities.notification"]

    def send_a_reminder_to_the_current_approver(self):
        group_id = self.env.context.get("group_id", False)
        model_name = self.env.context.get("model_name", False)
        record_id = self.env.context.get("record_id", False)

        model = self.env[model_name].browse(record_id)
        model._send_inbox(group_id)


class ApprovalStatus(models.Model):
    _name = "utilities.approval.status"
    _description = "Approval status records"
    _inherit = ["utilities.notification"]

    # slot fields
    _edit_field_permissions_list = {}
    name_for_noti = fields.Char("Name for noti", default="")
    message_id = fields.Char("message_id")

    # Primary fields
    approval_status = fields.Selection(
        "_get_main_approval_status",
        default=lambda self: self._get_first_option_value_of_main_approval_status(),
        string="Approval status",
        tracking=True,
    )

    secondary_approval_status = fields.Selection(
        "_get_secondary_approval_status",
        default=lambda self: self._get_first_option_value_of_secondary_approval_status(),
        string="Approval status 2",
        tracking=True,
    )

    # Compute fields
    xml_id = fields.Char(string="Group xml id", compute="_get_xml_id", store=True)

    # Boolean compute fields
    is_in_proposal_process = fields.Boolean(
        "Is in approval flow", compute="_get_is_in_proposal_process"
    )

    # Boolean fields
    is_off_approval = fields.Boolean("Is off approval", default=False)
    is_for_secondary_approval_flow = fields.Boolean(
        "Is for secondary approval flow", default=False
    )

    # compute functions
    @api.depends("approval_status", "secondary_approval_status")
    def _get_xml_id(self):
        for record in self:
            group_id = record._get_group_id_based_on_approval_status()

            record.xml_id = record._get_group_xml_by_group_id(group_id)

    @api.depends("approval_status", "secondary_approval_status")
    def _get_is_in_proposal_process(self):
        for record in self:
            approval_status = record._get_approval_status()
            last_level = record._get_the_last_value_of_the_flow()

            if record._is_approved() or record._is_rejected():
                record.is_in_proposal_process = False

            elif approval_status == last_level:
                record.is_in_proposal_process = False

            else:
                record.is_in_proposal_process = True

    # constrain functions

    def verify_user_permission(self, vals):
        """
        Verify if the current user is allowed to edit the record.

        Raises:
            odoo.exceptions.ValidationError: If the user is not allowed to edit.
        """
        self.ensure_one()
        bypass_checks = self.env.context.get("bypass_checks")

        if bypass_checks:
            return
        elif self.are_all_edit_field_permissions_list(vals):
            self.check_user_permission_in_edit_field_permissions_list(vals)
            return
        else:
            self._check_if_current_user_allowed_to_perform()

    def are_all_edit_field_permissions_list(self, vals):
        """
        Check if all field_names in vals belong to field_names in the permission list.

        Args:
            vals (iterable): The field names to check.

        Returns:
            bool: True if all field_names belong to field_names in the permission list, False otherwise.
        """
        self.ensure_one()
        field_names = self._edit_field_permissions_list.keys()

        return all(field_name in field_names for field_name in vals)

    def check_user_permission_in_edit_field_permissions_list(self, vals):
        """
        Checks if the current user has permissions in the sudo field permission list.

        Raises:
            odoo.exceptions.AccessDenied: If the current user does not have permissions in sudo fields.
        """
        self.ensure_one()

        for field_name, group_xml_ids in self._edit_field_permissions_list.items():
            if field_name not in vals:
                continue
            if group_xml_ids == []:
                # allow editing
                pass
            else:
                if not self.is_current_user_in_group_list(group_xml_ids):
                    self._check_if_current_user_allowed_to_perform()

    def is_current_user_in_group_list(self, group_xml_ids):
        """
        Checks if the current user has any of the provided groups.

        Args:
            group_xml_ids (list): List of group xml ids to check.

        Returns:
            bool: True if the user has any of the provided groups, False otherwise.
        """
        self.ensure_one()

        return any(
            [self.env.user.has_group(group_xml_id) for group_xml_id in group_xml_ids]
        )

    def _check_if_current_user_allowed_to_perform(self):
        self.ensure_one()
        user_has_admin_group = self.env.user.has_group(SUPER_ADMIN_GROUP_EXTERN_ID)
        if user_has_admin_group:
            return True

        user_has_group = self.env.user.has_group(self.xml_id)
        message = "Không có quyền thao tác, vui lòng liên hệ admin!"

        if not user_has_group:
            raise ValidationError(message)
        return False

    @api.model_create_multi
    def create(self, vals_list):
        result = super(ApprovalStatus, self).create(vals_list)
        return result

    def write(self, vals):
        for record in self:
            record.validate_approval_flow(vals)
            record.verify_user_permission(vals)

        result = super(ApprovalStatus, self).write(vals)

        for record in self:
            if record.is_off_approval:
                return result

            if not self.are_only_approval_fields_changed(vals):
                record._send_record_edited_notifications_to_users(vals)
            elif "approval_status" in vals or "secondary_approval_status" in vals:
                record._send_record_propose_request_notifications_to_users()

            if "approval_status" in vals or "secondary_approval_status" in vals:
                model_name = "utilities.model_utilities_approval_status_reminder_sender"
                name = f"Approval reminder notification {record._name}-{record.ref}"
                model_id = self.env.ref(model_name).id

                if record._is_approved() or record._is_rejected():
                    record.remove_approval_reminder_notification_cron(name, model_id)
                else:
                    record.approval_reminder_notification_cron(name, model_id)

        return result

    def get_group_by_current_approval_status(self):
        self.ensure_one()
        group_id = self._get_group_id_based_on_approval_status()
        group = self.env["res.groups"].browse(group_id)

        return group

    def shorten_url(self, long_url):
        s = pyshorteners.Shortener()
        short_url = s.tinyurl.short(long_url)
        return short_url

    def record_url(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        record_url = f"{base_url}/web#id={self.id}&model={self._name}&view_type=form"
        shorted_record_url = self.shorten_url(record_url)
        return shorted_record_url

    def get_tele_sendMessage_data(self):
        self.ensure_one()
        group = self.get_group_by_current_approval_status()
        message_1 = f"*{self._description}* cần duyệt *{self.name_for_noti}*({self.ref}).\nNgười duyệt: *{group.name}*\n"
        message_2 = f"[Xem chi tiết tại đây]({self.record_url()})"

        return message_1 + message_2

    def update_message_id(self, message_id):
        self.ensure_one()
        self.bypass_checks().message_id = message_id

    def get_message_id(self):
        self.ensure_one()
        raise ValidationError(f"{self.message_id}")

    def _send_record_propose_request_notifications_to_users(self):
        self.ensure_one()
        group_id = self._get_group_id_based_on_approval_status()
        company_id = self.company_id
        group = self.env["res.groups"].browse(group_id)
        name_for_noti = f"({self.name_for_noti})" if self.name_for_noti else ""
        classes = "title_request_color"
        subject = f"{self._description}(đề xuất)"
        message = (
            f"Bản ghi {self.ref}{name_for_noti} cần được xem qua bởi {group.name}!"
        )

        self._send_notification_by_group_id_and_company_id(
            group_id, company_id, subject, message, classes
        )

    def _send_record_edited_notifications_to_users(self, vals):
        edit_what = ",".join(vals)
        group_ids = self._get_group_ids_for_record_edited_notification()
        company_id = self.company_id
        current_user = self.env.user
        name_for_noti = f"({self.name_for_noti})" if self.name_for_noti else ""
        classes = "title_quote_color"
        subject = f"{self._description}(chỉnh sửa)"
        message = f"Bản ghi {self.ref}{name_for_noti} đã chỉnh sửa {edit_what} bởi {current_user.name}!"

        for group_id in group_ids:
            self._send_notification_by_group_id_and_company_id(
                group_id, company_id, subject, message, classes
            )

    def get_all_previous_option_values_based_on_approval_status(self):
        self.ensure_one()
        approval_status = self._get_approval_status()
        option_values = self._get_option_values_based_on_approval_status()

        if option_values:
            if self._is_approved() or self._is_rejected():
                approval_status = self._get_the_last_value_of_the_flow()

            index = self._get_index_by_approval_status_value(approval_status)

            return option_values[0:index]
        else:
            return []

    def _get_group_ids_for_record_edited_notification(self):
        option_values = self.get_all_previous_option_values_based_on_approval_status()

        return [self._get_group_id_by_option_value(e) for e in option_values]

    def are_only_approval_fields_changed(self, vals):
        approval_model_fields = [
            "approval_status",
            "secondary_approval_status",
            "name_for_noti",
            "is_off_approval",
            "xml_id",
            "is_in_proposal_process",
        ]

        are_only_approval_fields_changed = all(x in approval_model_fields for x in vals)

        if are_only_approval_fields_changed:
            return True
        else:
            return False

    def remove_approval_reminder_notification_cron(self, name, model_id):
        cron_job = (
            self.env["ir.cron"]
            .sudo()
            .search(
                [
                    ("name", "=", name),
                    ("model_id", "=", model_id),
                ]
            )
        )

        if cron_job:
            cron_job.sudo().unlink()

    def approval_reminder_notification_cron(self, name, model_id):
        self.ensure_one()
        timeout = timedelta(seconds=10)
        scheduled_time = datetime.now() + timeout

        self.remove_approval_reminder_notification_cron(name, model_id)
        context = {
            "group_id": self._get_group_id_based_on_approval_status(),
            "model_name": self._name,
            "record_id": self.id,
        }
        default_model = self._get_default_value_model()
        variable_name_1 = (
            CONST.INTEGER_UTILITIES_APPROVAL_STATUS_INTERVAL_NUMBER_TIME_FOR_APPROVER
        )
        variable_name_2 = CONST.STRING_UTILITIES_APPROVAL_STATUS_INTERVAL_TYPE_TIME_FOR_APPROVER
        interval_number = (
            default_model._get_default_value_by_variable_name(variable_name_1) or 2
        )
        interval_type = (
            default_model._get_default_value_by_variable_name(variable_name_2)
            or "hours"
        )

        self.env["ir.cron"].sudo().create(
            {
                "name": name,
                "model_id": model_id,
                "type": "ir.actions.server",
                "state": "code",
                "code": f"model.with_context({context}).send_a_reminder_to_the_current_approver()",
                "active": True,
                "nextcall": scheduled_time.strftime("%Y-%m-%d %H:%M:%S"),
                "interval_number": interval_number,
                "interval_type": interval_type,
                "numbercall": "-1",
            }
        )

    def _send_inbox(self, group_id):
        self.ensure_one()
        company_id = self.sudo().company_id
        subject = f"Yêu cầu duyệt từ {self._description}"
        message = f"Bản ghi cần được duyệt!"

        self._send_notification_by_group_id_and_company_id(
            group_id, company_id, subject, message
        )

    def _send_noti_for_people_after_approve_record(self):
        self.ensure_one()
        default_value_model = self._get_default_value_model()
        variable_name = CONST.USERS_UTILITIES_APPROVAL_STATUS_NOTIFICATION_FOR_APPROVED
        user_ids = default_value_model._get_default_value_by_variable_name(
            variable_name
        )

        classes = "title_approved_color"
        subject = "Đơn đã duyệt xong!!"
        message = f"Vui lòng kiểm tra bản ghi {self.ref}!!"

        for user in user_ids:
            self._send_notification_by_user(user, subject, message, classes)

    def _get_default_value_model(self):
        model_name = "utilities.default.value"
        default_value_model = self.env[model_name].search([])

        return default_value_model

    def unlink(self):
        return super(ApprovalStatus, self).unlink()

    # get approval status

    def _get_main_approval_status(self):
        selection = self._get_main_approval_selection()
        selection.append((CONST.REJECTED, "Từ chối"))
        selection.append((CONST.APPROVED, "Chấp thuận"))
        return selection

    def _get_secondary_approval_status(self):
        selection = self._get_secondary_approval_selection()
        selection.append((CONST.REJECTED, "Từ chối"))
        selection.append((CONST.APPROVED, "Chấp thuận"))
        return selection

    # default value functions
    def _get_first_option_value_of_main_approval_status(self):
        selection = self._get_main_approval_selection()
        first_option_value = None

        if selection:
            first_option = selection[0]
            if first_option:
                first_option_value = first_option[0]

        return first_option_value

    def _get_first_option_value_of_secondary_approval_status(self):
        selection = self._get_secondary_approval_selection()
        first_option_value = None

        if selection:
            first_option = selection[0]
            if first_option:
                first_option_value = first_option[0]

        return first_option_value

    # approval functions
    def bypass_checks(self):
        self.ensure_one()
        context = dict(self.env.context)
        context.update({"bypass_checks": True})

        return self.with_context(context)

    def restart_flow(self):
        self.ensure_one()
        first_option_value = (
            self._get_first_option_value_based_on_current_approval_status_flow()
        )
        self.bypass_checks()._set_approval_status(first_option_value)

    def sudo_approve(self):
        self.ensure_one()
        self = self.bypass_checks()._set_approval_status(CONST.APPROVED)

    def action_propose(self):
        self.ensure_one()

        if self._is_validate_to_propose_record():
            approval_status = self._get_next_level_to_propose()
            self._set_approval_status(approval_status)

    def action_unpropose(self):
        self.ensure_one()

        if self._is_approved() or self._is_rejected():
            approval_status = self._get_option_value_of_second_last_approval_level()
            self._set_approval_status(approval_status)

        else:
            if self._is_validate_to_unpropose_record():
                approval_status = self._get_previous_level_to_unpropose()
                self._set_approval_status(approval_status)

    def action_approve(self):
        self.ensure_one()
        self._set_approval_status(CONST.APPROVED)

    def action_reject(self):
        self.ensure_one()
        self._set_approval_status(CONST.REJECTED)

    def _is_approved(self):
        self.ensure_one()
        approval_status = self._get_approval_status()

        return approval_status == CONST.APPROVED

    def _is_rejected(self):
        self.ensure_one()
        approval_status = self._get_approval_status()

        return approval_status == CONST.REJECTED

    # switch functions
    def switch_to_main_approval_status(self):
        self.ensure_one()

        if self.is_for_secondary_approval_flow:
            self.bypass_checks().write(
                {
                    "is_for_secondary_approval_flow": False,
                    "approval_status": self._get_first_option_value_of_main_approval_status(),
                    "secondary_approval_status": self._get_first_option_value_of_secondary_approval_status(),
                }
            )

    def switch_to_secondary_approval_status(self):
        self.ensure_one()

        if not self.is_for_secondary_approval_flow:
            self.bypass_checks().write(
                {
                    "is_for_secondary_approval_flow": True,
                    "approval_status": self._get_first_option_value_of_main_approval_status(),
                    "secondary_approval_status": self._get_first_option_value_of_secondary_approval_status(),
                }
            )

    # validate functions
    def validate_approval_flow(self, vals):
        self.ensure_one()
        message = f"Không có quyền thao thác, vui lòng gửi lại hoặc liên hệ admin!"

        bypass_checks = self.env.context.get("bypass_checks")
        if bypass_checks:
            return

        if self._is_proposing(vals):
            self.not_allow_user_to_propose_more_than_1_level(vals)

        # elif self.is_leave_from_approve_or_reject_process(vals):
        #     if not self.is_move_to_penultimate_level(vals):
        #         raise ValidationError(message)

        elif self._is_move_to_approve_or_reject_process(vals):
            if not self.is_move_from_last_level(vals):
                raise ValidationError(message)

    def _is_proposing(self, vals):
        self.ensure_one()
        old_status, new_status, option_values = (
            self._get_old_new_and_option_values_of_approval_status(vals)
        )

        return old_status in option_values and new_status in option_values

    def _get_old_new_and_option_values_of_approval_status(self, vals):
        self.ensure_one()
        option_values = self._get_option_values_based_on_approval_status()
        old_status = self._get_approval_status()
        new_status = vals.get("approval_status")

        return old_status, new_status, option_values

    def not_allow_user_to_propose_more_than_1_level(self, vals):
        """
        Check if the user is not allowed to propose changes that span more than one approval level.
        """
        self.ensure_one()

        if self._get_proposal_level(vals) >= 2:
            raise ValidationError(f"Không thể đẩy từ 2 cấp độ trở lên!")

    def _get_proposal_level(self, vals):
        self.ensure_one()
        new_status = vals.get("approval_status")
        old_index = self._get_index_of_current_approval_status()
        new_index = self._get_index_by_approval_status_value(new_status)

        if self._is_proposing(vals):
            return abs(old_index - new_index)
        else:
            return False

    def _get_index_by_approval_status_value(self, approval_status):
        self.ensure_one()
        option_values = self._get_option_values_based_on_approval_status()

        if approval_status in option_values:
            return option_values.index(approval_status)
        else:
            message = f"Trạng thái duyệt không có trong luồng duyệt hiện tại, vui lòng xem lại!"
            raise ValidationError(message)

    def _is_move_to_approve_or_reject_process(self, vals):
        old_status, new_status, option_values = (
            self._get_old_new_and_option_values_of_approval_status(vals)
        )

        is_approved = new_status == CONST.APPROVED
        is_rejected = new_status == CONST.REJECTED

        return old_status in option_values and (is_approved or is_rejected)

    def is_move_from_last_level(self, vals):
        self.ensure_one()
        old_status, new_status, option_values = (
            self._get_old_new_and_option_values_of_approval_status(vals)
        )
        return old_status == option_values[-1]

    # others
    def _get_main_approval_selection(self):
        level_ids = self.get_main_approval_levels()

        return [self._get_option_by_level_id(level_id) for level_id in level_ids]

    def _get_secondary_approval_selection(self):
        level_ids = self.get_secondary_approval_levels()

        return [self._get_option_by_level_id(level_id) for level_id in level_ids]

    def get_main_approval_levels(self):
        approval_flow_id = self._get_main_approval_flow_id()
        level_ids = approval_flow_id.approval_level_ids

        if level_ids:
            return level_ids
        else:
            return []

    def get_secondary_approval_levels(self):
        approval_flow_id = self._get_secondary_approval_flow_id()
        level_ids = approval_flow_id.approval_level_ids

        if level_ids:
            return level_ids
        else:
            return []

    def _get_main_approval_flow_id(self):
        model_name = "utilities.approval.flow"
        condition = [("model_name", "=", self._name), ("is_secondary", "=", False)]

        return self.env[model_name].search(condition, limit=1)

    def _get_secondary_approval_flow_id(self):
        model_name = "utilities.approval.flow"
        condition = [("model_name", "=", self._name), ("is_secondary", "=", True)]

        return self.env[model_name].search(condition, limit=1)

    def _get_option_by_level_id(self, level_id):
        value = self._get_option_value_by_level_id(level_id)
        label = level_id.name

        option = (value, label)
        return option

    def _get_option_value_by_level_id(self, level):
        group_id = level.user_group.id

        return self._get_option_value_for_approval_status(group_id, level.second_time)

    def _get_option_value_for_approval_status(self, group_id, is_second=False):
        if is_second:
            return f"{group_id}-{CONST.SECOND_TIME_APPROVAL_OPTION_VALUE}"
        else:
            return str(group_id)

    def _get_approval_status(self):
        self.ensure_one()

        if self.is_for_secondary_approval_flow:
            return self.secondary_approval_status
        else:
            return self.approval_status

    def _set_approval_status(self, value):
        self.ensure_one()

        if self.is_for_secondary_approval_flow:
            self.secondary_approval_status = value
        else:
            self.approval_status = value

    def _get_group_xml_by_group_id(self, group_id):
        self.ensure_one()
        group = self.env["res.groups"].browse(group_id)
        xml_id = "EMPTY.EMPTY"

        if group:
            xml_id = list(group.ensure_one().get_xml_id().values())[0]

        return xml_id

    def _get_group_id_by_option_value(self, option_value):
        self.ensure_one()

        if CONST.SECOND_TIME_APPROVAL_OPTION_VALUE in str(option_value):
            group_id = option_value.split("-")[0]

            return int(group_id)
        else:
            return int(option_value)

    def _get_group_id_based_on_approval_status(self):
        self.ensure_one()
        approval_status = self._get_approval_status()

        if self._is_approved() or self._is_rejected():
            group_id = self._get_the_last_group_id_of_the_flow()
            return int(group_id)

        elif CONST.SECOND_TIME_APPROVAL_OPTION_VALUE in str(approval_status):
            group_id = approval_status.split("-")[0]

            return int(group_id)
        else:
            return int(approval_status)

    def _get_the_last_group_id_of_the_flow(self):
        self.ensure_one()
        level_ids = self._get_level_ids_based_on_approval_status()
        last_level_id = level_ids[-1]

        if not level_ids:
            raise ValidationError(f"Không tìm thấy luồng duyệt cho {self._name}")
        else:
            return last_level_id.user_group.id

    def _get_option_values_based_on_approval_status(self):
        """
        return option values from current approval selection base on level_ids
        """
        self.ensure_one()
        level_ids = self._get_level_ids_based_on_approval_status()

        return [self._get_option_value_by_level_id(level_id) for level_id in level_ids]

    def _get_level_ids_based_on_approval_status(self):
        self.ensure_one()

        if self.is_for_secondary_approval_flow:
            return self.get_secondary_approval_levels()
        else:
            return self.get_main_approval_levels()

    def _get_the_last_value_of_the_flow(self):
        self.ensure_one()
        option_values = self._get_option_values_based_on_approval_status()

        if len(option_values) >= 1:
            return option_values[-1]

    def _get_the_first_value_of_the_flow(self):
        self.ensure_one()
        option_values = self._get_option_values_based_on_approval_status()

        if option_values:
            return option_values[0]

    def _is_the_end_of_proposition(self):
        self.ensure_one()
        status = self._get_approval_status()
        last_approval_level = self._get_the_last_value_of_the_flow()

        return status == last_approval_level

    def _is_the_beginning_of_proposition(self):
        self.ensure_one()
        status = self._get_approval_status()
        first_approval_level = self._get_the_first_value_of_the_flow()

        return status == first_approval_level

    def _is_validate_to_propose_record(self):
        self.ensure_one()

        if (
            not self._is_approved()
            and not self._is_rejected()
            and not self._is_the_end_of_proposition()
        ):
            return True
        else:
            return False

    def _is_validate_to_unpropose_record(self):
        self.ensure_one()

        if (
            not self._is_approved()
            and not self._is_rejected()
            and not self._is_the_beginning_of_proposition()
        ):
            return True
        else:
            return False

    def _get_index_of_current_approval_status(self):
        self.ensure_one()
        option_values = self._get_option_values_based_on_approval_status()
        status = self._get_approval_status()

        if status in option_values:
            return option_values.index(status)
        else:
            message = f"Trạng thái duyệt không có trong luồng duyệt hiện tại, vui lòng xem lại!"
            raise ValidationError(message)

    def _get_next_level_to_propose(self):
        self.ensure_one()
        option_values = self._get_option_values_based_on_approval_status()
        index = self._get_index_of_current_approval_status()

        return option_values[index + 1]

    def _get_previous_level_to_unpropose(self):
        self.ensure_one()
        option_values = self._get_option_values_based_on_approval_status()
        index = self._get_index_of_current_approval_status()

        return option_values[index - 1]

    def _get_option_value_of_second_last_approval_level(self):
        self.ensure_one()
        option_values = self._get_option_values_based_on_approval_status()

        if len(option_values) >= 2:
            return option_values[-2]

    def send_an_email_to_remind_the_current_approver(self, group_id, user_id):
        self.ensure_one()
        template = self.env.ref("utilities.email_to_remind_the_current_approver").id
        role_id = self.env["res.groups"].browse(group_id)

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        record_url = f"{base_url}/web#id={self.id}&view_type=form&model={self._name}"

        context = {
            "self": self,
            "role_name": role_id.name,
            "record_url": record_url,
        }
        email_values = {
            "email_to": user_id.email,
        }
        (
            self.env["mail.template"]
            .browse(template)
            .with_context(context)
            .send_mail(self.id, email_values=email_values, force_send=False)
        )

    def _get_first_option_value_based_on_current_approval_status_flow(self):
        self.ensure_one()
        if self.is_for_secondary_approval_flow:
            return self._get_first_option_value_of_secondary_approval_status()
        else:
            return self._get_first_option_value_of_main_approval_status()

    def is_at_this_approval_level(self, group_xml_id):

        group = self.get_group_by_group_xml_id(group_xml_id)
        group_id = self._get_group_id_based_on_approval_status()

        return group_id == group.id

    def is_second_time_level(self):
        self.ensure_one()
        approval_status = self._get_approval_status()
        return CONST.SECOND_TIME_APPROVAL_OPTION_VALUE in approval_status

    def get_group_by_group_xml_id(self, group_xml_id):
        module = "utilities"
        module_group_xml_id = f"{module}.{group_xml_id}"

        return self.env.ref(module_group_xml_id, raise_if_not_found=False)

    def is_second_last_approval_level(self):
        self.ensure_one()
        approval_status_value = self._get_approval_status()
        second_last_value = self._get_option_value_of_second_last_approval_level()

        return approval_status_value == second_last_value

    def _off_approval(self):
        self.is_off_approval = True

    def _on_approval(self):
        self.is_off_approval = False

    def _is_approval_status_greater_than_this_group_xml_id(self, group_xml_id):
        self.ensure_one()
        group = self.get_group_by_group_xml_id(group_xml_id)
        str_group_id = str(group.id)

        if self._is_approved() or self._is_rejected():
            return True

        group_xml_id_index = self._get_index_by_approval_status_value(str_group_id)
        approval_status_index = self._get_index_of_current_approval_status()

        if approval_status_index > group_xml_id_index:
            return True
        else:
            return False

    def _get_supplier_group_id(self):
        supplier_id = self.get_group_by_group_xml_id(SHIP_CONST.SUPPLIER)

        return supplier_id

    def _propose_approval_to(self, xml_id, is_second=False):
        group = self.get_group_by_group_xml_id(xml_id)

        if group:
            value = self._get_option_value_for_approval_status(group.id, is_second)
            self.bypass_checks()._set_approval_status(value)

    def get_approval_status(self):
        records = self.search([])

        for record in records:
            if record.request_state == CONST.APPROVED:
                record.bypass_checks()._set_approval_status(CONST.APPROVED)
            elif record.request_state == CONST.REJECTED:
                record.bypass_checks()._set_approval_status(CONST.REJECTED)

    def mapped_status(self):
        status = []
        for record in self:
            status.append(record._get_approval_status())

        return status

    def mapped_unique_status(self):
        statuses = self.mapped_status()
        unique_statuses = list(set(statuses))

        if len(unique_statuses) == 1:
            return unique_statuses[0]
        else:
            return unique_statuses
