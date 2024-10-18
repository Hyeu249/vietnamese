# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
from datetime import datetime
from io import BytesIO

import openpyxl

from odoo import api, fields, models, _
from . import CONST
from ...utilities.models import CONST as CONST_UTILITIES
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta

SAMPLE_EQUIPMENT_SURVEY_DATA_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTX9qUEiRY8C2iNoHCZIA5XY2CjY_I8zeu5xxm3-7nsIggxodHRyBu9zH--JZPXzTJcafW8HbIb3r4y/pub?output=xlsx'

class DockingPlain(models.Model):
    _name = "docking.docking.plan"
    _description = "Docking plain records"
    _inherit = ["ship.date", "utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)
    date = fields.Date("Date", tracking=True)
    location = fields.Char("Location", tracking=True)
    start_date = fields.Date("Start date", tracking=True)
    end_date = fields.Date("End date", tracking=True)
    expected_start_date = fields.Date(
        "Expected start date",
        default=lambda self: self._get_expected_start_date(),
        required=True,
        tracking=True,
    )
    expected_end_date = fields.Date("Expected end date", tracking=True)
    supplier_emails = fields.Char(
        "Supplier emails", compute="_get_supplier_emails", store=True, tracking=True
    )
    is_allow_create_report = fields.Boolean(
        "Is allow create report", compute="_calc_is_allow_create_report"
    )
    is_completed = fields.Boolean("Is completed", readonly=True, tracking=True)
    is_3_months_noti_off = fields.Boolean("Is 3 months noti off", tracking=True)
    is_6_months_noti_off = fields.Boolean("Is 6 months noti off", tracking=True)
    inspection_event_len = fields.Integer(
        "Inspection event len", compute="_get_inspection_event_len", tracking=True
    )

    # Temporary field to upload equipment survey data for importing
    import_equipment_survey_data = fields.Binary(
        "Import equipment survey data",
        attachment=False
    )

    # relations
    equipment_survey_data_ids = fields.One2many(
        "docking.equipment.survey.data",
        "docking_plan_id",
        string="Equipment survey data",
        tracking=True,
    )
    material_survey_data_ids = fields.One2many(
        "docking.material.survey.data",
        "docking_plan_id",
        string="Material survey data",
        tracking=True,
    )
    expected_cost_report_ids = fields.One2many(
        "docking.expected.cost.report",
        "docking_plan_id",
        string="Expected cost report",
        tracking=True,
    )
    cost_settlement_report_ids = fields.One2many(
        "docking.cost.settlement.report",
        "docking_plan_id",
        string="Cost Settlement Report",
        tracking=True,
    )
    material_quote_request_ids = fields.One2many(
        "docking.material.quote.request",
        "docking_plan_id",
        string="Material quote request",
        tracking=True,
    )
    job_quote_request_ids = fields.One2many(
        "docking.job.quote.request",
        "docking_plan_id",
        string="Job quote request",
        tracking=True,
    )
    inspection_event_ids = fields.One2many(
        "docking.inspection.event",
        "docking_plan_id",
        string="Inspection event",
        tracking=True,
    )
    contract_ids = fields.One2many(
        "docking.contract",
        "docking_plan_id",
        string="Contract",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.constrains("is_completed")
    def only_1_uncompleted_docking_plan(self):
        for record in self:
            uncompleted_plans = self.search(
                [
                    ("id", "!=", record.id),
                    ("is_completed", "=", False),
                ]
            )
            if uncompleted_plans:
                message = "Docking Plan cũ chưa được hoàn thành, không thể tạo mới!"
                raise ValidationError(message)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("docking.docking.plan")
        result = super(DockingPlain, self).create(vals_list)

        for record in result:
            record._create_default_survey_datas()
        return result

    def unlink(self):
        for record in self:
            record.equipment_survey_data_ids.unlink()
            record.material_survey_data_ids.unlink()
            record.expected_cost_report_ids.unlink()
            record.cost_settlement_report_ids.unlink()
            record.material_quote_request_ids.unlink()
            record.job_quote_request_ids.unlink()
            record.inspection_event_ids.unlink()
        return super(DockingPlain, self).unlink()

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result

    def action_propose_material_surveys(self):
        self.ensure_one()
        for survey in self.material_survey_data_ids:
            survey.action_propose()

    def action_unpropose_material_surveys(self):
        self.ensure_one()
        for survey in self.material_survey_data_ids:
            survey.action_unpropose()

    def action_approve_material_surveys(self):
        self.ensure_one()
        for survey in self.material_survey_data_ids:
            survey.action_approve()

    def action_reject_material_surveys(self):
        self.ensure_one()
        for survey in self.material_survey_data_ids:
            survey.action_reject()

    @api.depends(
        "material_survey_data_ids",
        "material_quote_request_ids",
        "job_quote_request_ids",
    )
    def _get_supplier_emails(self):
        for record in self:
            material_emails = [
                email
                for material_survey_data_id in self.material_survey_data_ids
                for email in material_survey_data_id._get_emails()
            ]
            emails = list(set(material_emails))
            string_emails = ",".join(emails)

            record.supplier_emails = string_emails

    @api.depends("material_survey_data_ids", "equipment_survey_data_ids")
    def _calc_is_allow_create_report(self):
        for record in self:
            expected_cost_report_id = self._get_expected_cost_report_id()
            if not expected_cost_report_id and self._are_all_survey_datas_approved():
                record.is_allow_create_report = True
            else:
                record.is_allow_create_report = False

    def _create_default_survey_datas(self):
        self.ensure_one()
        if not self.material_survey_data_ids:
            model_name = "docking.material.survey.metadata"
            material_survey_metadatas = self.env[model_name].search([])
            for metadata in material_survey_metadatas:
                self._create_single_material_survey_data(metadata)

        if not self.equipment_survey_data_ids:
            model_name = "docking.equipment.survey.metadata"
            equipment_survey_metadatas = self.env[model_name].search([])
            for metadata in equipment_survey_metadatas:
                self._create_single_equipment_survey_data(metadata)

    def _create_single_material_survey_data(self, metadata):
        self.ensure_one()
        return self.env["docking.material.survey.data"].create(
            {
                "docking_plan_id": self.id,
                "material_survey_metadata_id": metadata.id,
            }
        )

    def _create_single_equipment_survey_data(self, metadata):
        self.ensure_one()
        return self.env["docking.equipment.survey.data"].create(
            {
                "docking_plan_id": self.id,
                "equipment_survey_metadata_id": metadata.id,
            }
        )

    def _get_expected_cost_report_id(self):
        report_ids = self.expected_cost_report_ids
        if report_ids:
            expected_cost_report_id = report_ids[0]
            return expected_cost_report_id
        else:
            return False

    def _are_all_survey_datas_approved(self):
        self.ensure_one()

        all_materials_approved = self._are_all_material_survey_datas_approved()
        all_equipments_approved = self._are_all_equipment_survey_datas_approved()

        return all_materials_approved and all_equipments_approved

    def _are_all_material_survey_datas_approved(self):
        self.ensure_one()

        all_materials_approved = all(
            [a._is_approved() for a in self.material_survey_data_ids]
        )
        return all_materials_approved

    def _are_all_equipment_survey_datas_approved(self):
        self.ensure_one()

        all_equipments_approved = all(
            [a._is_approved() for a in self.equipment_survey_data_ids]
        )
        return all_equipments_approved

    def create_expect_cost_report(self):
        self.ensure_one()
        return (
            self.env["docking.expected.cost.report"]
            .sudo()
            .create(
                {
                    "docking_plan_id": self.id,
                }
            )
        )

    def remove_unfinished_report_out_in_its_maintenance_scope(self):
        self.ensure_one()
        report_ids = self.equipment_survey_data_ids.maintenance_scope_report_ids
        unfinished_report_ids = report_ids.filtered(lambda e: not e.finished_at)

        for report_id in unfinished_report_ids:
            report_id.maintenance_scope_id = False

    def complete_docking_plan(self):
        self.ensure_one()
        self.is_completed = True
        two_and_a_half_years = timedelta(days=913)

        self.remove_unfinished_report_out_in_its_maintenance_scope()

        return (
            self.env["docking.docking.plan"]
            .sudo()
            .create(
                {"expected_start_date": self.expected_start_date + two_and_a_half_years}
            )
        )

    def auto_notifications_in_docking_plan(self):
        uncompleted_plans = self.search(
            [
                ("is_completed", "=", False),
            ]
        )

        for record in uncompleted_plans:
            is_need_fill_in = record._is_expected_start_date_within(days=14)
            noti_before_3_months = record._is_expected_start_date_within(days=90)
            noti_before_6_months = record._is_expected_start_date_within(days=180)

            if is_need_fill_in:
                record._need_fill_in_start_date_notification()

            if noti_before_3_months:
                if not record.is_3_months_noti_off:
                    record._noti_docking_plan_before_3_months()

            if noti_before_6_months:
                if not record.is_6_months_noti_off:
                    record._noti_docking_plan_before_6_months()

    def _is_expected_start_date_within(self, days=0):
        self.ensure_one()
        today = fields.Date.today()
        expected_start_date = self.expected_start_date

        date_difference = (expected_start_date - today).days
        greater_than_today = date_difference <= days
        if not self.start_date and greater_than_today:
            return True
        return False

    def _need_fill_in_start_date_notification(self):
        self.ensure_one()
        default_value_model = self._get_default_value_model()
        variable_name = CONST_UTILITIES.USERS_DOCKING_DOCKING_PLAN_FILL_IN_START_DATE
        user_ids = default_value_model._get_default_value_by_variable_name(
            variable_name
        )

        classes = "title_docking_date_color"
        subject = "Thiếu ngày docking cho kế hoạch Docking!!"
        message = f"Bản ghi {self.ref}({self.expected_start_date}) cần điền ngày Docking thực tế!!!"

        for user in user_ids:
            self._send_notification_by_user(user, subject, message, classes)

    def _noti_docking_plan_before_3_months(self):
        self.ensure_one()
        default_value_model = self._get_default_value_model()
        variable_name = CONST_UTILITIES.USERS_DOCKING_DOCKING_PLAN_NOTI_BEFORE_3_MONTHS
        user_ids = default_value_model._get_default_value_by_variable_name(
            variable_name
        )

        classes = "title_docking_date_color"
        subject = "Chuẩn bị docking cho 3 tháng tới!!"
        message = f"3 tháng tới đến ngày {self.expected_start_date} dự kiến có docking, người dùng kiểm tra và chuẩn bị các hạng mục!!!"

        for user in user_ids:
            self._send_notification_by_user(user, subject, message, classes)

    def _noti_docking_plan_before_6_months(self):
        self.ensure_one()
        default_value_model = self._get_default_value_model()
        variable_name = CONST_UTILITIES.USERS_DOCKING_DOCKING_PLAN_NOTI_BEFORE_6_MONTHS
        user_ids = default_value_model._get_default_value_by_variable_name(
            variable_name
        )

        classes = "title_docking_date_color"
        subject = "Chuẩn bị docking cho 6 tháng tới!!"
        message = f"6 tháng tới đến ngày {self.expected_start_date} dự kiến có docking, user kiểm tra và chuẩn bị các hạng mục quan trọng cần làm trước!!!"

        for user in user_ids:
            self._send_notification_by_user(user, subject, message, classes)

    def _get_default_value_model(self):
        model_name = "utilities.default.value"
        default_value_model = self.env[model_name].search([])

        return default_value_model

    def _get_expected_start_date(self):
        default_value_model = self._get_default_value_model()
        variable_name = CONST_UTILITIES.DATE_DOCKING_DOCKING_PLAN_EXPECTED_DATE
        return default_value_model._get_default_value_by_variable_name(variable_name)

    def create_inspection_event(self):
        self.ensure_one()
        model_name = "docking.inspection.event.metadata"
        inspection_event_metadata_ids = self.env[model_name].search([])
        if self.start_date and not self.inspection_event_ids:
            for metadata in inspection_event_metadata_ids:
                day_no = metadata.days_after_real_docking_start_date
                start_date = self.start_date

                self.env["docking.inspection.event"].create(
                    {
                        "docking_plan_id": self.id,
                        "inspection_event_metadata_id": metadata.id,
                        "inspection_date": self._plus_date(start_date, day_no),
                    }
                )

    @api.depends("inspection_event_ids")
    def _get_inspection_event_len(self):
        for record in self:
            record.inspection_event_len = len(self.inspection_event_ids)

    def create_cost_settlement_reports(self):
        self.ensure_one()
        supplier_ids = self._get_unique_suppliers_ids_from_quotes()
        for supplier_id in supplier_ids:
            self.env["docking.cost.settlement.report"].create(
                {
                    "docking_plan_id": self.id,
                    "supplier_id": supplier_id,
                }
            )

    def _get_unique_suppliers_ids_from_quotes(self):
        self.ensure_one()
        supplier_ids = self._get_suppliers_ids_from_job_quotes()
        supplier_ids += self._get_supplisers_ids_from_material_quotes()
        supplier_ids = list(set(supplier_ids))
        return supplier_ids

    def _get_suppliers_ids_from_job_quotes(self):
        self.ensure_one()
        supplier_ids = []
        # loop over the list of job quote requests
        for quote_request in self.job_quote_request_ids:
            for quote in quote_request.job_quote_ids:
                # if there is a selected job supplier quote
                if quote.job_supplier_quote_id:
                    supplier_ids.append(quote.job_supplier_quote_id.supplier_id.id)
        return supplier_ids

    def _get_supplisers_ids_from_material_quotes(self):
        self.ensure_one()
        supplier_ids = []
        # loop over the list of material quote requests
        for quote_request in self.material_quote_request_ids:
            for quote in quote_request.material_quote_ids:
                # if there is a selected material supplier quote
                if quote.material_supplier_quote_id:
                    supplier_ids.append(quote.material_supplier_quote_id.supplier_id.id)
        return supplier_ids
    
    def download_sample_equipment_survey_data(self):
        url = str(SAMPLE_EQUIPMENT_SURVEY_DATA_URL)
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }

    @api.onchange("import_equipment_survey_data")
    def _import_equipment_survey_data(self):
        self.ensure_one()
        if self.import_equipment_survey_data is False:
            return
        logging.info(f"IMPORTING - importing equipment survey data for docking plan: {self.name}. ID: {self._origin.id}")
        try:
            workbook = openpyxl.load_workbook(   
                filename=BytesIO(
                    base64.b64decode(self.import_equipment_survey_data)
                ),
                read_only=True
            )
            ws = workbook.active
            new_equipment_survey_metadata_dict = {}
            # read from the row number 4
            for row in ws.iter_rows(min_row=4):
                # break loop the row if the 2nd cell is empty
                # means the end of the data
                if not row[1].value:
                    break
                equipment_survey_metadata_name = \
                    row[1].value.strip() if row[1].value else ""
                equipment_survey_metadata_description = \
                    row[2].value.strip() if row[2].value else ""

                # get or create a new equipment survey metadata
                equipment_survey_metadata, is_new = self._create_or_get_equipment_survey_metadata(
                    equipment_survey_metadata_name,
                    equipment_survey_metadata_description,
                )
                if is_new and equipment_survey_metadata.id not in new_equipment_survey_metadata_dict:
                    new_equipment_survey_metadata_dict[
                        equipment_survey_metadata.id
                    ] = equipment_survey_metadata
                # get or create a new maintenance scope
                maintenance_scope_name = \
                    row[3].value.strip() if row[3].value else ""
                maintenance_scope_description = \
                    row[4].value.strip() if row[4].value else ""
                maintenance_scope = self._create_or_get_maintainance_scope(
                    equipment_survey_metadata,
                    maintenance_scope_name,
                    maintenance_scope_description,
                )
                # get or create a new job
                job_name = row[5].value.strip() if row[5].value else ""
                job_description = row[6].value.strip() if row[6].value else ""
                self._create_or_get_job(
                    maintenance_scope,
                    job_name,
                    job_description,
                )
            
            # create new equipment survey datas after importing
            self._create_equipment_survey_datas_by_metadata_dict(
                new_equipment_survey_metadata_dict
            )

        except Exception as e:
            logging.error("error when importing equipment survey data: %s", e)
            raise UserError(_('Please insert a valid file'))
        finally:
            # clear the binary field after importing
            self.import_equipment_survey_data = False

    def _create_or_get_equipment_survey_metadata(self, name, description):
        self.ensure_one()
        is_new = False
        if not name:
            raise UserError(_("Equipment survey metadata name is required"))
        search_conditions = [
            ("name", "=", name),
        ]
        if description:
            search_conditions.append(("description", "=", description))
        equipment_survey_metadata = self.env["docking.equipment.survey.metadata"].search(
            search_conditions,
            order="id asc",
        )
        if not equipment_survey_metadata:
            logging.info(f"IMPORTING - equipment survey metadata name: {name} does not exist, creating a new one")
            equipment_survey_metadata = self.env["docking.equipment.survey.metadata"].create(
                {
                    "name": name,
                    "description": description,
                }
            )
            is_new = True
            logging.info(f"IMPORTING - created new equipment survey metadata: {name}")
        if len(equipment_survey_metadata) > 1:
            equipment_survey_metadata = equipment_survey_metadata[0]
        return equipment_survey_metadata, is_new

    def _create_or_get_maintainance_scope(self, equipment_survey_metadata, name, description):
        self.ensure_one()
        if not name:
            raise UserError(_("Maintenance scope name is required"))
        search_conditions = [
            ("name", "=", name),
            ("equipment_survey_metadata_id", "=", equipment_survey_metadata.id),
        ]
        if description:
            search_conditions.append(("description", "=", description))
        maintenance_scope = self.env["docking.maintenance.scope"].search(
            search_conditions,
            order="id asc",
        )
        if not maintenance_scope:
            logging.info("IMPORTING - maintenance scope does not exist, creating a new one")
            maintenance_scope = self.env["docking.maintenance.scope"].create(
                {
                    "name": name,
                    "description": description,
                    "equipment_survey_metadata_id": equipment_survey_metadata.id,
                }
            )
        if len(maintenance_scope) > 1:
            maintenance_scope = maintenance_scope[0]
        return maintenance_scope
    
    def _create_or_get_job(self, maintenance_scope, name, description):
        self.ensure_one()
        if not name:
            raise UserError(_("Job name is required"))
        search_conditions = [
            ("name", "=", name),
            ("maintenance_scope_id", "=", maintenance_scope.id),
        ]
        if description:
            search_conditions.append(("description", "=", description))
        job = self.env["docking.job"].search(
            [
                ("name", "=", name),
                ("maintenance_scope_id", "=", maintenance_scope.id),
            ],
            order="id asc",
        )
        if not job:
            logging.info("IMPORTING - job does not exist, creating a new one")
            job = self.env["docking.job"].create(
                {
                    "name": name,
                    "description": description,
                    "maintenance_scope_id": maintenance_scope.id,
                }
            )
        if len(job) > 1:
            job = job[0]
        return job

    def _create_equipment_survey_datas_by_metadata_dict(self, equipment_survey_metadata_dict):
        self.ensure_one()
        for metadata in equipment_survey_metadata_dict.values():
            self._origin._create_single_equipment_survey_data(metadata)
