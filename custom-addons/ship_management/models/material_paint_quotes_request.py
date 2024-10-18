# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from ...utilities.models import CONST as CONST_UTILITIES
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging


class MaterialPaintQuotesRequest(models.Model):
    _name = "ship.material.paint.quotes.request"
    _description = "Yêu cầu cấp vật tư, sơn"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True
    _edit_field_permissions_list = {
        "material_quote_ids": [
            "utilities.group_ship_ship_crew",
            "utilities.group_ship_vice_captain",
            "utilities.group_ship_captain",
            "utilities.group_ship_head_of_machinery",
            "utilities.group_ship_vice_captain_head_machinery",
        ],
    }

    expected_delivery_date = fields.Date("Expected delivery date", tracking=True)
    deadline = fields.Date("Deadline", tracking=True)
    description = fields.Text("Description", tracking=True)

    supplier_emails = fields.Char(
        "Supplier emails",
        readonly=lambda self: not self.user.has_group("utilities.group_ship_admin"),
        tracking=True,
    )
    not_allowed_to_see_price = fields.Boolean(
        "Not allow crew", compute="_calc_not_allowed_to_see_price"
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    material_quote_ids = fields.Many2many(
        "ship.material.quote",
        "ship_material_quote_ship_material_paint_quotes_request_rel",
        "material_paint_quotes_request_id",
        "material_quote_id",
        domain=f"[('material_paint_quotes_request_id', '=', False), ('material_type', '!=', '{CONST.SPARE_PART}')]",
        string="Material quote",
        tracking=True,
    )

    spare_part_quote_ids = fields.Many2many(
        "ship.material.quote",
        "ship_spare_part_quote_ship_material_paint_quotes_request_rel",
        "material_paint_quotes_request_id",
        "spare_part_quote_id",
        domain=f"[('material_paint_quotes_request_id', '=', False), ('material_type', '=', '{CONST.SPARE_PART}')]",
        string="Material quote",
        tracking=True,
    )

    paint_quote_ids = fields.Many2many(
        "ship.paint.quote",
        "ship_paint_quote_ship_material_paint_quotes_request_rel",
        "material_paint_quotes_request_id",
        "paint_quote_id",
        domain=f"[('material_paint_quotes_request_id', '=', False)]",
        string="Paint quote",
        tracking=True,
    )

    unsent_supplier_quote_portal_change_notification_ids = fields.One2many(
        "ship.supplier.quote.portal.change.notification",
        "material_paint_quotes_request_id",
        string="Supplier quote portal change notifications",
        domain=[("is_notified", "=", False)],
    )

    supplier_for_filter_id = fields.Many2one(
        "ship.supplier",
        string="Supplier for filter",
        domain="""[
            ('id', 'in', selected_supplier_ids),
        ]""",
    )

    selected_supplier_ids = fields.Many2many(
        "ship.supplier", compute="_compute_selected_supplier_ids"
    )

    total_price_on_supplier = fields.Float(
        "Total price on supplier", compute="_get_total_price_on_supplier", tracking=True
    )
    total_prices = fields.Float(
        "Total prices", compute="_get_total_prices", tracking=True
    )
    lowest_total_price = fields.Float(
        "Lowest total price", compute="_get_lowest_total_price", tracking=True
    )

    technical_incident_id = fields.Many2one("legis.technical.incident", readonly=True)
    serious_accident_team_id = fields.Many2one(
        "legis.serious.accident.team", readonly=True
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.constrains("technical_incident_id", "serious_accident_team_id")
    def only_technical_incident_or_serious_accident(self):
        for record in self:
            if record.technical_incident_id and record.serious_accident_team_id:
                message = "Chỉ được giao vật tư cho 1 model, liên hệ kỹ thuật!"
                raise ValidationError(message)

    @api.depends(
        "material_quote_ids",
        "spare_part_quote_ids",
        "paint_quote_ids",
        "approval_status",
    )
    def _compute_selected_supplier_ids(self):
        for record in self:
            material_supplier_quote_ids = record.material_quote_ids.mapped(
                "material_supplier_quote_id"
            )
            spare_part_supplier_q_ids = record.spare_part_quote_ids.mapped(
                "material_supplier_quote_id"
            )
            paint_supplier_quote_ids = record.paint_quote_ids.mapped(
                "paint_supplier_quote_id"
            )
            material_supplier_ids = material_supplier_quote_ids.mapped("supplier_id")
            spare_part_supplier_ids = spare_part_supplier_q_ids.mapped("supplier_id")
            paint_supplier_ids = paint_supplier_quote_ids.mapped("supplier_id")

            supplier_ids = material_supplier_ids.ids
            supplier_ids += spare_part_supplier_ids.ids
            supplier_ids += paint_supplier_ids.ids

            record.selected_supplier_ids = supplier_ids

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.material.paint.quotes.request"
            )
        result = super(MaterialPaintQuotesRequest, self).create(vals_list)

        for record in result:
            material_quote_added_ids = [quote.id for quote in record.material_quote_ids]
            spare_part_quote_added_ids = [
                quote.id for quote in record.spare_part_quote_ids
            ]
            record._handle_added_material_quotes(material_quote_added_ids)
            record._handle_added_spare_part_quotes(spare_part_quote_added_ids)
            record._get_supplier_emails()

        return result

    def create_material_quotes(self):
        self.ensure_one()
        material_ids = self.env["ship.material"].search(
            [("company_id", "=", self.company_id.id)]
        )

        for material_id in material_ids:
            beginning_status = self._get_first_option_value_of_main_approval_status()
            needed_quantity = material_id.min_quantity - material_id.available_quantity
            needed_quantity = needed_quantity if needed_quantity > 0 else 0

            system_quote = self.env["ship.material.quote"].search(
                [
                    ("material_id", "=", material_id.id),
                    ("company_id", "=", self.company_id.id),
                    ("approval_status", "!=", CONST.APPROVED),
                    ("approval_status", "!=", CONST.REJECTED),
                    ("is_system_create", "=", True),
                ]
            )

            if system_quote:
                # if system_quote.approval_status == beginning_status:
                #     system_quote.quantity = needed_quantity
                pass
            else:
                self.env["ship.material.quote"].create(
                    {
                        "material_id": material_id.id,
                        "company_id": self.company_id.id,
                        "quantity": needed_quantity,
                        "is_system_create": True,
                    }
                )

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def write(self, vals):
        self.ensure_one()
        old_material_q_ids = self.material_quote_ids.ids
        old_spare_part_q_ids = self.spare_part_quote_ids.ids
        old_paint_quote_ids = self.paint_quote_ids.ids

        result = super(MaterialPaintQuotesRequest, self).write(vals)
        new_material_q_ids = self.material_quote_ids.ids
        new_spare_part_q_ids = self.spare_part_quote_ids.ids
        new_paint_quote_ids = self.paint_quote_ids.ids

        material_quote_removed_ids = set(old_material_q_ids) - set(new_material_q_ids)
        material_quote_added_ids = set(new_material_q_ids) - set(old_material_q_ids)

        spare_part_removed_ids = set(old_spare_part_q_ids) - set(new_spare_part_q_ids)
        spare_part_added_ids = set(new_spare_part_q_ids) - set(old_spare_part_q_ids)

        paint_removed_ids = set(old_paint_quote_ids) - set(new_paint_quote_ids)
        paint_added_ids = set(new_paint_quote_ids) - set(old_paint_quote_ids)

        if material_quote_removed_ids:
            self._handle_removed_material_quotes(list(material_quote_removed_ids))
        if material_quote_added_ids:
            self._handle_added_material_quotes(list(material_quote_added_ids))

        if spare_part_removed_ids:
            self._handle_removed_spare_part_quotes(list(spare_part_removed_ids))
        if spare_part_added_ids:
            self._handle_added_spare_part_quotes(list(spare_part_added_ids))

        if paint_removed_ids:
            self._handle_removed_paint_quotes(list(paint_removed_ids))
        if paint_added_ids:
            self._handle_added_paint_quotes(list(paint_added_ids))

        if "approval_status" in vals:
            if self.is_at_this_approval_level(CONST.SUPPLIER):
                supplier_ids = []
                for material_quote in self.material_quote_ids:
                    if not material_quote.material_supplier_quote_ids:
                        material_quote._create_material_supplier_quotes()
                    # get supplier ids from material quote
                    for supplier in material_quote.material_id.supplier_ids:
                        # check if supplier id is not in supplier_ids
                        if supplier.id not in supplier_ids:
                            supplier_ids.append(supplier.id)

                for spare_part_quote in self.spare_part_quote_ids:
                    if not spare_part_quote.material_supplier_quote_ids:
                        spare_part_quote._create_material_supplier_quotes()
                    # get supplier ids from material quote
                    for supplier in spare_part_quote.material_id.supplier_ids:
                        # check if supplier id is not in supplier_ids
                        if supplier.id not in supplier_ids:
                            supplier_ids.append(supplier.id)

                for paint_quote in self.paint_quote_ids:
                    if not paint_quote.paint_supplier_quote_ids:
                        paint_quote._create_paint_supplier_quotes()
                    # get supplier ids from paint quote
                    for supplier in paint_quote.paint_id.supplier_ids:
                        # check if supplier id is not in supplier_ids
                        if supplier.id not in supplier_ids:
                            supplier_ids.append(supplier.id)

                # create new SupplierQuotePortalChangeNotification records
                new_noti_records = []
                for supplier_id in supplier_ids:
                    new_noti_records.append(
                        {
                            "supplier_id": supplier_id,
                            "material_paint_quotes_request_id": self.id,
                        }
                    )
                self.env["ship.supplier.quote.portal.change.notification"].create(
                    new_noti_records
                )

            if self.is_at_this_approval_level(CONST.MATERIAL_EXPERT):
                if self.is_second_time_level():
                    for material_quote in self.material_quote_ids:
                        material_quote._get_lowest_material_supplier_price()

                    for spare_part_quote in self.spare_part_quote_ids:
                        spare_part_quote._get_lowest_material_supplier_price()

                    for paint_quote in self.paint_quote_ids:
                        paint_quote._get_lowest_paint_supplier_price()

            if (
                "material_quote_ids" in vals
                or "spare_part_quote_ids" in vals
                or "paint_quote_ids" in vals
                or "approval_status" in vals
            ):
                self._get_supplier_emails()

        return result

    def _handle_removed_material_quotes(self, removed_ids):
        self.ensure_one()
        if self._are_send_quotes_to_suppliers():
            raise ValidationError("Không thể xóa báo giá khi đơn đã gửi nhà cung cấp")
        for id in removed_ids:
            material_quote_id = self.material_quote_ids.browse(id)
            material_quote_id.material_paint_quotes_request_id = False

    def _handle_added_material_quotes(self, added_ids):
        self.ensure_one()
        if self._are_send_quotes_to_suppliers():
            raise ValidationError("Không thể thêm báo giá khi đơn đã gửi nhà cung cấp")
        for id in added_ids:
            material_quote_id = self.material_quote_ids.browse(id)
            material_quote_id.material_paint_quotes_request_id = self.id

    def _handle_removed_spare_part_quotes(self, removed_ids):
        self.ensure_one()
        if self._are_send_quotes_to_suppliers():
            raise ValidationError("Không thể xóa báo giá khi đơn đã gửi nhà cung cấp")
        for id in removed_ids:
            spare_part_quote_id = self.spare_part_quote_ids.browse(id)
            spare_part_quote_id.material_paint_quotes_request_id = False

    def _handle_added_spare_part_quotes(self, added_ids):
        self.ensure_one()
        if self._are_send_quotes_to_suppliers():
            raise ValidationError("Không thể thêm báo giá khi đơn đã gửi nhà cung cấp")
        for id in added_ids:
            spare_part_quote_id = self.spare_part_quote_ids.browse(id)
            spare_part_quote_id.material_paint_quotes_request_id = self.id

    def _handle_removed_paint_quotes(self, removed_ids):
        self.ensure_one()
        if self._are_send_quotes_to_suppliers():
            raise ValidationError("Không thể xóa báo giá khi đơn đã gửi nhà cung cấp")

    def _handle_added_paint_quotes(self, added_ids):
        self.ensure_one()
        if self._are_send_quotes_to_suppliers():
            raise ValidationError("Không thể thêm báo giá khi đơn đã gửi nhà cung cấp")

    def _check_supplier_quote_status_is_complete(self):
        all_quotes_have_price = self._is_all_quotes_have_price()

        if all_quotes_have_price and self.is_at_this_approval_level(CONST.SUPPLIER):
            self.bypass_checks().action_propose()

    def _check_all_material_quotes_price(self):
        for material_quote in self.material_quote_ids:
            is_have_price = material_quote._are_all_suppliers_have_priced()

            if not is_have_price:
                return False
        return True

    def _check_all_spare_part_quotes_price(self):
        for spare_part_quote in self.spare_part_quote_ids:
            is_have_price = spare_part_quote._are_all_suppliers_have_priced()

            if not is_have_price:
                return False
        return True

    def _check_all_paint_quotes_price(self):
        for paint_quote in self.paint_quote_ids:
            is_have_price = paint_quote._are_all_suppliers_have_priced()

            if not is_have_price:
                return False
        return True

    def _is_all_quotes_have_price(self):
        material_quotes_are_priced = self._check_all_material_quotes_price()
        spare_part_quotes_are_priced = self._check_all_spare_part_quotes_price()
        paint_quotes_are_priced = self._check_all_paint_quotes_price()

        if material_quotes_are_priced:
            if spare_part_quotes_are_priced:
                if paint_quotes_are_priced:
                    return True
        return False

    @api.onchange("expected_delivery_date")
    def _set_deadline(self):
        self.ensure_one()
        deadline_days = self._get_deadline_days()
        if self.expected_delivery_date:
            self.deadline = self.expected_delivery_date - timedelta(days=deadline_days)

    def _get_default_value_model(self):
        model_name = "utilities.default.value"
        default_value_model = self.env[model_name].search([])

        return default_value_model

    def _get_deadline_days(self):
        default_value_model = self._get_default_value_model()
        variable_name = (
            CONST_UTILITIES.INTEGER_SHIP_MATERIAL_PAINT_QUOTES_REQUEST_DEADLINE_DAY_COUNT
        )
        return default_value_model._get_default_value_by_variable_name(variable_name)

    def _are_send_quotes_to_suppliers(self):
        self.ensure_one()
        are_sended_to_suppliers = (
            self._is_approval_status_greater_than_this_group_xml_id(CONST.SUPPLIER)
        )
        return are_sended_to_suppliers

    def run_material_paint_quote_requests_daily_cronjobs(self):
        self._propose_to_material_expert_when_reaching_deadline()

    def _propose_to_material_expert_when_reaching_deadline(self):
        today = fields.Date.today()
        supplier_id = self._get_supplier_group_id()

        conditions = [
            ("deadline", "=", today),
            ("approval_status", "=", supplier_id.id),
        ]
        due_requests = self.search(conditions)

        for request in due_requests:
            request.action_propose()

    def _get_supplier_emails(self):
        for record in self:
            material_emails = [
                email
                for material_quote_id in record.material_quote_ids
                for email in material_quote_id._get_emails()
            ]
            spare_part_emails = [
                email
                for spare_part_quote_id in record.spare_part_quote_ids
                for email in spare_part_quote_id._get_emails()
            ]
            paint_emails = [
                email
                for paint_quote_id in record.paint_quote_ids
                for email in paint_quote_id._get_emails()
            ]
            emails = list(set(material_emails + spare_part_emails + paint_emails))
            string_emails = ",".join(emails)
            record.bypass_checks().supplier_emails = string_emails

    @api.depends(
        "approval_status",
        "material_quote_ids",
        "spare_part_quote_ids",
        "paint_quote_ids",
    )
    def _get_total_prices(self):
        for record in self:
            get_normal_quote = lambda e: e.quote_state == CONST.NORMAL
            material_q_ids = record.material_quote_ids.filtered(get_normal_quote)
            spare_part_q_ids = record.spare_part_quote_ids.filtered(get_normal_quote)
            paint_quote_ids = record.paint_quote_ids.filtered(get_normal_quote)

            total_prices = 0
            if material_q_ids:
                total_prices = sum(material_q_ids.mapped("total_price"))
            if spare_part_q_ids:
                total_prices = sum(spare_part_q_ids.mapped("total_price"))
            if paint_quote_ids:
                total_prices = total_prices + sum(paint_quote_ids.mapped("unit_price"))

            record.total_prices = total_prices

    @api.depends(
        "approval_status",
        "material_quote_ids",
        "spare_part_quote_ids",
        "paint_quote_ids",
    )
    def _get_lowest_total_price(self):
        for record in self:
            get_normal_quote = lambda e: e.quote_state == CONST.NORMAL
            material_q_ids = record.material_quote_ids.filtered(get_normal_quote)
            spare_part_q_ids = record.spare_part_quote_ids.filtered(get_normal_quote)
            paint_quote_ids = record.paint_quote_ids.filtered(get_normal_quote)

            lowest_total_price = 0
            if material_q_ids:
                lowest_total_price = sum(material_q_ids.mapped("lowest_total_price"))
            if spare_part_q_ids:
                lowest_total_price = sum(spare_part_q_ids.mapped("lowest_total_price"))
            if paint_quote_ids:
                lowest_total_price = sum(paint_quote_ids.mapped("lowest_total_price"))

            record.lowest_total_price = lowest_total_price

    @api.depends(
        "supplier_for_filter_id",
        "material_quote_ids",
        "spare_part_quote_ids",
        "paint_quote_ids",
    )
    def _get_total_price_on_supplier(self):
        for record in self:
            material_sup_quote_id_name = "material_supplier_quote_id.supplier_id"
            paint_sup_quote_id_name = "paint_supplier_quote_id.supplier_id"
            material_quote_ids = self.env["ship.material.quote"].search(
                [
                    ("approval_status", "=", CONST.APPROVED),
                    ("quote_state", "=", CONST.NORMAL),
                    ("material_paint_quotes_request_id", "=", record.id),
                    (material_sup_quote_id_name, "=", record.supplier_for_filter_id.id),
                ]
            )
            paint_quote_ids = self.env["ship.paint.quote"].search(
                [
                    ("approval_status", "=", CONST.APPROVED),
                    ("quote_state", "=", CONST.NORMAL),
                    ("material_paint_quotes_request_id", "=", record.id),
                    (paint_sup_quote_id_name, "=", record.supplier_for_filter_id.id),
                ]
            )

            total_price = 0
            if material_quote_ids:
                total_price = sum(material_quote_ids.mapped("total_price"))
            if paint_quote_ids:
                total_price = total_price + sum(paint_quote_ids.mapped("unit_price"))

            record.total_price_on_supplier = total_price

    def remove_supplier_for_filter(self):
        self.ensure_one()
        self.supplier_for_filter_id = False

    def action_send_emails_to_all_uninformed_requests(self):
        for request in self.search([]):
            supplier_ids = request.approved_but_uninformed_quotes(
                return_type="supplier"
            )

            for supplier_id in supplier_ids:
                material_quote_ids = request.get_material_quotes_by_supplier(
                    supplier_id
                )

                spare_part_quote_ids = request.get_spare_part_quotes_by_supplier(
                    supplier_id
                )

                paint_quote_ids = request.get_paint_quotes_by_supplier(supplier_id)

                try:
                    for quote in material_quote_ids:
                        quote.is_selected_supplier_informed = True
                    for quote in spare_part_quote_ids:
                        quote.is_selected_supplier_informed = True
                    for quote in paint_quote_ids:
                        quote.is_selected_supplier_informed = True
                    request.action_inform_selected_email(
                        supplier_id,
                        material_quote_ids,
                        spare_part_quote_ids,
                        paint_quote_ids,
                    )
                except Exception as e:
                    for quote in material_quote_ids:
                        quote.is_selected_supplier_informed = False
                    for quote in spare_part_quote_ids:
                        quote.is_selected_supplier_informed = False
                    for quote in paint_quote_ids:
                        quote.is_selected_supplier_informed = False
                    raise e

    def get_material_quotes_by_supplier(self, supplier_id):
        self.ensure_one()
        material_quote_ids = self.material_quote_ids.filtered(
            lambda e: e.material_supplier_quote_id.supplier_id == supplier_id
        )
        return material_quote_ids

    def get_spare_part_quotes_by_supplier(self, supplier_id):
        self.ensure_one()
        spare_part_quote_ids = self.spare_part_quote_ids.filtered(
            lambda e: e.material_supplier_quote_id.supplier_id == supplier_id
        )
        return spare_part_quote_ids

    def get_paint_quotes_by_supplier(self, supplier_id):
        self.ensure_one()
        paint_quote_ids = self.paint_quote_ids.filtered(
            lambda e: e.paint_supplier_quote_id.supplier_id == supplier_id
        )
        return paint_quote_ids

    def approved_but_uninformed_quotes(self, return_type):
        self.ensure_one()

        material_quote_ids = self.material_quote_ids.filtered(
            lambda e: e._is_quote_approved() and e._is_not_informed()
        )

        spare_part_quote_ids = self.spare_part_quote_ids.filtered(
            lambda e: e._is_quote_approved() and e._is_not_informed()
        )

        paint_quote_ids = self.paint_quote_ids.filtered(
            lambda e: e._is_quote_approved() and e._is_not_informed()
        )

        material_supplier_ids = [
            quote.material_supplier_quote_id.supplier_id
            for quote in material_quote_ids
            if quote.material_supplier_quote_id.supplier_id
        ]

        spare_part_supplier_ids = [
            quote.material_supplier_quote_id.supplier_id
            for quote in spare_part_quote_ids
            if quote.material_supplier_quote_id.supplier_id
        ]

        paint_quote_ids = [
            quote.paint_supplier_quote_id.supplier_id
            for quote in paint_quote_ids
            if quote.paint_supplier_quote_id.supplier_id
        ]

        supplier_ids = list(
            set(material_supplier_ids + spare_part_supplier_ids + paint_quote_ids)
        )

        if return_type == "material_quote":
            return material_quote_ids
        elif return_type == "spare_part_quote":
            return spare_part_quote_ids
        elif return_type == "paint_quote":
            return paint_quote_ids
        elif return_type == "supplier":
            return supplier_ids

    def action_inform_selected_email(
        self, supplier_id, material_quote_ids, spare_part_quote_ids, paint_quote_ids
    ):
        """Send email when the supplier is selected"""
        template = self.env.ref(
            "ship_management.email_template_materials_for_supplier_mark_done"
        ).id

        supplier_ref = supplier_id.ref
        access_token = supplier_id.access_token
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        params = f"supplier_ref={supplier_ref}&access_token={access_token}"
        portal_access_url = f"{base_url}/material-paint-quotes/{self.ref}?{params}"

        context = {
            "supplier_id": supplier_id,
            "material_quote_ids": material_quote_ids,
            "spare_part_quote_ids": spare_part_quote_ids,
            "paint_quote_ids": paint_quote_ids,
            "portal_access_url": portal_access_url,
        }
        email_values = {
            "email_to": supplier_id.email,
        }
        self.env["mail.template"].browse(template).with_context(context).send_mail(
            self.id, email_values=email_values, force_send=False
        )

    def _calc_not_allowed_to_see_price(self):
        admin_xml_id = f"utilities.group_ship_admin"
        crew_xml_id = f"utilities.group_ship_ship_crew"
        captain_xml_id = f"utilities.group_ship_captain"
        vice_captain_xml_id = f"utilities.group_ship_vice_captain"
        head_of_machinery_xml_id = f"utilities.group_ship_head_of_machinery"
        not_allow_roles = [
            crew_xml_id,
            captain_xml_id,
            vice_captain_xml_id,
            head_of_machinery_xml_id,
        ]

        if self.env.user.has_group(admin_xml_id):
            self.not_allowed_to_see_price = False
            return

        for xml_id in not_allow_roles:
            if self.env.user.has_group(xml_id):
                self.not_allowed_to_see_price = True
                return

        self.not_allowed_to_see_price = False

    def _is_approved_request(self):
        self.ensure_one()
        return self.approval_status == CONST.APPROVED

    def add_material_quote(self):
        self.ensure_one()
        material_quote_id = self.material_quote_ids.create({})
        self.material_quote_ids = [(4, material_quote_id.id)]

    def add_spare_part_quote(self):
        self.ensure_one()
        spare_part_quote_id = self.spare_part_quote_ids.create({})
        self.spare_part_quote_ids = [(4, spare_part_quote_id.id)]

    def add_paint_quote(self):
        self.ensure_one()
        paint_quote_id = self.paint_quote_ids.create({})
        self.paint_quote_ids = [(4, paint_quote_id.id)]
