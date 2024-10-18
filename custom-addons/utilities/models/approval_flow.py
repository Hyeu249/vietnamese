# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from collections import defaultdict
from odoo.exceptions import ValidationError
import logging
from . import CONST


class Many2ManyWithCustomOrder(fields.Many2many):
    def __init__(self, *args, **kwargs):
        super(Many2ManyWithCustomOrder, self).__init__(*args, **kwargs)
        self._order_by_field = kwargs.get("order_by_field", None)

    def read(self, records):
        context = {"active_test": False}
        context.update(self.context)
        comodel = records.env[self.comodel_name].with_context(**context)
        domain = self.get_domain_list(records)
        comodel._flush_search(domain)
        wquery = comodel._where_calc(domain)
        comodel._apply_ir_rules(wquery, "read")
        order_by = comodel._generate_order_by(None, wquery)
        # overwrite order_by if order_by_field is specified
        if self._order_by_field:
            order_by = f" ORDER BY {self._order_by_field}"
        from_c, where_c, where_params = wquery.get_sql()
        query = """ SELECT {rel}.{id1}, {rel}.{id2} FROM {rel}, {from_c}
                    WHERE {where_c} AND {rel}.{id1} IN %s AND {rel}.{id2} = {tbl}.id
                    {order_by}
                """.format(
            rel=self.relation,
            id1=self.column1,
            id2=self.column2,
            tbl=comodel._table,
            from_c=from_c,
            where_c=where_c or "1=1",
            order_by=order_by,
        )
        where_params.append(tuple(records.ids))

        # retrieve lines and group them by record
        group = defaultdict(list)
        records._cr.execute(query, where_params)
        for row in records._cr.fetchall():
            group[row[0]].append(row[1])

        # store result in cache
        values = [tuple(group[id_]) for id_ in records._ids]
        records.env.cache.insert_missing(records, self, values)


class ApprovalFlow(models.Model):
    _name = "utilities.approval.flow"
    _description = "Approval flow records"
    _inherit = ["utilities.notification"]

    name = fields.Char("Name", tracking=True)
    description = fields.Text("Description", tracking=True)
    model_name = fields.Char("Model name", tracking=True)
    is_secondary = fields.Boolean("Is secondary", tracking=True)
    approval_flow_type = fields.Selection(
        CONST.APPROVAL_FLOW_TYPES,
        string="Approval flow type",
        default=CONST.APPROVAL_FLOW_TYPE_SURVEY,
        tracking=True,
    )

    approval_level_ids = Many2ManyWithCustomOrder(
        "utilities.approval.level",
        relation="utilities_approval_level_ordering",
        column1="approval_flow_id",
        column2="approval_level_id",
        order_by_field="utilities_approval_level_ordering.id",
        string="Approval levels",
    )
    instant_approve_role_ids = fields.Many2many(
        "res.groups",
        string="Instant approve role",
        tracking=True,
        domain="[('category_id.name', '=', \"Ship Roles\")]",
    )

    def has_duplicates(self, list):
        counts = {}
        for item in list:
            if item in counts:
                return True
            counts[item] = 1
        return False

    def _get_all_flow_types_that_not_allow_duplicate(self):
        result = self.search([])
        flow_types = [
            record.approval_flow_type
            for record in result
            if not record._is_survey_flow_type()
        ]
        return flow_types

    def _is_survey_flow_type(self):
        self.ensure_one()
        survey_type = self.approval_flow_type == CONST.APPROVAL_FLOW_TYPE_SURVEY
        blank_type = self.approval_flow_type == False
        return survey_type or blank_type

    @api.constrains("approval_flow_type")
    def _prevent_restricted_flow_type_duplication(self):
        flow_types = self._get_all_flow_types_that_not_allow_duplicate()
        if self.has_duplicates(flow_types):
            message = "Loại flow hiện tại không được trùng lập, vui lòng liên hệ quản trị viên!"
            raise ValidationError(message)

    @api.model_create_multi
    def create(self, vals_list):
        result = super(ApprovalFlow, self).create(vals_list)
        for record in result:
            approval_level_ids = record.approval_level_ids
            if approval_level_ids:
                for index, approval_level in enumerate(approval_level_ids):
                    self.env["utilities.approval.level.ordering"].search(
                        [
                            ("approval_level_id", "=", approval_level.id),
                            ("approval_flow_id", "=", record.id),
                        ],
                        limit=1,
                    ).write({"ordering": index})
        return result

    def unlink(self):
        for record in self:
            # delete all approval level ordering
            self.env["utilities.approval.level.ordering"].search(
                [("approval_flow_id", "=", record.id)]
            ).unlink()
        return super(ApprovalFlow, self).unlink()

    def write(self, vals):
        self.ensure_one()
        result = super(ApprovalFlow, self).write(vals)
        # if aproval level order is changed, update ordering
        if "approval_level_ids" in vals:
            approval_level_ids = vals["approval_level_ids"][0]
            self.update_approval_level_ordering(approval_level_ids)
        return result

    def update_approval_level_ordering(self, approval_level_ids):
        approval_level_id_list_loc = 2
        # remove all approval level ordering
        self.env["utilities.approval.level.ordering"].search(
            [("approval_flow_id", "=", self.id)]
        ).unlink()
        # create new approval level ordering
        for index, approval_level in enumerate(
            approval_level_ids[approval_level_id_list_loc]
        ):
            self.env["utilities.approval.level.ordering"].create(
                {
                    "approval_level_id": approval_level,
                    "approval_flow_id": self.id,
                    "ordering": index,
                }
            )

    def get_next_approval_level(self, current_approval_level_id):
        self.ensure_one()
        # get current approval level index
        current_approval_level_index = self._get_approval_level_index(
            current_approval_level_id
        )
        # get next approval level index
        next_approval_level_index = current_approval_level_index + 1
        # get next approval level
        next_approval_level = self._get_approval_level_by_index(
            next_approval_level_index
        )
        return next_approval_level

    def get_previous_approval_level(self, current_approval_level_id):
        self.ensure_one()
        # get current approval level index
        current_approval_level_index = self._get_approval_level_index(
            current_approval_level_id
        )
        # get previous approval level index
        previous_approval_level_index = current_approval_level_index - 1
        # get previous approval level
        previous_approval_level = self._get_approval_level_by_index(
            previous_approval_level_index
        )
        return previous_approval_level

    def is_last_approval_level(self, current_approval_level_id):
        self.ensure_one()
        # get current approval level index
        current_approval_level_index = self._get_approval_level_index(
            current_approval_level_id
        )
        # get last approval level index
        last_approval_level_index = len(self.approval_level_ids) - 1
        return current_approval_level_index == last_approval_level_index

    def get_first_approval_level(self):
        self.ensure_one()
        if len(self.approval_level_ids) == 0:
            raise ValidationError("There is no approval level!")
        return self.approval_level_ids[0]

    def _get_approval_level_index(self, approval_level_id):
        self.ensure_one()
        approval_level_ids = self.approval_level_ids.ids
        return approval_level_ids.index(approval_level_id)

    def _get_approval_level_by_index(self, index):
        self.ensure_one()
        approval_level_ids = self.approval_level_ids
        if index < len(approval_level_ids) and index >= 0:
            return approval_level_ids[index]
        raise ValidationError("Index out of range!")
