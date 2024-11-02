# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, Command
from . import CONST
from odoo.exceptions import ValidationError
import logging


class IrModel(models.Model):
    _inherit = "ir.model"

    def get_default_field_ids(self):
        return [
            (
                0,
                0,
                {
                    "name": "x_ref",
                    "field_description": "Code",
                    "ttype": "char",
                    "default_char": "New",
                    "name_select": True,
                },
            ),
            (
                0,
                0,
                {
                    "sequence": 1,
                    "name": "x_name_copy",
                    "field_description": "Name",
                    "ttype": "char",
                    "name_select": True,
                },
            ),
        ]

    name = fields.Char(string="Name", required=True)
    model = fields.Char(default=lambda self: self._get_model_name(), required=True)

    prefix_name = fields.Char(string="Prefix name")
    vietnamese_custom_table = fields.Boolean(string="Vietnamese custom table")

    # relations
    field_ids = fields.One2many(
        "ir.model.fields",
        "vietnamese_model_id",
        string="Fields",
        default=get_default_field_ids,
        tracking=True,
    )
    sequence_id = fields.Many2one(
        "ir.sequence",
        string="Sequence",
        readonly=True,
    )
    sequence_base_automation_id = fields.Many2one(
        "base.automation",
        string="Sequence base automation",
        readonly=True,
    )
    tree_view_id = fields.Many2one(
        "ir.ui.view",
        string="Tree view",
        readonly=True,
    )
    form_view_id = fields.Many2one(
        "ir.ui.view",
        string="Form view",
        readonly=True,
    )
    search_view_id = fields.Many2one(
        "ir.ui.view",
        string="Search view",
        readonly=True,
    )

    parent_menu_id = fields.Many2one(
        "ir.ui.menu",
        string="Parent menu",
        # default=lambda self: self.env.ref("vietnamese.menu_vietnamese_tables"),
        domain="[('parent_id.name', '=', 'Vietnamese')]",
        required=True,
    )

    menu_id = fields.Many2one(
        "ir.ui.menu",
        string="Menu",
        readonly=True,
    )

    access_ids = fields.One2many(
        "ir.model.access",
        "model_id",
        string="Access right",
        default=lambda self: [
            (
                0,
                0,
                {
                    "name": "access_vietnamese_init_for_" + self._get_model_name(),
                    "group_id": self.env.ref("base.group_user").id,
                },
            ),
        ],
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["model"] = self.env["ir.sequence"].next_by_code(self._name)

        result = super(IrModel, self).create(vals_list)

        for record in result:
            record.create_sequence()
            record.create_sequence_base_automation()
            record.create_tree_view_id()
            record.create_form_view_id()
            record.create_search_view_id()
            record.update_arch_base_tree_view()
            record.update_arch_base_form_view()
            record.update_arch_base_search_view()
            record.set_name_get_field()
            record.create_menu()
            record.update_default_value()

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(IrModel, self).write(vals)

        if "name" in vals:
            self.menu_id.name = self.name
            self.menu_id.action.name = self.name
            self.sequence_id.name = self.name
        if "prefix" in vals:
            self.sequence_id.prefix = self.prefix
        if "parent_menu_id" in vals:
            self.menu_id.parent_id = self.parent_menu_id

        return result

    def unlink(self):

        return super(IrModel, self).unlink()

    def _get_model_name(self):
        sequence = self.env["ir.sequence"].search([("code", "=", self._name)])

        return f"{sequence.prefix}{sequence.number_next_actual}"

    def create_sequence(self):
        self.ensure_one()
        self.sequence_id = self.env["ir.sequence"].create(
            {
                "name": self.name,
                "code": self.model,
                "prefix": self.prefix_name,
                "padding": 2,
            }
        )

    def create_sequence_base_automation(self):
        self.ensure_one()
        self.sequence_base_automation_id = self.env["base.automation"].create(
            {
                "name": "Set sequence for model",
                "trigger": "on_create",
                "state": "code",
                "code": """
for record in records:
    record["x_ref"] = env["ir.sequence"].next_by_code(record._name)
                """,
                "model_id": self.id,
                "filter_pre_domain": "[]",
            }
        )

    def set_name_get_field(self):
        self.ensure_one()
        x_name_field = self.field_id.filtered(lambda self: self.name == "x_name")

        x_name_field.field_description = "Name select"
        x_name_field.store = False
        self.update_name_select_depends()
        x_name_field.compute = """
for record in self:
    model_id = self.env["ir.model"].search([("model", "=", record._name)])
    sorted_field_ids = model_id.field_ids.sorted(key=lambda self: self.sequence)
    name_select_ids = sorted_field_ids.filtered(lambda self: self.name_select)
    field_names = []
    for field_name in name_select_ids.mapped("name"):
        field_names.append(str(record[field_name]))
    record['x_name'] = "-".join(field_names)
        """

    def update_name_select_depends(self):
        self.ensure_one()
        x_name_field = self.field_id.filtered(lambda self: self.name == "x_name")
        depend_ids = self.field_ids.filtered(lambda self: self.name_select)
        x_name_field.depends = ", ".join(depend_ids.mapped("name"))

    def create_model_act_window(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"].create(
            {
                "name": self.name,
                "res_model": self.model,
                "type": "ir.actions.act_window",
                "view_mode": "tree,form",
                # "view_ids": [
                #     (5, 0, 0),
                #     (0, 0, {"view_id": tree_view.id, "view_mode": "tree"}),
                #     (0, 0, {"view_id": form_view.id, "view_mode": "form"}),
                # ],
                "target": "current",
                # "context": "{'create': True}",
            }
        )
        return action

    def create_menu(self):
        self.ensure_one()
        action_id = self.create_model_act_window()

        self.menu_id = self.env["ir.ui.menu"].create(
            {
                "name": self.name,
                "parent_id": self.parent_menu_id.id,
                "action": f"ir.actions.act_window,{action_id.id}",
            }
        )

    def create_tree_view_id(self):
        self.tree_view_id = self.tree_view_id.create(
            {
                "name": self.model + ".tree",
                "model": self.model,
                "arch_base": """<tree></tree>""",
            }
        )

    def create_form_view_id(self):
        self.form_view_id = self.form_view_id.create(
            {
                "name": self.model + ".form",
                "model": self.model,
                "arch_base": """<form></form>""",
            },
        )

    def create_search_view_id(self):
        self.search_view_id = self.search_view_id.create(
            {
                "name": self.model + ".search",
                "model": self.model,
                "arch_base": """<search></search>""",
            },
        )

    def update_arch_base_search_view(self):
        self.ensure_one()
        s_field_ids = self.field_ids.sorted(key=lambda self: self.sequence)
        field_tags = [f"<field name='{field.name}'/>\n" for field in s_field_ids]

        if self.search_view_id:
            self.search_view_id.arch_base = f"""
                <search>
                    {''.join(field_tags)}
                </search>
            """

    def update_arch_base_tree_view(self):
        self.ensure_one()
        s_field_ids = self.field_ids.sorted(key=lambda self: self.sequence)
        hide_field_ids = s_field_ids.filtered(lambda self: self.hide_tree_view)
        visible_field_ids = s_field_ids.filtered(lambda self: not self.hide_tree_view)

        one2many = lambda s: s.ttype == "one2many"

        field_ids = visible_field_ids.filtered(lambda s: not one2many(s))
        one2many_fields = visible_field_ids.filtered(one2many)

        field_tags = [f"<field name='{field.name}'/>\n" for field in field_ids]
        one2many_tags = [
            f"<field name='{field.name}' widget='many2many_tags'/>\n"
            for field in one2many_fields
        ]
        invisible_field_tags = [
            f"<field name='{field.name}' invisible='1'/>\n" for field in hide_field_ids
        ]

        if self.tree_view_id:
            self.tree_view_id.arch_base = f"""
                <tree>
                    {''.join(field_tags)}
                    {''.join(one2many_tags)}
                    {''.join(invisible_field_tags)}
                </tree>
            """

    def update_arch_base_form_view(self):
        self.ensure_one()
        s_field_ids = self.field_ids.sorted(key=lambda self: self.sequence)
        hide_field_ids = s_field_ids.filtered(lambda self: self.hide_form_view)
        visible_field_ids = s_field_ids.filtered(lambda self: not self.hide_form_view)

        is_ref = lambda s: s.name == "x_ref"
        one2many = lambda s: s.ttype == "one2many"
        meta_field = lambda s: s.meta_field

        x_refs = visible_field_ids.filtered(is_ref)
        field_ids = visible_field_ids.filtered(
            lambda s: not is_ref(s) and not one2many(s) and not meta_field(s)
        )
        one2many_fields = visible_field_ids.filtered(one2many)
        meta_fields = visible_field_ids.filtered(
            lambda s: meta_field(s) and not one2many(s) and not is_ref(s)
        )

        x_ref_tag = self.get_x_ref_tags(x_refs)
        field_tags = self.get_field_tags(field_ids)
        one2many_pages = self.get_one2many_pages(one2many_fields)
        meta_page = self.get_meta_page(meta_fields)
        invisible_field_tags = [
            f"<field name='{field.name}'/>\n" for field in hide_field_ids
        ]

        if self.form_view_id:
            self.form_view_id.arch_base = f"""  
                <form>
                    <sheet>
                        {''.join(x_ref_tag)}
                        <group>
                            {''.join(field_tags)}
                        </group>

                        <group invisible='1'>
                            {''.join(invisible_field_tags)}
                        </group>

                        <notebook>
                            {''.join(one2many_pages)}
                            {''.join(meta_page)}
                        </notebook>
                    </sheet>
                </form>
            """

    def get_x_ref_tags(self, x_refs):
        return [
            f"""
                <div class="oe_title">
                    <h1>
                        <field name="{field.name}" readonly="1"/>
                    </h1>
                </div>
            """
            for field in x_refs
        ]

    def get_field_tags(self, field_ids):
        return [f"<field name='{field.name}'/>\n" for field in field_ids]

    def get_one2many_pages(self, one2many_fields):
        return [
            f"""
                <page string="{field.field_description}" name="{field.name}">
                    <field name="{field.name}"/>
                </page>\n
            """
            for field in one2many_fields
        ]

    def get_meta_page(self, meta_fields):
        meta_field_tags = [f"<field name='{field.name}'/>\n" for field in meta_fields]
        if meta_fields:
            return f"""
                <page string="Meta" name="meta">
                    <group>
                        {''.join(meta_field_tags)}
                    </group>
                </page>
            """
        else:
            return ""

    def update_default_value(self):
        self.ensure_one()
        if not self.menu_id:
            return

        action_id = self.menu_id.action
        context = {}

        for field in self.field_ids:
            default_name = f"default_{field.name}"
            context[default_name] = field.get_default_value()

        action_id.context = context


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    def unlink(self):
        for record in self:
            vietnamese_id = self.env.ref("vietnamese.menu_vietnamese_root")
            operation_id = self.env.ref("vietnamese.menu_vietnamese_operator")
            tables_id = self.env.ref("vietnamese.menu_vietnamese_tables")
            action_discus_id = self.env.ref("mail.action_discuss")

            if (
                record.id == vietnamese_id.id
                or record.id == operation_id.id
                or record.id == tables_id.id
            ):
                raise ValidationError(f"Không được xóa các menu gốc!")

            if (
                record.parent_id
                and record.action
                and record.parent_id.id == vietnamese_id.id
                and record.action.id == action_discus_id.id
            ):
                for child in record.child_id:
                    child.parent_id = tables_id

        return super(IrUiMenu, self).unlink()


class IrModelAccess(models.Model):
    _inherit = "ir.model.access"

    perm_read = fields.Boolean(default=True)
    perm_write = fields.Boolean(default=True)
    perm_create = fields.Boolean(default=True)
    perm_unlink = fields.Boolean(default=True)


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

    sequence = fields.Integer("Sequence")
    name = fields.Char(
        string="Field Name",
        default=lambda self: self.get_name(),
        required=True,
        index=True,
    )
    ttype = fields.Selection(
        selection="_get_dynamic_ttype_selection", string="Field Type", required=True
    )
    relation_selection = fields.Selection(
        selection="_get_relation_selection",
        string="Relation selection",
    )
    meta_field = fields.Boolean("Meta field")
    hide_tree_view = fields.Boolean("Hide tree view")
    hide_form_view = fields.Boolean("Hide form view")
    name_select = fields.Boolean("Name select")

    # default value
    default_char = fields.Char("default char")
    default_text = fields.Text("default text")
    default_integer = fields.Integer("default integer")
    default_float = fields.Float("default float")
    default_boolean = fields.Boolean("default boolean")
    default_selection = fields.Selection(
        selection="_get_dynamic_default_selection", string="default selection"
    )
    default_date = fields.Date("default date")
    default_datetime = fields.Datetime("default datetime")
    default_html = fields.Html("default html")
    default_many2one = fields.Integer("default many2one")
    default_one2many = fields.Char("default one2many")
    based_on_target = fields.Char("Based on target")

    # relations
    vietnamese_model_id = fields.Many2one("ir.model")
    base_automation_id = fields.Many2one("base.automation", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self.set_vietnamese_model_if_not_have_model(vals)

        result = super(IrModelFields, self).create(vals_list)

        for record in result:
            if record.vietnamese_model_id:
                record.vietnamese_model_id.update_arch_base_tree_view()
                record.vietnamese_model_id.update_arch_base_form_view()
                record.vietnamese_model_id.update_arch_base_search_view()
                record.vietnamese_model_id.update_default_value()

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(IrModelFields, self).write(vals)

        if "name_select" in vals:
            self.vietnamese_model_id.update_name_select_depends()

        if (
            "sequence" in vals
            or "field_description" in vals
            or "hide_tree_view" in vals
            or "hide_form_view" in vals
            or "meta_field" in vals
        ):
            if self.vietnamese_model_id:
                self.vietnamese_model_id.update_arch_base_tree_view()
                self.vietnamese_model_id.update_arch_base_form_view()
                self.vietnamese_model_id.update_arch_base_search_view()

        if (
            "default_char" in vals
            or "default_text" in vals
            or "default_integer" in vals
            or "default_float" in vals
            or "default_boolean" in vals
            or "default_selection" in vals
            or "default_date" in vals
            or "default_datetime" in vals
            or "default_html" in vals
            or "default_many2one" in vals
        ):
            self.vietnamese_model_id.update_default_value()

        return result

    def unlink(self):
        vietnamese_model_ids = self.mapped("vietnamese_model_id")

        for record in self:
            if record.name == "x_ref":
                raise ValidationError("Không được xóa trường x_ref!")

            if record.name == "x_name" and record.vietnamese_model_id:
                raise ValidationError("Không được xóa trường x_name!")

        result = super(IrModelFields, self).unlink()

        for vietnamese_model_id in vietnamese_model_ids:
            vietnamese_model_id.update_arch_base_tree_view()
            vietnamese_model_id.update_arch_base_form_view()
            vietnamese_model_id.update_arch_base_search_view()

        return result

    def get_name(self):
        return self.env["ir.sequence"].next_by_code(self._name)

    def set_vietnamese_model_if_not_have_model(self, vals):
        vietnamese_model_id = vals.get("vietnamese_model_id")
        model_id = vals.get("model_id")

        if vietnamese_model_id and not model_id:
            vals["model_id"] = vietnamese_model_id

    # retrieve field types defined by the framework only (not extensions)
    FIELD_TYPES = [(key, key) for key in sorted(fields.Field.by_type)]

    def _get_dynamic_ttype_selection(self):
        table_view = self.env.context.get("vietnamese_view")

        if table_view:
            return [
                ("char", "char"),
                ("text", "text"),
                ("integer", "integer"),
                ("float", "float"),
                ("boolean", "boolean"),
                ("selection", "selection"),
                ("date", "date"),
                ("datetime", "datetime"),
                ("html", "html"),
                ("many2one", "many2one"),
                ("one2many", "one2many"),
            ]
        else:
            return self.FIELD_TYPES

    def _get_relation_selection(self):
        model_ids = self.env["ir.model"].search(
            [("vietnamese_custom_table", "=", True)]
        )
        selection = [(model_id.model, model_id.name) for model_id in model_ids]

        return selection

    def _get_dynamic_default_selection(self):
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")

        if active_model == "ir.model.fields":
            selection_ids = self.env["ir.model.fields.selection"].search(
                [("field_id", "=", active_id)]
            )
        else:
            selection_ids = self.env["ir.model.fields.selection"].search([])

        return [(selection.value, selection.name) for selection in selection_ids]

    def open_edit_view(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "view_id": self.env.ref(
                "vietnamese.view_ir_model_fields_form_in_vietnamese"
            ).id,
            "target": "current",
            "context": self.env.context,
        }

    def get_default_value(self):
        self.ensure_one()
        if self.ttype == "char":
            return self.default_char
        if self.ttype == "text":
            return self.default_text
        if self.ttype == "integer":
            return self.default_integer
        if self.ttype == "float":
            return self.default_float
        if self.ttype == "boolean":
            return self.default_boolean
        if self.ttype == "selection":
            return self.default_selection
        if self.ttype == "date":
            return self.default_date
        if self.ttype == "datetime":
            return self.default_datetime
        if self.ttype == "html":
            return self.default_html
        if self.ttype == "many2one":
            return self.default_many2one


class BaseAutomation(models.Model):
    _inherit = "base.automation"

    @api.model_create_multi
    def create(self, vals_list):

        return super(BaseAutomation, self).create(vals_list)

    def write(self, vals):
        result = super(BaseAutomation, self).write(vals)
        return result


class IrModelSelection(models.Model):
    _inherit = "ir.model.fields.selection"

    value = fields.Char(
        required=True,
        default=lambda self: self.get_value(),
    )

    def get_value(self):
        return self.env["ir.sequence"].next_by_code(self._name)
