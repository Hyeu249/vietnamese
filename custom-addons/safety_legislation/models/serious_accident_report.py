# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class SeriousAccidentReport(models.Model):
    _name = "legis.serious.accident.report"
    _description = "Serious accident records"
    _inherit = ["utilities.approval.status"]

    _check_company_auto = True

    description = fields.Html(
        "Description", related="serious_accident_id.description", tracking=True
    )
    is_completed = fields.Boolean("Is completed", tracking=True)
    help = fields.Char(
        "Help",
        readonly=True,
        tracking=True,
        help="""
        1.thuyền trưởng vào phần mềm, để chọn tai nạn nghiêm trọng và liên lạc
        2.thuyền trưởng lập báo cáo 0402, 1928 và kháng nghị hàng hải
        3.trình duyệt DPA
        4.DPA tập hợp đội sự cố ERT(tự động có thông báo đến ERT)
        5.DPA lập form 1927
        6.ERT thực hiện các công việc của mình(có view tổng thể)
        7.DPA hoặc giám đốc duyệt hoàn thành sự cố          
    """,
    )

    # relations
    serious_accident_id = fields.Many2one(
        "legis.serious.accident",
        string="Serious accident",
        tracking=True,
    )
    accident_report_id = fields.Many2one(
        "legis.accident.report",
        default=lambda self: self.env["legis.accident.report"].create({}),
        tracking=True,
    )

    investigative_report_id = fields.Many2one(
        "legis.investigative.report",
        default=lambda self: self.env["legis.investigative.report"].create({}),
        tracking=True,
    )
    sea_protest_id = fields.Many2one(
        "legis.sea.protest",
        default=lambda self: self.env["legis.sea.protest"].create({}),
        tracking=True,
    )
    team_checklist_id = fields.Many2one(
        "legis.team.checklist",
        default=lambda self: self.env["legis.team.checklist"].create({}),
        tracking=True,
    )

    serious_accident_team_ids = fields.One2many(
        "legis.serious.accident.team",
        "serious_accident_report_id",
        string="Serious accident team",
        tracking=True,
    )
    serious_accident_team_len = fields.Integer(
        "serious_accident_team_len", compute="get_serious_accident_team_len"
    )

    @api.depends("serious_accident_team_ids")
    def get_serious_accident_team_len(self):
        for record in self:
            record.serious_accident_team_len = len(record.serious_accident_team_ids)

    # accident report

    # investigative report

    # sea protest report

    # team checklist report

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.serious.accident.report"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(SeriousAccidentReport, self).create(vals_list)

        return result

    def name_get(self):
        result = []
        for report in self:
            accident_name = report.serious_accident_id.name or _("New")
            name = accident_name + "(" + report.ref + ")"
            result.append((report.id, name))
        return result

    def edit_accident_report(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "legis.accident.report",
            "view_mode": "form",
            "res_id": self.accident_report_id.id,
            "target": "current",
            "context": self.env.context,
        }

    def edit_investigative_report(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "legis.investigative.report",
            "view_mode": "form",
            "res_id": self.investigative_report_id.id,
            "target": "current",
            "context": self.env.context,
        }

    def edit_sea_protest(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "legis.sea.protest",
            "view_mode": "form",
            "res_id": self.sea_protest_id.id,
            "target": "current",
            "context": self.env.context,
        }

    def edit_team_checklist(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "legis.team.checklist",
            "view_mode": "form",
            "res_id": self.team_checklist_id.id,
            "target": "current",
            "context": self.env.context,
        }

    def ert_assemble(self):
        self.ensure_one()
        ert_team = self.env["legis.ert.role.meta"].search([])
        context = dict(self.env.context)

        if not self.serious_accident_team_ids:
            for ert in ert_team:
                context.update({"default_tasks_by_ert_id": ert.id})
                self.with_context(context).serious_accident_team_ids.create(
                    {
                        "serious_accident_report_id": self.id,
                        "ert_role_meta_id": ert.id,
                    }
                )

    def open_ert_tree_view(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Tree View",
            "view_type": "kanban",
            "view_mode": "kanban,tree,form",
            "res_model": "legis.serious.accident.task",
            "target": "current",
            "domain": [("serious_accident_report_id", "=", self.id)],
        }
