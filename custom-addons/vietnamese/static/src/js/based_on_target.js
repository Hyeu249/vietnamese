/** @odoo-module */

import { standardFieldProps } from "@web/views/fields/standard_field_props";
import {
  Component,
  xml,
  useState,
  onWillUpdateProps,
  onMounted,
  useRef,
  useEffect,
} from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import GetDataComponent from "./getDataComponent";

class CustomWidget extends Component {
  selectRef = useRef("select");
  setup() {
    this.default_one2many = this.props?.record?.data?.default_one2many;
    this.based_on_target = this.get_based_on_target();
    this.ttype = this.props?.record?.data?.ttype;
    const table_id = this.props?.record?.data?.table_id;
    this.current_table_id = table_id.length ? table_id[0] : false;

    this.orm = useService("orm");
    this.action = useService("action");

    useEffect(
      () => {
        this.fetchData();

        return () => {};
      },
      () => []
    );

    onWillUpdateProps(async (nextProps) => {
      this.default_one2many = nextProps.record.data.default_one2many;
      this.based_on_target = this.get_based_on_target();
      this.fetchData();
    });
  }

  async fetchData() {
    if (this.ttype !== "one2many") return;
    // if (!this.based_on_target) return;
    const option_1 = await this.get_options_1();
    const option_2 = await this.get_options_2();
    const option_tags = [...option_1, ...option_2];

    this.selectRef.el.innerHTML = option_tags.length
      ? "<option value=''></option>" + option_tags.join()
      : `<option></option>`;

    return () => {};
  }

  async get_options_1() {
    if (!this.based_on_target) return [];
    const based_on_field = await this.get_field_by_name(this.based_on_target);

    const value = `create_by_all__${this.based_on_target}`;
    const label = `Lấy tất cả ${based_on_field.field_description} để tạo`;
    const selected = value === this.props.value ? "selected" : null;

    return [
      `
      <option value="${value}" ${selected ? "selected" : ""}>
        ${label}
      </option>
      `,
    ];
  }
  async get_options_2() {
    const fields = await this.get_fields_from_current_table();
    const filtered_fields = fields.filter((e) => e.ttype === "many2one");
    const options = [];

    for (const field of filtered_fields) {
      const correspond_fields =
        await this.find_fields_that_corresponds_based_on_field(field.relation);

      for (const correspond_field of correspond_fields) {
        const value = `create_by_and_in__${correspond_field.name}__${field.name}`;
        const label = `Lấy '${correspond_field.field_description}' ở trong '${field.field_description}' để tạo`;
        const selected = value === this.props.value ? "selected" : null;

        options.push(`
          <option value="${value}" ${selected ? "selected" : ""}>
            ${label}
          </option>
        `);
      }
    }

    return options;
  }

  async find_fields_that_corresponds_based_on_field(relation) {
    const table = await this.get_table_by_model_name(relation);
    const fields = await this.get_field_by_ids(table.field_ids);
    const based_on_field = await this.get_field_by_name(this.based_on_target);
    const filtered_fields = fields.filter(
      (e) => e.ttype === "one2many" && e.relation === based_on_field.relation
    );

    return filtered_fields;
  }

  async get_fields_from_current_table() {
    const current_table = await this.get_table_by_id(this.current_table_id);
    const fields = await this.get_field_by_ids(current_table.field_ids);

    return fields;
  }

  async get_table_by_id(id) {
    const current_table_s = await this.orm.searchRead(
      "vietnamese.table",
      [["id", "=", id]],
      ["id", "field_ids"]
    );

    if (current_table_s.length) return current_table_s[0];
  }

  async get_table_by_model_name(model_name) {
    const current_table_s = await this.orm.searchRead(
      "vietnamese.table",
      [["model", "=", model_name]],
      []
    );

    if (current_table_s.length) return current_table_s[0];
  }

  async get_field_by_ids(ids) {
    const fields = await this.orm.searchRead(
      "ir.model.fields",
      [["id", "=", ids]],
      []
    );

    if (fields.length) return fields;
  }

  async get_field_by_name(name) {
    const fields = await this.orm.searchRead(
      "ir.model.fields",
      [["name", "=", name]],
      []
    );

    if (fields.length) return fields[0];
    return {};
  }

  get_based_on_target() {
    if (
      typeof this.default_one2many !== "string" ||
      this.default_one2many.length <= 0
    ) {
      return;
    }

    return this.default_one2many.split("__")[4];
  }

  updateValue(event) {
    const value = event.target.value;
    this.props.update(value);
  }
}

CustomWidget.template = xml`
    <select t-ref="select" t-on-change="updateValue" style="border: none;">
    </select>
`;

CustomWidget.props = {
  ...standardFieldProps,
};
CustomWidget.supportedTypes = ["char"];

registry.category("fields").add("based_on_target", CustomWidget);
