# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from collections import defaultdict
from odoo.exceptions import ValidationError


class HandbookRevisionReport(models.Model):
    _name = "legis.handbook.revision.report"
    _description = "Handbook revision report records"
    _inherit = ["utilities.notification"]

    meeting_date = fields.Date("Meeting date", tracking=True)
    duration = fields.Integer("Duration", tracking=True)
    place = fields.Char("Place", tracking=True)
    description = fields.Char("Description", tracking=True)
    received_date = fields.Date("Received date", tracking=True)

    # relations
    attendant_ids = fields.Many2many(
        "res.users",
        "res_users_legis_attendants_rel",
        string="Attendants",
        tracking=True,
    )

    performer_ids = fields.Many2many(
        "res.users",
        "res_users_legis_performers_rel",
        string="Responsible to follow",
        tracking=True,
    )
    chaired_by = fields.Many2one("res.users", string="Chaired by", tracking=True)
    recorder_id = fields.Many2one("res.users", string="Recorded by", tracking=True)
    approved_id = fields.Many2one("res.users", string="Approved by", tracking=True)
    receiver_id = fields.Many2one("res.users", string="Receiver", tracking=True)

    handbook_revision_report_page_ids = fields.One2many(
        "legis.content.page",
        "handbook_revision_report_id",
        string="Handbook revision report page",
        default=lambda self: self.get_default_handbook_revision_report_page_ids(),
        tracking=True,
    )

    handbook_revision_report_html = fields.Html(
        "Handbook revision report html",
        related="handbook_revision_report_page_id.content",
    )
    report_page_len = fields.Integer("Pages", compute="get_report_page_len")
    handbook_revision_report_page_id = fields.Many2one(
        "legis.content.page",
        string="Handbook revision report page",
        domain="[('id', 'in', handbook_revision_report_page_ids)]",
    )

    @api.depends(
        "handbook_revision_report_page_id", "handbook_revision_report_page_ids"
    )
    def get_report_page_len(self):
        for record in self:
            section_id = record.handbook_revision_report_page_id.id
            section_ids = record.handbook_revision_report_page_ids.ids
            if (
                record.handbook_revision_report_page_id
                and record.handbook_revision_report_page_ids
            ):
                record.report_page_len = section_ids.index(section_id) + 1
            else:
                record.report_page_len = 0

    @api.constrains(
        "handbook_revision_report_page_id", "handbook_revision_report_page_ids"
    )
    def check_consistent_section_id(self):
        for record in self:
            section_id = record.handbook_revision_report_page_id.id
            section_ids = record.handbook_revision_report_page_ids.ids

            if (
                record.handbook_revision_report_page_id
                and record.handbook_revision_report_page_ids
            ):
                if section_id not in section_ids:
                    message = "Accident Page không nhất quán, vui lòng kiểm tra lại!"
                    raise ValidationError(message)

    def move_to_next_report_page(self):
        self.ensure_one()
        section_ids = self.handbook_revision_report_page_ids.ids
        section_id = self.handbook_revision_report_page_id.id
        if section_ids and section_id:
            try:
                index = section_ids.index(section_id)
                self.handbook_revision_report_page_id = section_ids[index + 1]
            except IndexError:
                self.handbook_revision_report_page_id = section_ids[0]
        elif section_ids and not section_id:
            self.handbook_revision_report_page_id = section_ids[0]

    def move_to_prev_report_page(self):
        self.ensure_one
        section_ids = self.handbook_revision_report_page_ids.ids
        section_id = self.handbook_revision_report_page_id.id
        if section_ids and section_id:
            index = section_ids.index(section_id)
            self.handbook_revision_report_page_id = section_ids[index - 1]
        elif section_ids and not section_id:
            self.handbook_revision_report_page_id = section_ids[0]

    def get_default_handbook_revision_report_page_ids(self):
        page_ids = self._get_pages_by_meta_form()
        report_pages = self.handbook_revision_report_page_ids.create(
            [{} for _ in page_ids]
        )

        return report_pages.ids

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.handbook.revision.report"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(HandbookRevisionReport, self).create(vals_list)

        for record in result:
            record.render_html_content()

        return result

    def write(self, vals):
        self.ensure_one()

        result = super(HandbookRevisionReport, self).write(vals)
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

        return field_values

    def _get_pages_by_meta_form(self):
        meta_form = self.env["legis.meta.form"].search(
            [("form_name", "=", CONST.HANDBOOK_REVISION_REPORT)]
        )
        return meta_form.content_page_ids

    def render_html_content(self):
        self.ensure_one()
        page_ids = self._get_pages_by_meta_form()

        for i, page in enumerate(page_ids):
            handbook_revision_report_page_id = self.handbook_revision_report_page_ids[i]

            placeholders = self.get_field_values()
            handbook_revision_report_page_id.content = str(page.content).format(
                **placeholders
            )
