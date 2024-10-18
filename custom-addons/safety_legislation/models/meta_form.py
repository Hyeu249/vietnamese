# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class MetaForm(models.Model):
    _name = "legis.meta.form"
    _description = "Serious accident records"
    _inherit = ["utilities.notification"]

    form_name = fields.Selection(
        CONST.FORM_NAME,
        string="Form name",
        default=CONST.ACCIDENT_REPORT,
        required=True,
        tracking=True,
    )

    # relations
    content_page_ids = fields.One2many(
        "legis.content.page",
        "meta_form_id",
        string="Content page",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        return super(MetaForm, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.form_name or _("New")
            result.append((report.id, name))
        return result


class ContentPage(models.Model):
    _name = "legis.content.page"
    _description = "Serious accident records"
    _inherit = ["utilities.notification"]

    content = fields.Html("Content", tracking=True)

    # relations
    meta_form_id = fields.Many2one(
        "legis.meta.form",
        string="Meta form",
        tracking=True,
    )

    # accident report
    accident_report_id = fields.Many2one(
        "legis.accident.report",
        string="Accident report",
        tracking=True,
    )

    # investigative report
    investigative_report_id = fields.Many2one(
        "legis.investigative.report",
        string="Accident report",
        tracking=True,
    )

    # sea protest
    sea_protest_id = fields.Many2one(
        "legis.sea.protest",
        string="Sea protest",
        tracking=True,
    )

    # team checklist
    team_checklist_id = fields.Many2one(
        "legis.team.checklist",
        string="Team checklist report",
        tracking=True,
    )

    # technical incident report
    technical_incident_report_id = fields.Many2one(
        "legis.technical.incident.report",
        string="Technical incident report",
        tracking=True,
    )

    # handbook revision report
    handbook_revision_report_id = fields.Many2one(
        "legis.handbook.revision.report",
        string="Handbook revision report",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        return super(ContentPage, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = "{form_name}({report_id})".format(
                form_name=report.meta_form_id.form_name, report_id=report.id
            )
            name = name or _("New")
            result.append((report.id, name))
        return result
