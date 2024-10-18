# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
import logging


class Table(models.Model):
    _name = "vietnamese.table"
    _description = "Table records"
    _inherit = ["mail.thread"]

    model = fields.Char(
        "Model name",
        default=lambda self: self._get_model_name(),
        tracking=True,
        required=True,
    )
    name = fields.Char("Name", required=True, tracking=True)
    prefix = fields.Char("Prefix", tracking=True)
    is_show_settings = fields.Boolean("Is show settings")

    # relations
    parent_menu_id = fields.Many2one(
        "ir.ui.menu",
        string="Parent menu",
        default=lambda self: self.env.ref("vietnamese.menu_vietnamese_tables"),
        domain="[('parent_id.name', '=', 'Vietnamese')]",
        required=True,
        tracking=True,
    )
    model_id = fields.Many2one(
        "ir.model",
        string="Model",
        readonly=True,
        tracking=True,
    )
    menu_id = fields.Many2one(
        "ir.ui.menu",
        string="Menu",
        readonly=True,
    )
    sequence_id = fields.Many2one(
        "ir.sequence",
        string="Sequence",
        readonly=True,
    )
    ir_model_access_ids = fields.One2many(
        "ir.model.access",
        "table_id",
        string="Access right",
        default=lambda self: self.get_default_ir_model_access_ids(),
        tracking=True,
    )
    field_ids = fields.One2many(
        "ir.model.fields",
        "table_id",
        string="Fields",
        default=lambda self: self.get_default_field_ids(),
        tracking=True,
    )
    base_automation_ids = fields.One2many(
        "base.automation",
        "table_id",
        string="Base automation",
        default=lambda self: self.get_default_base_automation_ids(),
        tracking=True,
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

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company

    def get_default_field_ids(self):
        return [
            (
                0,
                0,
                {
                    "name": "x_ref",
                    "field_description": "Code",
                    "ttype": "char",
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

    def get_default_ir_model_access_ids(self):
        return [
            (
                0,
                0,
                {
                    "name": "access_vietnamese_init_for_" + self._get_model_name(),
                    "group_id": self.env.ref("base.group_user").id,
                },
            ),
        ]

    def get_default_base_automation_ids(self):
        return [
            (
                0,
                0,
                {
                    "name": "Set sequence for model",
                    "trigger": "on_create",
                    "state": "code",
                    "code": """
                        for record in records:
                            if not record.x_ref or record.x_ref == 'New':
                                record["x_ref"] = env["ir.sequence"].next_by_code(record._name)
                        """,
                    "filter_pre_domain": "[]",
                },
            ),
        ]

    def create_tree_view_id(self, model_name):
        return self.tree_view_id.create(
            {
                "name": model_name + ".tree",
                "model": model_name,
                "arch_base": """<tree></tree>""",
            }
        )

    def create_form_view_id(self, model_name):
        return self.form_view_id.create(
            {
                "name": model_name + ".form",
                "model": model_name,
                "arch_base": """<form></form>""",
            },
        )

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

    def get_field_tags(self, field_ids):
        return [f"<field name='{field.name}'/>\n" for field in field_ids]

    def _get_model_name(self):
        model_name = "vietnamese.table"
        number_next_actual = self.sequence_id.next_by_number(model_name)

        return f"x_vietnamese.table.{number_next_actual}"

    @api.constrains("model", "model_id")
    def model_and_model_id_consistent(self):
        for record in self:
            if record.model != record.model_id.model:
                message = f"Trường model({record.model}) không nhất quán với model_id.model({record.model_id.model})!"
                raise ValidationError(message)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model = self._get_model_name()
            model_id = self.create_model(vals["name"], model)

            vals["model"] = model
            vals["model_id"] = model_id.id
            vals["tree_view_id"] = self.create_tree_view_id(model).id
            vals["form_view_id"] = self.create_form_view_id(model).id
            vals["ref"] = self.env["ir.sequence"].next_by_code("vietnamese.table")

        result = super(Table, self).create(vals_list)

        for record in result:
            record.create_menu()
            record.create_sequence()
            record.set_name_get_field()

        return result

    def set_name_get_field(self):
        self.ensure_one()
        x_name_field = self.model_id.field_id.filtered(
            lambda self: self.name == "x_name"
        )

        x_name_field.field_description = "Name select"
        x_name_field.store = False
        self.update_name_select_depends()
        x_name_field.compute = """
for record in self:
    table_id = self.env["vietnamese.table"].search([("model", "=", record._name)])
    sorted_field_ids = table_id.field_ids.sorted(key=lambda self: self.sequence)
    name_select_ids = sorted_field_ids.filtered(lambda self: self.name_select)
    field_names = []
    for field_name in name_select_ids.mapped("name"):
        field_names.append(str(record[field_name]))
    record['x_name'] = "-".join(field_names)
        """

    def update_name_select_depends(self):
        self.ensure_one()
        x_name_field = self.model_id.field_id.filtered(
            lambda self: self.name == "x_name"
        )
        depend_ids = self.field_ids.filtered(lambda self: self.name_select)
        x_name_field.depends = ", ".join(depend_ids.mapped("name"))

    def remove_name_select_depends(self):
        x_name_field = self.model_id.field_id.filtered(
            lambda self: self.name == "x_name"
        )
        x_name_field.depends = ""

    def write(self, vals):
        self.ensure_one()
        result = super(Table, self).write(vals)

        if "model" in vals:
            raise ValidationError("Không được sửa trường model!")

        if "name" in vals:
            self.model_id.name = self.name
            self.menu_id.name = self.name
            self.menu_id.action.name = self.name
            self.sequence_id.name = self.name
        if "prefix" in vals:
            self.sequence_id.prefix = self.prefix
        if "parent_menu_id" in vals:
            self.menu_id.parent_id = self.parent_menu_id

        return result

    def unlink(self):
        for record in self:
            if record.model_id:
                record.tree_view_id.unlink()
                record.form_view_id.unlink()
                record.base_automation_ids.unlink()
                record.menu_id.action.unlink()
                record.menu_id.unlink()

                record.ir_model_access_ids.unlink()
                record.sequence_id.unlink()

                record.remove_name_select_depends()
                record.model_id.unlink()
        return super(Table, self).unlink()

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result

    def create_model(self, name, model):
        return self.model_id.create(
            {
                "name": name,
                "model": model,  # Model name with 'x_' prefix
                "state": "manual",
            }
        )

    def create_model_act_window(self, tree_view="", form_view=""):
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

    def create_sequence(self):
        # Create a sequence
        self.sequence_id = self.env["ir.sequence"].create(
            {
                "name": self.name,
                "code": self.model,
                "prefix": self.prefix,
                "padding": 2,
            }
        )

    def toggle_advanced_settings(self):
        self.ensure_one()
        if self.is_show_settings:
            self.is_show_settings = False
        else:
            self.is_show_settings = True


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

    # relations
    table_id = fields.Many2one("vietnamese.table")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            table_id = vals.get("table_id")
            table_id = self.env["vietnamese.table"].browse(table_id)
            model_id = vals.get("model_id")

            if table_id.model_id and not model_id:
                vals["model_id"] = table_id.model_id.id

        return super(IrModelAccess, self).create(vals_list)


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    def next_by_number(self, sequence_code):
        sequence = self.env["ir.sequence"].search(
            [("code", "=", sequence_code)], limit=1
        )
        return sequence.number_next_actual


class IrModelFields(models.Model):
    _inherit = "ir.model.fields"

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
    sequence = fields.Integer("Sequence")
    meta_field = fields.Boolean("Meta field")
    hide_tree_view = fields.Boolean("Hide tree view")
    hide_form_view = fields.Boolean("Hide form view")
    name_select = fields.Boolean("Name select")

    # relations
    table_id = fields.Many2one("vietnamese.table")

    # retrieve field types defined by the framework only (not extensions)
    FIELD_TYPES = [(key, key) for key in sorted(fields.Field.by_type)]

    def _get_dynamic_ttype_selection(self):
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

    def _get_relation_selection(self):
        table_ids = self.env["vietnamese.table"].search([])
        selection = [(table_id.model, table_id.name) for table_id in table_ids]

        return selection

    def get_name(self):
        return self.env["ir.sequence"].next_by_code(self._name)

    @api.onchange("relation_selection")
    def _onchange_relation_selection(self):
        self.relation = self.relation_selection

    def create_new_relation_field(self, one2many_table_id, many2one_table_id):
        name = self.env["ir.sequence"].next_by_code("relation_field")

        relation_field = self.create(
            {
                "table_id": many2one_table_id.id,
                "model_id": many2one_table_id.model_id.id,
                "name": name,
                "field_description": one2many_table_id.name,
                "ttype": "many2one",
                "relation": one2many_table_id.model,
            },
        )
        return relation_field.name

    def remove_relation_field(self, relation_field_name):
        return self.search([("name", "=", relation_field_name)]).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("table_id"):
                self.set_model_id_based_on_table_id(vals)
                self.set_default_relation_for_many2one_type(vals)
                self.set_default_relation_for_one2many_type(vals)

        result = super(IrModelFields, self).create(vals_list)

        for record in result:
            if record.table_id:
                record.table_id.update_arch_base_tree_view()
                record.table_id.update_arch_base_form_view()

        return result

    def write(self, vals):
        old_relation_fields = self.onchange_one2many_relation_value(vals)
        result = super(IrModelFields, self).write(vals)

        for relation_field in old_relation_fields:
            self.remove_relation_field(relation_field)

        for record in self:
            if "name_select" in vals:
                record.table_id.update_name_select_depends()

            if (
                "sequence" in vals
                or "field_description" in vals
                or "hide_tree_view" in vals
                or "hide_form_view" in vals
                or "meta_field" in vals
            ):
                if record.table_id:
                    record.table_id.update_arch_base_tree_view()
                    record.table_id.update_arch_base_form_view()

        return result

    def unlink(self):
        for record in self:
            if record.name == "x_ref":
                raise ValidationError("Không được xóa trường x_ref!")

            if record.name == "x_name" and record.table_id:
                raise ValidationError("Không được xóa trường x_name!")

        table_ids = self.mapped("table_id")
        for table_id in table_ids:
            table_id.tree_view_id.arch_base = """<tree></tree>"""
            table_id.form_view_id.arch_base = """<form></form>"""

        result = super(IrModelFields, self).unlink()

        for table_id in table_ids:
            table_id.update_arch_base_tree_view()
            table_id.update_arch_base_form_view()

        return result

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

    def set_model_id_based_on_table_id(self, vals):
        table_id = self.env["vietnamese.table"].browse(vals.get("table_id"))
        if not vals.get("model_id"):
            vals["model_id"] = table_id.model_id.id

    def set_default_relation_for_many2one_type(self, vals):
        if vals.get("ttype") == "many2one" and not vals.get("relation"):
            table_id = self.env["vietnamese.table"].browse(vals.get("table_id"))
            vals["relation"] = table_id.model_id.model

    def set_default_relation_for_one2many_type(self, vals):
        table_id = self.env["vietnamese.table"].browse(vals.get("table_id"))
        relation = vals.get("relation")
        relation_field = vals.get("relation_field")

        if vals.get("ttype") == "one2many" and not relation and not relation_field:
            vals["relation"] = table_id.model_id.model
            vals["relation_field"] = self.create_new_relation_field(table_id, table_id)

    def get_table_by_model_name(self, model):
        return self.env["vietnamese.table"].search([("model", "=", model)], limit=1)

    def onchange_one2many_relation_value(self, vals):
        old_relation_fields = []

        for record in self:
            if record.ttype != "one2many" or not record.table_id:
                return []

            new_model = vals.get("relation")
            relation_field = vals.get("relation_field")
            many2one_table_id = self.get_table_by_model_name(new_model)

            if new_model and new_model != record.relation and not relation_field:
                old_relation_fields.append(record.relation_field)
                vals["relation_field"] = self.create_new_relation_field(
                    record.table_id, many2one_table_id
                )

            if "relation" in vals and not new_model:
                raise ValidationError("Không để trống trường relation!")

        return old_relation_fields


class BaseAutomation(models.Model):
    _inherit = "base.automation"

    # relations
    table_id = fields.Many2one("vietnamese.table")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            table_id = vals.get("table_id")
            table_id = self.env["vietnamese.table"].browse(table_id)
            model_id = vals.get("model_id")

            if table_id.model_id and not model_id:
                vals["model_id"] = table_id.model_id.id

        return super(BaseAutomation, self).create(vals_list)


class IrModelSelection(models.Model):
    _inherit = "ir.model.fields.selection"

    value = fields.Char(
        required=True,
        default=lambda self: self.get_value(),
    )

    def get_value(self):
        return self.env["ir.sequence"].next_by_code(self._name)
