# -*- coding: utf-8 -*-
#############################################################################
#
from odoo import http, fields, _
from odoo.http import request, Controller, Request
from odoo.exceptions import ValidationError
from ..models import CONST

request: Request


class ExpressConfirmMaterialPaintDelivery(Controller):
    @http.route(
        ["/material_paint_quote/confirm_delivery/<string:quote_ref>"],
        type="http",
        auth="user",
        website=True,
        methods=["GET"],
    )
    def get_express_material_paint_delivery(self, quote_ref, **kw):
        try:
            quote = self._get_quote(quote_ref)
            if not quote:
                message = "Báo giá không tồn tại!!!"
                self._send_failure_notification(quote_ref, message)
                return self._not_found_response()
            if not self._is_quote_valid(quote_ref, quote):
                return self._bad_request_response()
            material_paint_name = self._get_material_paint_name(quote)
            to_be_delivered_quantity = self._get_to_be_delivered_quantity(quote)
            selected_supplier_name = self._get_selected_supplier_name(quote)
            data = {
                "quote_ref": quote_ref,
                "material_paint_name": material_paint_name,
                "delivered_quantity": to_be_delivered_quantity,
                "unit": quote.unit if hasattr(quote, 'unit') else "Lít/Chiếc",
                "selected_supplier_name": selected_supplier_name,
            }
            return request.make_json_response(data)
            
        except ValidationError as e:
            self._send_failure_notification(quote_ref, e.name)
            return self._error_response(e.name)
        
    
    @http.route(
        ["/material_paint_quote/confirm_delivery"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def post_express_material_paint_delivery(self, **post):
        quote_ref = post.get("quote_ref")
        delivered_quantity = post.get("delivered_quantity")
        try:
            quote = self._get_quote(quote_ref)
            if not quote:
                message = "Báo giá không tồn tại!!!"
                self._send_failure_notification(quote_ref, message)
                return self._not_found_response()
            if not self._is_quote_valid(quote_ref, quote):
                return self._bad_request_response()
            quote.action_confirm_delivered(delivered_quantity)
            self._send_successfully_notification(quote_ref)
            return request.make_json_response(data={"status": "success"})
        except ValidationError as e:
            self._send_failure_notification(quote_ref, e.name)
            return self._error_response(e.name)
        
    def _get_quote(self, quote_ref):
        material_quote = self._get_material_by_ref_code(quote_ref)
        docking_material_quote = self._get_docking_material_by_ref_code(quote_ref)
        paint_quote = self._get_paint_by_ref_code(quote_ref)
        quote = material_quote or paint_quote or docking_material_quote or None
        return quote
    
    def _is_quote_valid(self, quote_ref, quote):
        is_approved = self._is_approved(quote)
        is_added_to_warehouse = self._is_added_to_warehouse(quote)

        if not is_approved:
            message = "Báo giá chưa duyệt, vui lòng thử mã khác!"
            self._send_failure_notification(quote_ref, message)
            return False

        if is_added_to_warehouse:
            message = "Báo giá đã nhận, vui lòng thử mã khác!"
            self._send_failure_notification(quote_ref, message)
            return False
        
        return True
    
    def _get_material_paint_name(self, quote):
        if hasattr(quote, 'material_id') and quote.material_id.name:
            return quote.material_id.name
        if hasattr(quote, 'paint_id') and quote.paint_id.name:
            return quote.paint_id.name
        if hasattr(quote, 'material_name'):
            return quote.material_name
        return None
    
    def _get_to_be_delivered_quantity(self, quote):
        if hasattr(quote, 'quantity'):
            return quote.quantity
        if hasattr(quote, 'quantity_liter'):
            return quote.quantity_liter
        return None
    
    def _get_selected_supplier_name(self, quote):
        if hasattr(quote, 'selected_supplier_name'):
            return quote.selected_supplier_name
        if hasattr(quote, 'material_supplier_quote_id') and quote.material_supplier_quote_id.supplier_id.name:
            return quote.material_supplier_quote_id.supplier_id.name
        if hasattr(quote, 'paint_supplier_quote_id') and quote.paint_supplier_quote_id.supplier_id.name:
            return quote.paint_supplier_quote_id.supplier_id.name
        return None


    def _send_successfully_notification(self, quote_ref):
        subject = f"Báo giá của {quote_ref}!"
        body = "Nhận đơn hàng thành công!"
        request.env["bus.bus"]._sendone(
            request.env.user.partner_id,
            "simple_notification",
            {"title": subject, "message": body, "sticky": False, "warning": False},
        )

    def _send_failure_notification(self, quote_ref, body):
        subject = f"Báo giá của {quote_ref}!"
        request.env["bus.bus"]._sendone(
            request.env.user.partner_id,
            "simple_notification",
            {"title": subject, "message": body, "sticky": False, "warning": True},
        )

    def _get_material_by_ref_code(self, quote_ref):
        return request.env["ship.material.quote"].search([("ref", "=", quote_ref)])

    def _get_docking_material_by_ref_code(self, quote_ref):
        return request.env["docking.material.quote"].search([("ref", "=", quote_ref)])

    def _get_paint_by_ref_code(self, quote_ref):
        return request.env["ship.paint.quote"].search([("ref", "=", quote_ref)])

    def _is_added_to_warehouse(self, quote):
        if not quote:
            return False

        if quote.added_to_warehouse:
            return True
        else:
            return False

    def _is_approved(self, quote):
        if not quote:
            return False

        if quote.approval_status == CONST.APPROVED:
            return True
        else:
            return False

    def _error_response(self, e):
        return request.make_json_response(
            data={"status": "error", "message": e},
            status=400,
        )

    def _bad_request_response(self):
        return request.make_json_response(
            data={"status": "error", "message": ("Ref code is not valid.")},
            status=400,
        )

    def _not_found_response(self):
        return request.make_json_response(
            data={"status": "error", "message": ("Ref code is not found.")},
            status=404,
        )
