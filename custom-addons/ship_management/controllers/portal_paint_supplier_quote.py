# -*- coding: utf-8 -*-
#############################################################################
#
from odoo import http, fields, _
from odoo.http import request, Controller, Request
from ..models import CONST

request: Request


class RFQPaintSupplierPortal(Controller):
    @http.route(
        ["/vendor_rfpq/<string:rfpq_ref>"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def portal_get_vendor_rfq(self, rfpq_ref, **kw):
        """displaying the RFQ (Request For Quote) details"""
        # get access_token via request.get_http_params()
        params = request.get_http_params()
        access_token = params.get("access_token")

        # query a already-created quote from the db with rfpq_id and access_token
        quote = (
            request.env["ship.paint.supplier.quote"]
            .sudo()
            .search([("ref", "=", rfpq_ref), ("access_token", "=", access_token)])
        )
        # if no quote, return 404
        if not quote:
            return request.not_found("Quote not found. Please contact us for support.")
        # get paint quote data from quote
        paint_quote = (
            request.env["ship.paint.quote"]
            .sudo()
            .search([("id", "=", quote.paint_quote_id.id)])
        )
        # check if paint quote is valid
        if not self._is_paint_quote_valid(paint_quote=paint_quote):
            return request.not_found(
                "Quote deadline has passed. Please contact us for support."
            )
        # get paint data from paint quote
        paint = (
            request.env["ship.paint"]
            .sudo()
            .search([("id", "=", paint_quote.paint_id.id)])
        )

        supplier = (
            request.env["ship.supplier"]
            .sudo()
            .search([("id", "=", quote.supplier_id.id)])
        )

        # map values
        values = dict(
            {
                "paint": paint,
                "paint_quote": paint_quote,
                "quote": quote,
                "supplier": supplier,
                "vendor_rfq": {
                    "rfq_ref": rfpq_ref,
                    "access_token": access_token,
                },
            }
        )

        # render data to template
        return request.render("ship_management.portal_my_vendor_paint_rfq", values)

    @http.route(
        ["/vendor_rfpq/submit"],
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
    )
    def portal_post_quote_details(self, **post):
        # get access_token via request.get_http_params()
        rfpq_ref = post.get("rfq_ref")
        access_token = post.get("access_token")

        # query a already-created quote from the db with rfpq_id and access_token
        quote = (
            request.env["ship.paint.supplier.quote"]
            .sudo()
            .search([("ref", "=", rfpq_ref), ("access_token", "=", access_token)])
        )
        # if no quote, return 404
        if not quote:
            return request.not_found("Quote not found. Please contact us for support.")
        # check if paint quote is valid
        if not self._is_paint_quote_valid(paint_quote=quote.paint_quote_id):
            return request.not_found(
                "Quote deadline has passed. Please contact us for support."
            )
        # update quote
        quote.write(
            {
                "unit_price": post.get("quoted_unit_price"),
                "estimated_delivery_date": post.get("estimated_delivery_date"),
                "note": post.get("note"),
                "is_responded": True,
            }
        )

        return request.redirect(
            "/vendor_rfpq/%s?access_token=%s" % (rfpq_ref, access_token)
        )

    @staticmethod
    def _is_paint_quote_valid(paint_quote_id="", paint_quote=None):
        if not paint_quote:
            paint_quote = (
                request.env["ship.paint.quote"]
                .sudo()
                .search([("id", "=", paint_quote_id)])
            )
        if paint_quote.approval_status != CONST.SUPPLIER:
            return False
        if paint_quote.deadline:
            if paint_quote.deadline < fields.Date.today():
                return False
        return True
