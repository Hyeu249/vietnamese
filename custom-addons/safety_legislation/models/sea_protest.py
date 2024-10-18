# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class SeaProtest(models.Model):
    _name = "legis.sea.protest"
    _description = "Sea protest records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    imo = fields.Char("IMO", tracking=True)
    weight = fields.Float("Weight", tracking=True)
    port = fields.Char("Port", tracking=True)
    flag = fields.Char("Flag", tracking=True)
    ship_owner = fields.Char("Ship owner", tracking=True)
    address = fields.Char("Address", tracking=True)
    operator = fields.Char("Operator", tracking=True)
    statement = fields.Text("Statement", tracking=True)

    # relations
    sea_protest_page_ids = fields.One2many(
        "legis.content.page",
        "sea_protest_id",
        string="Sea protest page",
        default=lambda self: self.get_default_sea_protest_page_ids(),
        tracking=True,
    )

    sea_protest_html = fields.Html(
        "Sea Protest html", related="sea_protest_page_id.content"
    )
    sea_protest_page_len = fields.Integer("Pages", compute="get_sea_protest_page_len")
    sea_protest_page_id = fields.Many2one(
        "legis.content.page",
        string="Sea Protest page",
        domain="[('id', 'in', sea_protest_page_ids)]",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Captain",
        domain="[('id', '=', user_ids)]",
    )
    user_ids = fields.Many2many("res.users", string="Captain", compute="get_captains")

    def get_captains(self):
        for record in self:
            group_xml_id = "utilities.group_ship_captain"
            group = self.env.ref(group_xml_id, raise_if_not_found=False)
            group_id = group.id if group else None

            user_ids = self.env["res.users"].search(
                [
                    ("groups_id", "=", group_id),
                    ("company_ids", "=", record.company_id.id),
                ]
            )

            if user_ids:
                record.user_ids = user_ids.ids
            else:
                record.user_ids = False

    @api.depends("sea_protest_page_id", "sea_protest_page_ids")
    def get_sea_protest_page_len(self):
        for record in self:
            section_id = record.sea_protest_page_id.id
            section_ids = record.sea_protest_page_ids.ids
            if record.sea_protest_page_id and record.sea_protest_page_ids:
                record.sea_protest_page_len = section_ids.index(section_id) + 1
            else:
                record.sea_protest_page_len = 0

    @api.constrains("sea_protest_page_id", "sea_protest_page_ids")
    def check_consistent_section_id(self):
        for record in self:
            section_id = record.sea_protest_page_id.id
            section_ids = record.sea_protest_page_ids.ids

            if record.sea_protest_page_id and record.sea_protest_page_ids:
                if section_id not in section_ids:
                    message = "Sea Protest Page không nhất quán, vui lòng kiểm tra lại!"
                    raise ValidationError(message)

    def move_to_next_sea_protest_page(self):
        self.ensure_one()
        section_ids = self.sea_protest_page_ids.ids
        section_id = self.sea_protest_page_id.id
        if section_ids and section_id:
            try:
                index = section_ids.index(section_id)
                self.sea_protest_page_id = section_ids[index + 1]
            except IndexError:
                self.sea_protest_page_id = section_ids[0]
        elif section_ids and not section_id:
            self.sea_protest_page_id = section_ids[0]

    def move_to_prev_sea_protest_page(self):
        self.ensure_one
        section_ids = self.sea_protest_page_ids.ids
        section_id = self.sea_protest_page_id.id
        if section_ids and section_id:
            index = section_ids.index(section_id)
            self.sea_protest_page_id = section_ids[index - 1]
        elif section_ids and not section_id:
            self.sea_protest_page_id = section_ids[0]

    def get_default_sea_protest_page_ids(self):
        page_ids = self._get_pages_by_meta_form()
        pages = self.sea_protest_page_ids.create([{} for _ in page_ids])

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
            model_name = "legis.sea.protest"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(SeaProtest, self).create(vals_list)

        for record in result:
            record.render_html_content()

        return result

    def write(self, vals):
        self.ensure_one()

        result = super(SeaProtest, self).write(vals)
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
            [("form_name", "=", CONST.SEA_PROTEST)]
        )
        return meta_form.content_page_ids

    def render_html_content(self):
        self.ensure_one()
        page_ids = self._get_pages_by_meta_form()

        for i, page in enumerate(page_ids):
            page_id = self.sea_protest_page_ids[i]

            placeholders = self.get_field_values()
            page_id.content = str(page.content).format(**placeholders)
