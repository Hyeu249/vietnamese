# -*- coding: utf-8 -*-
#############################################################################
#
from odoo import http, fields, _
from odoo.http import request, Controller, Request
from ..models import CONST

request: Request


class RFQMaterialSupplierPortal(Controller):
    @http.route(
        ["/vendor_rfmq/<string:rfmq_ref>"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def portal_get_vendor_rfq(self, rfmq_ref, **kw):
        """displaying the RFQ (Request For Quote) details"""
        # get access_token via request.get_http_params()
        params = request.get_http_params()
        access_token = params.get("access_token")

        # query a already-created quote from the db with rfmq_id and access_token
        quote = (
            request.env["ship.material.supplier.quote"]
            .sudo()
            .search([("ref", "=", rfmq_ref), ("access_token", "=", access_token)])
        )
        # if no quote, return 404
        if not quote:
            return request.not_found("Quote not found. Please contact us for support.")
        # get material quote data from quote
        material_quote = (
            request.env["ship.material.quote"]
            .sudo()
            .search([("id", "=", quote.material_quote_id.id)])
        )
        # check if material quote is valid
        if not self._is_material_quote_valid(material_quote=material_quote):
            return request.not_found(
                "Quote deadline has passed. Please contact us for support."
            )
        # get material data from material quote
        material = (
            request.env["ship.material"]
            .sudo()
            .search([("id", "=", material_quote.material_id.id)])
        )

        supplier = (
            request.env["ship.supplier"]
            .sudo()
            .search([("id", "=", quote.supplier_id.id)])
        )

        # map values
        values = dict(
            {
                "material": material,
                "material_quote": material_quote,
                "quote": quote,
                "supplier": supplier,
                "vendor_rfq": {
                    "rfq_ref": rfmq_ref,
                    "access_token": access_token,
                },
            }
        )

        # render data to template
        return request.render("ship_management.portal_my_vendor_material_rfq", values)

    @http.route(
        ["/vendor_rfmq/submit"],
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
    )
    def portal_post_quote_details(self, **post):
        # get access_token via request.get_http_params()
        rfmq_ref = post.get("rfq_ref")
        access_token = post.get("access_token")

        # query a already-created quote from the db with rfmq_id and access_token
        quote = (
            request.env["ship.material.supplier.quote"]
            .sudo()
            .search([("ref", "=", rfmq_ref), ("access_token", "=", access_token)])
        )
        # if no quote, return 404
        if not quote:
            return request.not_found("Quote not found. Please contact us for support.")
        # check if material quote is valid
        if not self._is_material_quote_valid(quote.material_quote_id.id):
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
            "/vendor_rfmq/%s?access_token=%s" % (rfmq_ref, access_token)
        )

    @staticmethod
    def _is_material_quote_valid(material_quote_id="", material_quote=None):
        if not material_quote:
            material_quote = (
                request.env["ship.material.quote"]
                .sudo()
                .search([("id", "=", material_quote_id)])
            )
        if material_quote.approval_status != CONST.SUPPLIER:
            return False
        # check if material quote has a deadline, validate material quote's deadline.
        if material_quote.deadline:
            if material_quote.deadline < fields.Date.today():
                return False
        return True
