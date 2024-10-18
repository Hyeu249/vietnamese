# -*- coding: utf-8 -*-
#############################################################################
#
import logging
from collections import OrderedDict
from odoo import http, fields, _
from odoo.http import request, Controller, Request
from ..models import CONST

request: Request


class RFQJobSupplierPortal(Controller):
    @http.route(
        ["/vendor_rfjq/<string:rfjq_ref>"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def portal_get_vendor_rfq(self, rfjq_ref, **kw):
        """displaying the RFQ (Request For Quote) details"""
        # get access_token via request.get_http_params()
        params = request.get_http_params()
        access_token = params.get("access_token")

        # query a already-created quote from the db with rfjq_id and access_token
        quote = (
            request.env["ship.job.supplier.quote"]
            .sudo()
            .search([("ref", "=", rfjq_ref), ("access_token", "=", access_token)])
        )
        # if no quote, return 404
        if not quote:
            return request.not_found("Quote not found. Please contact us for support.")
        # get job quote data from quote
        job_quote = (
            request.env["ship.job.quote"]
            .sudo()
            .search([("id", "=", quote.job_quote_id.id)])
        )
        # check if job quote is valid
        if not self._is_job_quote_valid(job_quote=job_quote):
            return request.not_found(
                "Quote deadline has passed. Please contact us for support."
            )
        # get job data from job quote
        job = request.env["ship.job"].sudo().search([("id", "=", job_quote.job_id.id)])

        supplier = (
            request.env["ship.supplier"]
            .sudo()
            .search([("id", "=", quote.supplier_id.id)])
        )

        # map values
        values = dict(
            {
                "job": job,
                "job_quote": job_quote,
                "quote": quote,
                "supplier": supplier,
                "vendor_rfq": {
                    "rfq_ref": rfjq_ref,
                    "access_token": access_token,
                },
            }
        )

        # render data to template
        return request.render("ship_management.portal_my_vendor_job_rfq", values)

    @http.route(
        ["/vendor_rfjq/submit"],
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
    )
    def portal_post_quote_details(self, **post):
        # get access_token via request.get_http_params()
        rfjq_ref = post.get("rfq_ref")
        access_token = post.get("access_token")

        # query a already-created quote from the db with rfjq_id and access_token
        quote = (
            request.env["ship.job.supplier.quote"]
            .sudo()
            .search([("ref", "=", rfjq_ref), ("access_token", "=", access_token)])
        )
        # if no quote, return 404
        if not quote:
            return request.not_found("Quote not found. Please contact us for support.")
        # check if job quote is valid
        if not self._is_job_quote_valid(job_quote=quote.job_quote_id):
            return request.not_found(
                "Quote deadline has passed. Please contact us for support."
            )
        # update quote
        quote.write(
            {
                "labor_cost": post.get("labor_cost"),
                "estimated_delivery_date": post.get("estimated_delivery_date"),
                "note": post.get("note"),
                "is_responded": True,
            }
        )

        return request.redirect(
            "/vendor_rfjq/%s?access_token=%s" % (rfjq_ref, access_token)
        )

    @staticmethod
    def _is_job_quote_valid(job_quote_id="", job_quote=None):
        if not job_quote:
            job_quote = (
                request.env["ship.job.quote"].sudo().search([("id", "=", job_quote_id)])
            )
        if not job_quote.is_at_this_approval_level(CONST.SUPPLIER):
            return False
        # check if job quote has a deadline, validate job quote's deadline.
        if job_quote.deadline:
            if job_quote.deadline < fields.Date.today():
                return False
        return True
