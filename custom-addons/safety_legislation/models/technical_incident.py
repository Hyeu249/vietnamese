# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ...utilities.models import CONST as UTILITIES_CONST
from . import CONST
from odoo.exceptions import ValidationError
import logging


class MaintenanceScopeReport(models.Model):
    _inherit = "ship.maintenance.scope.report"

    technical_incident_id = fields.Many2one("legis.technical.incident")


class MaterialPaintQuotesRequest(models.Model):
    _inherit = "ship.material.paint.quotes.request"

    technical_incident_id = fields.Many2one("legis.technical.incident")


class TechnicalIncident(models.Model):
    _name = "legis.technical.incident"
    _description = "Sự cố kỹ thuật"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    finished_at = fields.Date("Finished at", tracking=True)
    repair_status = fields.Selection(
        CONST.REPAIR_STATUS,
        string="Repair status",
        default=CONST.PENDING,
        required=True,
        tracking=True,
    )

    is_insurace_involved = fields.Boolean("Is insurace involved", tracking=True)
    is_noti_for_legal_department = fields.Boolean("is noti for legal department")
    insurance_deductible_cost = fields.Float("Insurance deductible cost", tracking=True)
    total_price = fields.Float("Total price", compute="_get_total_price", tracking=True)
    warning_text = fields.Char(
        "warning_text", compute="_get_warning_text", tracking=True
    )

    help = fields.Char(
        "Help",
        readonly=True,
        tracking=True,
        help="""
        1.Thuyền trưởng lập form 0405 và kháng nghị hàng hải
        2.Thuyền trường chọn trạng thái có thể sửa và không thể sửa cho sự cố
        ------------------------------
        Có thể sửa:
        1.Thuyền trưởng điền tên các công việc
        2.Trình duyệt lên Trưởng kỹ thuật(form 0405, kháng nghị hàng hải, các công việc)
        3.Trưởng kỹ thuật đánh giá, và đưa lên Trưởng phòng quản lý tàu
        4.Trưởng phòng quản lý tàu có quyền duyệt thẳng và đóng sự cố kỹ thuật
        5.Nếu cần được xem xét thêm, TP.QLT đưa lên cấp cao hơn DPA và CEO.
        ------------------------------
        Không thể sửa:
        1.Thuyền trưởng tạo báo cáo sửa chữa, hoặc yêu cầu vật tư(cho đơn vị ngoài thực hiện)
        2.Khi có tổng giá, phần mềm thông báo đến Trưởng pháp chế
        3.Trưởng pháp chế điền mức khấu trừ
        4.Phần mềm so sánh mức khấu trừ, để gợi ý Trưởng pháp chế mời bảo hiểm
        5.Đóng sự cố nếu không mời
        6.Nếu có mời bảo hiểm, phần mềm triển khai luồng duyệt đồng thời để quyết định có mời bảo hiểm hay không
        7.Nếu quyết định là có, phần mềm gửi mail qua bên bảo hiểm
        8.Trưởng pháp chế upload kết quả đàm phán với bên bảo hiểm + hồ sơ thanh toán + đề nghị thanh toán lên trên phần mềm
        9.Trưởng phòng quản lý tàu(thay kế toán) xác nhận ở phần mềm rằng đã nhận tiền từ bảo hiểm
        10.Đóng sự cố.

        *Lưu ý: các form báo cáo có thể được xuất
    """,
    )

    @api.depends("maintenance_scope_report_ids", "material_paint_quotes_request_ids")
    def _get_total_price(self):
        for record in self:
            if not record.are_all_reports_and_requests_approved():
                record.total_price = 0
            else:
                requests = record.material_paint_quotes_request_ids
                report_prices = record.maintenance_scope_report_ids.mapped(
                    "total_price"
                )
                request_prices = requests.mapped("total_prices")
                record.total_price = sum(report_prices + request_prices)

                if not record.is_noti_for_legal_department:
                    record._noti_for_legal_department()

    @api.depends("total_price", "insurance_deductible_cost")
    def _get_warning_text(self):
        for record in self:
            if record.insurance_deductible_cost >= record.total_price:
                record.warning_text = "Tổng giá ổn định"
            elif not record.technical_incident_insurance_ids:
                record.warning_text = "Yêu cầu PCAT xem xét mời bảo hiểm"
            elif record.insurance_approval_status == UTILITIES_CONST.APPROVED:
                record.warning_text = "Bảo hiểm đã được chấp thuận"
            elif record.insurance_approval_status == UTILITIES_CONST.PENDING:
                record.warning_text = "Bảo hiểm đang được phê duyệt"
            else:
                record.warning_text = "Bảo hiểm đã bị hủy"

    def _noti_for_legal_department(self):
        self.ensure_one()
        group_xml_id = "group_ship_head_of_legal"
        classes = "technical_incident_color"
        subject = f"Gợi ý bảo hiểm cho sự cố kỹ thuật!"
        body = f"Bản ghi {self.ref} cần yêu cầu bảo hiểm!"
        company_id = self.company_id

        self._send_notification_by_group_xml_and_company_id(
            group_xml_id, company_id, subject, body, classes
        )
        self.is_noti_for_legal_department = True

    def are_all_reports_and_requests_approved(
        self, at_least_one_report_or_request=False
    ):
        self.ensure_one()
        requests = self.material_paint_quotes_request_ids
        reports = self.maintenance_scope_report_ids
        approved_requests = requests.filtered(lambda e: e._is_approved_request())
        approved_reports = reports.filtered(lambda e: e._is_approved_report())
        requests_len = len(requests)
        reports_len = len(reports)
        approved_requests_len = len(approved_requests)
        approved_reports_len = len(approved_reports)
        have_one_report = reports_len >= 1
        have_one_request = requests_len >= 1
        at_least_one_report_or_request = have_one_report or have_one_request

        if (
            requests_len == approved_requests_len
            and reports_len == approved_reports_len
            and at_least_one_report_or_request
        ):
            return True
        else:
            return False

    # related
    name_for_noti = fields.Char(
        related="technical_incident_report_id.problem",
        string="Problem",
    )

    # relations
    sea_protest_id = fields.Many2one(
        "legis.sea.protest",
        default=lambda self: self.env["legis.sea.protest"].create({}),
        tracking=True,
    )
    technical_incident_report_id = fields.Many2one(
        "legis.technical.incident.report",
        default=lambda self: self.env["legis.technical.incident.report"].create({}),
        tracking=True,
    )
    technical_incident_job_ids = fields.One2many(
        "legis.technical.incident.job",
        "technical_incident_id",
        string="Technical incident job",
        tracking=True,
    )
    technical_incident_insurance_ids = fields.One2many(
        "legis.technical.incident.insurance",
        "technical_incident_id",
        string="Technical incident insurance",
        tracking=True,
    )

    insurance_approval_status = fields.Char(
        compute="_get_insurance_approval_status",
    )

    @api.depends("technical_incident_insurance_ids")
    def _get_insurance_approval_status(self):
        for record in self:
            insurance_ids = record.technical_incident_insurance_ids
            if insurance_ids:
                insurance_id = insurance_ids[0]
                record.insurance_approval_status = (
                    insurance_id.approval_status_for_all_approval
                )
            else:
                record.insurance_approval_status = False

    @api.constrains("technical_incident_insurance_ids")
    def only_1_technical_incident_insurance(self):
        for record in self:
            if len(record.technical_incident_insurance_ids) > 1:
                message = "Chỉ có 1 bảo hiểm!"
                raise ValidationError(message)

    maintenance_scope_report_ids = fields.One2many(
        "ship.maintenance.scope.report",
        "technical_incident_id",
        string="Maintenance scope report",
        tracking=True,
    )

    material_paint_quotes_request_ids = fields.One2many(
        "ship.material.paint.quotes.request",
        "technical_incident_id",
        string="Material paint quotes request",
        tracking=True,
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.technical.incident"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(TechnicalIncident, self).create(vals_list)

        for record in result:
            record._on_off_approvals_base_on_conditions()

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(TechnicalIncident, self).write(vals)

        if self.are_only_approval_fields_changed(vals):
            return result

        if "repair_status" in vals:
            self._on_off_approvals_base_on_conditions()

        return result

    def _on_off_approvals_base_on_conditions(self):
        self.ensure_one()
        if self.repair_status == CONST.PENDING:
            self._off_approval()

        elif self.repair_status == CONST.FIXABLE:
            self._on_approval()

        elif self.repair_status == CONST.UNFIXABLE:
            self._off_approval()

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

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

    def edit_technical_incident_report(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "legis.technical.incident.report",
            "view_mode": "form",
            "res_id": self.technical_incident_report_id.id,
            "target": "current",
            "context": self.env.context,
        }

    def edit_technical_incident_insurance(self):
        self.ensure_one()
        insurance_ids = self.technical_incident_insurance_ids

        if insurance_ids:
            insurance_id = insurance_ids[0]
            return {
                "type": "ir.actions.act_window",
                "res_model": "legis.technical.incident.insurance",
                "view_mode": "form",
                "res_id": insurance_id.id,
                "target": "current",
                "context": self.env.context,
            }

    def create_technical_incident_insurance(self):
        self.ensure_one()
        self.env["legis.technical.incident.insurance"].create(
            {"technical_incident_id": self.id}
        )
