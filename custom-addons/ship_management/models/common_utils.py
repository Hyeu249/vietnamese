import random
import string
from . import CONST
from odoo.fields import Date
import datetime
import logging


def generate_token():
    # generate a unique token using random.choices
    return "".join(
        random.choices(
            string.ascii_uppercase + string.digits, k=CONST.ACCESS_TOKEN_LENGTH
        )
    )


def format_field_date(date: Date, from_format="%Y-%m-%d", to_format: str = "%d/%m/%Y"):
    """
    Format a date field to a specific format
    :param date: the date field
    :param from_format: the format of the date field
    :param to_format: the format to convert to
    :return: the formatted date if the date field is valid, otherwise return an empty string
    """
    try:
        date_str = Date.to_string(date)
        to_datetime = datetime.datetime.strptime(date_str, from_format)
        return to_datetime.strftime(to_format)
    except Exception as e:
        logging.error(e)
        return ""
