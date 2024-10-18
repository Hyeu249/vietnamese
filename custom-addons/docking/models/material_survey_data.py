# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class MaterialSurveyData(models.Model):
    _name = "docking.material.survey.data"
    _description = "Khảo sát vật tư"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    quantity = fields.Float("Quantity", tracking=True)
    note = fields.Char("Note", tracking=True)
    survey_type = fields.Selection(
        CONST.ARISE_SELECTION,
        string="Survey type",
        default=CONST.NORMAL,
        tracking=True,
    )

    # related
    name_for_noti = fields.Char(
        related="material_survey_metadata_id.name",
        string="Name",
    )
    unit = fields.Char(
        "Unit",
        related="material_survey_metadata_id.unit",
        store=True,
        tracking=True,
    )

    # relations
    material_survey_metadata_id = fields.Many2one(
        "docking.material.survey.metadata",
        string="Material survey metadata",
        required=True,
        tracking=True,
    )
    docking_plan_id = fields.Many2one(
        "docking.docking.plan", string="Docking plan", tracking=True
    )
    material_quote_ids = fields.One2many(
        "docking.material.quote",
        "material_survey_data_id",
        string="Material quote",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "docking.material.survey.data"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)

        result = super(MaterialSurveyData, self).create(vals_list)
        for record in result:
            if record._is_arise():
                record.sudo_approve()
        return result

    def write(self, vals):
        self._post_chatter_message_to_related_model_on_write(
            vals, "docking_plan_id", tracking_fields=["quantity", "note", "survey_type"]
        )
        result = super(MaterialSurveyData, self).write(vals)

        if "survey_type" in vals:
            raise ValidationError("Không được sửa trường survey_type!!")

        for record in self:
            if "approval_status" in vals and record.quantity == 0:
                raise ValidationError("Số lượng chưa có, vui lòng kiểm tra lại!!")

            if "approval_status" in vals:
                if record._is_approved() and not record.material_quote_ids:
                    record._create_single_material_quote()

            # if record._is_arise():
            #     message = "Không được tham gia luồng duyệt, khi khảo sát là phát sinh!!"
            #     if "approval_status" in vals:
            #         raise ValidationError(message)

        return result

    def _get_chatter_message_on_write(self, old_values, vals):
        """
        Get the chatter message on write.
        Args:
            old_values: a dict of old values of changed fields
            vals: the vals of the write method
        """
        message_text = f"Khảo sát vật tư {self.material_survey_metadata_id.name} (mã: \
            <b>{self.ref}</b>) đã được cập nhật với các thông tin sau: <br/>"
        for field in old_values:
            if old_values[field] != vals[field]:
                message_text += f"{field}: {old_values[field]} -> {vals[field]} <br/>"
        return message_text

    def unlink(self):
        for record in self:
            record.material_quote_ids.unlink()
        return super(MaterialSurveyData, self).unlink()

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _get_emails(self):
        emails = [
            supplier_quote.supplier_id.email
            for quote in self.material_quote_ids
            for supplier_quote in quote.material_supplier_quote_ids
        ]
        return emails

    def _create_single_material_quote(self):
        self.ensure_one()
        return self.env["docking.material.quote"].create(
            {
                "material_survey_data_id": self.id,
            }
        )

    def _get_material_quote_id(self):
        quote_ids = self.material_quote_ids
        if quote_ids:
            material_quote_id = quote_ids[0]
            return material_quote_id
        else:
            return False

    def _is_arise(self):
        self.ensure_one()
        return self.survey_type == CONST.ARISE

    def open_record(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
            "context": self.env.context,
        }
