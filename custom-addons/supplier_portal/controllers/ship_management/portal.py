from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from odoo import http
from ...help_func import validate_access_token, generate_qr_code_base64, SHIP_MANAGEMENT
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Home(CustomerPortal):
    @http.route(["/material-paint-quotes"], type="http", auth="public", website=True)
    def material_paint_quotes_list_view(self, **kw):
        is_validate, supplier = validate_access_token(SHIP_MANAGEMENT)

        if is_validate:
            material_paint_quotes_list = (
                request.env["ship.material.paint.quotes.request"]
                .sudo()
                .search([("supplier_emails", "ilike", supplier.email)])
            )
            vals = {
                "material_paint_quotes_list": material_paint_quotes_list,
                "page_name": "material_paint_quotes_list_view",
            }
            return request.render(
                "supplier_portal.material_paint_quotes_list_view_portal", vals
            )
        else:
            vals = {
                "supplier": supplier,
                "route_request": "/material-paint-quotes",
                "module": SHIP_MANAGEMENT,
            }
            return request.render("supplier_portal.portal_request_access", vals)

    @http.route(
        ["/material-paint-quotes/<string:list_ref>"],
        type="http",
        auth="public",
        website=True,
    )
    def material_paint_quotes_detail_view(self, list_ref, **kw):
        is_validate, supplier = validate_access_token(SHIP_MANAGEMENT)

        if is_validate:
            material_paint_quotes = (
                request.env["ship.material.paint.quotes.request"]
                .sudo()
                .search(
                    [
                        ("ref", "=", list_ref),
                        ("supplier_emails", "ilike", supplier.email),
                    ],
                    limit=1,
                )
            )

            if material_paint_quotes:
                material_supplier_quotes = material_paint_quotes.material_quote_ids.material_supplier_quote_ids.filtered(
                    lambda quote: quote.supplier_id == supplier
                )
                spare_part_supplier_quotes = material_paint_quotes.spare_part_quote_ids.material_supplier_quote_ids.filtered(
                    lambda quote: quote.supplier_id == supplier
                )
                paint_supplier_quotes = material_paint_quotes.paint_quote_ids.paint_supplier_quote_ids.filtered(
                    lambda quote: quote.supplier_id == supplier
                )

                vals = {
                    "material_paint_quotes_ref": material_paint_quotes.ref,
                    "material_supplier_quotes": material_supplier_quotes,
                    "spare_part_supplier_quotes": spare_part_supplier_quotes,
                    "paint_supplier_quotes": paint_supplier_quotes,
                    "supplier": supplier,
                    "page_name": "material_paint_quotes_detail_view",
                }
                return request.render(
                    "supplier_portal.material_paint_quotes_detail_view_portal", vals
                )
            else:
                return request.not_found("Không tìm thấy!!")
        else:
            vals = {
                "supplier": supplier,
                "route_request": f"/material-paint-quotes/{list_ref}",
                "module": SHIP_MANAGEMENT,
            }
            return request.render("supplier_portal.portal_request_access", vals)

    @http.route(
        ["/material-supplier-quote/<string:quote_ref>"],
        type="http",
        auth="public",
        methods=["POST", "GET"],
        website=True,
    )
    def material_supplier_quote_detail_view(self, quote_ref, **kw):
        is_validate, supplier, access_token, supplier_ref = validate_access_token(
            SHIP_MANAGEMENT, get_params=True
        )

        if is_validate:
            material_supplier_quote = (
                request.env["ship.material.supplier.quote"]
                .sudo()
                .search(
                    [
                        ("ref", "=", quote_ref),
                        ("supplier_id", "=", supplier.id),
                    ],
                    limit=1,
                )
            )
            list_ref = (
                material_supplier_quote.material_quote_id.material_paint_quotes_request_id.ref
            )

            if material_supplier_quote:
                if request.httprequest.method == "POST":
                    selected_currency_id = request.env["res.currency"].search(
                        [("name", "=", kw.get("currency_id"))], limit=1
                    )
                    material_supplier_quote.write(
                        {
                            "unit_price": kw.get("unit_price"),
                            "estimated_delivery_date": kw.get(
                                "estimated_delivery_date"
                            ),
                            "note": kw.get("note"),
                            "currency_id": selected_currency_id.id,
                            "is_responded": True,
                        }
                    )

                    return request.redirect(
                        f"/material-paint-quotes/{list_ref}?supplier_ref={supplier_ref}&access_token={access_token}"
                    )

                vals = {
                    "list_ref": list_ref,
                    "supplier_id": supplier.id,
                    "material_supplier_quote": material_supplier_quote,
                    "page_name": "material_supplier_quote_form_view",
                    "qrCode_base64": generate_qr_code_base64(
                        material_supplier_quote.material_quote_id.ref
                    ),
                }
                return request.render(
                    "supplier_portal.material_supplier_form_view_portal", vals
                )
            else:
                return request.not_found("Không tìm thấy!!")
        else:
            vals = {
                "supplier": supplier,
                "route_request": f"/material-supplier-quote/{quote_ref}",
                "module": SHIP_MANAGEMENT,
            }
            return request.render("supplier_portal.portal_request_access", vals)

    @http.route(
        ["/paint-supplier-quote/<string:quote_ref>"],
        type="http",
        auth="public",
        methods=["POST", "GET"],
        website=True,
    )
    def paint_supplier_quote_detail_view(self, quote_ref, **kw):
        is_validate, supplier, access_token, supplier_ref = validate_access_token(
            SHIP_MANAGEMENT, get_params=True
        )

        if is_validate:
            paint_supplier_quote = (
                request.env["ship.paint.supplier.quote"]
                .sudo()
                .search(
                    [
                        ("ref", "=", quote_ref),
                        ("supplier_id", "=", supplier.id),
                    ],
                    limit=1,
                )
            )
            list_ref = (
                paint_supplier_quote.paint_quote_id.material_paint_quotes_request_id.ref
            )

            if paint_supplier_quote:
                if request.httprequest.method == "POST":
                    selected_currency_id = request.env["res.currency"].search(
                        [("name", "=", kw.get("currency_id"))], limit=1
                    )
                    paint_supplier_quote.write(
                        {
                            "unit_price": kw.get("unit_price"),
                            "estimated_delivery_date": kw.get(
                                "estimated_delivery_date"
                            ),
                            "note": kw.get("note"),
                            "currency_id": selected_currency_id.id,
                            "is_responded": True,
                        }
                    )

                    return request.redirect(
                        f"/material-paint-quotes/{list_ref}?supplier_ref={supplier_ref}&access_token={access_token}"
                    )

                vals = {
                    "list_ref": list_ref,
                    "supplier_id": supplier.id,
                    "paint_supplier_quote": paint_supplier_quote,
                    "page_name": "paint_supplier_quote_form_view",
                    "qrCode_base64": generate_qr_code_base64(
                        paint_supplier_quote.paint_quote_id.ref
                    ),
                }
                return request.render(
                    "supplier_portal.paint_supplier_form_view_portal", vals
                )
            else:
                return request.not_found("Không tìm thấy!!")
        else:
            vals = {
                "supplier": supplier,
                "route_request": f"/paint-supplier-quote/{quote_ref}",
                "module": SHIP_MANAGEMENT,
            }
            return request.render("supplier_portal.portal_request_access", vals)

    @http.route(["/job-supplier-quotes"], type="http", auth="public", website=True)
    def job_supplier_quote_list_view(self, **kw):
        is_validate, supplier = validate_access_token(SHIP_MANAGEMENT)

        if is_validate:
            job_supplier_quotes = (
                request.env["ship.job.supplier.quote"]
                .sudo()
                .search([("supplier_id", "=", supplier.id)])
            )
            vals = {
                "job_supplier_quotes": job_supplier_quotes,
                "supplier": supplier,
                "page_name": "job_supplier_quote_list_view",
            }
            return request.render(
                "supplier_portal.job_supplier_quote_list_view_portal", vals
            )
        else:
            vals = {
                "supplier": supplier,
                "route_request": "/job-supplier-quotes",
                "module": SHIP_MANAGEMENT,
            }
            return request.render("supplier_portal.portal_request_access", vals)

    @http.route(
        ["/job-supplier-quote/<string:quote_ref>"],
        type="http",
        auth="public",
        methods=["POST", "GET"],
        website=True,
    )
    def job_supplier_quote_detail_view(self, quote_ref, **kw):
        is_validate, supplier, access_token, supplier_ref = validate_access_token(
            SHIP_MANAGEMENT, get_params=True
        )

        if is_validate:
            job_supplier_quote = (
                request.env["ship.job.supplier.quote"]
                .sudo()
                .search(
                    [
                        ("ref", "=", quote_ref),
                        ("supplier_id", "=", supplier.id),
                    ],
                    limit=1,
                )
            )

            if job_supplier_quote:
                supplier_id = job_supplier_quote.job_quote_id._get_supplier_group_id()
                if request.httprequest.method == "POST":
                    job_supplier_quote.write(
                        {
                            "labor_cost": kw.get("labor_cost"),
                            "estimated_delivery_date": kw.get(
                                "estimated_delivery_date"
                            ),
                            "note": kw.get("note"),
                            "is_responded": True,
                        }
                    )

                    return request.redirect(
                        f"/job-supplier-quotes?supplier_ref={supplier_ref}&access_token={access_token}"
                    )

                vals = {
                    "job_supplier_quote": job_supplier_quote,
                    "supplier_id": supplier_id,
                    "page_name": "job_supplier_quote_form_view",
                }
                return request.render(
                    "supplier_portal.job_supplier_quote_form_view_portal", vals
                )
            else:
                return request.not_found("Không tìm thấy!!")
        else:
            vals = {
                "supplier": supplier,
                "route_request": f"/job-supplier-quote/{quote_ref}",
                "module": SHIP_MANAGEMENT,
            }
            return request.render("supplier_portal.portal_request_access", vals)

    @http.route(
        ["/vendor_rfuq/<string:rfuq_ref>"],
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
    )
    def portal_get_vendor_rfq(self, rfuq_ref, **kw):
        """Displaying the RFQ (Request For Quote) details for suppliers"""
        # get access_token via request.get_http_params()
        params = request.get_http_params()
        access_token = params.get("access_token")
        message = kw.get("message")

        # Search for the fuel request using the provided reference
        fuel_request = (
            request.env["ship.fuel.quotes.request"]
            .sudo()
            .search([("ref", "=", rfuq_ref), ("access_token", "=", access_token)])
        )

        if not fuel_request:
            _logger.error(f"No fuel request found for ref: {rfuq_ref}")
            return request.not_found(
                "Fuel Request not found. Please contact us for support."
            )

        # Search for all fuel supplier quotes linked to the fuel request
        fuel_quotes = (
            request.env["ship.fuel.quote"]
            .sudo()
            .search([("fuel_quote_request_id", "=", fuel_request.id)])
            )
        fuel_quotes_grease = (
                request.env["ship.fuel.quote.grease"]
                .sudo()
                .search([("fuel_quote_request_id", "=", fuel_request.id)])
            )

        # Combine both lists
        all_fuel_quotes_data = []
        for quote in fuel_quotes:
            all_fuel_quotes_data.append(quote)
        for grease_quote in fuel_quotes_grease:
            all_fuel_quotes_data.append(grease_quote)

        if not all_fuel_quotes_data:
            _logger.error(f"No fuel  quotes found for fuel request: {fuel_request}")
            return request.not_found(
                "Fuel  Quotes not found. Please contact us for support."
            )
        # Prepare data for template rendering
        values = {
            "fuel_request": fuel_request,
            "fuel_quotes": all_fuel_quotes_data,
            "rfuq_ref": rfuq_ref,
            "access_token": access_token,
            "message": message,
        }

        # render data to template
        return request.render("supplier_portal.portal_my_vendor_fuel_rfq", values)

    @http.route(
        ["/vendor_rfuq/confirm"],
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def confirm_vendor_rfuq(self, **post):
        """Handle RFQ confirmation"""
        rfuq_ref = post.get("rfuq_ref")
        access_token = post.get("access_token")
        fuel_request = (
            request.env["ship.fuel.quotes.request"]
            .sudo()
            .search([("ref", "=", rfuq_ref), ("access_token", "=", access_token)])
        )

        if not fuel_request:
            return request.redirect(
                "/vendor_rfuq/%s?access_token=%s&message=%s"
                % (rfuq_ref, access_token, "Fuel Request not found")
            )
        try:
            fuel_request.write({"is_responded": True})
            return request.redirect(
                "/vendor_rfuq/%s?access_token=%s&message=%s"
                % (rfuq_ref, access_token, "RFQ confirmed successfully")
            )
        except Exception as e:
            return request.redirect(
                "/vendor_rfuq/%s?access_token=%s&message=%s"
                % (rfuq_ref, access_token, str(e))
            )
