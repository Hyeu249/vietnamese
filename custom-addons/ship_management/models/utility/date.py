# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models
from datetime import datetime, timedelta
import calendar
from odoo.exceptions import ValidationError
from .. import CONST


class Date(models.Model):
    _name = "ship.date"
    _description = "Date records"
    _inherit = ["utilities.notification"]

    def _get_week_number(self, target_date):
        week_number = int(self.get_monday_of_its_week(target_date).strftime("%W"))
        return week_number

    def get_monday_of_its_week(self, input_date):
        day_of_week = input_date.weekday()
        monday_of_current_week = input_date - timedelta(days=day_of_week)
        return monday_of_current_week

    def get_sunday_of_its_week(self, input_date):
        day_of_week = input_date.weekday()
        sunday_of_current_week = input_date + timedelta(days=(6 - day_of_week))
        return sunday_of_current_week

    def get_last_date_of_its_month(self, input_date):
        _, last_day_of_month = calendar.monthrange(input_date.year, input_date.month)
        last_date_of_month = datetime(
            input_date.year, input_date.month, last_day_of_month
        )
        return last_date_of_month.date()

    def get_last_date_of_next_month(self, input_date):
        day_of_month = input_date.day
        days_for_over_month = 32 - day_of_month
        next_month = input_date + timedelta(days=days_for_over_month)
        last_date_of_next_month = self.get_last_date_of_its_month(next_month)
        return last_date_of_next_month

    def get_last_date_of_previous_month(self, input_date):
        last_date_of_previous_month = input_date.replace(day=1) - timedelta(days=1)
        return last_date_of_previous_month

    def _plus_date(self, target_date, days, return_type=CONST.DATE):
        if not target_date:
            raise ValidationError("Date is required!")
        date_format = "%Y-%m-%d"
        target_datetime = datetime.strptime(str(target_date), date_format)
        target_date = target_datetime + timedelta(days=days)
        if return_type == CONST.STR:
            return target_date.strftime(date_format)
        elif return_type == CONST.DATE:
            return target_date.date()

    def _minus_date(self, target_date, days, return_type=CONST.DATE):
        if not target_date:
            raise ValidationError("Date is required!")
        date_format = "%Y-%m-%d"
        target_datetime = datetime.strptime(str(target_date), date_format)
        target_date = target_datetime - timedelta(days=days)
        if return_type == CONST.STR:
            return target_date.strftime(date_format)
        elif return_type == CONST.DATE:
            return target_date.date()
