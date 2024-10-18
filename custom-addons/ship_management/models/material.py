# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
import logging

machinery = "machinery"
boong = "boong"
tool = "tool"

WAREHOUSES = [
    (machinery, "Machinery"),
    (boong, "Boong"),
    (tool, "Tool"),
]


class Material(models.Model):
    _name = "ship.material"
    _description = "Material records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", required=True, tracking=True)
    description = fields.Char("Description", tracking=True)
    spare_part_no = fields.Char("Spare part no", tracking=True)
    internal_code = fields.Char("Internal code", tracking=True)
    imba_code = fields.Char("IMBA code", tracking=True)
    note = fields.Char("Note", tracking=True)
    unit = fields.Char("Unit", tracking=True)
    min_quantity = fields.Float("Min quantity", tracking=True)
    available_quantity = fields.Float("Available quantity", compute="_cacl_quantity")
    transfer_quantity = fields.Float("Transfer quantity", tracking=True)
    origin = fields.Char("Origin", tracking=True)
    is_quantity_low = fields.Boolean("Is quantity low", default=False, readonly=True)
    is_essential_material = fields.Boolean("Is essential material", tracking=True)
    is_used_for_lifespan = fields.Boolean("Is used for lifespan", tracking=True)
    warehouse = fields.Selection(
        selection=WAREHOUSES,
        string="Warehouse",
        default=machinery,
        required=True,
        tracking=True,
    )
    material_type = fields.Selection(
        CONST.MATERIAL_TYPE,
        string="Material Type",
        default=CONST.MATERIAL,
        tracking=True,
    )

    type_of_medicine = fields.Char("Type of medicine", tracking=True)
    concentration = fields.Char("Concentration", tracking=True)
    expiration_date = fields.Date("Expiration date", tracking=True)

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    unit_id = fields.Many2one("ship.unit", string="Unit", tracking=True)
    material_usage_type_id = fields.Many2one(
        "ship.material.usage.type", string="Material Usage Type", tracking=True
    )
    material_group_id = fields.Many2one(
        "ship.material.group", string="Material Group", tracking=True
    )
    supplier_ids = fields.Many2many(
        "ship.supplier",
        string="Supplier",
        domain="[('classified_for_material', '=', True)]",
        tracking=True,
    )
    material_entity_ids = fields.One2many(
        "ship.material.entity",
        inverse_name="material_id",
        string="Material Entity",
        tracking=True,
    )
    material_assignment_ids = fields.One2many(
        "ship.material.assignment",
        "material_id",
        string="Material assignment",
        tracking=True,
    )
    replacement_diary_ids = fields.One2many(
        "ship.replacement.diary",
        "material_id",
        string="Replacement diary",
        tracking=True,
    )
    lashing_material_fix_stats_ids = fields.One2many(
        "ship.lashing.material.fix.stats",
        "material_id",
        string="Lashing material fix stats",
        tracking=True,
    )

    # proposed_liquidation_ids = fields.Many2many(
    #     "ship.proposed.liquidation",
    #     string="Proposed liquidation",
    #     tracking=True,
    # )

    liquidation_minute_ids = fields.Many2many(
        "ship.liquidation.minute",
        string="Liquidation minute",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.depends("material_entity_ids")
    def _cacl_quantity(self):
        for record in self:
            available_quantity = record.material_entity_ids.mapped("available_quantity")
            record.available_quantity = sum(available_quantity)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.material")
        return super(Material, self).create(vals_list)

    def write(self, vals):
        return super(Material, self).write(vals)

    def unlink(self):
        for material in self:
            if material._is_material_in_material_quotes():
                raise ValidationError(
                    "You cannot delete material that has in progress material quote."
                )
        return super(Material, self).unlink()

    def name_get(self):
        result = []
        for report in self:
            name = f"{report.name or _('New')}"
            result.append((report.id, name))
        return result

    def _is_material_in_material_quotes(self):
        count = self.env["ship.material.quote"].search_count(
            [
                ("material_id", "=", self.id),
                ("company_id", "=", self.company_id.id),
                ("approval_status", "!=", CONST.APPROVED),
                ("approval_status", "!=", CONST.REJECTED),
            ]
        )
        return count > 0

    def _create_material_entities(self, quantity, material_supplier_quote_id=False):
        self.ensure_one()

        if not quantity:
            return

        entity_object = {
            "name": self.name,
            "material_id": self.id,
            "material_supplier_quote_id": material_supplier_quote_id,
        }

        if self.is_used_for_lifespan:
            self._create_lifespan_material_entities(quantity, entity_object)
        else:
            entity_object["quantity"] = quantity
            self.env["ship.material.entity"].create(entity_object)

    def _create_lifespan_material_entities(self, quantity, vals):
        int_quantity = int(quantity)
        for _ in range(int_quantity):
            self.env["ship.material.entity"].create(vals)

    def _assign_materials_based_on_type(self, quantity, job_quote_id=None):
        if self.is_used_for_lifespan:
            self._assign_each_entities(quantity, job_quote_id)
        else:
            self._assign_group_entities(quantity, job_quote_id)

    def _assign_each_entities(self, quantity, job_quote_id=None):
        self.ensure_one()
        available_entity = lambda e: e.available_quantity
        entities = self.material_entity_ids.filtered(available_entity)

        for material_entity in entities[: int(quantity)]:
            self.env["ship.material.assignment"].create(
                {
                    "material_id": self.id,
                    "material_entity_id": material_entity.id,
                    "job_quote_id": job_quote_id.id,
                }
            )

    def _assign_group_entities(self, quantity, job_quote_id=None):
        self.ensure_one()
        available_entity = lambda e: e.available_quantity >= quantity
        entities = self.material_entity_ids.filtered(available_entity)

        if entities:
            entity = entities[0]
            self.env["ship.material.assignment"].create(
                {
                    "material_id": self.id,
                    "quantity": quantity,
                    "material_entity_id": entity.id,
                    "job_quote_id": job_quote_id.id,
                }
            )

    def remove_material_that_not_assigned(self):
        for record in self:
            if not record.material_assignment_ids:
                record.unlink()

    def create_transfer_quantity(self):
        for record in self:
            if record.transfer_quantity:
                record._create_material_entities(record.transfer_quantity)
                record.transfer_quantity = 0

    def _create_material_quote_based_on_min_quantity(self):
        self.ensure_one()
        needed_quantity = self.min_quantity - self.available_quantity

        if needed_quantity > 0:
            return self.env["ship.material.quote"].create(
                {
                    "material_id": self.id,
                    "company_id": self.company_id.id,
                    "quantity": needed_quantity,
                }
            )

    def organize_for_material_have_lifespan(self):
        self.ensure_one()
        entity_ids = self.material_entity_ids

        for entity_id in self.material_entity_ids:
            self._validate_to_organize_entity(entity_id)

        self.check_if_many_expiration_dates_by_entities(entity_ids)
        self.check_if_many_discard_entities_by_entities(entity_ids)
        self.check_if_is_suggested_to_discard_by_entities(entity_ids)
        self.check_if_is_currently_proposed_to_replace_by_entities(entity_ids)

        self._create_lifespan_material_entity_for_organize()

    def _create_normal_material_entity_for_organize_by_entity(self, entity_ids):
        if entity_ids:
            entity_id = entity_ids[0]
            quantity = sum(entity_ids.mapped("quantity"))
            vals = self._get_material_entity_object(entity_id)
            vals["quantity"] = quantity
            self.env["ship.material.entity"].create(vals)

            entity_ids.hard_unlink(sudo=True)

    def organize_for_material_dont_have_lifespan(self):
        self.ensure_one()
        entity_ids = self.material_entity_ids

        for entity_id in self.material_entity_ids:
            self._validate_to_organize_entity(entity_id)

        self.check_if_many_expiration_dates_by_entities(entity_ids)
        self.check_if_many_discard_entities_by_entities(entity_ids)
        self.check_if_is_suggested_to_discard_by_entities(entity_ids)
        self.check_if_is_currently_proposed_to_replace_by_entities(entity_ids)

        self._create_entity_based_on_material_supplier_quote_id()
        self._create_entity_based_on_false_quote_entity_id()

    def _create_entity_based_on_material_supplier_quote_id(self):
        self.ensure_one()
        supplier_quote_ids = self.material_entity_ids.mapped(
            "material_supplier_quote_id"
        )

        for quote_id in supplier_quote_ids:
            entity_ids = self._get_entity_by_quote_ids(quote_id)

            self._create_normal_material_entity_for_organize_by_entity(entity_ids)

    def _create_entity_based_on_false_quote_entity_id(self):
        self.ensure_one()
        entity_ids = self.material_entity_ids.filtered(
            lambda e: not e.material_supplier_quote_id
        )

        self._create_normal_material_entity_for_organize_by_entity(entity_ids)

    def _create_lifespan_material_entity_for_organize(self):
        self.ensure_one()

        for entity_id in self.material_entity_ids:
            int_quantity = int(entity_id.quantity)

            for _ in range(int_quantity):
                vals = self._get_material_entity_object(entity_id)
                self.env["ship.material.entity"].create(vals)

            entity_id.hard_unlink(sudo=True)

    def check_if_many_expiration_dates_by_entities(self, entity_ids):
        refs = entity_ids.mapped("ref")
        expired_arr = list(set(entity_ids.mapped("expiration_date")))
        message = f"Có nhiều ngày hết hạn trong 1 báo giá nhà cung cấp-{refs}"

        if len(expired_arr) >= 2:
            raise ValidationError(message)
        else:
            return False

    def check_if_many_discard_entities_by_entities(self, entity_ids):
        refs = entity_ids.mapped("ref")
        discarded_arr = list(set(entity_ids.mapped("is_discarded")))
        message = f"Có 2 loại loại bỏ trong 1 báo giá nhà cung cấp-{refs}"

        if len(discarded_arr) >= 2:
            raise ValidationError(message)
        else:
            return False

    def check_if_is_suggested_to_discard_by_entities(self, entity_ids):
        refs = entity_ids.mapped("ref")
        suggested_arr = list(set(entity_ids.mapped("is_suggested_to_discard")))
        message = f"Không được có vật tư được đề nghị để loại bỏ-{refs}"

        if any(suggested_arr):
            raise ValidationError(message)
        else:
            return False

    def check_if_is_currently_proposed_to_replace_by_entities(self, entity_ids):
        refs = entity_ids.mapped("ref")
        proposed_arr = list(set(entity_ids.mapped("is_currently_proposed_to_replace")))
        message = f"Không được có vật tư được đề xuất để thay thế-{refs}"

        if any(proposed_arr):
            raise ValidationError(message)
        else:
            return False

    def _get_entity_by_quote_ids(self, quote_id):
        self.ensure_one()
        entity_ids = self.material_entity_ids.filtered(
            lambda e: e.material_supplier_quote_id == quote_id
        )

        return entity_ids

    def _validate_to_organize_entity(self, entity_id):
        if entity_id.material_assignment_ids:
            refs = entity_id.material_assignment_ids.mapped("ref")
            message = f"Vật tự đã được nhận, không thể thao tác{refs}-{entity_id.ref}"
            raise ValidationError(message)

        if entity_id.replacement_diary_ids:
            refs = entity_id.replacement_diary_ids.mapped("ref")
            message = f"Vật tự đã có nhật ký, không thể thao tác{refs}-{entity_id.ref}"
            raise ValidationError(message)

        if entity_id.expired_material_entity_replacement_proposal_ids:
            proposals = entity_id.expired_material_entity_replacement_proposal_ids
            refs = proposals.mapped("ref")
            message = f"Vật tự đã có đề xuất thay thế, không thể thao tác{refs}-{entity_id.ref}"
            raise ValidationError(message)

    def _get_material_entity_object(self, entity_id):
        return {
            "name": entity_id.name,
            "quantity": 1,
            "image": entity_id.image,
            "expiration_date": entity_id.expiration_date,
            "is_discarded": entity_id.is_discarded,
            "discard_date": entity_id.discard_date,
            "material_id": entity_id.material_id.id,
            "material_supplier_quote_id": entity_id.material_supplier_quote_id.id,
            # "material_assignment_ids": entity_id.material_assignment_ids,
            # "replacement_diary_ids": entity_id.replacement_diary_ids,
            # "expired_material_entity_replacement_proposal_ids": entity_id.expired_material_entity_replacement_proposal_ids,
            # "is_suggested_to_discard": entity_id.is_suggested_to_discard,
            # "is_currently_proposed_to_replace": entity_id.is_currently_proposed_to_replace,
            # "available_quantity": entity_id.available_quantity,
            # "min_life_span_hours": entity_id.min_life_span_hours,
            # "max_life_span_hours": entity_id.max_life_span_hours,
            # "total_hours": entity_id.total_hours,
            # "is_used_for_lifespan": entity_id.is_used_for_lifespan,
            # "delivered_at": entity_id.delivered_at,
            # "material_type": entity_id.material_type,
            # "unit": entity_id.unit,
            # "company_id": self.company_id.id,
        }

    def get_default_unit(self):
        for record in self:
            unit_id = record.unit_id
            if unit_id:
                record.unit = unit_id.name

                if unit_id.store_type == CONST.EACH_ENTITY:
                    record.is_used_for_lifespan = True
                elif unit_id.store_type == CONST.GROUP_ENTITY:
                    record.is_used_for_lifespan = False
