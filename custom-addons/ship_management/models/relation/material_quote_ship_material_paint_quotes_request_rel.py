from odoo import fields, models, api, _
from .. import CONST


class ShipMaterialQuoteShipMaterialPaintQuotesRequestRel(models.Model):
    _name = "ship.material.quote.ship.material.paint.quotes.request.rel"
    _description = "Ship material quote ship material paint quotes request rel"
    _inherit = ["utilities.notification"]

    material_type = fields.Selection(
        related="material_quote_id.material_type",
        string="Material Type",
        tracking=True,
    )

    material_quote_id = fields.Many2one(
        "ship.material.quote",
        string="Material Quote",
        required=True,
    )
    material_paint_quotes_request_id = fields.Many2one(
        "ship.material.paint.quotes.request",
        string="Material paint quotes request",
        required=True,
    )

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_material_quote_id",
            "unique (material_quote_id)",
            "material_quote_id must be unique.",
        ),
    ]
