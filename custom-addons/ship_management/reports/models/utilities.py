from odoo import models
import copy
from ...models import CONST
from io import BytesIO


class Utilities(models.AbstractModel):
    _name = "report.utilities"
    _description = "Utilities records"

    def _get_image_by_path(self, image_path="/mnt/extra-addons/images/vsico-1.png"):

        with open(image_path, "rb") as f:
            image_data = f.read()

        image_stream = BytesIO(image_data)

        return image_stream

    def get_normal_format(
        self,
        bold=True,
        align="center",
        # font_name="Arial",
        font_name="Times New Roman",
        italic=False,
        bg_color=False,
        border=False,
        right=False,
        left=False,
        bottom=False,
        top=False,
        font_size=10,
        text_wrap=True,
    ):
        base_format = {
            "font_name": font_name,
            "font_size": font_size,
            "valign": "vcenter",
            "bold": bold,
            "italic": italic,
            "text_wrap": text_wrap,
        }

        if bg_color:
            base_format["bg_color"] = bg_color

        if border:
            base_format["border"] = border

        if right:
            base_format["right"] = right

        if top:
            base_format["top"] = top

        if left:
            base_format["left"] = left

        if bottom:
            base_format["bottom"] = bottom

        if align != False:
            base_format["align"] = align

        return base_format
