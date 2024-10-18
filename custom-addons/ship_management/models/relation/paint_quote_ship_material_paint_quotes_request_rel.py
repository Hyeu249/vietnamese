from odoo import fields, models, _


class ShipPaintQuoteShipMaterialPaintQuotesRequestRel(models.Model):
    _name = "ship.paint.quote.ship.material.paint.quotes.request.rel"
    _description = "Ship paint quote ship material paint quotes request rel"

    paint_quote_id = fields.Many2one(
        "ship.paint.quote", string="Paint Quote", required=True
    )
    material_paint_quotes_request_id = fields.Many2one(
        "ship.material.paint.quotes.request",
        string="Material paint quotes request",
        required=True,
    )

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_paint_quote_id",
            "unique (paint_quote_id)",
            "paint_quote_id must be unique.",
        ),
    ]
