# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class MaterialAssignment(models.Model):
    _name = "ship.material.assignment"
    _description = "Material Assignment records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    quantity = fields.Float("Quantity", default=1, tracking=True)
    start_time_of_use = fields.Datetime("Start Time of Use", tracking=True)
    end_time_of_use = fields.Datetime("End Time of Use", tracking=True)
    total_hours = fields.Float("Total hours", compute="_get_total_hours", store=True)

    # related

    unit = fields.Char(
        related="material_id.unit",
        string="Unit",
        store=False,
    )

    # relations
    material_id = fields.Many2one("ship.material", string="Material", tracking=True)
    material_entity_id = fields.Many2one(
        "ship.material.entity",
        string="Material entity",
        domain="[('material_id', '=', material_id), ('available_quantity', '>', 0), ('is_discarded', '=', False)]",
        required=True,
        tracking=True,
    )
    job_quote_id = fields.Many2one(
        "ship.job.quote",
        string="Job Quote",
        tracking=True,
    )

    technical_incident_job_id = fields.Many2one("legis.technical.accident.job")

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.depends("start_time_of_use", "end_time_of_use")
    def _get_total_hours(self):
        for record in self:
            start_time = record.start_time_of_use
            end_time = record.end_time_of_use
            if start_time and end_time:
                record.total_hours = (end_time - start_time).total_seconds() / 3600
            else:
                record.total_hours = 0

    @api.constrains("job_quote_id", "technical_incident_job_id")
    def _only_one_receiver_relation(self):
        for record in self:
            if record.job_quote_id and record.technical_incident_job_id:
                message = "Chỉ được giao vật tư cho 1 model, liên hệ kỹ thuật!"
                raise ValidationError(message)

    @api.constrains("quantity")
    def quantity_must_be_equal_to_1_when_the_material_is_for_lifespan(self):
        for record in self:
            message = "Số lượng phải bằng 1 khi vật tư có tuổi thọ!"
            if record.material_entity_id.is_used_for_lifespan:
                if record.quantity != 1:
                    raise ValidationError(message)

    @api.constrains("material_entity_id", "quantity")
    def check_if_available_quantity_is_valid(self):
        for record in self:
            message = "Số lượng sử dụng không được vượt quá số lượng vật tư tồn tại!"
            if record.material_entity_id.available_quantity < 0:
                raise ValidationError(message)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model = "ship.material.assignment"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model)

            self.raise_if_material_entity_quantity_equal_or_less_than_0(vals)

        return super(MaterialAssignment, self).create(vals_list)

    def write(self, vals):
        self.ensure_one()
        old_material = self.material_id
        result = super(MaterialAssignment, self).write(vals)
        new_material = self.material_id

        if new_material != old_material and old_material:
            message = "Làm ơn tạo mới bản ghi, không thể thay đổi vật tư!"
            raise ValidationError(message)

        if "start_time_of_use" in vals or "end_time_of_use" in vals:
            self.material_entity_id._cacl_quantity()

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _get_technical_incident_job_by_id(self, id):
        model_name = "legis.technical.incident.job"
        return self.env[model_name].browse(id)

    def action_reset_usage_time(self):
        self.ensure_one()
        self.start_time_of_use = False
        self.end_time_of_use = False

    def start_use(self, start_date=fields.Datetime.now(), force=True):
        for record in self:
            if not record.start_time_of_use:
                record.start_time_of_use = start_date

            elif force:
                record.start_time_of_use = start_date

    def end_use(self, end_date=fields.Datetime.now(), force=True):
        for record in self:
            if not record.end_time_of_use:
                record.end_time_of_use = end_date
            elif force:
                record.end_time_of_use = end_date

    def raise_if_material_entity_quantity_equal_or_less_than_0(self, vals):
        entity_id = vals["material_entity_id"]
        if entity_id:
            entity = self.env["ship.material.entity"].browse(entity_id)
            if entity.available_quantity <= 0:
                raise ValidationError("Không thể gán cho vật tư có số lượng bằng 0")
