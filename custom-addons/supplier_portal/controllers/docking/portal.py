from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from odoo import http
from ...help_func import validate_access_token, generate_qr_code_base64, DOCKING
from ....docking.models import CONST
from odoo.exceptions import ValidationError


class Home(CustomerPortal):
    @http.route(["/docking/docking-plans"], type="http", auth="public", website=True)
    def docking_plan_list_view(self, **kw):
        is_validate, supplier = validate_access_token(DOCKING)

        if is_validate:
            docking_plan_list = (
                request.env["docking.docking.plan"]
                .sudo()
                .search([("supplier_emails", "ilike", supplier.email)])
            )
            vals = {
                "docking_plan_list": docking_plan_list,
                "page_name": "docking_docking_plan_list_view",
            }
            return request.render(
                "supplier_portal.docking_docking_plan_list_view_portal", vals
            )
        else:
            vals = {
                "supplier": supplier,
                "route_request": "/docking/docking-plans",
                "module": DOCKING,
            }
            return request.render("supplier_portal.portal_request_access", vals)

    @http.route(
        ["/docking/docking-plan/<string:list_ref>"],
        type="http",
        auth="public",
        website=True,
    )
    def docking_plan_detail_view(self, list_ref, **kw):
        is_validate, supplier = validate_access_token(DOCKING)

        if is_validate:
            docking_plan = (
                request.env["docking.docking.plan"]
                .sudo()
                .search(
                    [
                        ("ref", "=", list_ref),
                        ("supplier_emails", "ilike", supplier.email),
                    ],
                    limit=1,
                )
            )

            if docking_plan:
                material_supplier_quote_ids = (
                    docking_plan.material_survey_data_ids.material_quote_ids.material_supplier_quote_ids
                )

                material_supplier_quotes = material_supplier_quote_ids.filtered(
                    lambda quote: quote.supplier_id == supplier
                    and quote.material_type == CONST.MATERIAL
                )
                spare_part_supplier_quotes = material_supplier_quote_ids.filtered(
                    lambda quote: quote.supplier_id == supplier
                    and quote.material_type == CONST.SPARE_PART
                )
                paint_supplier_quotes = material_supplier_quote_ids.filtered(
                    lambda quote: quote.supplier_id == supplier
                    and quote.material_type == CONST.PAINT
                )

                vals = {
                    "docking_plan_ref": docking_plan.ref,
                    "material_supplier_quotes": material_supplier_quotes,
                    "spare_part_supplier_quotes": spare_part_supplier_quotes,
                    "paint_supplier_quotes": paint_supplier_quotes,
                    "supplier": supplier,
                    "page_name": "docking_docking_plan_detail_view",
                }
                return request.render(
                    "supplier_portal.docking_docking_plan_detail_view_portal", vals
                )
            else:
                return request.not_found("Không tìm thấy!!")
        else:
            vals = {
                "supplier": supplier,
                "route_request": f"/docking/docking-plan/{list_ref}",
                "module": DOCKING,
            }
            return request.render("supplier_portal.portal_request_access", vals)

    @http.route(
        ["/docking/material-supplier-quote/<string:quote_ref>"],
        type="http",
        auth="public",
        methods=["POST", "GET"],
        website=True,
    )
    def docking_material_supplier_quote_detail_view(self, quote_ref, **kw):
        is_validate, supplier, access_token, supplier_ref = validate_access_token(
            DOCKING, get_params=True
        )

        if is_validate:
            material_supplier_quote = (
                request.env["docking.material.supplier.quote"]
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
                material_supplier_quote.material_quote_id.material_survey_data_id.docking_plan_id.ref
            )

            if material_supplier_quote:
                if request.httprequest.method == "POST":
                    material_supplier_quote.write(
                        {
                            "unit_price": kw.get("unit_price"),
                            "estimated_delivery_date": kw.get(
                                "estimated_delivery_date"
                            ),
                            "note": kw.get("note"),
                            "is_responded": True,
                        }
                    )

                    return request.redirect(
                        f"/docking/docking-plan/{list_ref}?supplier_ref={supplier_ref}&access_token={access_token}"
                    )

                vals = {
                    "list_ref": list_ref,
                    "supplier_id": supplier.id,
                    "material_supplier_quote": material_supplier_quote,
                    "page_name": "docking_material_supplier_quote_form_view",
                    "qrCode_base64": generate_qr_code_base64(
                        material_supplier_quote.material_quote_id.ref
                    ),
                }
                return request.render(
                    "supplier_portal.docking_material_supplier_form_view_portal", vals
                )
            else:
                return request.not_found("Không tìm thấy!!")
        else:
            vals = {
                "supplier": supplier,
                "route_request": f"/docking/material-supplier-quote/{quote_ref}",
                "module": DOCKING,
            }
            return request.render("supplier_portal.portal_request_access", vals)

    @http.route(
        ["/docking/job-supplier-quotes"], type="http", auth="public", website=True
    )
    def docking_job_supplier_quote_list_view(self, **kw):
        is_validate, supplier = validate_access_token(DOCKING)

        if is_validate:
            job_supplier_quotes = (
                request.env["docking.job.supplier.quote"]
                .sudo()
                .search([("supplier_id", "=", supplier.id)])
            )
            vals = {
                "job_supplier_quotes": job_supplier_quotes,
                "supplier": supplier,
                "page_name": "docking_job_supplier_quote_list_view",
            }
            return request.render(
                "supplier_portal.docking_job_supplier_quote_list_view_portal", vals
            )
        else:
            vals = {
                "supplier": supplier,
                "route_request": "/docking/job-supplier-quotes",
                "module": DOCKING,
            }
            return request.render("supplier_portal.portal_request_access", vals)

    @http.route(
        ["/docking/job-supplier-quote/<string:quote_ref>"],
        type="http",
        auth="public",
        methods=["POST", "GET"],
        website=True,
    )
    def docking_job_supplier_quote_detail_view(self, quote_ref, **kw):
        is_validate, supplier, access_token, supplier_ref = validate_access_token(
            DOCKING, get_params=True
        )

        if is_validate:
            job_supplier_quote = (
                request.env["docking.job.supplier.quote"]
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
                        f"/docking/job-supplier-quotes?supplier_ref={supplier_ref}&access_token={access_token}"
                    )

                vals = {
                    "job_supplier_quote": job_supplier_quote,
                    "page_name": "docking_job_supplier_quote_form_view",
                }
                return request.render(
                    "supplier_portal.docking_job_supplier_quote_form_view_portal", vals
                )
            else:
                return request.not_found("Không tìm thấy!!")
        else:
            vals = {
                "supplier": supplier,
                "route_request": f"/docking/job-supplier-quote/{quote_ref}",
                "module": DOCKING,
            }
            return request.render("supplier_portal.portal_request_access", vals)
