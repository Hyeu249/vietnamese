# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class JobQuoteExpectedParameterSet(models.Model):
    _name = "docking.job.quote.expected.parameter.set"
    _description = "Job Quote expected parameter set records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    quantity = fields.Float("Quantity", tracking=True)
    weight = fields.Float("Weight", tracking=True)
    length = fields.Float("Length", default=1, tracking=True)
    width = fields.Float("Width", default=1, tracking=True)
    height = fields.Float("Height", default=1, tracking=True)
    factor = fields.Float("Factor", default=1, tracking=True)
    unit_price = fields.Float(
        "Unit price",
        related="job_quote_id.job_supplier_quote_id.labor_cost",
        tracking=True,
    )
    unit = fields.Char("Unit", related="job_quote_id.unit", tracking=True)
    final_cost_mathematic_formula = fields.Text(
        "Final Cost Mathematic Formula",
        related="job_quote_id.job_id.job_final_cost_formula_id.formula",
        tracking=True,
    )
    final_cost = fields.Float(
        "Final Cost", compute="_calculate_final_cost", tracking=True
    )

    # related
    maintenance_scope_name = fields.Char(
        "Maintenance scope",
        related="job_quote_id.job_id.maintenance_scope_id.name",
        tracking=True,
    )

    # relations
    job_quote_id = fields.Many2one(
        "docking.job.quote",
        string="Job quote",
        tracking=True,
    )
    factor_note_option_id = fields.Many2one(
        "docking.factor.note.option",
        string="Factor note option",
        domain="[('maintenance_scope_string', 'ilike', maintenance_scope_name)]",
        tracking=True,
    )

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_job_quote_id",
            "unique (job_quote_id)",
            "job_quote_id must be unique.",
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
            model_name = "docking.job.quote.expected.parameter.set"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)

        result = super(JobQuoteExpectedParameterSet, self).create(vals_list)

        for record in result:
            record._set_factor_value()
            if not record.job_quote_id._get_job_quote_final_parameter_set_id():
                record.job_quote_id._set_parameter_for_job_quote(record)

        return result

    def write(self, vals):
        self.ensure_one()

        result = super(JobQuoteExpectedParameterSet, self).write(vals)

        if "factor_note_option_id" in vals:
            self._set_factor_value()

        if not self.job_quote_id._get_job_quote_final_parameter_set_id():
            self.job_quote_id._set_parameter_for_job_quote(self)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _set_factor_value(self):
        self.ensure_one()
        if self.factor_note_option_id:
            self.factor = self.factor_note_option_id.value

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

    @api.depends("quantity", "weight", "length", "width", "height", "factor", "unit_price")
    def _calculate_final_cost(self):
        for record in self:
            quantity = record.quantity or 0
            weight = record.weight or 0
            length = record.length or 0
            width = record.width or 0
            height = record.height or 0
            factor = record.factor or 0
            unit_price = record.unit_price or 0
            if record.final_cost_mathematic_formula:
                final_cost = eval(record.final_cost_mathematic_formula)
                # if final cost is not integer or float, raise error
                if isinstance(final_cost, (int, float)):
                    record.final_cost = final_cost

            else:
                record.final_cost = unit_price
