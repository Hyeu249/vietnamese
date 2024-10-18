# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ..models import CONST
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class CreateReviewPlanWiz(models.TransientModel):
    _name = "ship.create.review.plan.wiz"
    _description = "Create review plan wiz records"
    _inherit = ["utilities.notification"]

    expected_review_date = fields.Date(
        string="Expected review date",
        default=lambda self: self.get_default_expected_review_date(),
        tracking=True,
    )

    # relations
    review_plan_id = fields.Many2one("ship.review.plan", readonly=True)

    def get_default_expected_review_date(self):
        today = fields.Date.today()
        return today + relativedelta(years=1)

    def action_confirm(self):
        today = fields.Date.today()
        self.review_plan_id.review_date = today

        self.env["ship.review.plan"].create(
            {"expected_review_date": self.expected_review_date}
        )
