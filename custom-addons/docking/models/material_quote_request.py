# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
from ...ship_management.models import CONST as SHIP_CONST


class MaterialQuoteRequest(models.Model):
    _name = "docking.material.quote.request"
    _description = "Yêu cầu báo giá công việc-docking"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    comment = fields.Char("Comment", tracking=True)
    deadline = fields.Date("Deadline", tracking=True)
    survey_type = fields.Selection(
        CONST.ARISE_SELECTION,
        string="Survey type",
        default=CONST.NORMAL,
        required=True,
        tracking=True,
    )

    # related
    name_for_noti = fields.Char(
        related="docking_plan_id.name",
        string="Docking name",
    )

    # relations
    docking_plan_id = fields.Many2one(
        "docking.docking.plan",
        string="Docking plan",
        tracking=True,
    )

    material_quote_ids = fields.One2many(
        "docking.material.quote",
        "material_quote_request_id",
        string="Material Quote",
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
            model_name = "docking.material.quote.request"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)

        results = super(MaterialQuoteRequest, self).create(vals_list)
        return results

    def write(self, vals):
        old_material_quote_ids = self.material_quote_ids.ids
        old_material_qs = {q.id: q.name_for_noti for q in self.material_quote_ids}

        result = super(MaterialQuoteRequest, self).write(vals)

        new_material_q_ids = self.material_quote_ids.ids

        if old_material_quote_ids != new_material_q_ids:
            added_quotes = list(set(new_material_q_ids) - set(old_material_quote_ids))
            removed_quotes = list(set(old_material_quote_ids) - set(new_material_q_ids))
            removed_names = self.get_removed_quote_name(removed_quotes, old_material_qs)

            self._log_material_quote_changes_to_chatter(added_quotes, removed_names)

        if "approval_status" in vals:
            docking_plan_id = self.docking_plan_id
            all_approved = docking_plan_id._are_all_material_survey_datas_approved()
            message = "Báo cáo chưa đủ điều kiện để tham gia luồng duyệt, vui lòng liên hệ quản trị viên!"

            if not all_approved:
                raise ValidationError(message)

        if "approval_status" in vals:
            for material_q in self.material_quote_ids:
                if not material_q._is_approved() or not material_q._is_rejected():
                    material_q.approval_status = self.approval_status

        return result

    def get_removed_quote_name(self, removed_ids, quotes):
        removed_name = []

        for id, name in quotes.items():
            if id in removed_ids:
                removed_name.append(name)

        return removed_name

    def _log_material_quote_changes_to_chatter(self, added_quotes, removed_names):
        message = ""
        if added_quotes:
            added_names = (
                self.env["docking.material.quote"]
                .browse(added_quotes)
                .mapped("name_for_noti")
            )
            message += "<li>Added quotes: {}</li>".format(", ".join(added_names))

        if removed_names:
            message += "<li>Removed quotes: {}</li>".format(", ".join(removed_names))

        if message:
            full_message = "<ul>{}</ul>".format(message)
            self.message_post(body=full_message)

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def get_new_material_quote_ids(self):
        self.ensure_one()
        material_quote_ids = self._get_material_quote_ids()
        self.material_quote_ids = [(6, 0, material_quote_ids)]

    def _get_material_quote_ids(self):
        survey_ids = self.docking_plan_id.material_survey_data_ids
        get_survey_type = lambda e: e.survey_type == self.survey_type
        material_survey_data_ids = survey_ids.filtered(get_survey_type)

        material_quote_ids = [
            quote.id
            for survey in material_survey_data_ids
            for quote in survey.material_quote_ids
            if quote._arise_or_approved_survey()
        ]
        return material_quote_ids

    def _check_supplier_quote_status_is_complete(self):
        all_quotes_have_price = self._check_all_material_quotes_price()

        if all_quotes_have_price and self.is_at_this_approval_level(CONST.SUPPLIER):
            self.action_propose()

    def _check_all_material_quotes_price(self):
        for material_quote in self.material_quote_ids:
            is_have_price = material_quote._are_all_suppliers_have_priced()

            if not is_have_price:
                return False
        return True

    def open_record(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
            "context": self.env.context,
        }

    def run_material_quote_request_daily_cronjobs(self):
        self._propose_to_material_expert_when_reaching_deadline()

    def _propose_to_material_expert_when_reaching_deadline(self):
        today = fields.Date.today()
        supplier_id = self._get_supplier_group_id()

        conditions = [
            ("deadline", "=", today),
            ("approval_status", "=", supplier_id.id),
        ]
        due_requests = self.search(conditions)

        for request in due_requests:
            request.action_propose()
