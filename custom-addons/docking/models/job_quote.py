# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from ...ship_management.models import CONST as SHIP_CONST
from odoo.exceptions import ValidationError


class JobQuote(models.Model):
    _name = "docking.job.quote"
    _description = "Báo giá công việc-docking"
    _inherit = ["ship.job.quote.template"]
    _check_company_auto = True

    unit = fields.Char("Unit", tracking=True)
    specification = fields.Char("Specification", tracking=True)
    result_evaluate = fields.Char(
        "Result Evaluation",
        tracking=True,
    )

    # for cost settlement report
    quantity = fields.Float("Quantity", tracking=True)
    weight = fields.Float("Weight", tracking=True)
    length = fields.Float("Length", tracking=True)
    width = fields.Float("Width", tracking=True)
    height = fields.Float("Height", tracking=True)
    factor = fields.Float("Factor", tracking=True)

    # for expected cost report
    expected_quantity = fields.Float("Quantity", tracking=True)
    expected_weight = fields.Float("Weight", tracking=True)
    expected_length = fields.Float("Length", tracking=True)
    expected_width = fields.Float("Width", tracking=True)
    expected_height = fields.Float("Height", tracking=True)
    expected_factor = fields.Float("Factor", tracking=True)

    _order = "implement_date ASC"

    # compute
    final_cost = fields.Float(
        "Final Cost", compute="_calculate_final_cost", store=True, tracking=True
    )
    expected_final_cost = fields.Float(
        "Expected final Cost",
        compute="_calculate_expected_final_cost",
        store=True,
        tracking=True,
    )

    # related
    equipment_name = fields.Char(
        "Equipment name",
        related="maintenance_scope_report_id.equipment_survey_data_id.equipment_survey_metadata_id.name",
        store=True,
        tracking=True,
    )
    selected_supplier_name = fields.Char(
        "Selected supplier name",
        related="job_supplier_quote_id.supplier_id.name",
        store=True,
        tracking=True,
    )
    labor_cost = fields.Float(
        "Labor cost",
        related="job_supplier_quote_id.labor_cost",
        store=True,
        tracking=True,
    )
    name_for_noti = fields.Char(
        "Name for noti",
        related="job_id.name",
        store=True,
        tracking=True,
    )
    survey_type = fields.Selection(
        CONST.ARISE_SELECTION,
        string="Survey type",
        related="maintenance_scope_report_id.equipment_survey_data_id.survey_type",
        store=True,
        tracking=True,
    )

    docking_plan_id = fields.Many2one(
        "docking.docking.plan",
        related="maintenance_scope_report_id.equipment_survey_data_id.docking_plan_id",
        string="Docking plan",
        store=True,
        tracking=True,
    )
    unit_price = fields.Float(
        "Unit price", related="job_supplier_quote_id.labor_cost", tracking=True
    )
    final_cost_mathematic_formula = fields.Text(
        "Final Cost Mathematic Formula",
        related="job_id.job_final_cost_formula_id.formula",
        tracking=True,
    )
    maintenance_scope_name = fields.Char(
        related="job_id.maintenance_scope_id.name",
        string="Maintnance scope",
        store=False,
    )
    inspection_date = fields.Date(
        "Inspection Date",
        related="maintenance_scope_report_id.inspection_date",
        store=True,
        readonly=True,
        tracking=True,
        depends=[
            "maintenance_scope_report_id",
            "maintenance_scope_report_id.inspection_date",
        ],
    )

    # relations
    job_supplier_quote_id = fields.Many2one(
        "docking.job.supplier.quote",
        domain="[('job_quote_id', '=', id)]",
        string="Selected job supplier quote",
        tracking=True,
    )
    job_supplier_quote_ids = fields.One2many(
        "docking.job.supplier.quote",
        "job_quote_id",
        string="Job supplier quotes",
        tracking=True,
    )
    job_quote_final_parameter_set_ids = fields.One2many(
        "docking.job.quote.final.parameter.set",
        "job_quote_id",
        string="Job Quote Final Parameter Set",
        tracking=True,
    )
    job_quote_expected_parameter_set_ids = fields.One2many(
        "docking.job.quote.expected.parameter.set",
        "job_quote_id",
        string="Job Quote Expected Parameter Set",
        tracking=True,
    )
    maintenance_scope_job_ids = fields.One2many(
        "docking.job",
        "job_quote_id",
        related="maintenance_scope_report_id.maintenance_scope_id.job_ids",
        string="Job",
        tracking=True,
    )
    job_id = fields.Many2one(
        "docking.job",
        string="Job",
        domain="[('id', 'in', maintenance_scope_job_ids)]",
        tracking=True,
    )
    maintenance_scope_report_id = fields.Many2one(
        "docking.maintenance.scope.report",
        string="Maintenance scope report",
        tracking=True,
    )
    expected_cost_report_id = fields.Many2one(
        "docking.expected.cost.report",
        string="Expected cost report",
        tracking=True,
    )
    cost_settlement_report_id = fields.Many2one(
        "docking.cost.settlement.report",
        string="Cost Settlement Report",
        tracking=True,
    )
    job_quote_request_id = fields.Many2one(
        "docking.job.quote.request",
        string="Job quote request",
        tracking=True,
    )
    job_predefined_factor_id = fields.Many2one(
        "docking.job.final.cost.predefined.factor",
        string="Job predefined factor",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.constrains(
        "quantity",
        "weight",
        "length",
        "width",
        "height",
        "factor",
    )
    def only_allow_edit_specifications_when_job_quote_completed(self):
        message = "Chưa thể điền thông số chính thức, khi công việc chưa hoàn thành!"
        for record in self:

            if record.job_state != CONST.COMPLETED:
                if (
                    record.quantity > 0
                    or record.weight > 0
                    or record.length > 0
                    or record.width > 0
                    or record.height > 0
                    or record.factor > 0
                ):
                    raise ValidationError(f"{message}")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("docking.job.quote")

        result = super(JobQuote, self).create(vals_list)

        return result

    def write(self, vals):
        if not self.are_only_approval_fields_changed(vals):
            # post chatter message to expected cost report
            self._post_chatter_message_to_related_model_on_write(
                vals,
                "expected_cost_report_id",
            )

            # post chatter message to job quote request
            self._post_chatter_message_to_related_model_on_write(
                vals,
                "job_quote_request_id",
                tracking_fields=["job_supplier_quote_id", "labor_cost"],
            )

        result = super(JobQuote, self).write(vals)

        return result

    def unlink(self):
        for record in self:
            record.job_quote_final_parameter_set_ids.unlink()
            record.job_quote_expected_parameter_set_ids.unlink()
        return super(JobQuote, self).unlink()

    def handle_job_state(self, handle_job_state):
        self.ensure_one()
        report_id = self.maintenance_scope_report_id
        if (
            self._is_approved()
            and self.job_state != CONST.TODO
            and not report_id._is_approved()
        ):
            message = "Báo cáo sửa chữa chưa được duyệt, vui lòng thao tác sau!"
            raise ValidationError(message)
        else:
            super(JobQuote, self).handle_job_state(handle_job_state)

    def _set_parameter_for_job_quote(self, parameters):
        self.ensure_one()
        self.write(
            {
                "quantity": parameters.quantity,
                "weight": parameters.weight,
                "length": parameters.length,
                "width": parameters.width,
                "height": parameters.height,
                "factor": parameters.factor,
            }
        )

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    @api.depends(
        "quantity",
        "weight",
        "length",
        "width",
        "height",
        "factor",
        "unit_price",
        "expected_quantity",
        "expected_weight",
        "expected_length",
        "expected_width",
        "expected_height",
        "expected_factor",
    )
    def _calculate_final_cost(self):
        for record in self:
            quantity = record.quantity or record.expected_quantity or 0
            weight = record.weight or record.expected_weight or 0
            length = record.length or record.expected_length or 0
            width = record.width or record.expected_width or 0
            height = record.height or record.expected_height or 0
            factor = record.factor or record.expected_factor or 0
            unit_price = record.unit_price or 0
            if record.final_cost_mathematic_formula:
                final_cost = eval(record.final_cost_mathematic_formula)
                # if final cost is not integer or float, raise error
                if isinstance(final_cost, (int, float)):
                    record.final_cost = final_cost
                else:
                    record.final_cost = unit_price

    @api.depends(
        "expected_quantity",
        "expected_weight",
        "expected_length",
        "expected_width",
        "expected_height",
        "expected_factor",
    )
    def _calculate_expected_final_cost(self):
        for record in self:
            quantity = record.expected_quantity or 0
            weight = record.expected_weight or 0
            length = record.expected_length or 0
            width = record.expected_width or 0
            height = record.expected_height or 0
            factor = record.expected_factor or 0
            unit_price = record.unit_price or 0
            if record.final_cost_mathematic_formula:
                final_cost = eval(record.final_cost_mathematic_formula)
                # if final cost is not integer or float, raise error
                if isinstance(final_cost, (int, float)):
                    record.expected_final_cost = final_cost
                else:
                    record.expected_final_cost = unit_price

    def _arise_or_approved_survey(self):
        self.ensure_one()
        survey = self.maintenance_scope_report_id.equipment_survey_data_id

        if survey._is_arise() or survey._is_approved():
            return True

        return False

    @api.onchange("job_predefined_factor_id")
    def _set_factor_by_predefined_factor(self):
        self.ensure_one()
        if self.job_predefined_factor_id:
            self.factor = self.job_predefined_factor_id.factor
            self.expected_factor = self.job_predefined_factor_id.factor

    def _get_job_quote_expected_parameter_set_id(self):
        self.ensure_one()
        if self.job_quote_expected_parameter_set_ids:
            return self.job_quote_expected_parameter_set_ids[0]
        else:
            return False

    def _get_job_quote_final_parameter_set_id(self):
        self.ensure_one()
        if self.job_quote_final_parameter_set_ids:
            return self.job_quote_final_parameter_set_ids[0]
        else:
            return False

    def _get_chatter_message_on_write(self, old_values, vals):
        """
        Get the chatter message on write.
        Args:
            old_values: a dict of old values of changed fields
            vals: the vals of the write method
        """
        # get job name
        job_name = ""
        if self.job_id:
            job_name = self.job_id.name
        message_text = f"Báo giá công việc {job_name} (mã: \
            <b>{self.ref}</b>) đã được cập nhật với các thông tin sau: <br/>"
        for field in old_values:
            if old_values[field] != vals[field]:
                if field == "job_supplier_quote_id":
                    # get supplier
                    model_name = "docking.job.supplier.quote"
                    job_supplier = self.env[model_name].browse(vals[field])
                    if job_supplier:
                        supplier = job_supplier.supplier_id
                        message_text += f"Nhà cung cấp: {old_values[field].supplier_id.name} -> {supplier.name} <br/>"
                else:
                    message_text += (
                        f"{field}: {old_values[field]} -> {vals[field]} <br/>"
                    )
        return message_text

    def send_email_to_selected_supplier_after_approved(self):
        self.ensure_one()
        if self._is_approved() and not self.is_for_crew and self.job_supplier_quote_id:
            template = "docking.selected_quote_email_in_docking_job_supplier_quote"
            self.job_supplier_quote_id.send_email_to_supplier_to_notify_successed_quote(
                template
            )

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

    def get_specifications(self):
        for record in self:
            if not record.length:
                record.length = record.expected_length

            if not record.width:
                record.width = record.expected_width

            if not record.height:
                record.height = record.expected_height

            if not record.quantity:
                record.quantity = record.expected_quantity

            if not record.weight:
                record.weight = record.expected_weight
