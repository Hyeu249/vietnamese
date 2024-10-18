# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from .common_utils import generate_token
from ...utilities.models import CONST as UTILITIES_CONST
import logging
from . import CONST


# Đề xuất thay thế vật tư hết hạn sử dụng
class ExpiredMaterialEntityReplacementProposal(models.Model):
    _name = "ship.expired.material.entity.replacement.proposal"
    _description = "Đề xuất thay thế vật tư hết hạn"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    material_entity_name_list = fields.Char(
        "Material entity name list",
        compute="_compute_material_entity_name_list",
    )

    proposed_date = fields.Date(
        "Proposed date", default=fields.Date.today, readonly=True
    )

    # relations
    material_entity_ids = fields.Many2many(
        "ship.material.entity",
        relation="ship_replacement_proposal_ship_material_entity_rel",
        string="Material entities",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "ship.expired.material.entity.replacement.proposal"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(ExpiredMaterialEntityReplacementProposal, self).create(vals_list)

        for record in result:
            record._send_noti_for_people_need_to_review_proposal()

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(ExpiredMaterialEntityReplacementProposal, self).write(vals)

        if "approval_status" in vals:
            if self._is_approved():
                self.create_replacement_diary_for_all_entities()
            elif self._is_rejected():
                self.not_propose_to_replace_material_entities()

        return result

    @api.depends("material_entity_ids")
    def _compute_material_entity_name_list(self):
        for record in self:
            name_list = ""
            for material_entity in record.material_entity_ids:
                name_list += f"{material_entity.name} ({material_entity.ref}), "
            record.material_entity_name_list = name_list

    # def action_approve(self):
    #     self.ensure_one()
    #     super(ExpiredMaterialEntityReplacementProposal, self).action_approve()
    #     # after approved, create replacement diary records
    #     for material_entity in self.material_entity_ids:
    #         material = material_entity.material_id
    #         # create a new ship.replacement.diary record
    #         self.env["ship.replacement.diary"].create(
    #             {
    #                 "material_id": material.id,
    #                 "material_entity_id": material_entity.id,
    #                 "date": fields.Date.today(),
    #                 "description": f"Vật tư hết hạn sử dụng. Đề xuất thay thế vật tư: {material.name} ({material.internal_code}, mã thực thể {material_entity.ref}). Ngày hết hạn sử dụng: {material_entity.expiration_date}.",
    #                 "quantity": 1,
    #                 "reason": "Vật tư hết hạn sử dụng",
    #                 "condition": "Hết hạn sử dụng",
    #                 "internal_code": material.internal_code,
    #                 "material_description": material.description,
    #             }
    #         )

    def create_replacement_diary_for_all_entities(self):
        self.ensure_one()
        for material_entity in self.material_entity_ids:
            material = material_entity.material_id
            self.env["ship.replacement.diary"].create(
                {
                    "material_id": material.id,
                    "material_entity_id": material_entity.id,
                    "date": fields.Date.today(),
                    "description": f"Vật tư hết hạn sử dụng. Đề xuất thay thế vật tư: {material.name} ({material.internal_code}, mã thực thể {material_entity.ref}). Ngày hết hạn sử dụng: {material_entity.expiration_date}.",
                    "quantity": 1,
                    "reason": "Vật tư hết hạn sử dụng",
                    "condition": "Hết hạn sử dụng",
                    "internal_code": material.internal_code,
                    "material_description": material.description,
                }
            )

    # def action_reject(self):
    #     self.ensure_one()
    #     super(ExpiredMaterialEntityReplacementProposal, self).action_reject()
    #     if self.material_entity_ids:
    #         self.material_entity_ids.write({"is_currently_proposed_to_replace": False})

    def not_propose_to_replace_material_entities(self):
        self.ensure_one()
        for entity in self.material_entity_ids:
            entity.is_currently_proposed_to_replace = False

    def _send_noti_for_people_need_to_review_proposal(self):
        self.ensure_one()
        group_xml_id = "group_ship_captain"
        company_id = self.company_id

        classes = "title_replacement_proposal_color"
        subject = f"Đề nghị duyệt danh sách vật tư hết hạn!"
        body = f"Bản ghi {self.ref} cần duyệt danh sách các vật tư hết hạn!"

        self._send_notification_by_group_xml_and_company_id(
            group_xml_id, company_id, subject, body, classes
        )
