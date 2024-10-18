# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
import logging
from ...ship_management.models.common_utils import format_field_date

EMAIL_NOTI_TYPE = "email"
NOTI_TYPES = [
    (EMAIL_NOTI_TYPE, "Email"),
]


class SupplierQuotePortalChangeNotification(models.Model):
    _name = "ship.supplier.quote.portal.change.notification"
    _description = "Supplier quote portal change notification records"
    _inherit = ["mail.thread"]
    _check_company_auto = True

    notification_type = fields.Selection(
        NOTI_TYPES, string="Notification type", default=EMAIL_NOTI_TYPE
    )
    is_notified = fields.Boolean("Is notified", default=False)
    notified_at = fields.Datetime("Notified at")

    # Computed field supplier_name
    supplier_name = fields.Char(
        compute="_compute_supplier_name", string="Supplier name"
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    supplier_id = fields.Many2one("ship.supplier", string="Supplier", required=True)
    material_paint_quotes_request_id = fields.Many2one(
        "ship.material.paint.quotes.request", string="Material paint quotes request"
    )
    maintenance_scope_report_id = fields.Many2one(
        "ship.maintenance.scope.report", string="Maintenance scope report"
    )

    @api.depends("supplier_id")
    def _compute_supplier_name(self):
        for record in self:
            record.supplier_name = record.supplier_id.name

    def send_email_notify_quote_portal_change(self):
        self.ensure_one()
        self.is_notified = True
        try:
            quote_req_ref = self.material_paint_quotes_request_id.ref
            quote_req_deadline = format_field_date(
                self.material_paint_quotes_request_id.deadline
            )
            self.supplier_id.send_email_notify_quote_portal_change(
                quote_req_ref, quote_req_deadline
            )
            self.notified_at = fields.Datetime.now()
        except Exception as e:
            self.is_notified = False
            raise e

    def get_unsent_notifications(self, age_stale_in_days=1):
        """
        Get unsent notifications that are created within the last `age_stale_in_days` days.
        """
        return self.search([("is_notified", "=", False)])

    def action_send_batch_email_notify_quote_portal_change(self):
        """
        Send batch email notifications for unsent notifications.
        """
        unsent_notifications = self.get_unsent_notifications()
        for unsent_notification in unsent_notifications:
            unsent_notification.send_email_notify_quote_portal_change()
