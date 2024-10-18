# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class TeamChecklist(models.Model):
    _name = "legis.team.checklist"
    _description = "Team checklist report records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    accident_date = fields.Date("Accident date", tracking=True)
    accident_type = fields.Char("Accident type", tracking=True)
    location = fields.Char("Location", tracking=True)
    current_condition = fields.Char("Current condition", tracking=True)
    distance_to_shore = fields.Char("Distance to shore", tracking=True)
    agency_notified = fields.Char("Agency notified", tracking=True)
    direction_and_speed = fields.Char("Direction and speed", tracking=True)
    number_people = fields.Char("Number people", tracking=True)
    death_injury = fields.Char("Death injury", tracking=True)
    ship_damage = fields.Char("Ship damage", tracking=True)
    other_ship_damage = fields.Char("Other ship damage", tracking=True)
    stability_condition = fields.Char("Stability condition", tracking=True)
    type_of_good = fields.Char("Type of good", tracking=True)
    quantity_of_good = fields.Char("Quantity of good", tracking=True)
    is_pollute = fields.Char("Is pollute", tracking=True)
    amount_of_pollution = fields.Char("Amount of pollution", tracking=True)
    pollution_risk = fields.Char("Pollution risk", tracking=True)
    are_charts_intact = fields.Char("Are charts intact", tracking=True)
    is_ECDIS_retained = fields.Char("Is ECDIS retained?", tracking=True)
    is_VDR_saved = fields.Char("Is VDR saved?", tracking=True)
    current_weather = fields.Char("Current weather", tracking=True)
    weather_forecast = fields.Char("Weather forecast", tracking=True)
    local_tide_infomation = fields.Char("Local tide infomation", tracking=True)
    local_sunsire_or_sunset_time = fields.Char(
        "Local sunsire or sunset time", tracking=True
    )
    action_taken = fields.Char("Action taken", tracking=True)
    action_to_be_taken = fields.Char("Action to be_taken", tracking=True)
    radio_station = fields.Char("Radio station", tracking=True)
    phone_contact = fields.Char("Phone contact", tracking=True)
    will_ship_call_back = fields.Char("Will ship call back", tracking=True)
    time_ship_will_call_back = fields.Char("Time ship will call back", tracking=True)
    office_phone = fields.Char("Office phone", tracking=True)
    contact_schedule = fields.Char("Contact schedule", tracking=True)

    # relations
    team_checklist_page_ids = fields.One2many(
        "legis.content.page",
        "team_checklist_id",
        string="Team checklist page",
        default=lambda self: self.get_default_team_checklist_page_ids(),
        tracking=True,
    )

    team_checklist_html = fields.Html(
        "Team Checklist html", related="team_checklist_page_id.content"
    )
    team_checklist_page_len = fields.Integer(
        "Pages", compute="get_team_checklist_page_len"
    )
    team_checklist_page_id = fields.Many2one(
        "legis.content.page",
        string="Team Checklist page",
        domain="[('id', 'in', team_checklist_page_ids)]",
    )

    @api.depends("team_checklist_page_id", "team_checklist_page_ids")
    def get_team_checklist_page_len(self):
        for record in self:
            section_id = record.team_checklist_page_id.id
            section_ids = record.team_checklist_page_ids.ids
            if record.team_checklist_page_id and record.team_checklist_page_ids:
                record.team_checklist_page_len = section_ids.index(section_id) + 1
            else:
                record.team_checklist_page_len = 0

    @api.constrains("team_checklist_page_id", "team_checklist_page_ids")
    def check_consistent_section_id(self):
        for record in self:
            section_id = record.team_checklist_page_id.id
            section_ids = record.team_checklist_page_ids.ids

            if record.team_checklist_page_id and record.team_checklist_page_ids:
                if section_id not in section_ids:
                    message = (
                        "Team Checklist Page không nhất quán, vui lòng kiểm tra lại!"
                    )
                    raise ValidationError(message)

    def move_to_next_team_checklist_page(self):
        self.ensure_one()
        section_ids = self.team_checklist_page_ids.ids
        section_id = self.team_checklist_page_id.id
        if section_ids and section_id:
            try:
                index = section_ids.index(section_id)
                self.team_checklist_page_id = section_ids[index + 1]
            except IndexError:
                self.team_checklist_page_id = section_ids[0]
        elif section_ids and not section_id:
            self.team_checklist_page_id = section_ids[0]

    def move_to_prev_team_checklist_page(self):
        self.ensure_one
        section_ids = self.team_checklist_page_ids.ids
        section_id = self.team_checklist_page_id.id
        if section_ids and section_id:
            index = section_ids.index(section_id)
            self.team_checklist_page_id = section_ids[index - 1]
        elif section_ids and not section_id:
            self.team_checklist_page_id = section_ids[0]

    def get_default_team_checklist_page_ids(self):
        page_ids = self._get_pages_by_meta_form()
        pages = self.team_checklist_page_ids.create([{} for _ in page_ids])

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
            model_name = "legis.team.checklist"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(TeamChecklist, self).create(vals_list)

        for record in result:
            record.render_html_content()

        return result

    def write(self, vals):
        self.ensure_one()

        result = super(TeamChecklist, self).write(vals)
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
            [("form_name", "=", CONST.EMERGENCY_RESPONSE_TEAM_CHECKLIST)]
        )
        return meta_form.content_page_ids

    def render_html_content(self):
        self.ensure_one()
        page_ids = self._get_pages_by_meta_form()

        for i, page in enumerate(page_ids):
            page_id = self.team_checklist_page_ids[i]

            placeholders = self.get_field_values()
            page_id.content = str(page.content).format(**placeholders)
