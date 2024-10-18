# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
import difflib
from bs4 import BeautifulSoup


class HandbookSection(models.Model):
    _name = "legis.handbook.section"
    _description = "Handbook section records"
    _inherit = ["utilities.notification"]

    control_number = fields.Char("Control number", tracking=True)
    title = fields.Char("Title", tracking=True)
    content = fields.Html("Content", tracking=True)
    modified_content = fields.Html(
        "Modified content", related="modified_section_version_id.content"
    )
    are_need_metas = fields.Boolean("Are need metas", default=False, tracking=True)
    content_old_new_diff = fields.Html("Test diff")

    # relations
    safety_management_handbook_id = fields.Many2one(
        "legis.safety.management.handbook",
        string="Safety management handbook",
        tracking=True,
    )
    handbook_parent_section_id = fields.Many2one(
        "legis.handbook.section",
        string="Handbook parent section",
        readonly=True,
        tracking=True,
    )
    handbook_child_section_ids = fields.One2many(
        "legis.handbook.section",
        "handbook_parent_section_id",
        string="Handbook child section",
        tracking=True,
    )
    modified_section_version_id = fields.Many2one(
        "legis.handbook.section",
        string="modified section version",
        readonly=True,
        tracking=True,
    )
    incidence_type_meta_ids = fields.One2many(
        "legis.incidence.type.meta",
        "handbook_section_id",
        string="Incidence type meta",
        tracking=True,
    )
    ert_role_meta_ids = fields.One2many(
        "legis.ert.role.meta",
        "handbook_section_id",
        string="Rrt role meta",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.handbook.section"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(HandbookSection, self).create(vals_list)

        for record in result:
            record.check_security()

            parent_control_number = record.handbook_parent_section_id.control_number
            if not record.control_number and parent_control_number:
                record.control_number = parent_control_number

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(HandbookSection, self).write(vals)

        if (
            "content_old_new_diff" not in vals
            and "modified_section_version_id" not in vals
        ):
            self.check_security()

        find_original_section = ("modified_section_version_id", "=", self.id)
        original_section_id = self.search([find_original_section], limit=1)
        if "content" in vals and original_section_id:
            original_section_id.get_section_old_new_diff()

        return result

    def unlink(self):
        for record in self:
            record.check_security()
        return super(HandbookSection, self).unlink()

    def check_security(self):
        self.ensure_one()
        user_has_admin_group = self.env.user.has_group("utilities.group_ship_admin")
        message = "Không được thao tác trực tiếp handbook, vui lòng chỉnh sửa vào bản copy, vui lòng liên hệ Admin!"

        if (
            self.safety_management_handbook_id
            or self.handbook_parent_section_id
            or self.modified_section_version_id
        ):
            if not user_has_admin_group:
                raise ValidationError(message)

    def name_get(self):
        result = []
        for report in self:
            name = None
            if (
                not report.safety_management_handbook_id
                and not report.handbook_parent_section_id
            ):
                name = report.title or _("New")
            else:
                name = report.ref or _("New")

            result.append((report.id, name))
        return result

    def edit_current_section(self):
        self.ensure_one()
        section_id = None
        modified_section = self.modified_section_version_id

        if modified_section:
            section_id = modified_section
        else:
            section_id = self.create(
                {
                    "control_number": self.control_number,
                    "title": self.title,
                    "content": self.content,
                }
            )
            self.modified_section_version_id = section_id

        return {
            "type": "ir.actions.act_window",
            "res_model": section_id._name,
            "view_mode": "form",
            "res_id": section_id.id,
            "target": "current",
            "context": section_id.env.context,
        }

    def recursive_action(self, something, return_result_from_somthing=False):
        self.ensure_one()

        result = something(self, return_result_from_somthing)

        # Recurse through all child sections
        for child_section in self.handbook_child_section_ids:
            child_section.recursive_action(something, result)

        return result

    def get_section_old_new_diff(self):
        self.ensure_one()
        old = self.content
        new = self.modified_section_version_id.content

        old = BeautifulSoup(old).prettify() if old else ""
        new = BeautifulSoup(new).prettify() if new else ""

        old = BeautifulSoup(old).get_text()
        new = BeautifulSoup(new).get_text()

        diff = difflib.HtmlDiff(wrapcolumn=45).make_file(
            old.splitlines(), new.splitlines()
        )
        self.content_old_new_diff = diff

    def set_ert_role_meta_ids_to_new_section(self, new_section):
        self.ensure_one()
        for meta in self.ert_role_meta_ids:
            meta.handbook_section_id = new_section

    def set_incidence_type_meta_ids_to_new_section(self, new_section):
        self.ensure_one()
        for meta in self.incidence_type_meta_ids:
            meta.handbook_section_id = new_section
