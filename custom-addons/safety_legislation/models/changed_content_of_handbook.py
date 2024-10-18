# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
import difflib
from difflib import Differ
from bs4 import BeautifulSoup
from odoo.exceptions import ValidationError
import logging


class ChangedContentOfHandbook(models.Model):
    _name = "legis.changed.content.of.handbook"
    _description = "Changed Content Of Handbook records"
    _inherit = ["utilities.notification"]

    control_number = fields.Char(string="control number", tracking=True)
    revision_state = fields.Selection(
        [
            (CONST.APPROVED_HANDBOOK_SECTION_VERSION, "Approved"),
            (CONST.REJECTED_HANDBOOK_SECTION_VERSION, "Rejected"),
            (CONST.PENDING_HANDBOOK_SECTION_VERSION, "Pending"),
        ],
        string="Revision state",
        default=CONST.PENDING_HANDBOOK_SECTION_VERSION,
        required=True,
        tracking=True,
    )
    existing_content = fields.Html(
        string="Existing content",
        compute="existing_handbook_section_content_id_content",
        tracking=True,
    )
    change_to = fields.Html(
        string="Change to",
        compute="handbook_section_change_to_id_content",
        tracking=True,
    )
    content_old_new_diff = fields.Html(
        string="Content old new diff",
        related="existing_handbook_section_content_id.content_old_new_diff",
        store=True,
        tracking=True,
    )
    is_hide_content_old_new_diff = fields.Boolean(
        string="Is hide content old new diff",
        related="requisition_for_handbook_revision_id.is_hide_content_old_new_diff",
        tracking=True,
    )
    note = fields.Char(string="Note", tracking=True)

    # relations
    requisition_for_handbook_revision_id = fields.Many2one(
        "legis.requisition.for.handbook.revision",
        string="Requisition for handbook revision",
        tracking=True,
    )
    existing_handbook_section_content_id = fields.Many2one(
        "legis.handbook.section",
        string="Existing handbook section content",
        readonly=True,
        tracking=True,
    )
    handbook_section_change_to_id = fields.Many2one(
        "legis.handbook.section",
        string="Handbook section change to",
        readonly=True,
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.changed.content.of.handbook"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(ChangedContentOfHandbook, self).create(vals_list)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    @api.depends("existing_handbook_section_content_id")
    def existing_handbook_section_content_id_content(self):
        for record in self:
            dif_content = record.get_diff_html_content()
            lines = record.filter_minus_lines(dif_content)
            record.existing_content = "".join(
                [
                    f"<div style='background-color:#ffaaaa; {'margin-bottom:10px;' if index != len(lines) - 1 else '' }'>{line}</div>"
                    for index, line in enumerate(lines)
                ]
            )

    @api.depends("handbook_section_change_to_id")
    def handbook_section_change_to_id_content(self):
        for record in self:
            dif_content = record.get_diff_html_content()
            lines = record.filter_plus_lines(dif_content)
            record.change_to = "".join(
                [
                    f"<div style='background-color:#aaffaa; {'margin-bottom:10px;' if index != len(lines) - 1 else '' }'>{line}</div>"
                    for index, line in enumerate(lines)
                ]
            )

    def get_diff_html_content(self):
        self.ensure_one()
        old = self.existing_handbook_section_content_id.content
        new = self.handbook_section_change_to_id.content

        old = BeautifulSoup(old).prettify() if old else ""
        new = BeautifulSoup(new).prettify() if new else ""

        old = BeautifulSoup(old).get_text()
        new = BeautifulSoup(new).get_text()

        old = old.splitlines()
        new = new.splitlines()

        old = self.remove_non_text_leading(old)
        new = self.remove_non_text_leading(new)

        dif = Differ()

        return list(dif.compare(old, new))

    def remove_non_text_leading(self, lines):
        for index, line in enumerate(lines):
            line = line.strip()
            for letter in line:
                if letter in ["-", "+", " "]:
                    line = line.replace(letter, "", 1)
                else:
                    break
            lines[index] = line

        lines = [item.strip() for item in lines if item.strip()]
        return lines

    def filter_plus_lines(self, lines):
        filtered_lines = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("+"):
                filtered_lines.append(stripped_line)
        return filtered_lines

    def filter_minus_lines(self, lines):
        filtered_lines = []
        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("-"):
                filtered_lines.append(stripped_line)
        return filtered_lines

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

    def get_tr_changed_content_htmls(self):
        tr_arr = [record.changed_content_html() for record in self]

        return "".join(tr_arr)

    def changed_content_html(self):
        self.ensure_one()
        status = None
        if self.revision_state == CONST.PENDING_HANDBOOK_SECTION_VERSION:
            status = "Pending"
        if self.revision_state == CONST.APPROVED_HANDBOOK_SECTION_VERSION:
            status = "Approved"
        if self.revision_state == CONST.REJECTED_HANDBOOK_SECTION_VERSION:
            status = "Rejected"

        return f"""
            <tr>
                <td><p>{self.control_number}</p></td>
                <td><p>{status}</p></td>
                <td><p>{self.existing_content}</p></td>
                <td><p>{self.change_to}</p></td>
                <td><p>{self.note}</p></td>
            </tr>
        """
