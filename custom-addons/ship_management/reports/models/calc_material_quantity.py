from odoo import models
import copy
from ...models import CONST
from odoo.exceptions import ValidationError


class CalcMaterialQuantity(models.AbstractModel):
    _name = "report.cacl.material.quantity"
    _description = "Cacl material quantity records"

    def _get_begining_stock(self, material_id, start_date):
        result = self.env["ship.material.entity"].read_group(
            [
                ("material_id", "=", material_id),
                ("create_date", "<", start_date),
                "|",
                ("discard_date", ">", start_date),
                ("discard_date", "=", False),
            ],
            ["quantity:sum"],
            ["material_id"],
        )
        if result:
            history = result[0]
            return history.get("quantity", 0)
        else:
            return 0

    def _get_ROB_stock(self, material_id, start_date, end_date):
        material = self.env["ship.material"].browse(material_id)

        result = self.env["ship.material.entity"].read_group(
            [
                ("material_id", "=", material_id),
                ("create_date", "<=", end_date),
                ("is_discarded", "=", False),
            ],
            ["quantity:sum"],
            ["material_id"],
        )
        if result:
            history = result[0]
            quantity = history.get("quantity", 0)

            if not material.is_used_for_lifespan:
                quantity = quantity - self._get_total_consumed_for_consumable_material(
                    material_id, start_date, end_date
                )

            return quantity
        else:
            return 0

    def _get_receiving_in_month(self, material_id, start_date, end_date):
        result = self.env["ship.material.entity"].read_group(
            [
                ("material_id", "=", material_id),
                ("create_date", ">=", start_date),
                ("create_date", "<=", end_date),
            ],
            ["quantity:sum"],
            ["material_id"],
        )
        if result:
            history = result[0]
            return history.get("quantity", 0)
        else:
            return 0

    def _get_total_consumed(self, material_id, start_date, end_date):
        material = self.env["ship.material"].browse(material_id)

        if not material.is_used_for_lifespan:
            return self._get_total_consumed_for_consumable_material(
                material_id, start_date, end_date
            )
        else:
            return self._get_total_consumed_for_normal_material(
                material_id, start_date, end_date
            )

    def _get_total_consumed_for_consumable_material(
        self, material_id, start_date, end_date
    ):
        result = self.env["ship.material.assignment"].read_group(
            [
                ("material_id", "=", material_id),
                ("start_time_of_use", ">=", start_date),
                ("start_time_of_use", "<=", end_date),
            ],
            ["quantity:sum"],
            ["material_id"],
        )

        if result:
            history = result[0]
            return history.get("quantity", 0)
        else:
            return 0

    def _get_total_consumed_for_normal_material(
        self, material_id, start_date, end_date
    ):
        result = self.env["ship.material.entity"].read_group(
            [
                ("material_id", "=", material_id),
                ("discard_date", ">=", start_date),
                ("discard_date", "<=", end_date),
                ("is_discarded", "=", True),
            ],
            ["quantity:sum"],
            ["material_id"],
        )

        if result:
            history = result[0]
            return history.get("quantity", 0)
        else:
            return 0
