from odoo import fields, models, _
from .. import CONST


class ShipSparePartQuoteShipMaterialPaintQuotesRequestRel(models.Model):
    _name = "ship.spare.part.quote.ship.material.paint.quotes.request.rel"
    _description = "Ship spare part quote ship material paint quotes request rel"

    material_type = fields.Selection(
        related="spare_part_quote_id.material_type",
        string="Material Type",
        tracking=True,
    )

    spare_part_quote_id = fields.Many2one(
        "ship.material.quote",
        string="Material Quote(spare part)",
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
            "unique_spare_part_quote_id",
            "unique (spare_part_quote_id)",
            "spare_part_quote_id must be unique.",
        ),
    ]
