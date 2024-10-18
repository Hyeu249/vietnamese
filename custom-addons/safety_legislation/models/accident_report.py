# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from collections import defaultdict
from odoo.exceptions import ValidationError


class AccidentReport(models.Model):
    _name = "legis.accident.report"
    _description = "Accident report records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    date_of_event = fields.Date("Date of event", tracking=True)
    ship_movement = fields.Char("Ship movement", tracking=True)
    voy_no = fields.Char("Voy no", tracking=True)
    location = fields.Char("Location", tracking=True)
    weather_condition = fields.Char("Weather condition", tracking=True)
    deck_condition = fields.Char("Deck condition", tracking=True)
    lighting_condition = fields.Char("Lighting condition", tracking=True)

    damage = fields.Text("Damage", tracking=True)
    reason = fields.Text("Reason", tracking=True)
    review = fields.Text("Review", tracking=True)
    comment = fields.Text("Comment", tracking=True)

    # relations
    accident_page_ids = fields.One2many(
        "legis.content.page",
        "accident_report_id",
        string="Accident page",
        default=lambda self: self.get_default_accident_page_ids(),
        tracking=True,
    )

    accident_report_html = fields.Html(
        "Accident report html", related="accident_page_id.content"
    )
    accident_page_len = fields.Integer("Pages", compute="get_accident_page_len")
    accident_page_id = fields.Many2one(
        "legis.content.page",
        string="Accident page",
        domain="[('id', 'in', accident_page_ids)]",
    )

    @api.depends("accident_page_id", "accident_page_ids")
    def get_accident_page_len(self):
        for record in self:
            section_id = record.accident_page_id.id
            section_ids = record.accident_page_ids.ids
            if record.accident_page_id and record.accident_page_ids:
                record.accident_page_len = section_ids.index(section_id) + 1
            else:
                record.accident_page_len = 0

    @api.constrains("accident_page_id", "accident_page_ids")
    def check_consistent_section_id(self):
        for record in self:
            section_id = record.accident_page_id.id
            section_ids = record.accident_page_ids.ids

            if record.accident_page_id and record.accident_page_ids:
                if section_id not in section_ids:
                    message = "Accident Page không nhất quán, vui lòng kiểm tra lại!"
                    raise ValidationError(message)

    def move_to_next_accident_page(self):
        self.ensure_one()
        section_ids = self.accident_page_ids.ids
        section_id = self.accident_page_id.id
        if section_ids and section_id:
            try:
                index = section_ids.index(section_id)
                self.accident_page_id = section_ids[index + 1]
            except IndexError:
                self.accident_page_id = section_ids[0]
        elif section_ids and not section_id:
            self.accident_page_id = section_ids[0]

    def move_to_prev_accident_page(self):
        self.ensure_one
        section_ids = self.accident_page_ids.ids
        section_id = self.accident_page_id.id
        if section_ids and section_id:
            index = section_ids.index(section_id)
            self.accident_page_id = section_ids[index - 1]
        elif section_ids and not section_id:
            self.accident_page_id = section_ids[0]

    def get_default_accident_page_ids(self):
        page_ids = self._get_pages_by_meta_form()
        accident_pages = self.accident_page_ids.create([{} for _ in page_ids])

        return accident_pages.ids

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.accident.report"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(AccidentReport, self).create(vals_list)

        for record in result:
            record.render_html_content()

        return result

    def write(self, vals):
        self.ensure_one()

        result = super(AccidentReport, self).write(vals)
        self.render_html_content()

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def get_field_values(self):
        self.ensure_one()
        field_values = {}
        for field_name in self._fields:
            value = getattr(self, field_name)
            field_values[field_name] = value

        field_values["company_id"] = self.company_id.name

        return field_values

    def _get_pages_by_meta_form(self):
        meta_form = self.env["legis.meta.form"].search(
            [("form_name", "=", CONST.ACCIDENT_REPORT)]
        )
        return meta_form.content_page_ids

    def render_html_content(self):
        self.ensure_one()
        page_ids = self._get_pages_by_meta_form()

        for i, page in enumerate(page_ids):
            accident_page_id = self.accident_page_ids[i]

            placeholders = self.get_field_values()
            accident_page_id.content = str(page.content).format(**placeholders)
