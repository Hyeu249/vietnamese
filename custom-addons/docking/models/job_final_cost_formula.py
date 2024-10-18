from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class JobFinalCostFormula(models.Model):
    _name = "docking.job.final.cost.formula"
    _description = "Job quote cost formula records"
    _inherit = ["mail.thread"]

    name = fields.Char("Name", tracking=True)
    description = fields.Text("Description", tracking=True)
    formula = fields.Text("Formula", tracking=True, required=True)

    # relations
    job_ids = fields.One2many(
        "docking.job",
        "job_final_cost_formula_id",
        string="Jobs",
        tracking=True,
        domain="[('job_final_cost_formula_id', '=', False)]",
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            formula = vals.get("formula")
            # check if formula is valid by using dummy data
            quantity = 1
            weight = 1
            length = 1
            width = 1
            height = 1
            factor = 1
            unit_price = 1
            try:
                eval(formula)
            except ZeroDivisionError:
                raise ValidationError(_("Cannot divide by zero"))
            except NameError:
                raise ValidationError(_("Final cost mathematic formula is not valid."))
        return super(JobFinalCostFormula, self).create(vals_list)

    def write(self, vals):
        if "formula" in vals:
            formula = vals.get("formula")
            # check if formula is valid by using dummy data
            quantity = 1
            weight = 1
            length = 1
            width = 1
            height = 1
            factor = 1
            unit_price = 1
            try:
                eval(formula)
            except ZeroDivisionError:
                raise ValidationError(_("Cannot divide by zero"))
            except NameError:
                raise ValidationError(_("Final cost mathematic formula is not valid."))
        return super(JobFinalCostFormula, self).write(vals)
