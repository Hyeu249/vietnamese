# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from odoo.exceptions import ValidationError


class Notification(models.Model):
    _name = "utilities.notification"
    _description = "Notification records"
    _inherit = ["mail.thread"]

    def _get_users_by_group_id_and_company_id(self, group_id, company_id):
        return self.env["res.users"].search(
            [("groups_id", "=", group_id), ("company_ids", "=", company_id.id)]
        )

    def _get_users_by_group_xml_id_and_company_id(self, group_xml_id, company_id):
        group = self.env.ref(f"utilities.{group_xml_id}", raise_if_not_found=False)

        group_id = group.id if group else None

        users = self.env["res.users"].search(
            [("groups_id", "=", group_id), ("company_ids", "=", company_id.id)]
        )
        return users

    def _send_notification_by_group_xml_and_company_id(
        self, group_xml_id, company_id, subject, body, className="default_title_color"
    ):
        group_users = self._get_users_by_group_xml_id_and_company_id(
            group_xml_id, company_id
        )
        current_user = self.env.user

        users_except_current = group_users.filtered(lambda user: user != current_user)

        for user in users_except_current:
            self._send_notification_by_user(user, subject, body, className)

    def _send_notification_by_group_id_and_company_id(
        self, group_id, company_id, subject, body, className="default_title_color"
    ):
        users = self._get_users_by_group_id_and_company_id(group_id, company_id)
        current_user = self.env.user
        users_except_current = users.filtered(lambda user: user != current_user)

        for user in users_except_current:
            self._send_notification_by_user(user, subject, body, className)

    def _send_notification_by_user(
        self, user, subject, body, className="default_title_color"
    ):
        self._send_single_message_post(user.partner_id, subject, body, className)
        self._send_simple_notification(user.partner_id, subject, body)

    def _send_simple_notification(self, partner_id, subject, body):
        self.env["bus.bus"]._sendone(
            partner_id,
            "simple_notification",
            {
                "title": subject,
                "message": body,
                "sticky": False,
            },
        )

    def _send_single_message_post(self, partner_id, subject, body, className):
        html_subject = f"<div class='bold {className}'>{subject}</div>"
        html_body = f"<div>{body}</div>"

        self.message_post(
            body=f"<div>{html_subject}{html_body}</div>",
            partner_ids=[partner_id.id],
            message_type="notification",
            subtype_xmlid="mail.mt_comment",
        )

    def _message_post_channel(self, channel, subject, body):
        if channel:
            channel.message_post(
                subject=subject,
                body=body,
                message_type="comment",
                subtype_xmlid="mail.mt_comment",
            )

    def _console_log(self, body):
        self.env["bus.bus"]._sendone(
            self.env.user.partner_id,
            "simple_notification",
            {
                "title": "console.log",
                "message": f"{body}",
                "sticky": True,
            },
        )

    def _post_chatter_message_to_related_model_on_write(
        self, vals, related_model_name, tracking_fields=None
    ):
        """
        Post a chatter message to the related model on write.
        Args:
            vals: the vals of the write method
            related_model_name: the name of the related model
            tracking_fields: a list of fields to track changes. Default is None, which means track all fields
        """
        for record in self:
            # get old values of changed fields
            # from the record. Only check for fields
            # in tracking_fields
            old_values = {}
            for field in vals:
                if tracking_fields and field not in tracking_fields:
                    continue
                old_values[field] = getattr(record, field)
            # if old_values is empty, then no need to log the changes
            if not old_values:
                continue
            # create a chatter message to log the changes
            message_text = record._get_chatter_message_on_write(old_values, vals)
            # if this survey data is linked to a record of the related model
            # then log the changes in the chatter of the related model
            if getattr(record, related_model_name) and message_text:
                getattr(record, related_model_name).message_post(body=message_text)

    def _get_chatter_message_on_write(self, old_values, vals):
        """
        Get a chatter message to log the changes on write.
        Args:
            old_values: the old values of the record
            vals: the vals of the write method
        Returns: a string of the message
        """
        return None
