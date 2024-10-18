# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from ...utilities.models import CONST as CONST_UTILITIES
from odoo.exceptions import ValidationError
import difflib
from bs4 import BeautifulSoup
from collections import defaultdict


class Contract(models.Model):
    _name = "docking.contract"
    _description = "Hợp đồng"
    _inherit = ["utilities.approval.status", "mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)
    unrendered_html_content = fields.Html(
        "Editable contract content",
        default=lambda self: self._get_contract_html_content_template(),
        tracking=True,
    )
    rendered_html_content = fields.Html(
        "Rendered contract",
    )
    is_completed = fields.Boolean("Is completed", readonly=True, tracking=True)
    total_price = fields.Integer(
        "Total price", compute="_get_total_price", tracking=True
    )
    progress = fields.Integer(string="Progress", compute="_compute_progress")

    contract_old_new_diff = fields.Html("Test diff")

    # related
    name_for_noti = fields.Char(
        related="name",
        string="Name",
    )

    # relations
    docking_plan_id = fields.Many2one(
        "docking.docking.plan",
        string="Docking plan",
        tracking=True,
    )
    supplier_id = fields.Many2one(
        "docking.supplier",
        string="Supplier",
        tracking=True,
    )
    contract_payment_instalment_id = fields.Many2one(
        "docking.contract.payment.instalment",
        domain="[('contract_id', '=', id)]",
        string="Contract Payment Instalment",
        tracking=True,
    )
    contract_payment_instalment_ids = fields.One2many(
        "docking.contract.payment.instalment",
        "contract_id",
        string="Contract Payment Instalment",
        tracking=True,
    )
    contract_history_ids = fields.One2many(
        "docking.contract.history",
        "contract_id",
        domain="[('contract_id', '=', False)]",
        string="Contract history",
        tracking=True,
    )
    contract_history_id = fields.Many2one(
        "docking.contract.history",
        domain="[('contract_id', '=', id)]",
        string="Old contract",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    def get_contract_old_new_diff(self):
        self.ensure_one()
        history_html = self.contract_history_id.html
        old = BeautifulSoup(history_html).prettify() if history_html else ""
        new = BeautifulSoup(self.rendered_html_content).prettify()
        old = BeautifulSoup(old).get_text()
        new = BeautifulSoup(new).get_text()
        diff = difflib.HtmlDiff(wrapcolumn=75).make_file(
            old.splitlines(), new.splitlines()
        )
        self.contract_old_new_diff = diff

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("docking.contract")
        result = super(Contract, self).create(vals_list)

        for record in result:
            for i in range(3):
                record._create_contract_payment_instalment(i + 1, 33.333)
            record.render_html_content()
        return result

    def write(self, vals):
        old_rendered_html_content = self.rendered_html_content
        old_contract_history_id = self.contract_history_id
        result = super(Contract, self).write(vals)

        if "approval_status" in vals:
            if self._is_rejected():
                self.is_completed = False

        # if unrendered_html_content is changed, re-render the html content
        if "unrendered_html_content" in vals:
            self.render_html_content()
        if "rendered_html_content" in vals:
            if old_rendered_html_content != self.rendered_html_content:
                self._create_array_value(old_rendered_html_content, set_array_id=True)

        if "contract_history_id" in vals:
            if old_contract_history_id != self.contract_history_id:
                self.get_contract_old_new_diff()

        return result

    def unlink(self):
        for record in self:
            record.contract_payment_instalment_ids.unlink()
        return super(Contract, self).unlink()

    def _create_array_value(self, html, set_array_id=False):
        self.ensure_one()
        contract_history_id = self.env["docking.contract.history"].create(
            {
                "html": html,
                "contract_id": self.id,
            }
        )

        if set_array_id:
            self.contract_history_id = contract_history_id

        return contract_history_id

    def _get_default_value_model(self):
        model_name = "utilities.default.value"
        default_value_model = self.env[model_name].search([])

        return default_value_model

    def _get_contract_html_content_template(self):
        default_value_model = self._get_default_value_model()
        variable_name = CONST_UTILITIES.HTML_DOCKING_CONTRACT_UNRENDERED_CONTENT
        return default_value_model._get_default_value_by_variable_name(variable_name)

    def render_html_content(self):
        self.ensure_one()
        placeholders = {
            "ship_name": self.company_id.name,
            "supplier_name": self.supplier_id.name,
            "today": fields.Date.today().strftime("%d-%m-%Y"),
            "total_price": self.total_price,
        }
        # add payment instalments' percentage
        for instalment in self.contract_payment_instalment_ids:
            placeholders[f"instalment_{instalment.sequence}"] = instalment.percentage

        new_html_contract = str(self.unrendered_html_content).format_map(
            defaultdict(lambda: "", placeholders)
        )

        self.rendered_html_content = (
            new_html_contract + self._render_html_expected_cost_report_table()
        )

    def _render_html_expected_cost_report_table(self):
        return f"""
            <table class="table table-bordered o_table">
                <tbody>
                    <tr style="height: 48px;">
                        <td style="width: 604px;"><br>
                        </td>
                        <td style="width: 604px;">
                            <h1 style="text-align:center;">Dự toán chi phí</h1>
                        </td>
                    </tr>
                    <tr>
                        <td class="bg-o-color-4">
                            <h3 style="text-align:center;">Vietnamese</h3>
                        </td>
                        <td class="bg-o-color-4">
                            <h3 style="text-align:center;">English</h3>
                        </td>
                    </tr>
                    {self._render_html_material_rows()}
                    {self._render_html_job_rows()}
                </tbody>
            </table>
            <p><br></p>
        """

    def _render_html_material_rows(self):
        material_quote_ids = self._get_material_quote_ids_by_supplier()
        material_quote_rows = [
            self._render_html_material_row(quote) for quote in material_quote_ids
        ]
        if material_quote_ids:
            return f"""
                <tr style="height: 43px;">
                    <td class="bg-400">
                        <h2 style="text-align:center;">Vật tư</h2>
                    </td>
                    <td class="bg-400">
                        <h2 style="text-align:center;">Material</h2>
                    </td>
                </tr>
                {" ".join(material_quote_rows)}
            """
        else:
            return ""

    def _render_html_job_rows(self):
        job_quote_ids = self._get_job_quote_ids_by_supplier()
        job_quote_rows = [self._render_html_job_row(quote) for quote in job_quote_ids]

        if job_quote_ids:
            return f"""
                <tr style="height: 43px;">
                    <td class="bg-400">
                        <h2 style="text-align:center;">Công việc</h2>
                    </td>
                    <td class="bg-400">
                        <h2 style="text-align:center;">Job</h2>
                    </td>
                </tr>
                {" ".join(job_quote_rows)}
            """
        else:
            return ""

    def _render_html_material_row(self, quote):
        return f"""
            <tr>
                <td>
                    <div>
                        <strong>Tên vật tư</strong>: {quote.material_name}
                    </div>
                    <div>
                        <strong>Số lượng</strong>: {quote.quantity}
                    </div>
                    <div>
                        <strong>Giá đơn vị</strong>: {quote.unit_price}
                    </div>
                    <div>
                        <strong>Tổng giá</strong>: {quote.total_price}
                    </div>
                </td>
                <td>
                    <div>
                        <strong>Material</strong>: {quote.material_name}
                    </div>
                    <div>
                        <strong>Quantity​</strong>: {quote.quantity}
                    </div>
                    <div>
                        <strong>Unit price</strong>: {quote.unit_price}
                    </div>
                    <div>
                        <strong>Total price</strong>: {quote.total_price}
                    </div>
                </td>
            </tr>
        """

    def _render_html_job_row(self, quote):
        return f"""
            <tr>
                <td>
                    <div>
                        <strong>Tên thiết bị</strong>: {quote.equipment_name}
                    </div>
                    <div>
                        <strong>Tên công việc</strong>: {quote.job_id.name}
                    </div>
                    <div>
                        <strong>Giá nhân công</strong>: {quote.labor_cost}
                    </div>
                    <div>
                        <strong>Thành tiền</strong>: {quote.final_cost}
                    </div>
                </td>
                <td>
                    <div>
                        <strong>Equipment</strong>: {quote.equipment_name}
                    </div>
                    <div>
                        <strong>Job</strong>: {quote.job_id.name}
                    </div>
                    <div>
                        <strong>Labor cost</strong>: {quote.labor_cost}
                    </div>
                    <div>
                        <strong>Final cost</strong>: {quote.final_cost}
                    </div>
                </td>
            </tr>
        """

    def _get_material_quote_ids_by_supplier(self):
        expected_cost_report = self.docking_plan_id._get_expected_cost_report_id()

        if expected_cost_report and expected_cost_report._is_approved():
            material_quote_ids = expected_cost_report.material_quote_ids.filtered(
                lambda e: e.material_supplier_quote_id.supplier_id == self.supplier_id
                and e._is_approved()
            )
            if material_quote_ids:
                return material_quote_ids

        return []

    def _get_job_quote_ids_by_supplier(self):
        expected_cost_report = self.docking_plan_id._get_expected_cost_report_id()

        if expected_cost_report and expected_cost_report._is_approved():
            job_quote_ids = expected_cost_report.job_quote_ids.filtered(
                lambda e: e.job_supplier_quote_id.supplier_id == self.supplier_id
                and e._is_approved()
            )
            if job_quote_ids:
                return job_quote_ids

        return []

    def _get_total_price_of_all_quotes(self):
        material_quote_ids = self._get_material_quote_ids_by_supplier()
        job_quote_ids = self._get_job_quote_ids_by_supplier()

        sum_material_q_price = sum([quote.total_price for quote in material_quote_ids])
        sum_job_q_price = sum([quote.labor_cost for quote in job_quote_ids])

        return sum_material_q_price + sum_job_q_price

    def complete_contract(self):
        self.ensure_one()
        if self._is_approved():
            self.is_completed = True

    def _create_contract_payment_instalment(self, sequence, percentage):
        return self.env["docking.contract.payment.instalment"].create(
            {"contract_id": self.id, "sequence": sequence, "percentage": percentage}
        )

    @api.depends("docking_plan_id", "supplier_id")
    def _get_total_price(self):
        for record in self:
            record.total_price = self._get_total_price_of_all_quotes()

    @api.depends("contract_payment_instalment_ids")
    def _compute_progress(self):
        for record in self:
            payment_ids = record.contract_payment_instalment_ids
            if payment_ids:
                completed = sum(
                    [record.percentage for record in payment_ids if record._is_paid()]
                )

                record.progress = completed
            else:
                record.progress = 0

    def send_contract_to_supplier_by_email(self):
        self.ensure_one()
        try:
            template = self.env.ref("docking.contract_for_supplier_template").id
            email_values = self.supplier_id._get_email_values()

            context = {
                "supplier_name": self.supplier_id.name,
            }

            self.supplier_id._send_email(self.id, template, context, email_values)
        except Exception as e:
            raise ValidationError(e)
