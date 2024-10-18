# -*- coding: utf-8 -*-
#############################################################################
#
from odoo import http, fields, _
from odoo.http import request, Controller, Request
from ..models import CONST
from odoo.exceptions import ValidationError

request: Request


class RFQSupplierPortal(Controller):
    @http.route(
        ["/vendor_rfq/<string:supplier_ref>"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def portal_get_vendor_rfq(self, supplier_ref, **kw):
        """displaying the RsFQ (Requests For Quote) details"""
        # get access_token via request.get_http_params()
        params = request.get_http_params()
        access_token = params.get("access_token")

        # get supplier data from supplier_ref. TODO: check if access_token is valid
        supplier = (
            request.env["ship.supplier"].sudo().search([("ref", "=", supplier_ref)])
        )
        # if no supplier, return 404
        if not supplier:
            return request.not_found(
                "Supplier not found. Please contact us for support."
            )

        values = dict(
            {
                "supplier": supplier,
            }
        )
        if access_token != supplier.access_token:
            return request.render(
                "ship_management.portal_request_access_my_vendor_rfq", values
            )

        # get material supplier quotes from supplier
        material_supplier_quote_list = (
            request.env["ship.material.supplier.quote"]
            .sudo()
            .search(
                [
                    ("supplier_id", "=", supplier.id),
                    ("material_quote_id.approval_status", "=", CONST.SUPPLIER),
                    "|",
                    ("material_quote_id.deadline", "=", False),
                    ("material_quote_id.deadline", ">=", fields.Date.today()),
                ],
                order="is_responded asc",
            )
        )
        # get pain supplier quotes from supplier
        paint_supplier_quote_list = (
            request.env["ship.paint.supplier.quote"]
            .sudo()
            .search(
                [
                    ("supplier_id", "=", supplier.id),
                    ("paint_quote_id.approval_status", "=", CONST.SUPPLIER),
                    "|",
                    ("paint_quote_id.deadline", "=", False),
                    ("paint_quote_id.deadline", ">=", fields.Date.today()),
                ],
                order="is_responded asc",
            )
        )
        # get job supplier quotes from supplier
        approval_model = request.env["utilities.approval.status"].sudo().search([])
        supplier_id = approval_model._get_supplier_group_id()
        job_supplier_quote_list = (
            request.env["ship.job.supplier.quote"]
            .sudo()
            .search(
                [
                    ("supplier_id", "=", supplier.id),
                    ("job_quote_id.secondary_approval_status", "=", supplier_id.id),
                    "|",
                    ("job_quote_id.deadline", "=", False),
                    ("job_quote_id.deadline", ">=", fields.Date.today()),
                ],
                order="is_responded asc",
            )
        )

        # get all unique mateial_paint_quotes_request_id.ref
        mateial_paint_quotes_request_ref_list = []
        for material_supplier_quote in material_supplier_quote_list:
            # check ref is not in mateial_paint_quotes_request_ref_list
            if (
                material_supplier_quote.material_quote_id.material_paint_quotes_request_id.ref
                not in mateial_paint_quotes_request_ref_list
            ):
                mateial_paint_quotes_request_ref_list.append(
                    material_supplier_quote.material_quote_id.material_paint_quotes_request_id.ref
                )
        for paint_supplier_quote in paint_supplier_quote_list:
            # check ref is not in mateial_paint_quotes_request_ref_list
            if (
                paint_supplier_quote.paint_quote_id.material_paint_quotes_request_id.ref
                not in mateial_paint_quotes_request_ref_list
            ):
                mateial_paint_quotes_request_ref_list.append(
                    paint_supplier_quote.paint_quote_id.material_paint_quotes_request_id.ref
                )

        values["material_supplier_quote_list"] = material_supplier_quote_list
        values["paint_supplier_quote_list"] = paint_supplier_quote_list
        values["job_supplier_quote_list"] = job_supplier_quote_list
        values["mateial_paint_quotes_request_ref_list"] = (
            mateial_paint_quotes_request_ref_list
        )

        return request.render("ship_management.portal_my_vendor_rfq", values)

    @http.route(
        ["/request_access_vendor_rfq/<string:supplier_ref>"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def portal_request_access_vendor_rfq(self, supplier_ref, **kw):
        """displaying the RsFQ (Requests For Quote) details"""
        # get supplier data from supplier_ref. TODO: check if access_token is valid
        supplier = (
            request.env["ship.supplier"].sudo().search([("ref", "=", supplier_ref)])
        )
        # if no supplier, return 404
        if not supplier:
            return request.not_found(
                "Supplier not found. Please contact us for support."
            )
        supplier.send_email_response_portal_request_access()
        return request.render(
            "ship_management.portal_request_access_my_vendor_rfq_sent",
            {"supplier": supplier},
        )
