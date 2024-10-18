from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class JobFinalCostPredefinedFactor(models.Model):
    _name = "docking.job.final.cost.predefined.factor"
    _description = "Predefined factors for job final cost calculation"
    _inherit = ["mail.thread"]

    name = fields.Char("Name", tracking=True)
    factor = fields.Float("Factor", store=True, tracking=True)
