# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from . import CONST
from ...utilities.models import CONST as UTILITIES_CONST
import logging


class MaterialEntity(models.Model):
    _name = "ship.material.entity"
    _description = "Material entity records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    quantity = fields.Float("Quantity", default=1, tracking=True)
    available_quantity = fields.Float(
        "Available quantity", compute="_cacl_quantity", store=True
    )
    image = fields.Image(
        "Image",
        tracking=True,
        max_width=CONST.MAX_IMAGE_UPLOAD_WIDTH,
        max_height=CONST.MAX_IMAGE_UPLOAD_HEIGHT,
    )
    expiration_date = fields.Date("Expiration date", tracking=True)
    min_life_span_hours = fields.Integer(
        "Min life span in hours",
        related="material_id.material_usage_type_id.min_life_span_hours",
        tracking=True,
    )
    max_life_span_hours = fields.Integer(
        "Max life span in hours",
        related="material_id.material_usage_type_id.max_life_span_hours",
        tracking=True,
    )
    is_discarded = fields.Boolean(
        "Is discarded", default=False, readonly=True, tracking=True
    )
    discard_date = fields.Date("Discarded date", tracking=True)
    total_hours = fields.Float(
        "Total usage time in hours", compute="_calc_total_hours", tracking=True
    )
    is_suggested_to_discard = fields.Boolean(
        "Is suggested to discard", readonly=True, tracking=True
    )

    is_currently_proposed_to_replace = fields.Boolean(
        "Is currently proposed to replace", readonly=True, tracking=True
    )
    is_used_for_lifespan = fields.Boolean(
        "Is used for lifespan",
        related="material_id.is_used_for_lifespan",
        store=True,
        tracking=True,
    )

    # related
    delivered_at = fields.Datetime(
        "Delivered at",
        related="material_supplier_quote_id.material_quote_id.delivered_at",
        tracking=True,
    )

    material_type = fields.Selection(
        string="Material Type",
        related="material_id.material_type",
        store=True,
        tracking=True,
    )

    unit = fields.Char(
        related="material_id.unit",
        string="Unit",
        store=False,
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    material_id = fields.Many2one("ship.material", string="Material", tracking=True)

    material_assignment_ids = fields.One2many(
        "ship.material.assignment",
        "material_entity_id",
        string="Material Assignment",
        tracking=True,
    )

    material_supplier_quote_id = fields.Many2one(
        "ship.material.supplier.quote", string="Material supplier quote", tracking=True
    )

    replacement_diary_ids = fields.One2many(
        "ship.replacement.diary",
        "material_entity_id",
        string="Replacement Diary",
        tracking=True,
    )

    expired_material_entity_replacement_proposal_ids = fields.Many2many(
        "ship.expired.material.entity.replacement.proposal",
        relation="ship_replacement_proposal_ship_material_entity_rel",
        string="Expired Material Entity Replacement Proposal",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.constrains("is_used_for_lifespan", "quantity")
    def quantity_must_be_equal_to_1_when_the_material_is_for_lifespan(self):
        for record in self:
            message = "Số lượng phải bằng 1 khi vật tư có tuổi thọ!"
            if record.is_used_for_lifespan:
                if record.quantity != 1:
                    raise ValidationError(message)

    @api.depends(
        "quantity", "is_discarded", "is_used_for_lifespan", "material_assignment_ids"
    )
    def _cacl_quantity(self):
        for record in self:
            if record.is_used_for_lifespan:
                quantity = record._get_available_quantiy_for_lifespan_material()
                record.available_quantity = quantity
            else:
                quantity = record._get_available_quantiy_for_normal_material()
                record.available_quantity = quantity

            if record.is_discarded:
                record.available_quantity = 0

    @api.depends("material_assignment_ids")
    def _calc_total_hours(self):
        for r in self:
            r.total_hours = sum(r.material_assignment_ids.mapped("total_hours"))

            if r._reaches_min_life_span_hours():
                r.is_suggested_to_discard = True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.material.entity")
        records = super(MaterialEntity, self).create(vals_list)
        for record in records:
            record._set_default_expiration_date_if_not()
        return records

    def _set_default_expiration_date_if_not(self):
        if self.expiration_date:
            return
        else:
            self.expiration_date = self.material_id.expiration_date

    def write(self, vals):
        self.ensure_one()
        old_material_id = self.material_id
        result = super(MaterialEntity, self).write(vals)
        new_material_id = self.material_id

        if "material_id" in vals:
            if new_material_id != old_material_id:
                if self.material_assignment_ids:
                    message = "Không thể thay đổi vật tư, khi vật tư đã qua sử dụng!"
                    raise ValidationError(message)

        return result

    def unlink(self):
        for material_entity in self:
            ref = material_entity.ref
            if not material_entity.is_discarded:
                message1 = f"Không thể xóa vật tư({ref}), khi vật tư chưa được loại bỏ!"
                raise ValidationError(message1)
            if material_entity.material_assignment_ids:
                message2 = f"Không thể xóa vật tư({ref}), khi vật tư đã qua sử dụng."
                raise ValidationError(message2)

        return super(MaterialEntity, self).unlink()

    def name_get(self):
        result = []
        for report in self:
            name = report.name
            available_quantity = report.available_quantity

            name = f"{name}({available_quantity})"
            result.append((report.id, name))
        return result

    def hard_unlink(self, sudo=False):
        admin_xml = "utilities.group_ship_admin"
        message = "Người dùng k có quyền sử dụng chức năng này!"

        if self.env.user.has_group(admin_xml) or sudo:
            for record in self:
                record.action_discard()
                record.unlink()
        else:
            raise ValidationError(message)

    def remove_material_entity_that_not_assigned(self):
        for record in self[:2500]:
            if not record.material_assignment_ids:
                record.hard_unlink()

    def action_discard(self):
        today = fields.Date.today()
        if not self.is_discarded:
            self.is_discarded = True
            self.discard_date = today

    def action_undiscard(self):
        if self.is_discarded:
            self.is_discarded = False
            self.discard_date = False

    def _reaches_min_life_span_hours(self):
        self.ensure_one()
        if self.total_hours >= self.min_life_span_hours:
            if self.min_life_span_hours > 0:
                return True
        return False

    def _reaches_max_life_span_hours(self):
        self.ensure_one()
        if self.total_hours >= self.max_life_span_hours:
            if self.max_life_span_hours > 0:
                return True
        return False

    def _get_available_quantiy_for_lifespan_material(self):
        self.ensure_one()
        if self._is_lifespan_material_using_in_assignment():
            return 0
        elif self._reaches_max_life_span_hours():
            return 0
        else:
            return self.quantity

    def _get_available_quantiy_for_normal_material(self):
        used_quantity = sum(self.material_assignment_ids.mapped("quantity"))
        return self.quantity - used_quantity

    def _is_lifespan_material_using_in_assignment(self):
        self.ensure_one()
        is_using = any(
            [
                not e.start_time_of_use or not e.end_time_of_use
                for e in self.material_assignment_ids
            ]
        )

        return is_using

    def _get_all_nondiscarded_expired_materials(self):
        return self.search(
            [
                ("is_discarded", "=", False),
                ("expiration_date", "<=", fields.Date.today()),
                ("is_currently_proposed_to_replace", "=", False),
                ("is_suggested_to_discard", "=", False),
            ]
        )

    def action_propose_to_replace(self):
        expired_materials = self._get_all_nondiscarded_expired_materials()
        if expired_materials:
            # create a new ship.expired.material.entity.replacement.proposal
            self.env["ship.expired.material.entity.replacement.proposal"].create(
                {
                    "material_entity_ids": [(6, 0, expired_materials.ids)],
                }
            )
            for entity in expired_materials:
                entity.is_currently_proposed_to_replace = True
