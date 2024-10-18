# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class TechnicalIncidentReport(models.Model):
    _name = "legis.technical.incident.report"
    _description = "Technical incident report records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    # technical incident report fields
    trip = fields.Char("Trip", tracking=True)
    report_date = fields.Date("Report date", tracking=True)
    report_number = fields.Char("Report number", tracking=True)
    # for P.QLT
    assigned_cvkt = fields.Char("Assigned cvkt", tracking=True)
    director_comment_for_PQLT = fields.Char("Director comment for PQLT", tracking=True)
    # for SHIP
    department_in_charge = fields.Selection(
        CONST.DEPARTMENT_IN_CHARGE,
        string="Department in charge",
        default=CONST.MACHINERY,
        tracking=True,
    )
    maintenance_scope_ids = fields.Many2many(
        "ship.maintenance.scope", string="Maintenance scope", tracking=True
    )
    problem = fields.Char("Problem", tracking=True)
    temporary_action = fields.Char("Temporary action", tracking=True)
    recommend = fields.Char("Recommend", tracking=True)
    attachment_for_technical_incident = fields.Binary(
        "Attachment for technical incident", tracking=True
    )
    # others
    method = fields.Selection(
        CONST.TECHNICAL_INCIDENT_METHOD,
        string="Method",
        default=CONST.REPAIR_PROCESSING,
        tracking=True,
    )
    time = fields.Date("Time(waiting for materials + repair)", tracking=True)
    cost = fields.Float("Cost", tracking=True)
    origin = fields.Char("Origin", tracking=True)
    insurance = fields.Date("Insurance", tracking=True)

    # relations
    technical_incident_report_page_ids = fields.One2many(
        "legis.content.page",
        "technical_incident_report_id",
        string="Technical incident report page",
        default=lambda self: self.get_default_technical_incident_report_page_ids(),
        tracking=True,
    )

    technical_incident_report_html = fields.Html(
        "Sea Protest html", related="technical_incident_report_page_id.content"
    )
    technical_incident_report_page_len = fields.Integer(
        "Pages", compute="get_technical_incident_report_page_len"
    )
    technical_incident_report_page_id = fields.Many2one(
        "legis.content.page",
        string="Sea Protest page",
        domain="[('id', 'in', technical_incident_report_page_ids)]",
    )

    @api.depends(
        "technical_incident_report_page_id", "technical_incident_report_page_ids"
    )
    def get_technical_incident_report_page_len(self):
        for record in self:
            section_id = record.technical_incident_report_page_id.id
            section_ids = record.technical_incident_report_page_ids.ids
            if (
                record.technical_incident_report_page_id
                and record.technical_incident_report_page_ids
            ):
                record.technical_incident_report_page_len = (
                    section_ids.index(section_id) + 1
                )
            else:
                record.technical_incident_report_page_len = 0

    @api.constrains(
        "technical_incident_report_page_id", "technical_incident_report_page_ids"
    )
    def check_consistent_section_id(self):
        for record in self:
            section_id = record.technical_incident_report_page_id.id
            section_ids = record.technical_incident_report_page_ids.ids

            if (
                record.technical_incident_report_page_id
                and record.technical_incident_report_page_ids
            ):
                if section_id not in section_ids:
                    message = "Sea Protest Page không nhất quán, vui lòng kiểm tra lại!"
                    raise ValidationError(message)

    def move_to_next_technical_incident_report_page(self):
        self.ensure_one()
        section_ids = self.technical_incident_report_page_ids.ids
        section_id = self.technical_incident_report_page_id.id
        if section_ids and section_id:
            try:
                index = section_ids.index(section_id)
                self.technical_incident_report_page_id = section_ids[index + 1]
            except IndexError:
                self.technical_incident_report_page_id = section_ids[0]
        elif section_ids and not section_id:
            self.technical_incident_report_page_id = section_ids[0]

    def move_to_prev_technical_incident_report_page(self):
        self.ensure_one
        section_ids = self.technical_incident_report_page_ids.ids
        section_id = self.technical_incident_report_page_id.id
        if section_ids and section_id:
            index = section_ids.index(section_id)
            self.technical_incident_report_page_id = section_ids[index - 1]
        elif section_ids and not section_id:
            self.technical_incident_report_page_id = section_ids[0]

    def get_default_technical_incident_report_page_ids(self):
        page_ids = self._get_pages_by_meta_form()
        pages = self.technical_incident_report_page_ids.create([{} for _ in page_ids])

        return pages.ids

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.technical.incident.report"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(TechnicalIncidentReport, self).create(vals_list)

        for record in result:
            record.render_html_content()

        return result

    def write(self, vals):
        self.ensure_one()

        result = super(TechnicalIncidentReport, self).write(vals)
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
            [("form_name", "=", CONST.TECHNICAL_INCIDENT_REPORT)]
        )
        return meta_form.content_page_ids

    def render_html_content(self):
        self.ensure_one()
        page_ids = self._get_pages_by_meta_form()

        for i, page in enumerate(page_ids):
            page_id = self.technical_incident_report_page_ids[i]

            placeholders = self.get_field_values()
            page_id.content = str(page.content).format(**placeholders)
