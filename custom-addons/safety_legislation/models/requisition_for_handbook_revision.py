# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from ...utilities.models import CONST as UTILITIES_CONST
from odoo.exceptions import ValidationError


class RequisitionForHandbookRevision(models.Model):
    _name = "legis.requisition.for.handbook.revision"
    _description = "Requisition for handbook revision records"
    _inherit = ["utilities.required.all.approval"]

    note = fields.Text(string="Note", tracking=True)
    is_hide_content_old_new_diff = fields.Boolean(
        string="Is hide content old new diff",
        default=True,
        tracking=True,
    )
    requisition_html = fields.Html(
        "Requisition html",
        default=lambda self: self._get_request_html(),
    )

    # relations
    required_all_approval_group_ids = fields.Many2many(
        "utilities.required.all.approval.group",
        compute="get_required_all_approval_group_ids",
    )

    @api.depends("this_all_approval_group_id")
    def get_required_all_approval_group_ids(self):
        for record in self:
            group_id = record.this_all_approval_group_id
            record.required_all_approval_group_ids = (
                group_id.required_all_approval_group_ids.ids
            )

    changed_content_of_handbook_ids = fields.One2many(
        "legis.changed.content.of.handbook",
        "requisition_for_handbook_revision_id",
        string="Requisition for handbook revision",
        tracking=True,
    )
    editing_request_for_handbook_id = fields.Many2one(
        "legis.editing.request.for.handbook",
        string="Editing request for handbook",
        tracking=True,
    )
    safety_management_handbook_id = fields.Many2one(
        "legis.safety.management.handbook",
        related="editing_request_for_handbook_id.safety_management_handbook_id",
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.requisition.for.handbook.revision"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(RequisitionForHandbookRevision, self).create(vals_list)

        for record in result:
            record._create_this_all_approval_group(and_implement=False)
            record.get_changed_content_of_handbook()
            record.render_report()

        return result

    def write(self, vals):
        self.ensure_one()

        result = super(RequisitionForHandbookRevision, self).write(vals)

        if "requisition_html" not in vals:
            self.render_report()

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def get_changed_content_of_handbook(self):
        self.ensure_one()
        handbook_id = self.safety_management_handbook_id

        self.changed_content_of_handbook_ids.unlink()
        for section in handbook_id.handbook_section_ids:
            section.recursive_action(
                self.create_changed_content_of_handbook_based_on_modified_section_version
            )

    def create_changed_content_of_handbook_based_on_modified_section_version(
        self, section_id, return_result=False
    ):
        self.ensure_one()
        modified_version_id = section_id.modified_section_version_id

        if modified_version_id:
            self.create_changed_content_of_handbook(section_id, modified_version_id)

    def create_changed_content_of_handbook(self, existing_content_id, change_to_id):
        self.ensure_one()
        self.env["legis.changed.content.of.handbook"].create(
            {
                "requisition_for_handbook_revision_id": self.id,
                "control_number": existing_content_id.control_number,
                "existing_handbook_section_content_id": existing_content_id.id,
                "handbook_section_change_to_id": change_to_id.id,
            }
        )

    def _get_default_value_model(self):
        model_name = "utilities.default.value"
        default_value_model = self.env[model_name].search([])

        return default_value_model

    def _get_request_html(self):
        default_value_model = self._get_default_value_model()
        variable_name = UTILITIES_CONST.HTML_LEGIS_REQUISITION_FOR_HANDBOOK_REVISION
        return default_value_model._get_default_value_by_variable_name(variable_name)

    def render_report(self):
        self.ensure_one()

        default_handbook_html = str(self._get_request_html())

        content_htmls = (
            self.changed_content_of_handbook_ids.get_tr_changed_content_htmls()
        )
        new_string = default_handbook_html.replace("</tr>", "</tr>" + content_htmls)

        self.requisition_html = new_string
