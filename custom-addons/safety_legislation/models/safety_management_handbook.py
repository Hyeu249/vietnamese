# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from ...utilities.models import CONST as UTILITIES_CONST
from odoo.exceptions import ValidationError


class SafetyManagementHandbook(models.Model):
    _name = "legis.safety.management.handbook"
    _description = "Safety management handbook records"
    _inherit = ["utilities.notification"]

    revision_no = fields.Integer("Revision no", tracking=True)
    handbook_html = fields.Html("Handbook html")

    # relations
    handbook_section_ids = fields.One2many(
        "legis.handbook.section",
        "safety_management_handbook_id",
        string="Handbook section",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.safety.management.handbook"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
            if not vals.get("revision_no"):
                vals["revision_no"] = self._increase_revision()
        result = super(SafetyManagementHandbook, self).create(vals_list)

        return result

    def _increase_revision(self):
        last_value = self.search([], limit=1, order="revision_no desc").revision_no or 0
        return last_value + 1

    def name_get(self):
        result = []
        for report in self:
            name = None
            if report.revision_no:
                if isinstance(report.revision_no, int):
                    name = f"version-{report.revision_no}"
                else:
                    name = str(report.revision_no)
            else:
                name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _get_default_value_model(self):
        model_name = "utilities.default.value"
        default_value_model = self.env[model_name].search([])

        return default_value_model

    def _get_handbook_html(self):
        default_value_model = self._get_default_value_model()
        variable_name = UTILITIES_CONST.HTML_LEGIS_SAFETY_MANAGEMENT_HANDBOOK_CONTENT
        return default_value_model._get_default_value_by_variable_name(variable_name)

    def render_handbook(self):
        self.ensure_one()

        placeholders = {
            "section_htmls": self._get_section_htmls(),
        }

        default_handbook_html = str(self._get_handbook_html())

        self.handbook_html = default_handbook_html.format(**placeholders)

    def _get_section_htmls(self):
        self.ensure_one()
        all_content = []

        for section in self.handbook_section_ids:
            section.recursive_action(self.append_all_section_contents, all_content)

        str_htmls = [str(content) for content in all_content]
        return "".join(str_htmls)

    def append_all_section_contents(self, section_id, return_result=False):
        self.ensure_one()

        if section_id.content:
            return_result.append(section_id.content)

        return return_result
